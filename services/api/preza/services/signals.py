"""Shared lifecycle normalization for signal reads."""

from datetime import datetime

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from preza.models import Signal


async def expire_open_signals(session: AsyncSession, now: datetime) -> None:
    """Expire pending ideas before filtering or limiting; keep explicit decisions intact."""
    await session.execute(
        update(Signal)
        .where(Signal.status.in_(("new", "watching")), Signal.expires_at < now)
        .values(status="expired")
        .execution_options(synchronize_session="fetch")
    )
