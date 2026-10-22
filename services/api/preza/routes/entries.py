from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from preza.config import Settings, get_settings
from preza.db import get_session
from preza.domain.entries import EntryOut, EntryView, LadderLevelOut, RuleHitOut
from preza.domain.outcome import OutcomeStat
from preza.models import EntryCandidate, Instrument
from preza.queue import enqueue
from preza.routes.portfolio import Queued
from preza.services.outcomes import outcome_stats
from preza.services.radar_views import user_symbols

router = APIRouter(prefix="/entries", tags=["entries"])
Session = Annotated[AsyncSession, Depends(get_session)]

STATE_ORDER = {"in_zone": 0, "below": 1, "near": 2, "far": 3}


def entry_out(c: EntryCandidate, held: set[str], watched: set[str]) -> EntryOut:
    i = c.instrument
    return EntryOut(
        symbol=i.symbol,
        name=i.name,
        kind=i.kind,
        currency=i.currency,
        held=i.symbol in held,
        watched=i.symbol in watched,
        as_of=c.as_of,
        price=c.price,
        state=c.state,
        anchor=c.anchor,
        rules=[RuleHitOut.model_validate(r) for r in c.rules],
        zone_low=c.zone_low,
        zone_high=c.zone_high,
        stop=c.stop,
        atr=c.atr,
        distance_atr=c.distance_atr,
        drawdown_pct=c.drawdown_pct,
        valuation=dict(c.valuation or {}),
        ladder=[LadderLevelOut.model_validate(lv) for lv in c.ladder],
        cause=c.cause,
        thesis_intact=c.thesis_intact,
        dip_rationale=c.dip_rationale,
        dip_evidence=list(c.dip_evidence or []),
        dip_model=c.dip_model,
        analyzed_at=c.analyzed_at,
        signal_id=c.signal_id,
        source=c.source,
        updated_at=c.updated_at,
    )


@router.get("", response_model=list[EntryOut])
async def list_entries(session: Session, view: EntryView = EntryView.ALL) -> list[EntryOut]:
    held, watched = await user_symbols(session)
    rows = await session.scalars(select(EntryCandidate).join(Instrument))
    out = [entry_out(c, held, watched) for c in rows]
    if view == EntryView.PORTFOLIO:
        out = [e for e in out if e.held]
    elif view == EntryView.WATCHLIST:
        out = [e for e in out if e.watched and not e.held]
    return sorted(
        out,
        key=lambda e: (
            not e.rules,
            STATE_ORDER.get(e.state or "", 9),
            float(e.distance_atr) if e.distance_atr is not None else 99,
        ),
    )


@router.get("/outcomes", response_model=list[OutcomeStat])
async def outcomes(session: Session) -> list[dict[str, Any]]:
    return await outcome_stats(session)


@router.get("/{symbol}", response_model=EntryOut)
async def entry(session: Session, symbol: str) -> EntryOut:
    held, watched = await user_symbols(session)
    row = await session.scalar(
        select(EntryCandidate)
        .join(Instrument)
        .where(Instrument.symbol == symbol.upper())
        .order_by(Instrument.tradable_for_user.desc())
        .limit(1)
    )
    if row is None:
        raise HTTPException(404, detail="entry_not_found")
    return entry_out(row, held, watched)


@router.post("/refresh", response_model=Queued, status_code=202)
async def refresh(settings: Annotated[Settings, Depends(get_settings)]) -> Queued:
    job_id = await enqueue(settings, "entries", job_id="entries:manual")
    if job_id is None:
        raise HTTPException(503, detail="queue_unavailable")
    return Queued(job_id=job_id)
