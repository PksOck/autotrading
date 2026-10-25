"""Loads the curated UCITS ETF list into `instrument` (BL-026)."""

import logging
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from importlib.resources import files
from typing import Any

import yaml
from sqlalchemy.ext.asyncio import AsyncSession

from preza.domain.market import InstrumentKind
from preza.services.instruments import get_or_create

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class UcitsFacts:
    index: str | None = None
    ter: Decimal | None = None
    ter_source: str | None = None
    ter_as_of: date | None = None


def ucits_facts(symbol: str, exchange: str | None, *, isin: str | None = None) -> UcitsFacts | None:
    """Prefer share-class identity to listing identity; ignore unverified costs."""
    rows = read_ucits()
    matches = [
        row
        for row in rows
        if (
            row.get("isin") == isin
            if isin
            else (row.get("symbol") == symbol and row.get("exchange") == exchange)
        )
    ]
    if not matches:
        return None
    row = matches[0]
    index = row.get("index")
    index = index.strip() if isinstance(index, str) and index.strip() else None
    if not any(row.get(key) is not None for key in ("ter", "ter_source", "ter_as_of")):
        return UcitsFacts(index=index)
    try:
        raw_ter = row.get("ter")
        source = row.get("ter_source")
        raw_date = row.get("ter_as_of")
        if not isinstance(raw_ter, str):
            raise ValueError("TER must be a decimal string")
        ter = Decimal(raw_ter)
        if not ter.is_finite() or not Decimal(0) < ter < Decimal("0.05"):
            raise ValueError("TER outside fraction range")
        if not isinstance(source, str) or not source.strip() or len(source) > 64:
            raise ValueError("TER source missing or invalid")
        as_of = date.fromisoformat(raw_date) if isinstance(raw_date, str) else raw_date
        if type(as_of) is not date:
            raise ValueError("TER date missing or invalid")
    except (ValueError, TypeError, InvalidOperation) as exc:
        log.warning("Ignoring curated TER for %s: %s", row.get("symbol"), exc)
        return UcitsFacts(index=index)
    return UcitsFacts(index=index, ter=ter, ter_source=source.strip(), ter_as_of=as_of)


def read_ucits() -> list[dict[str, Any]]:
    raw = files("preza.universe").joinpath("ucits_etfs.yaml").read_text(encoding="utf-8")
    data = yaml.safe_load(raw) or {}
    return list(data.get("etfs", []))


async def load_ucits(session: AsyncSession) -> int:
    rows = read_ucits()
    for row in rows:
        instrument = await get_or_create(
            session,
            symbol=row["symbol"],
            source="universe",
            exchange=row["exchange"],
            name=row["name"],
            kind=InstrumentKind.ETF,
            currency=row["currency"],
            isin=row["isin"],
        )
        instrument.tradable_for_user = True
    return len(rows)
