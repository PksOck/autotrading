"""Add synthetic YTD captures to an existing isolated demo, without resetting any records."""

import asyncio
import os
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select

from preza.data.contract import SplitHistory
from preza.db import get_sessionmaker
from preza.domain.history import DEMO_SPLIT_BASIS
from preza.domain.market import BarIn
from preza.models import Bar, Instrument, Position, WatchlistItem
from preza.services.bars import last_trading_day
from preza.services.market_context import identity_status
from preza.services.price_history import store_capture


async def seed() -> int:
    if os.environ.get("PREZA_DEMO_DB") != "1":
        raise RuntimeError("requires_explicit_demo_opt_in")
    async with get_sessionmaker()() as session:
        positions = list(await session.scalars(select(Position)))
        if not positions or any(
            p.source != "demo" or not p.account_id.startswith("DEMO") for p in positions
        ):
            raise RuntimeError("refusing_non_demo_positions")
        ids = {p.instrument_id for p in positions} | set(
            await session.scalars(select(WatchlistItem.instrument_id))
        )
        targets = list(await session.scalars(select(Instrument).where(Instrument.id.in_(ids))))
        eligible = []
        for instrument in targets:
            if identity_status(instrument) != "resolved":
                continue
            latest = await session.scalar(
                select(Bar)
                .where(Bar.instrument_id == instrument.id, Bar.interval == "1d")
                .order_by(Bar.day.desc())
                .limit(1)
            )
            if (
                instrument.source not in {"demo", "universe"}
                or latest is None
                or latest.source != "demo"
            ):
                raise RuntimeError("refusing_non_demo_market_data")
            eligible.append((instrument, latest.close))
        now = datetime.now(UTC)
        end = last_trading_day(now.date() - timedelta(days=1))
        days = [date(now.year - 1, 12, 31)]
        day = date(now.year, 1, 1)
        while day <= end:
            if day.weekday() < 5:
                days.append(day)
            day += timedelta(days=1)
        if len(days) < 2:
            return 0
        for instrument, close in eligible:
            factor = Decimal(1) + Decimal(instrument.id % 5 - 2) / 10
            first = close / factor
            bars = []
            for index, day in enumerate(days):
                price = (
                    first + (close - first) * Decimal(index) / Decimal(len(days) - 1)
                ).quantize(Decimal("0.000001"))
                bars.append(BarIn(day=day, open=price, high=price, low=price, close=price))
            await store_capture(
                session,
                instrument,
                "demo",
                SplitHistory(
                    bars,
                    instrument.currency or "",
                    instrument.ib_con_id or instrument.id,
                    DEMO_SPLIT_BASIS,
                ),
                now=now,
                allow_demo=True,
            )
        await session.commit()
        return len(eligible)


if __name__ == "__main__":
    print(f"Synthetic YTD captures: {asyncio.run(seed())}")
