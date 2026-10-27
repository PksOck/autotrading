"""Weight calibration store (BL-103): propose, confirm or reject, and read active weights."""

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from fastapi import HTTPException
from pydantic import AwareDatetime, BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from preza.domain.calibration import (
    DEFAULT_WEIGHT,
    TUNABLE,
    CalibrationProposal,
    group_key,
    propose,
)
from preza.models import SignalWeightSet
from preza.services.track_record import load_outcome_rows

PROPOSED, ACTIVE, REJECTED, SUPERSEDED = "proposed", "active", "rejected", "superseded"


class WeightSetOut(BaseModel):
    id: uuid.UUID
    status: str
    horizon_days: int
    weights: dict[str, Decimal]
    created_at: AwareDatetime
    decided_at: AwareDatetime | None
    proposal: CalibrationProposal | None


class CalibrationOut(BaseModel):
    tunable: list[str]
    active: WeightSetOut | None
    proposal: WeightSetOut | None


def _out(row: SignalWeightSet) -> WeightSetOut:
    return WeightSetOut(
        id=row.id,
        status=row.status,
        horizon_days=row.horizon_days,
        weights={k: Decimal(v) for k, v in row.weights.items()},
        created_at=row.created_at,
        decided_at=row.decided_at,
        proposal=CalibrationProposal.model_validate(row.basis) if row.basis else None,
    )


async def _active(session: AsyncSession) -> SignalWeightSet | None:
    return await session.scalar(select(SignalWeightSet).where(SignalWeightSet.status == ACTIVE))


async def active_weights(session: AsyncSession) -> dict[str, Decimal]:
    row = await _active(session)
    return {k: Decimal(v) for k, v in row.weights.items()} if row else {}


async def active_weight(session: AsyncSession, kind: str, source: str) -> Decimal:
    return (await active_weights(session)).get(group_key(kind, source), DEFAULT_WEIGHT)


async def load_calibration(session: AsyncSession) -> CalibrationOut:
    pending = await session.scalar(
        select(SignalWeightSet)
        .where(SignalWeightSet.status == PROPOSED)
        .order_by(SignalWeightSet.created_at.desc())
    )
    active = await _active(session)
    return CalibrationOut(
        tunable=[group_key(k, s) for k, s in TUNABLE],
        active=_out(active) if active else None,
        proposal=_out(pending) if pending else None,
    )


async def create_proposal(session: AsyncSession, horizon_days: int) -> WeightSetOut:
    """Compute a fresh proposal; an older open proposal is superseded, never applied."""
    current = await active_weights(session)
    result = propose(
        await load_outcome_rows(session, horizon_days), horizon_days=horizon_days, current=current
    )
    now = datetime.now(UTC)
    for old in await session.scalars(
        select(SignalWeightSet).where(SignalWeightSet.status == PROPOSED)
    ):
        old.status, old.decided_at = SUPERSEDED, now
    row = SignalWeightSet(
        status=PROPOSED,
        horizon_days=horizon_days,
        weights={group_key(g.kind, g.source): str(g.proposed_weight) for g in result.groups},
        basis=result.model_dump(mode="json"),
        created_at=now,
    )
    session.add(row)
    await session.flush()
    return _out(row)


async def _pending(session: AsyncSession, set_id: uuid.UUID) -> SignalWeightSet:
    row = await session.get(SignalWeightSet, set_id, with_for_update=True)
    if row is None:
        raise HTTPException(404, detail="weight_set_not_found")
    if row.status != PROPOSED:
        raise HTTPException(409, detail="not_pending")
    return row


async def confirm_proposal(session: AsyncSession, set_id: uuid.UUID) -> WeightSetOut:
    """The only path that changes weights; called on an explicit user confirmation."""
    row = await _pending(session, set_id)
    basis = CalibrationProposal.model_validate(row.basis)
    if not basis.changed:
        raise HTTPException(422, detail="no_changes")
    current = await active_weights(session)
    if any(
        current.get(group_key(g.kind, g.source), DEFAULT_WEIGHT) != g.current_weight
        for g in basis.groups
    ):
        raise HTTPException(409, detail="stale_proposal")  # weights changed after the proposal
    now = datetime.now(UTC)
    previous = await _active(session)
    if previous is not None:
        previous.status, previous.decided_at = SUPERSEDED, now
        await session.flush()  # free the single active slot first
    row.status, row.decided_at = ACTIVE, now
    await session.flush()
    return _out(row)


async def reject_proposal(session: AsyncSession, set_id: uuid.UUID) -> WeightSetOut:
    row = await _pending(session, set_id)
    row.status, row.decided_at = REJECTED, datetime.now(UTC)
    await session.flush()
    return _out(row)
