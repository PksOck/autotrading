from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from preza.config import Settings, get_settings
from preza.db import get_session
from preza.domain.radar import ProposalAnalysisLink, ProposalCreate, ProposalOut, ProposalResult
from preza.models import AnalysisRun, Proposal, Signal
from preza.queue import enqueue

router = APIRouter(prefix="/proposals", tags=["proposals"])
Session = Annotated[AsyncSession, Depends(get_session)]


async def proposal_out(session: AsyncSession, proposal: Proposal) -> ProposalOut:
    signal_id = await session.scalar(select(Signal.id).where(Signal.proposal_id == proposal.id))
    analyses = list(
        await session.scalars(
            select(AnalysisRun)
            .where(AnalysisRun.proposal_id == proposal.id)
            .order_by(AnalysisRun.created_at.desc(), AnalysisRun.id.desc())
        )
    )
    result = None
    error_code = "analysis_failed" if proposal.status == "failed" else None
    if proposal.status == "done" and proposal.verdict:
        try:
            result = ProposalResult.model_validate_json(proposal.verdict)
        except (ValidationError, ValueError):
            error_code = "invalid_result"
    elif proposal.status == "done":
        error_code = "invalid_result"
    return ProposalOut(
        id=proposal.id,
        symbols=list(proposal.symbols),
        hypothesis=proposal.hypothesis,
        source_text=proposal.source_text,
        direction=proposal.direction,
        horizon=proposal.horizon,
        depth=proposal.depth,
        save_to=proposal.save_to,
        status=proposal.status,
        verdict=result.summary if result else None,
        verdict_result=result,
        error_code=error_code,
        signal_id=signal_id,
        analysis_id=analyses[0].id if analyses else None,
        analysis_links=[
            ProposalAnalysisLink(id=r.id, symbol=r.instrument.symbol, status=r.status)
            for r in analyses
        ],
        created_at=proposal.created_at,
        finished_at=proposal.finished_at,
    )


@router.post("", response_model=ProposalOut, status_code=202)
async def create(
    session: Session, settings: Annotated[Settings, Depends(get_settings)], data: ProposalCreate
) -> ProposalOut:
    if data.request_id:
        # Serialize acceptance for the same browser operation without a new table or queue job.
        await session.execute(
            text("SELECT pg_advisory_xact_lock(:key)"), {"key": data.request_id.int % (2**63 - 1)}
        )
        existing = await session.get(Proposal, data.request_id)
        if existing:
            expected = data.model_dump(mode="json", exclude={"request_id", "symbols"})
            same = all(getattr(existing, key) == value for key, value in expected.items())
            if not same or set(existing.symbols) != {s.upper() for s in data.symbols}:
                raise HTTPException(409, detail="idempotency_conflict")
            return await proposal_out(session, existing)
    proposal = Proposal(
        **data.model_dump(mode="json", exclude={"symbols", "request_id"}),
        symbols=sorted({s.upper() for s in data.symbols}),
        **({"id": data.request_id} if data.request_id else {}),
    )
    session.add(proposal)
    await session.flush()
    # If the queue is down the proposal stays "queued"; the worker's sweep picks it up later.
    await session.commit()
    await enqueue(
        settings, "analyze_proposal_job", str(proposal.id), job_id=f"proposal:{proposal.id}"
    )
    return await proposal_out(session, proposal)


@router.post("/{proposal_id}/retry", response_model=ProposalOut, status_code=202)
async def retry(
    session: Session, settings: Annotated[Settings, Depends(get_settings)], proposal_id: UUID
) -> ProposalOut:
    proposal = await session.scalar(
        select(Proposal).where(Proposal.id == proposal_id).with_for_update()
    )
    if proposal is None:
        raise HTTPException(404, detail="proposal_not_found")
    # Repeated clicks on an already accepted retry return the same pending operation.
    if proposal.status in {"queued", "running"}:
        return await proposal_out(session, proposal)
    if proposal.status != "failed":
        raise HTTPException(409, detail="proposal_not_failed")
    proposal.status = "queued"
    proposal.verdict = None
    proposal.finished_at = None
    await session.commit()
    await enqueue(
        settings, "analyze_proposal_job", str(proposal.id), job_id=f"proposal:{proposal.id}"
    )
    return await proposal_out(session, proposal)


@router.get("", response_model=list[ProposalOut])
async def list_all(session: Session) -> list[ProposalOut]:
    rows = await session.scalars(select(Proposal).order_by(Proposal.created_at.desc()).limit(200))
    return [await proposal_out(session, p) for p in rows]


@router.get("/{proposal_id}", response_model=ProposalOut)
async def get_one(session: Session, proposal_id: UUID) -> ProposalOut:
    proposal = await session.get(Proposal, proposal_id)
    if proposal is None:
        raise HTTPException(404, detail="proposal_not_found")
    return await proposal_out(session, proposal)
