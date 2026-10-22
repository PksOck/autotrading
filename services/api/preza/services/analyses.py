"""Creating deep analysis runs (M4). Shared by the API and by deep proposals (BL-090)."""

import uuid
from datetime import UTC, date, datetime, time

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from preza.config import Settings
from preza.models import AnalysisRun, Instrument
from preza.queue import AGENTS_QUEUE, enqueue


def job_id(run_id: uuid.UUID) -> str:
    return f"analysis:{run_id}"


async def used_today(session: AsyncSession) -> int:
    """Runs started today (UTC); failed runs do not count against the limit."""
    start = datetime.combine(datetime.now(UTC).date(), time.min, tzinfo=UTC)
    count = await session.scalar(
        select(func.count())
        .select_from(AnalysisRun)
        .where(AnalysisRun.created_at >= start, AnalysisRun.status != "failed")
    )
    return count or 0


async def limit_reached(session: AsyncSession, settings: Settings) -> bool:
    limit = settings.deep_daily_limit
    return limit > 0 and await used_today(session) >= limit


async def new_run(
    session: AsyncSession,
    instrument: Instrument,
    settings: Settings,
    *,
    trade_date: date | None = None,
    hypothesis: str | None = None,
    proposal_id: uuid.UUID | None = None,
) -> AnalysisRun:
    """Store a queued run; call `queue_run` after the commit."""
    run = AnalysisRun(
        instrument_id=instrument.id,
        engine="etf" if instrument.kind == "etf" else "tradingagents",
        trade_date=trade_date or datetime.now(UTC).date(),
        locale=settings.default_locale,
        hypothesis=hypothesis or None,
        proposal_id=proposal_id,
        caveats=[],
        reports={},
        models={},
    )
    session.add(run)
    await session.flush()
    return run


async def queue_run(settings: Settings, run_id: uuid.UUID) -> None:
    # A run stored while the queue is down is picked up by the agents' sweep.
    await enqueue(
        settings, "deep_analysis", str(run_id), job_id=job_id(run_id), queue_name=AGENTS_QUEUE
    )
