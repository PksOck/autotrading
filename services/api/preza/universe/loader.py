"""Loads the curated UCITS ETF list into `instrument` (BL-026)."""

from importlib.resources import files
from typing import Any

import yaml
from sqlalchemy.ext.asyncio import AsyncSession

from preza.domain.market import InstrumentKind
from preza.services.instruments import get_or_create


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
