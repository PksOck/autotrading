from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from preza.db import get_session
from preza.domain.radar import (
    Direction,
    EvidenceRef,
    Horizon,
    SignalKind,
    SignalOut,
    SignalSource,
    SignalStatus,
    SignalUpdate,
)
from preza.models import Signal

router = APIRouter(prefix="/signals", tags=["signals"])
Session = Annotated[AsyncSession, Depends(get_session)]


def signal_out(signal: Signal) -> SignalOut:
    return SignalOut(
        id=signal.id,
        symbol=signal.instrument.symbol,
        kind=SignalKind(signal.kind),
        source=SignalSource(signal.source),
        direction=Direction(signal.direction),
        horizon=Horizon(signal.horizon),
        strength=signal.strength,
        confidence=signal.confidence,
        entry_low=signal.entry_low,
        entry_high=signal.entry_high,
        stop=signal.stop,
        target=signal.target,
        rationale=signal.rationale,
        evidence=[EvidenceRef.model_validate(e) for e in signal.evidence],
        is_rumor=signal.is_rumor,
        status=SignalStatus(signal.status),
        event_id=signal.event_id,
        proposal_id=signal.proposal_id,
        created_at=signal.created_at,
        expires_at=signal.expires_at,
    )


@router.get("", response_model=list[SignalOut])
async def list_signals(
    session: Session,
    status: SignalStatus | None = None,
    kind: SignalKind | None = None,
    limit: int = 100,
) -> list[SignalOut]:
    query = select(Signal).order_by(Signal.created_at.desc()).limit(min(limit, 500))
    if status:
        query = query.where(Signal.status == status.value)
    if kind:
        query = query.where(Signal.kind == kind.value)
    now = datetime.now(UTC)
    out = []
    for signal in await session.scalars(query):
        if signal.expires_at and signal.expires_at < now and signal.status in ("new", "watching"):
            signal.status = SignalStatus.EXPIRED.value
        out.append(signal_out(signal))
    return out


@router.patch("/{signal_id}", response_model=SignalOut)
async def update_signal(session: Session, signal_id: UUID, data: SignalUpdate) -> SignalOut:
    signal = await session.get(Signal, signal_id)
    if signal is None:
        raise HTTPException(404, detail="signal_not_found")
    # A rumor can be watched or dismissed, but not accepted as a trade idea (AGENTS.md §3.4).
    if signal.is_rumor and data.status == SignalStatus.ACCEPTED:
        raise HTTPException(409, detail="rumor_cannot_be_accepted")
    signal.status = data.status.value
    signal.status_reason = data.reason
    await session.flush()
    return signal_out(signal)
