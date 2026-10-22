"""ETF profiles from Yahoo fund data (BL-083). Weekly; numbers are stored as published.

Yahoo publishes the top 10 holdings and sector weights for most UCITS listings. TER
comes from the annual report figure. Country weights are not published there and stay
empty until another source fills them.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from preza.data.symbols import yahoo_symbol
from preza.models import EtfProfile, Instrument, Position, WatchlistItem

log = logging.getLogger(__name__)

SOURCE = "yahoo"
TER_ROW = "Annual Report Expense Ratio"


@dataclass
class ProfileIn:
    as_of: date
    ter: Decimal | None = None
    index_name: str | None = None
    distribution: str | None = None
    holdings: list[dict[str, Any]] = field(default_factory=list)
    sectors: dict[str, float] = field(default_factory=dict)
    source: str = SOURCE

    @property
    def coverage(self) -> Decimal | None:
        if not self.holdings:
            return None
        return Decimal(str(round(sum(h["weight"] for h in self.holdings), 4)))


def distribution_from_name(name: str | None) -> str | None:
    """UCITS share class names say it: "(Acc)" or "(Dist)"."""
    if not name:
        return None
    match = re.search(r"\b(acc|dist)\b", name, re.IGNORECASE)
    return match.group(1).lower() if match else None


def _number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return None if pd.isna(number) else number


def profile_from_funds(
    top_holdings: pd.DataFrame | None,
    sector_weightings: dict[str, Any] | None,
    fund_operations: pd.DataFrame | None,
    fund_overview: dict[str, Any] | None,
    instrument_name: str | None,
    today: date,
) -> ProfileIn:
    holdings = []
    if top_holdings is not None and not top_holdings.empty:
        for symbol, row in top_holdings.iterrows():
            weight = _number(row.get("Holding Percent"))
            if weight is None or weight <= 0:
                continue
            holdings.append(
                {
                    "symbol": str(symbol).upper(),
                    "name": str(row.get("Name") or ""),
                    "weight": weight,
                }
            )
    sectors = {
        str(k): w
        for k, v in (sector_weightings or {}).items()
        if (w := _number(v)) is not None and w > 0
    }
    ter = None
    if fund_operations is not None and TER_ROW in fund_operations.index:
        value = _number(fund_operations.loc[TER_ROW].iloc[0])
        if value is not None and 0 < value < 0.05:  # a fraction; anything else is a unit mix-up
            ter = Decimal(str(round(value, 6)))
    return ProfileIn(
        as_of=today,
        ter=ter,
        index_name=(fund_overview or {}).get("categoryName"),
        distribution=distribution_from_name(instrument_name),
        holdings=sorted(holdings, key=lambda h: -h["weight"]),
        sectors=sectors,
    )


def fetch_profile(instrument: Instrument, today: date) -> ProfileIn:
    """Blocking network call; run it in a thread."""
    import yfinance as yf

    funds = yf.Ticker(yahoo_symbol(instrument.symbol, instrument.exchange)).funds_data
    return profile_from_funds(
        funds.top_holdings,
        funds.sector_weightings,
        funds.fund_operations,
        funds.fund_overview,
        instrument.name,
        today,
    )


async def store_profile(session: AsyncSession, instrument: Instrument, profile: ProfileIn) -> None:
    row = await session.get(EtfProfile, instrument.id) or EtfProfile(instrument_id=instrument.id)
    row.as_of = profile.as_of
    row.ter = profile.ter
    row.index_name = profile.index_name
    row.distribution = profile.distribution
    row.holdings = profile.holdings
    row.holdings_coverage = profile.coverage
    row.sectors = profile.sectors
    row.countries = row.countries or {}
    row.source = profile.source
    row.fetched_at = datetime.now(UTC)
    session.add(row)


async def user_etfs(session: AsyncSession) -> list[Instrument]:
    held = select(Position.instrument_id)
    watched = select(WatchlistItem.instrument_id)
    return list(
        await session.scalars(
            select(Instrument).where(
                Instrument.kind == "etf",
                Instrument.id.in_(held.union(watched)),
            )
        )
    )
