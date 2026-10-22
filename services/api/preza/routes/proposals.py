import json
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from preza.config import Settings, get_settings
from preza.db import get_session
from preza.domain.radar import ProposalCreate, ProposalOut
from preza.models import Proposal, Signal
from preza.queue import enqueue

router = APIRouter(prefix="/proposals", tags=["proposals"])
Session = Annotated[AsyncSession, Depends(get_session)]


async def proposal_out(session: AsyncSession, proposal: Proposal) -> ProposalOut:
    signal_id = await session.scalar(select(Signal.id).where(Signal.proposal_id == proposal.id))
    verdict = None
    if proposal.verdict:
        try:
            verdict = json.loads(proposal.verdict).get("summary")
        except (ValueError, AttributeError):
            verdict = proposal.verdict
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
        verdict=verdict,
        signal_id=signal_id,
        created_at=proposal.created_at,
        finished_at=proposal.finished_at,
    )


@router.post("", response_model=ProposalOut, status_code=202)
async def create(
    session: Session, settings: Annotated[Settings, Depends(get_settings)], data: ProposalCreate
) -> ProposalOut:
    proposal = Proposal(
        **data.model_dump(mode="json", exclude={"symbols"}),
        symbols=sorted({s.upper() for s in data.symbols}),
    )
    session.add(proposal)
    await session.flush()
    # If the queue is down the proposal stays "queued"; the worker's sweep picks it up later.
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
