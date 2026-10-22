"""Demo data for local development without IBKR or market data access.

Every row is marked source="demo" and the UI shows it as such. Never run against production data.
Run: python -m preza.cli.seed_demo
"""

import asyncio
import math
import random
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import delete, select

from preza.db import get_sessionmaker
from preza.domain.market import BarIn, InstrumentKind
from preza.domain.portfolio import CashIn, FlexStatement, PositionIn
from preza.models import Bar, Instrument, Position, WatchlistItem
from preza.services.bars import upsert_bars
from preza.services.instruments import get_or_create
from preza.services.portfolio import record_sync, store_statement
from preza.universe.loader import load_ucits

SOURCE = "demo"
STOCKS = [
    ("MSFT", "NASDAQ", "Microsoft Corp", 406.8),
    ("ASML", "NASDAQ", "ASML Holding NV", 702.5),
    ("AMZN", "NASDAQ", "Amazon.com Inc", 221.4),
    ("V", "NYSE", "Visa Inc", 271.4),
    ("NVDA", "NASDAQ", "NVIDIA Corp", 182.6),
    ("COST", "NASDAQ", "Costco Wholesale Corp", 918.2),
    ("ORCL", "NYSE", "Oracle Corp", 151.6),
]
ETF_PRICES = {"VWRA": 137.9, "EQQQ": 498.3, "IUES": 8.92, "SMH": 41.2, "CSPX": 640.1}
HOLDINGS = {
    "VWRA": 180,
    "MSFT": 25,
    "ASML": 10,
    "EQQQ": 17,
    "AMZN": 28,
    "IUES": 450,
    "V": 19,
    "NVDA": 20,
}
WATCH = [("COST", "active"), ("ORCL", "active"), ("SMH", "reserve"), ("CSPX", "reserve")]


def demo_bars(symbol: str, last_price: float, days: int = 520) -> list[BarIn]:
    rng = random.Random(symbol)
    closes = [last_price]
    for _ in range(days - 1):
        closes.append(closes[-1] / (1 + rng.gauss(0.0004, 0.014)))
    closes.reverse()
    out: list[BarIn] = []
    day = date.today()
    weekdays: list[date] = []
    while len(weekdays) < days:
        if day.weekday() < 5:
            weekdays.append(day)
        day -= timedelta(days=1)
    weekdays.reverse()
    for d, close in zip(weekdays, closes, strict=True):
        spread = abs(rng.gauss(0, 0.008)) * close
        open_ = close * (1 + rng.gauss(0, 0.005))
        high = max(open_, close) + spread
        low = min(open_, close) - spread
        out.append(
            BarIn(
                day=d,
                open=Decimal(f"{open_:.4f}"),
                high=Decimal(f"{high:.4f}"),
                low=Decimal(f"{low:.4f}"),
                close=Decimal(f"{close:.4f}"),
                volume=int(abs(rng.gauss(2e7, 5e6)) * (1 + math.sin(len(out) / 9) / 4)),
            )
        )
    return out


async def main() -> None:
    async with get_sessionmaker()() as session:
        await load_ucits(session)
        for symbol, exchange, name, _ in STOCKS:
            await get_or_create(
                session,
                symbol=symbol,
                source=SOURCE,
                exchange=exchange,
                name=name,
                kind=InstrumentKind.STOCK,
                currency="USD",
            )

        prices = {s: p for s, _, _, p in STOCKS} | ETF_PRICES
        instruments = {
            i.symbol: i
            for i in await session.scalars(select(Instrument).where(Instrument.symbol.in_(prices)))
            if i.symbol not in ("VWCE", "SXR8", "EUNL")
        }
        await session.execute(delete(Bar).where(Bar.source == SOURCE))
        for symbol, instrument in instruments.items():
            await upsert_bars(session, instrument.id, demo_bars(symbol, prices[symbol]), SOURCE)

        await session.execute(delete(Position).where(Position.source == SOURCE))
        today = date.today()
        statement = FlexStatement(
            positions=[
                PositionIn(
                    account_id="DEMO",
                    symbol=symbol,
                    exchange=instruments[symbol].exchange,
                    currency=instruments[symbol].currency or "USD",
                    kind=InstrumentKind(instruments[symbol].kind),
                    quantity=Decimal(qty),
                    avg_cost=Decimal(f"{prices[symbol] * 0.86:.2f}"),
                    market_price=Decimal(str(prices[symbol])),
                    market_value=Decimal(f"{prices[symbol] * qty:.2f}"),
                    unrealized_pnl=Decimal(f"{prices[symbol] * qty * 0.14:.2f}"),
                    fx_rate_to_base=Decimal("0.92")
                    if instruments[symbol].currency == "USD"
                    else Decimal("1.17"),
                    report_date=today,
                )
                for symbol, qty in HOLDINGS.items()
            ],
            trades=[],
            cash=[
                CashIn(account_id="DEMO", currency="EUR", amount=Decimal("6400"), report_date=today)
            ],
        )
        await store_statement(session, statement, source=SOURCE)
        await record_sync(session, "flex", "ok", "demo data (preza.cli.seed_demo)")

        for symbol, tier in WATCH:
            instrument = instruments[symbol]
            exists = await session.scalar(
                select(WatchlistItem).where(WatchlistItem.instrument_id == instrument.id)
            )
            if not exists:
                session.add(
                    WatchlistItem(
                        instrument_id=instrument.id,
                        tier=tier,
                        source=SOURCE,
                        tags=["demo"],
                        added_price=Decimal(str(prices[symbol] * 0.95)),
                    )
                )
        await session.commit()
    print(
        f"demo data: {len(instruments)} instruments, {len(HOLDINGS)} positions, "
        f"{len(WATCH)} watchlist items"
    )


if __name__ == "__main__":
    asyncio.run(main())
