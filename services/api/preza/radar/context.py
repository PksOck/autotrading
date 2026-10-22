"""Deterministic context for an event: price reaction and attention (BL-045). No LLM."""

import statistics
from datetime import UTC, datetime, timedelta
from itertools import pairwise

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from preza.models import Bar, Instrument, NewsItem, Position, WatchlistItem


async def reaction_z(session: AsyncSession, instrument_id: int, lookback: int = 60) -> float | None:
    """Latest daily return in standard deviations of the previous `lookback` returns."""
    closes = [
        float(c)
        for c in await session.scalars(
            select(Bar.close)
            .where(Bar.instrument_id == instrument_id)
            .order_by(Bar.day.desc())
            .limit(lookback + 2)
        )
    ][::-1]
    if len(closes) < 22:
        return None
    returns = [b / a - 1 for a, b in pairwise(closes)]
    history, last = returns[:-1], returns[-1]
    sd = statistics.pstdev(history)
    return round(last / sd, 4) if sd else None


async def attention(session: AsyncSession, symbol: str, now: datetime | None = None) -> float:
    """Mentions in the last 24 h relative to the daily average of the previous 30 days."""
    now = now or datetime.now(UTC)
    day = now - timedelta(days=1)
    month = now - timedelta(days=31)
    has_symbol = NewsItem.symbols.any(symbol)  # type: ignore[arg-type]
    recent = (
        await session.scalar(select(func.count()).where(has_symbol, NewsItem.published_at >= day))
        or 0
    )
    base = (
        await session.scalar(
            select(func.count()).where(
                has_symbol, NewsItem.published_at >= month, NewsItem.published_at < day
            )
        )
        or 0
    )
    baseline = max(base / 30.0, 1.0)
    return round(recent / baseline, 4)


async def relevance(session: AsyncSession, symbols: list[str]) -> tuple[float, int | None]:
    """Weight by the user's relation to the instrument, and the instrument id of the best match."""
    best: tuple[float, int | None] = (0.3, None)
    for symbol in symbols:
        instrument = await session.scalar(
            select(Instrument).where(Instrument.symbol == symbol).limit(1)
        )
        if instrument is None:
            continue
        held = (
            await session.scalar(
                select(func.count()).where(Position.instrument_id == instrument.id)
            )
            or 0
        )
        watched = (
            await session.scalar(
                select(func.count()).where(WatchlistItem.instrument_id == instrument.id)
            )
            or 0
        )
        weight = 1.0 if held else 0.8 if watched else 0.5
        if weight > best[0]:
            best = (weight, instrument.id)
    return best
