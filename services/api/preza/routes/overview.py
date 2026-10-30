"""Counts use persisted data and the same lifecycle as the signal inbox."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from preza.db import get_session
from preza.domain.radar import EventOut, SignalOut
from preza.domain.types import Num
from preza.models import Bar, Event, Instrument, NewsItem, Signal
from preza.routes.signals import signal_out
from preza.services.radar_views import event_out
from preza.services.signals import expire_open_signals

router = APIRouter(prefix="/overview", tags=["overview"])


class MarketIndicatorOut(BaseModel):
    key: str
    value: Num | None = None
    source: str | None = None
    as_of: date | None = None


def market_strip(spy_bars: list[Bar]) -> list[MarketIndicatorOut]:
    """SPY distance from its 200 daily closes; unsupported feeds stay missing."""
    rows = [MarketIndicatorOut(key=key) for key in ("spy", "vix", "us10y", "dxy")]
    if len(spy_bars) >= 200:
        window = spy_bars[:200]
        sma = sum((bar.close for bar in window), Decimal(0)) / 200
        if sma > 0:
            rows[0] = MarketIndicatorOut(
                key="spy",
                value=(window[0].close / sma - 1) * 100,
                source=" + ".join(sorted({bar.source for bar in window})),
                as_of=window[0].day,
            )
    return rows


class TimelineOut(BaseModel):
    since: datetime
    total: int
    events: list[EventOut]


class FunnelOut(BaseModel):
    since: datetime
    news: int
    events: int
    triaged: int
    signalled: int


class OverviewOut(BaseModel):
    as_of: datetime
    source: str = "database"
    signal_counts: dict[str, int]
    news_count: int
    event_count: int
    signals: list[SignalOut]
    market_strip: list[MarketIndicatorOut]
    timeline7d: TimelineOut
    funnel30d: FunnelOut


@router.get("", response_model=OverviewOut)
async def overview(session: Annotated[AsyncSession, Depends(get_session)]) -> OverviewOut:
    now = datetime.now(UTC)
    await expire_open_signals(session, now)
    counts = dict(
        (await session.execute(select(Signal.status, func.count()).group_by(Signal.status))).all()
    )
    signals = await session.scalars(
        select(Signal)
        .where(Signal.status.in_(("new", "watching")))
        .order_by(Signal.created_at.desc(), Signal.id.desc())
        .limit(6)
    )
    timeline_since = now - timedelta(days=7)
    # Positions use first detection, not a later article refresh. Include all views.
    timeline_filter = (Event.first_seen_at >= timeline_since, Event.first_seen_at <= now)
    timeline = list(
        await session.scalars(
            select(Event)
            .where(*timeline_filter)
            .order_by(Event.first_seen_at.desc(), Event.id.desc())
            .limit(100)
        )
    )
    since = now - timedelta(days=30)
    # One ingestion cohort, not four unrelated totals. Count distinct clusters throughout.
    cohort = select(NewsItem).where(NewsItem.fetched_at >= since, NewsItem.fetched_at <= now)
    cohort_news = cohort.subquery()
    cohort_events = select(NewsItem.event_id).where(
        NewsItem.fetched_at >= since, NewsItem.fetched_at <= now, NewsItem.event_id.is_not(None)
    )
    funnel_counts = (
        await session.execute(
            select(
                func.count(Event.id),
                func.count(Event.id).filter(Event.triaged_at.is_not(None)),
                func.count(Event.id).filter(
                    Event.id.in_(select(Signal.event_id).where(Signal.event_id.is_not(None)))
                ),
            ).where(Event.id.in_(cohort_events))
        )
    ).one()
    # One unambiguous instrument only: duplicate exchange symbols cannot be blended.
    spy_ids = list(await session.scalars(select(Instrument.id).where(Instrument.symbol == "SPY")))
    spy_bars = (
        list(
            await session.scalars(
                select(Bar)
                .where(Bar.instrument_id == spy_ids[0], Bar.interval == "1d", Bar.day <= now.date())
                .order_by(Bar.day.desc())
                .limit(200)
            )
        )
        if len(spy_ids) == 1
        else []
    )
    return OverviewOut(
        as_of=now,
        signal_counts=counts,
        news_count=await session.scalar(select(func.count()).select_from(NewsItem)) or 0,
        event_count=await session.scalar(select(func.count()).select_from(Event)) or 0,
        signals=[signal_out(signal) for signal in signals],
        market_strip=market_strip(spy_bars),
        timeline7d=TimelineOut(
            since=timeline_since,
            total=await session.scalar(
                select(func.count()).select_from(Event).where(*timeline_filter)
            )
            or 0,
            events=[event_out(event) for event in timeline],
        ),
        funnel30d=FunnelOut(
            since=since,
            news=await session.scalar(select(func.count()).select_from(cohort_news)) or 0,
            events=funnel_counts[0],
            triaged=funnel_counts[1],
            signalled=funnel_counts[2],
        ),
    )
