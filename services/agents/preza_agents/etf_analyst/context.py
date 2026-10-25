"""Gather what the ETF analyst needs from the database (BL-083)."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from preza.models import EntryCandidate, EtfProfile, Instrument
from preza.services.portfolio import get_portfolio
from preza_agents.deep_research.snapshot import DataSnapshot
from preza_agents.etf_analyst.analyst import EtfFacts, compute_facts
from preza_agents.etf_analyst.exposure import Holding, look_through, overlap


def profile_dict(row: EtfProfile) -> dict[str, Any]:
    return {
        "as_of": row.as_of.isoformat(),
        "ter": float(row.ter) if row.ter is not None else None,
        "ter_source": row.ter_source,
        "ter_as_of": row.ter_as_of.isoformat() if row.ter_as_of is not None else None,
        "index_name": row.index_name,
        "distribution": row.distribution,
        "holdings": list(row.holdings or []),
        "sectors": dict(row.sectors or {}),
        "countries": dict(row.countries or {}),
        "source": row.source,
    }


async def build_etf_facts(
    session: AsyncSession, instrument: Instrument, snapshot: DataSnapshot, base_currency: str
) -> EtfFacts:
    own = await session.get(EtfProfile, instrument.id)
    if own is not None and own.as_of > snapshot.as_of:
        own = None  # no look-ahead in a dated run
    portfolio = await get_portfolio(session, base_currency)
    holdings = [
        Holding(symbol=p.symbol, kind=str(p.kind), weight=float(p.weight_pct) / 100)
        for p in portfolio.positions
        if p.weight_pct is not None
    ]
    weight = sum(h.weight for h in holdings if h.symbol == instrument.symbol)
    # Overlap is with the rest of the portfolio; the fund overlapping itself says nothing.
    others = [h for h in holdings if h.symbol != instrument.symbol]
    etf_symbols = [h.symbol for h in others if h.kind == "etf"]
    rows = await session.scalars(
        select(EtfProfile).join(Instrument).where(Instrument.symbol.in_(etf_symbols))
    )
    profiles = {r.instrument.symbol: list(r.holdings or []) for r in rows}
    exposure = look_through(others, profiles)
    candidate = list(own.holdings or []) if own is not None else []
    entry_row = await session.get(EntryCandidate, instrument.id)
    entry = (
        {
            "state": entry_row.state,
            "zone_low": entry_row.zone_low,
            "zone_high": entry_row.zone_high,
            "distance_atr": entry_row.distance_atr,
            "rules": [r.get("rule") for r in entry_row.rules],
        }
        if entry_row is not None
        else None
    )
    return compute_facts(
        snapshot,
        profile_dict(own) if own is not None else None,
        weight,
        overlap(candidate, exposure) if candidate else None,
        entry,
    )
