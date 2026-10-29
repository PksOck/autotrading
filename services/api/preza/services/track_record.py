"""Loads outcome rows for the track record screen (BL-102)."""

from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from preza.domain.track_record import (
    OutcomeRow,
    TrackOutcome,
    TrackOutcomePage,
    TrackRecordOut,
    origin_of,
    track_record,
)
from preza.models import Instrument, Signal, SignalOutcome


def cohort_conditions(
    created_from: date | None, created_to: date | None
) -> list[ColumnElement[bool]]:
    conditions = []
    if created_from:
        conditions.append(Signal.created_at >= datetime.combine(created_from, time.min, UTC))
    if created_to:
        conditions.append(
            Signal.created_at < datetime.combine(created_to + timedelta(days=1), time.min, UTC)
        )
    return conditions


async def load_outcome_rows(
    session: AsyncSession,
    horizon_days: int,
    created_from: date | None = None,
    created_to: date | None = None,
) -> list[OutcomeRow]:
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
        .where(
            SignalOutcome.horizon_days == horizon_days, *cohort_conditions(created_from, created_to)
        )
    )
    return [
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


async def load_track_record(
    session: AsyncSession,
    horizon_days: int,
    benchmark: str | None,
    created_from: date | None = None,
    created_to: date | None = None,
) -> TrackRecordOut:
    conditions = cohort_conditions(created_from, created_to)
    items = await load_outcome_rows(session, horizon_days, created_from, created_to)
    signals_total = (
        await session.scalar(select(func.count()).select_from(Signal).where(*conditions)) or 0
    )
    as_of = await session.scalar(
        select(func.max(SignalOutcome.computed_at))
        .join(Signal)
        .where(SignalOutcome.horizon_days == horizon_days, *conditions)
    )
    stored = await session.scalars(
        select(SignalOutcome.benchmark)
        .join(Signal)
        .where(
            SignalOutcome.horizon_days == horizon_days,
            SignalOutcome.benchmark.is_not(None),
            *conditions,
        )
        .distinct()
    )
    # The stored benchmark wins over the setting: it is what the alpha was measured against.
    names = sorted(name for name in stored if name)
    result = track_record(
        items,
        horizon_days=horizon_days,
        signals_total=signals_total,
        benchmark=", ".join(names) if names else benchmark,
        as_of=as_of,
    )
    result.created_from, result.created_to = created_from, created_to
    return result


async def load_outcomes(
    session: AsyncSession,
    horizon_days: int,
    created_from: date | None,
    created_to: date | None,
    offset: int,
    limit: int,
) -> TrackOutcomePage:
    conditions = [
        SignalOutcome.horizon_days == horizon_days,
        *cohort_conditions(created_from, created_to),
    ]
    total = (
        await session.scalar(
            select(func.count()).select_from(SignalOutcome).join(Signal).where(*conditions)
        )
        or 0
    )
    rows = await session.execute(
        select(Signal, SignalOutcome, Instrument.symbol)
        .join(SignalOutcome, SignalOutcome.signal_id == Signal.id)
        .join(Instrument, Instrument.id == Signal.instrument_id)
        .where(*conditions)
        .order_by(Signal.created_at.desc(), Signal.id.desc())
        .offset(offset)
        .limit(limit)
    )
    return TrackOutcomePage(
        total=total,
        offset=offset,
        limit=limit,
        items=[
            TrackOutcome(
                signal_id=s.id,
                symbol=symbol,
                created_at=s.created_at,
                kind=s.kind,
                source=s.source,
                return_pct=o.return_pct,
                alpha_pct=o.alpha_pct,
                benchmark=o.benchmark,
            )
            for s, o, symbol in rows
        ],
    )
