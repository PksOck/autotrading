"""Demo data for local development without IBKR or market data access.

Every row is marked source="demo" and the UI shows it as such. Never run against production data.
Run: infra/scripts/demo-stack.sh up (a separate stack; refuses to run without PREZA_DEMO_DB=1)
"""

import asyncio
import math
import os
import random
import re
import uuid
from datetime import UTC, date, datetime, timedelta
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


DEMO_SL = {
    "Microsoft raises full-year cloud revenue guidance": (
        "Microsoft je zvišal letno napoved prihodkov v oblaku"
    ),
    "Microsoft lifts cloud guidance as AI demand grows": (
        "Microsoft zvišuje napoved za oblak zaradi rasti povpraševanja po UI"
    ),
    "Oracle directors buy shares in open market (Form 4)": (
        "Direktorji Oracla kupujejo delnice na trgu (obrazec 4)"
    ),
    "ASML supply-chain peer reports record orders": (
        "Dobavitelj iz verige ASML poroča o rekordnih naročilih"
    ),
    "Oil stays below $70 for a third week": "Nafta tretji teden ostaja pod 70 $",
    "CrowdStrike raises annual revenue outlook": "CrowdStrike zvišuje letno napoved prihodkov",
    "Reddit users speculate about a Kestrel Bio takeover": (
        "Uporabniki Reddita ugibajo o prevzemu podjetja Kestrel Bio"
    ),
}


class DemoTriage:
    """Stands in for the local model so the Radar can be demoed without Ollama."""

    def __init__(self) -> None:
        self.by_title = {title: row for row in DEMO_NEWS for title in [row[1]]}

    async def embed(self, texts: list[str]) -> list[list[float]]:
        from preza.llm.client import LlmUnavailableError

        raise LlmUnavailableError("demo: no embeddings")

    async def complete_json(self, role, system, user, schema):  # type: ignore[no-untyped-def]
        from preza.domain.radar import (
            EventType,
            TimeSensitivity,
            TranslatedText,
            TranslationBatch,
            TriageResult,
        )
        from preza.llm.client import LlmResult

        if schema is TranslationBatch:
            items = [
                TranslatedText(id=int(m[1]), text=DEMO_SL.get(m[2].rstrip("."), m[2]))
                for m in re.finditer(r"^\[(\d+)\] (.+)$", user, re.MULTILINE)
            ]
            return LlmResult(
                value=TranslationBatch(items=items),
                model="demo-translate",
                prompt_tokens=0,
                completion_tokens=0,
            )

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


DEMO_URL = "https://demo.preza.local/"


class DemoNews:
    name = "demo"

    async def fetch(self, since):  # type: ignore[no-untyped-def]
        from datetime import UTC, datetime, timedelta

        from preza.domain.radar import NewsIn

        now = datetime.now(UTC)
        return [
            NewsIn(
                source="demo" if kind != "social" else "reddit",
                url=f"{DEMO_URL}{symbol.lower()}/{i}",
                title=title,
                summary=title,
                published_at=now - timedelta(minutes=minutes),
                symbols=[symbol],
                kind=kind,
            )
            for i, (symbol, title, kind, minutes, *_rest) in enumerate(DEMO_NEWS)
        ]


async def seed_radar() -> None:
    from preza.models import Event, NewsItem, Signal
    from preza.radar.pipeline import run_radar

    async with get_sessionmaker()() as session:
        # Re-seeding replaces the demo Radar instead of deduplicating it away.
        demo_news = NewsItem.url.startswith(DEMO_URL)
        event_ids = select(NewsItem.event_id).where(demo_news, NewsItem.event_id.is_not(None))
        await session.execute(delete(Signal).where(Signal.event_id.in_(event_ids)))
        await session.execute(delete(Event).where(Event.id.in_(event_ids)))
        await session.execute(delete(NewsItem).where(demo_news))
        for symbol, name in (("CRWD", "CrowdStrike Holdings"), ("KSTL", "Kestrel Bio (fictional)")):
            await get_or_create(
                session,
                symbol=symbol,
                source=SOURCE,
                name=name,
                kind=InstrumentKind.STOCK,
                currency="USD",
            )
        result = await run_radar(session, [DemoNews()], DemoTriage(), threshold=0.2, locale="sl")
        await session.commit()
    print(f"demo radar: {result.events} events, {result.signals} signals")


DEMO_CAUSES = {"ORCL": "transient", "ASML": "sector", "NVDA": "fundamental"}
DEMO_DIP_TEXT = {
    "market": "Padec sledi širšemu trgu; o podjetju ni novic, ki bi spremenile dolgoročno sliko.",
    "sector": "Padel je celoten sektor polprevodnikov; podjetje samo ni poročalo slabših številk.",
    "transient": "Padec je povezan z enkratnim dogodkom; napoved in naročila ostajajo enaki.",
    "fundamental": "Demo: padec spremlja trajno nižja marža, kar spreminja dolgoročno sliko.",
}


class DemoDip:
    """Stands in for `dip_analyst` so SCR-03 can be demoed without a model."""

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return []

    async def complete_json(self, role, system, user, schema):  # type: ignore[no-untyped-def]
        import json

        from preza.entries.dip import DipCause, DipVerdict
        from preza.llm.client import LlmResult

        symbol = json.loads(user)["instrument"]["symbol"]
        cause = DipCause(DEMO_CAUSES.get(symbol, "market"))
        verdict = DipVerdict(
            cause=cause,
            thesis_intact=cause != DipCause.FUNDAMENTAL,
            confidence=0.6,
            rationale=DEMO_DIP_TEXT[cause.value],
        )
        return LlmResult(value=verdict, model="demo-dip", prompt_tokens=0, completion_tokens=0)


def demo_fundamentals(symbol: str, today: date) -> tuple[dict[str, float], dict[str, list]]:  # type: ignore[type-arg]
    """Five years of quarterly P/E and FCF yield around a symbol-specific median."""
    rng = random.Random(f"fund-{symbol}")
    pe_mid, fcf_mid = rng.uniform(18, 40), rng.uniform(2, 5)
    history: dict[str, list] = {"pe": [], "fcf_yield": []}  # type: ignore[type-arg]
    for q in range(20, 0, -1):
        day = (today - timedelta(days=91 * q)).isoformat()
        history["pe"].append([day, round(pe_mid * rng.uniform(0.75, 1.25), 2)])
        history["fcf_yield"].append([day, round(fcf_mid * rng.uniform(0.75, 1.25), 2)])
    cheap = rng.random() < 0.6
    current = {
        "pe": round(pe_mid * (0.85 if cheap else 1.15), 2),
        "fcf_yield": round(fcf_mid * (1.15 if cheap else 0.85), 2),
        "ev_ebit": None,
    }
    return current, history  # type: ignore[return-value]


async def seed_entries() -> None:
    from preza.entries.service import rebuild_entries
    from preza.models import EntryCandidate, Fundamentals, Signal

    async with get_sessionmaker()() as session:
        await session.execute(delete(EntryCandidate))
        await session.execute(delete(Signal).where(Signal.source == "rule"))
        today = date.today()
        for symbol, *_ in STOCKS:
            instrument = await session.scalar(select(Instrument).where(Instrument.symbol == symbol))
            if instrument is None:
                continue
            current, history = demo_fundamentals(symbol, today)
            row = await session.get(Fundamentals, instrument.id) or Fundamentals(
                instrument_id=instrument.id
            )
            row.as_of, row.metrics, row.history, row.source = today, current, history, SOURCE
            session.add(row)
        await session.flush()
        run = await rebuild_entries(session, DemoDip(), "sl")
        await session.commit()
    print(f"demo entries: {run.evaluated} evaluated, {run.active} active, {run.signals} signals")


DEMO_TRACK_NS = uuid.UUID("6f1c0d1e-5b7a-4d0e-9a51-0c2d7e1b3a10")
# (symbol, kind, source, strength, days ago): past signals whose outcomes SCR-10 measures.
DEMO_TRACK = [
    ("MSFT", "entry", "rule", "0.82", 150),
    ("ASML", "entry", "rule", "0.74", 140),
    ("AMZN", "catalyst", "radar", "0.66", 130),
    ("V", "entry", "rule", "0.58", 125),
    ("NVDA", "catalyst", "radar", "0.91", 120),
    ("COST", "entry", "agent", "0.47", 115),
    ("ORCL", "exit_warning", "rule", "0.35", 110),
    ("MSFT", "catalyst", "manual", "0.70", 105),
    ("ASML", "entry", "manual", "0.62", 100),
    ("AMZN", "entry", "rule", "0.28", 96),
    ("NVDA", "entry", "agent", "0.77", 92),
    ("V", "catalyst", "radar", "0.53", 88),
    ("COST", "exit_warning", "rule", "0.18", 70),
    ("ORCL", "entry", "rule", "0.86", 45),
]


async def seed_track_record() -> None:
    """Back-dated signals plus outcomes computed from the demo bars (BL-102)."""
    from preza.models import Signal
    from preza.services.outcomes import compute_outcomes

    ids = [uuid.uuid5(DEMO_TRACK_NS, str(i)) for i in range(len(DEMO_TRACK))]
    now = datetime.now(UTC)
    async with get_sessionmaker()() as session:
        await session.execute(delete(Signal).where(Signal.id.in_(ids)))
        for sid, (symbol, kind, source, strength, days) in zip(ids, DEMO_TRACK, strict=True):
            instrument = await session.scalar(select(Instrument).where(Instrument.symbol == symbol))
            if instrument is None:
                continue
            session.add(
                Signal(
                    id=sid,
                    instrument_id=instrument.id,
                    kind=kind,
                    source=source,
                    direction="down" if kind == "exit_warning" else "up",
                    horizon="weeks",
                    strength=Decimal(strength),
                    rationale=f"Demo {kind} signal for {symbol}.",
                    evidence=[{"label": "demo", "url": None}],
                    status="accepted" if source == "manual" else "dismissed",
                    created_at=now - timedelta(days=days),
                )
            )
        await session.flush()
        # Demo data has no SPY; CSPX tracks the same index.
        inserted = await compute_outcomes(session, "CSPX", now)
        await session.commit()
    print(f"demo track record: {len(ids)} signals, {inserted} outcomes")


async def seed_all() -> None:
    await main()
    await seed_radar()
    await seed_entries()
    await seed_track_record()
    from preza.cli.seed_demo_analysis import seed_analyses

    await seed_analyses()


def require_demo_db() -> None:
    """seed_entries clears every entry candidate and rule signal, so never run it on real data."""
    if os.environ.get("PREZA_DEMO_DB") != "1":
        raise SystemExit(
            "seed_demo replaces entries and rule signals. Run it only on a throwaway demo "
            "database (infra/scripts/demo-stack.sh) with PREZA_DEMO_DB=1."
        )


if __name__ == "__main__":
    require_demo_db()
    asyncio.run(seed_all())
