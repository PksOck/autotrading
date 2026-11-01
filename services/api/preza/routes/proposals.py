from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import ValidationError
from sqlalchemy import String, cast, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from preza.config import Settings, get_settings
from preza.db import get_session
from preza.domain.radar import ProposalAnalysisLink, ProposalCreate, ProposalOut, ProposalResult
from preza.models import AnalysisRun, Proposal, Signal
from preza.queue import enqueue

router = APIRouter(prefix="/proposals", tags=["proposals"])
Session = Annotated[AsyncSession, Depends(get_session)]


def verdict_data(
    proposal: Proposal,
) -> tuple[ProposalResult | None, Literal["analysis_failed", "invalid_result"] | None]:
    error: Literal["analysis_failed", "invalid_result"] | None = (
        "analysis_failed" if proposal.status == "failed" else None
    )
    if proposal.status == "done":
        try:
            return ProposalResult.model_validate_json(proposal.verdict or ""), None
        except (ValidationError, ValueError):
            return None, "invalid_result"
    return None, error


async def proposal_out(session: AsyncSession, proposal: Proposal) -> ProposalOut:
    signal_id = await session.scalar(select(Signal.id).where(Signal.proposal_id == proposal.id))
    analyses = list(
        await session.scalars(
            select(AnalysisRun)
            .where(AnalysisRun.proposal_id == proposal.id)
            .order_by(AnalysisRun.created_at.desc(), AnalysisRun.id.desc())
        )
    )
    result, error_code = verdict_data(proposal)
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
async def list_all(
    session: Session,
    status: Literal["all", "pending", "queued", "running", "done", "failed", "attention"] = "all",
    q: str = Query(default="", max_length=100),
    limit: int = Query(default=200, ge=1, le=200),
) -> list[ProposalOut]:
    statement = select(Proposal).order_by(Proposal.created_at.desc(), Proposal.id.desc())
    if status == "pending":
        statement = statement.where(Proposal.status.in_(["queued", "running"]))
    elif status == "attention":
        statement = statement.where(Proposal.status.in_(["failed", "done"]))
    elif status != "all":
        statement = statement.where(Proposal.status == status)
    if q.strip():
        statement = statement.where(
            or_(
                Proposal.hypothesis.icontains(q.strip(), autoescape=True),
                cast(Proposal.symbols, String).icontains(q.strip(), autoescape=True),
            )
        )
    # Validate verdict text before the limit; never cast arbitrary JSON in SQL.
    candidates = await session.stream_scalars(statement.execution_options(yield_per=200))
    selected = []
    try:
        async for proposal in candidates:
            _, error = verdict_data(proposal)
            if (status == "done" and error) or (status == "attention" and not error):
                continue
            selected.append(proposal)
            if len(selected) == limit:
                break
    finally:
        await candidates.close()
    return [await proposal_out(session, proposal) for proposal in selected]


@router.get("/{proposal_id}", response_model=ProposalOut)
async def get_one(session: Session, proposal_id: UUID) -> ProposalOut:
    proposal = await session.get(Proposal, proposal_id)
    if proposal is None:
        raise HTTPException(404, detail="proposal_not_found")
    return await proposal_out(session, proposal)
