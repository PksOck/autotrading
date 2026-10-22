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


# --- Radar demo (M2): demo news through the real pipeline, triaged by a deterministic stub ---

DEMO_NEWS = [
    (
        "MSFT",
        "Microsoft raises full-year cloud revenue guidance",
        "press_release",
        35,
        0.8,
        0.9,
        0.6,
        False,
    ),
    ("MSFT", "Microsoft lifts cloud guidance as AI demand grows", "news", 20, 0.8, 0.9, 0.6, False),
    (
        "ORCL",
        "Oracle directors buy shares in open market (Form 4)",
        "filing",
        90,
        0.6,
        0.9,
        0.4,
        False,
    ),
    ("ASML", "ASML supply-chain peer reports record orders", "news", 300, 0.6, 0.7, 0.5, False),
    ("IUES", "Oil stays below $70 for a third week", "news", 400, 0.7, 0.6, -0.5, False),
    (
        "CRWD",
        "CrowdStrike raises annual revenue outlook",
        "press_release",
        60,
        0.8,
        0.9,
        0.7,
        False,
    ),
    (
        "KSTL",
        "Reddit users speculate about a Kestrel Bio takeover",
        "social",
        15,
        0.6,
        0.7,
        0.5,
        True,
    ),
]


class DemoTriage:
    """Stands in for the local model so the Radar can be demoed without Ollama."""

    def __init__(self) -> None:
        self.by_title = {title: row for row in DEMO_NEWS for title in [row[1]]}

    async def embed(self, texts: list[str]) -> list[list[float]]:
        from preza.llm.client import LlmUnavailableError

        raise LlmUnavailableError("demo: no embeddings")

    async def complete_json(self, role, system, user, schema):  # type: ignore[no-untyped-def]
        from preza.domain.radar import EventType, TimeSensitivity, TriageResult
        from preza.llm.client import LlmResult

        row = next((r for title, r in self.by_title.items() if title in user), DEMO_NEWS[0])
        symbol, title, _, _, materiality, novelty, sentiment, rumor = row
        value = TriageResult(
            tickers=[symbol],
            event_type=EventType.RUMOR if rumor else EventType.GUIDANCE,
            is_rumor=rumor,
            sentiment=sentiment,
            materiality=materiality,
            novelty=novelty,
            time_sensitivity=TimeSensitivity.DAYS,
            summary=title + ".",
        )
        return LlmResult(value=value, model="demo-triage", prompt_tokens=0, completion_tokens=0)


class DemoNews:
    name = "demo"

    async def fetch(self, since):  # type: ignore[no-untyped-def]
        from datetime import UTC, datetime, timedelta

        from preza.domain.radar import NewsIn

        now = datetime.now(UTC)
        return [
            NewsIn(
                source="demo" if kind != "social" else "reddit",
                url=f"https://demo.preza.local/{symbol.lower()}/{i}",
                title=title,
                summary=title,
                published_at=now - timedelta(minutes=minutes),
                symbols=[symbol],
                kind=kind,
            )
            for i, (symbol, title, kind, minutes, *_rest) in enumerate(DEMO_NEWS)
        ]


async def seed_radar() -> None:
    from preza.radar.pipeline import run_radar

    async with get_sessionmaker()() as session:
        for symbol, name in (("CRWD", "CrowdStrike Holdings"), ("KSTL", "Kestrel Bio (fictional)")):
            await get_or_create(
                session,
                symbol=symbol,
                source=SOURCE,
                name=name,
                kind=InstrumentKind.STOCK,
                currency="USD",
            )
        result = await run_radar(session, [DemoNews()], DemoTriage(), threshold=0.2)
        await session.commit()
    print(f"demo radar: {result.events} events, {result.signals} signals")


async def seed_all() -> None:
    await main()
    await seed_radar()


if __name__ == "__main__":
    asyncio.run(seed_all())
