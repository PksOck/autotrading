"""Counts use persisted data and the same lifecycle as the signal inbox."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from preza.db import get_session
from preza.domain.radar import SignalOut
from preza.models import Event, NewsItem, Signal
from preza.routes.signals import signal_out
from preza.services.signals import expire_open_signals

router = APIRouter(prefix="/overview", tags=["overview"])


class OverviewOut(BaseModel):
    as_of: datetime
    source: str = "database"
    signal_counts: dict[str, int]
    news_count: int
    event_count: int
    signals: list[SignalOut]


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
    return OverviewOut(
        as_of=now,
        signal_counts=counts,
        news_count=await session.scalar(select(func.count()).select_from(NewsItem)) or 0,
        event_count=await session.scalar(select(func.count()).select_from(Event)) or 0,
        signals=[signal_out(signal) for signal in signals],
    )
