"""A frozen copy of everything a deep analysis may read, built from our database.

TradingAgents calls its data tools from worker threads; instead of opening database
sessions there, the run reads from this snapshot. The same snapshot, saved as JSON,
is the fixture for the agent regression tests (BL-086).
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from preza.models import Bar, Event, Fundamentals, Instrument, NewsItem

BAR_DAYS = 800  # enough for a 200-day average a year back
NEWS_DAYS = 30
GLOBAL_NEWS_LIMIT = 40
INSIDER_FORMS = ("4", "4/A")


class BarRow(BaseModel):
    day: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int | None = None


class NewsRow(BaseModel):
    published_at: datetime
    title: str
    summary: str | None = None
    source: str
    url: str
    kind: str
    filing_form: str | None = None
    is_rumor: bool = False
    symbols: list[str] = Field(default_factory=list)


class DataSnapshot(BaseModel):
    symbol: str
    name: str | None = None
    kind: str = "stock"
    exchange: str | None = None
    currency: str | None = None
    as_of: date
    bars: list[BarRow] = Field(default_factory=list)
    bars_source: str | None = None
    fundamentals: dict[str, Any] | None = None
    fundamentals_source: str | None = None
    fundamentals_as_of: date | None = None
    fundamentals_history: dict[str, list[tuple[date, float]]] = Field(default_factory=dict)
    news: list[NewsRow] = Field(default_factory=list)
    global_news: list[NewsRow] = Field(default_factory=list)


def _end_of(day: date) -> datetime:
    return datetime.combine(day, time.max, tzinfo=UTC)


async def _news(
    session: AsyncSession, since: datetime, until: datetime, symbol: str | None, limit: int | None
) -> list[NewsRow]:
    query = (
        select(NewsItem, Event.is_rumor)
        .outerjoin(Event, Event.id == NewsItem.event_id)
        .where(NewsItem.published_at >= since, NewsItem.published_at <= until)
        .order_by(NewsItem.published_at.desc())
    )
    if symbol is not None:
        query = query.where(NewsItem.symbols.contains([symbol]))
    if limit is not None:
        query = query.limit(limit)
    rows = (await session.execute(query)).all()
    return [
        NewsRow(
            published_at=item.published_at,
            title=item.title,
            summary=item.summary,
            source=item.source,
            url=item.url,
            kind=item.kind,
            filing_form=item.filing_form,
            is_rumor=bool(is_rumor),
            symbols=list(item.symbols or []),
        )
        for item, is_rumor in rows
    ]


def _history(raw: dict[str, Any] | None, as_of: date) -> dict[str, list[tuple[date, float]]]:
    out: dict[str, list[tuple[date, float]]] = {}
    for metric, points in (raw or {}).items():
        rows = [(date.fromisoformat(str(d)), float(v)) for d, v in points if v is not None]
        out[metric] = [(d, v) for d, v in rows if d <= as_of]
    return out


async def build_snapshot(
    session: AsyncSession, instrument: Instrument, as_of: date
) -> DataSnapshot:
    """Read bars, fundamentals and news known on `as_of` (no look-ahead)."""
    bars = list(
        await session.scalars(
            select(Bar)
            .where(
                Bar.instrument_id == instrument.id,
                Bar.interval == "1d",
                Bar.day <= as_of,
                Bar.day >= as_of - timedelta(days=BAR_DAYS),
            )
            .order_by(Bar.day)
        )
    )
    fundamentals = await session.get(Fundamentals, instrument.id)
    if fundamentals is not None and fundamentals.as_of > as_of:
        fundamentals = None  # a later snapshot would leak the future into a past run
    until = _end_of(as_of)
    news = await _news(
        session, until - timedelta(days=NEWS_DAYS), until, instrument.symbol, limit=None
    )
    global_news = await _news(
        session, until - timedelta(days=7), until, None, limit=GLOBAL_NEWS_LIMIT
    )
    return DataSnapshot(
        symbol=instrument.symbol,
        name=instrument.name,
        kind=instrument.kind,
        exchange=instrument.exchange,
        currency=instrument.currency,
        as_of=as_of,
        bars=[
            BarRow(day=b.day, open=b.open, high=b.high, low=b.low, close=b.close, volume=b.volume)
            for b in bars
        ],
        bars_source=bars[-1].source if bars else None,
        fundamentals=fundamentals.metrics if fundamentals else None,
        fundamentals_source=fundamentals.source if fundamentals else None,
        fundamentals_as_of=fundamentals.as_of if fundamentals else None,
        fundamentals_history=_history(fundamentals.history if fundamentals else None, as_of),
        news=news,
        global_news=global_news,
    )
