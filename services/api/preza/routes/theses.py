"""Thesis drafts and explicit user decisions. No broker, signals or LLM calls."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from preza.db import get_session
from preza.domain.thesis import (
    ThesisClaimOut,
    ThesisClaimStatusChange,
    ThesisDraftCreate,
    ThesisOut,
    ThesisRevisionOut,
    ThesisRevisionPatch,
    ThesisSummary,
)
from preza.domain.thesis_review import (
    AcceptProposal,
    ClaimReviewProposalOut,
    DismissProposal,
    ProposalState,
    ReviewOut,
)
from preza.services import theses, thesis_reviews

router = APIRouter(prefix="/theses", tags=["theses"])
Session = Annotated[AsyncSession, Depends(get_session)]


@router.post(
    "/drafts",
    response_model=ThesisRevisionOut,
    status_code=201,
    responses={200: {"model": ThesisRevisionOut}},
)
async def create_draft(
    body: ThesisDraftCreate, response: Response, session: Session
) -> ThesisRevisionOut:
    revision, created = await theses.create_draft(session, body.analysis_run_id)
    response.status_code = 201 if created else 200
    return await theses.revision_out(session, revision)


@router.get("", response_model=list[ThesisSummary])
async def list_theses(
    session: Session,
    symbol: Annotated[str | None, Query(min_length=1, max_length=20)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ThesisSummary]:
    return await theses.list_theses(session, symbol, limit, offset)


@router.get("/{thesis_id}", response_model=ThesisOut)
async def get_thesis(thesis_id: uuid.UUID, session: Session) -> ThesisOut:
    return await theses.detail(session, await theses.get_thesis(session, thesis_id))


@router.patch("/{thesis_id}/revisions/{revision_id}", response_model=ThesisRevisionOut)
async def patch_revision(
    thesis_id: uuid.UUID, revision_id: uuid.UUID, body: ThesisRevisionPatch, session: Session
) -> ThesisRevisionOut:
    revision = await theses.patch_revision(session, thesis_id, revision_id, body)
    return await theses.revision_out(session, revision)


@router.post("/{thesis_id}/revisions/{revision_id}/confirm", response_model=ThesisRevisionOut)
async def confirm_revision(
    thesis_id: uuid.UUID, revision_id: uuid.UUID, session: Session
) -> ThesisRevisionOut:
    revision = await theses.confirm_revision(session, thesis_id, revision_id)
    return await theses.revision_out(session, revision)


@router.post("/{thesis_id}/claims/{claim_id}/status", response_model=ThesisClaimOut)
async def change_claim_status(
    thesis_id: uuid.UUID, claim_id: uuid.UUID, body: ThesisClaimStatusChange, session: Session
) -> ThesisClaimOut:
    claim = await theses.change_claim_status(session, thesis_id, claim_id, body)
    revision = await theses.get_revision(session, thesis_id, claim.revision_id)
    out = await theses.revision_out(session, revision)
    return next(item for item in out.claims if item.id == claim.id)


@router.get("/{thesis_id}/reviews", response_model=list[ReviewOut])
async def list_reviews(
    thesis_id: uuid.UUID,
    session: Session,
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ReviewOut]:
    return [
        ReviewOut.model_validate(r)
        for r in await thesis_reviews.list_reviews(session, thesis_id, limit, offset)
    ]


@router.get("/{thesis_id}/review-proposals", response_model=list[ClaimReviewProposalOut])
async def list_review_proposals(
    thesis_id: uuid.UUID,
    session: Session,
    state: ProposalState | None = "pending",
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ClaimReviewProposalOut]:
    return [
        ClaimReviewProposalOut.model_validate(p)
        for p in await thesis_reviews.list_proposals(session, thesis_id, state, limit, offset)
    ]


@router.post(
    "/{thesis_id}/review-proposals/{proposal_id}/accept", response_model=ClaimReviewProposalOut
)
async def accept_review_proposal(
    thesis_id: uuid.UUID,
    proposal_id: uuid.UUID,
    body: AcceptProposal,
    session: Session,
) -> ClaimReviewProposalOut:
    return ClaimReviewProposalOut.model_validate(
        await thesis_reviews.accept_proposal(session, thesis_id, proposal_id, body)
    )


@router.post(
    "/{thesis_id}/review-proposals/{proposal_id}/dismiss", response_model=ClaimReviewProposalOut
)
async def dismiss_review_proposal(
    thesis_id: uuid.UUID,
    proposal_id: uuid.UUID,
    body: DismissProposal,
    session: Session,
) -> ClaimReviewProposalOut:
    return ClaimReviewProposalOut.model_validate(
        await thesis_reviews.dismiss_proposal(session, thesis_id, proposal_id, body)
    )
