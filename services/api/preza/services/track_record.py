"""Loads outcome rows for the track record screen (BL-102)."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from preza.domain.track_record import OutcomeRow, TrackRecordOut, origin_of, track_record
from preza.models import Signal, SignalOutcome


async def load_track_record(
    session: AsyncSession, horizon_days: int, benchmark: str | None
) -> TrackRecordOut:
    rows = await session.execute(
        select(
            Signal.kind,
            Signal.source,
            Signal.proposal_id,
            Signal.strength,
            SignalOutcome.return_pct,
            SignalOutcome.alpha_pct,
        )
        .join(Signal, Signal.id == SignalOutcome.signal_id)
        .where(SignalOutcome.horizon_days == horizon_days)
    )
    items = [
        OutcomeRow(
            kind=kind,
            source=source,
            origin=origin_of(source, proposal_id),
            strength=strength,
            return_pct=return_pct,
            alpha_pct=alpha_pct,
        )
        for kind, source, proposal_id, strength, return_pct, alpha_pct in rows
    ]
    signals_total = await session.scalar(select(func.count()).select_from(Signal)) or 0
    as_of = await session.scalar(
        select(func.max(SignalOutcome.computed_at)).where(
            SignalOutcome.horizon_days == horizon_days
        )
    )
    stored = await session.scalars(
        select(SignalOutcome.benchmark)
        .where(SignalOutcome.horizon_days == horizon_days, SignalOutcome.benchmark.is_not(None))
        .distinct()
    )
    # The stored benchmark wins over the setting: it is what the alpha was measured against.
    names = sorted(name for name in stored if name)
    return track_record(
        items,
        horizon_days=horizon_days,
        signals_total=signals_total,
        benchmark=", ".join(names) if names else benchmark,
        as_of=as_of,
    )
