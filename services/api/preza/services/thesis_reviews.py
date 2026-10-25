"""Deterministic review publication and explicit user decisions (ADR-0012).

All functions use the caller's transaction and never commit or call an LLM. Reserve
and commit a snapshot, then mark_dispatched and commit BEFORE external dispatch.
Only its successful dispatcher may finalize. A restart after dispatch must fail
unknown, never send again. Snapshots must not be edited after reservation.
"""

import json
import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any
from urllib.parse import urlsplit

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from preza.domain.thesis import ThesisClaimStatusChange, ThesisEvidence
from preza.domain.thesis_review import AcceptProposal, DismissProposal, ReviewBatch
from preza.models import (
    Event,
    NewsItem,
    Signal,
    Thesis,
    ThesisClaim,
    ThesisClaimEvent,
    ThesisClaimReviewProposal,
    ThesisReview,
    ThesisRevision,
)
from preza.services import theses

MAX_CLAIMS = 20
MAX_EVIDENCE = 30
MAX_INPUT_BYTES = 32 * 1024
TERMINAL = {"done", "done_no_evidence", "failed", "failed_unknown", "stale", "skipped_limits"}
# Notification priority only, NOT a probability of a thesis break.
BREAK_PRIORITY = Decimal("0.8")


def week_start(at: datetime) -> date:
    if at.tzinfo is None or at.utcoffset() is None:
        raise ValueError("timezone required")
    day = at.astimezone(UTC).date()
    return day - timedelta(days=day.weekday())


def is_official(kind: str, source: str, url: str) -> bool:
    """Explicit ingest + host allowlist. Kind or a model's assertion is insufficient."""
    try:
        parsed = urlsplit(url)
        host = parsed.hostname
    except ValueError:
        return False
    if parsed.scheme != "https" or parsed.username or parsed.password:
        return False
    return (
        kind == "filing"
        and source == "edgar"
        and host in {"sec.gov", "www.sec.gov", "archives.sec.gov"}
    ) or (
        kind == "press_release"
        and source == "rss:prnewswire"
        and host in {"prnewswire.com", "www.prnewswire.com"}
    )


def evidence_policy(
    kind: str, source: str, url: str, *, triaged: bool = False, event_is_rumor: bool = True
) -> tuple[bool, bool]:
    official = is_official(kind, source, url)
    rumor = kind == "social" or (not official and (not triaged or event_is_rumor))
    return official, rumor


def validate_batch(snapshot: dict[str, Any], batch: ReviewBatch) -> None:
    expected = {c["claim_id"] for c in snapshot["claims"]}
    if {str(c.claim_id) for c in batch.claims} != expected:
        raise ValueError("claim_ids_mismatch")
    allowed = {e["ref"] for e in snapshot["evidence"]}
    if any(ref not in allowed for c in batch.claims for ref in c.evidence_ids):
        raise ValueError("evidence_ids_mismatch")


def signal_eligible(suggested_status: str | None, cited: list[dict[str, Any]]) -> bool:
    return suggested_status == "broken" and any(e["official"] and not e["is_rumor"] for e in cited)


async def _last_event(session: AsyncSession, claim_id: uuid.UUID) -> uuid.UUID | None:
    return await session.scalar(
        select(ThesisClaimEvent.id)
        .where(ThesisClaimEvent.claim_id == claim_id)
        .order_by(ThesisClaimEvent.created_at.desc(), ThesisClaimEvent.id.desc())
        .limit(1)
    )


async def build_snapshot(
    session: AsyncSession, revision_id: uuid.UUID, cutoff: datetime
) -> dict[str, Any]:
    """Resolve provenance from news_item, not from the model. Caller holds thesis lock."""
    week_start(cutoff)  # require an aware time
    cutoff = cutoff.astimezone(UTC)
    revision = await session.get(ThesisRevision, revision_id)
    if revision is None:
        raise HTTPException(404, "thesis_revision_not_found")
    thesis = await theses.get_thesis(session, revision.thesis_id)
    previous = await session.scalar(
        select(func.max(ThesisReview.input_cutoff)).where(
            ThesisReview.revision_id == revision_id,
            ThesisReview.status.in_(("done", "done_no_evidence")),
            ThesisReview.input_cutoff < cutoff,
        )
    )
    input_from = previous or cutoff - timedelta(days=30)
    claims = list(
        await session.scalars(
            select(ThesisClaim)
            .where(ThesisClaim.revision_id == revision_id)
            .order_by(ThesisClaim.ordinal)
        )
    )
    snapshot: dict[str, Any] = {
        "revision_id": str(revision_id),
        "thesis_id": str(thesis.id),
        "symbol": thesis.instrument.symbol,
        "locale": revision.locale,
        "input_from": input_from.isoformat(),
        "input_cutoff": cutoff.isoformat(),
        "window_mode": "fetched_at" if previous else "published_at",
        "claims": [],
        "evidence": [],
        "selected_ids": [],
        "omitted_count": 0,
        "truncated": False,
    }
    if not claims or len(claims) > MAX_CLAIMS:
        snapshot["limit_error"] = "claim_limit"
        snapshot["claim_count"] = len(claims)
        return snapshot
    for claim in claims:
        last = await _last_event(session, claim.id)
        snapshot["claims"].append(
            {
                "claim_id": str(claim.id),
                "statement": claim.statement,
                "original_text": claim.original_text,
                "trigger_kind": claim.trigger_kind,
                "invalidated_if": claim.invalidated_if,
                "status": claim.status,
                "last_event_id": str(last) if last else None,
            }
        )
    query = (
        select(NewsItem, Event.is_rumor, Event.triaged_at)
        .outerjoin(Event, Event.id == NewsItem.event_id)
        .where(
            NewsItem.symbols.contains([thesis.instrument.symbol]),
            NewsItem.source != "demo",
            NewsItem.kind.in_(("news", "filing", "press_release", "social")),
            NewsItem.published_at <= cutoff,
            NewsItem.fetched_at <= cutoff,
            NewsItem.fetched_at > input_from if previous else NewsItem.published_at >= input_from,
        )
        .order_by(NewsItem.fetched_at.desc(), NewsItem.id.desc())
    )
    evidence = []
    for item, event_rumor, triaged_at in await session.execute(query):
        official, rumor = evidence_policy(
            item.kind,
            item.source,
            item.url,
            triaged=triaged_at is not None,
            event_is_rumor=event_rumor if event_rumor is not None else True,
        )
        evidence.append(
            {
                "ref": f"news_item:{item.id}",
                "source": item.source,
                "as_of": item.published_at.isoformat(),
                "url": item.url,
                "is_rumor": rumor,
                "official": official,
                "kind": item.kind,
                "title": item.title,
                "excerpt": (item.summary or "")[:1000],
                "fetched_at": item.fetched_at.isoformat(),
            }
        )
    reserved = [e for e in evidence if e["official"]][:10]
    refs = {e["ref"] for e in reserved}
    selected = (
        reserved + [e for e in evidence if e["ref"] not in refs][: MAX_EVIDENCE - len(reserved)]
    )
    # Restore the deterministic fetched_at DESC, id DESC order, including reserved items.
    selected_refs = {e["ref"] for e in selected}
    snapshot["evidence"] = [e for e in evidence if e["ref"] in selected_refs]
    snapshot["selected_ids"] = [e["ref"] for e in snapshot["evidence"]]
    snapshot["omitted_count"] = len(evidence) - len(selected)
    snapshot["truncated"] = bool(snapshot["omitted_count"])
    while len(json.dumps(snapshot, ensure_ascii=False).encode("utf-8")) > MAX_INPUT_BYTES:
        texts = [(e, k) for e in snapshot["evidence"] for k in ("excerpt", "title") if e[k]]
        if not texts:
            snapshot["limit_error"] = "input_limit"
            break
        item, key = max(texts, key=lambda pair: len(pair[0][pair[1]]))
        item[key] = item[key][: len(item[key]) // 2]
        snapshot["truncated"] = True
    return snapshot


async def reserve_review(
    session: AsyncSession,
    revision_id: uuid.UUID,
    *,
    cutoff: datetime | None = None,
    prompt_version: str = "thesis-review-v1",
) -> tuple[ThesisReview, bool]:
    """Reserve once per UTC ISO week. Existing reservations are never redispatched here."""
    cutoff = cutoff or datetime.now(UTC)
    monday = week_start(cutoff)
    revision = await session.get(ThesisRevision, revision_id)
    if revision is None:
        raise HTTPException(404, "thesis_revision_not_found")
    await theses.get_thesis(session, revision.thesis_id, lock=True)
    await session.refresh(revision)
    existing = await session.scalar(
        select(ThesisReview)
        .where(ThesisReview.revision_id == revision_id, ThesisReview.week_start == monday)
        .execution_options(populate_existing=True)
    )
    if existing is not None:
        return existing, False
    if revision.status != "active":
        raise HTTPException(409, "claim_revision_not_active")
    snapshot = await build_snapshot(session, revision_id, cutoff)
    status = "queued"
    if snapshot.get("limit_error"):
        status = "skipped_limits"
    elif not snapshot["evidence"]:
        status = "done_no_evidence"
    review = ThesisReview(
        revision_id=revision_id,
        week_start=monday,
        status=status,
        as_of=cutoff.astimezone(UTC),
        input_cutoff=cutoff.astimezone(UTC),
        input_from=datetime.fromisoformat(snapshot["input_from"]),
        snapshot=snapshot,
        truncated=snapshot["truncated"],
        prompt_version=prompt_version,
        error_code=snapshot.get("limit_error"),
        finished_at=datetime.now(UTC) if status in TERMINAL else None,
    )
    session.add(review)
    await session.flush()
    return review, True


async def _locked_review(
    session: AsyncSession, review_id: uuid.UUID
) -> tuple[ThesisReview, ThesisRevision, Thesis]:
    review = await session.get(ThesisReview, review_id)
    if review is None:
        raise HTTPException(404, "thesis_review_not_found")
    revision = await session.get(ThesisRevision, review.revision_id)
    assert revision is not None
    thesis = await theses.get_thesis(session, revision.thesis_id, lock=True)
    await session.refresh(revision)
    await session.refresh(review, with_for_update=True)
    return review, revision, thesis


async def mark_dispatched(session: AsyncSession, review_id: uuid.UUID) -> ThesisReview:
    """CAS dispatch guard. Commit before HTTP. A second worker gets 409, not permission."""
    review, revision, _ = await _locked_review(session, review_id)
    if review.status != "queued" or review.dispatch_at is not None:
        raise HTTPException(409, "review_already_dispatched_or_finished")
    if revision.status != "active":
        review.status = "stale"
        review.finished_at = datetime.now(UTC)
    else:
        review.status = "running"
        review.started_at = review.dispatch_at = datetime.now(UTC)
    await session.flush()
    return review


async def fail_review(
    session: AsyncSession,
    review_id: uuid.UUID,
    error_code: str,
    *,
    unknown: bool = False,
    attempts: int = 0,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    cost: Decimal | None = None,
    model: str | None = None,
) -> ThesisReview:
    """Store safe codes only; never provider text, prompts or credentials."""
    allowed = {
        "role_unavailable",
        "timeout",
        "invalid_output",
        "invalid_references",
        "interrupted",
        "internal_error",
    }
    review, _, _ = await _locked_review(session, review_id)
    if review.status in TERMINAL:
        return review
    review.status = "failed_unknown" if unknown else "failed"
    review.error_code = error_code if error_code in allowed else "internal_error"
    review.attempts, review.prompt_tokens, review.completion_tokens = (
        attempts,
        prompt_tokens,
        completion_tokens,
    )
    review.cost, review.model = cost, model
    review.finished_at = datetime.now(UTC)
    await session.flush()
    return review


async def finalize_review(
    session: AsyncSession,
    review_id: uuid.UUID,
    batch: ReviewBatch,
    *,
    model: str | None = None,
    attempts: int = 1,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    cost: Decimal | None = None,
) -> ThesisReview:
    """Validate all references before atomic publication. Never writes claims or events."""
    review, revision, thesis = await _locked_review(session, review_id)
    if review.status in TERMINAL:
        return review
    if review.status != "running" or review.dispatch_at is None:
        raise HTTPException(409, "review_not_dispatched")
    if revision.status != "active":
        review.model, review.cost = model, cost
        review.attempts, review.prompt_tokens, review.completion_tokens = (
            attempts,
            prompt_tokens,
            completion_tokens,
        )
        review.status, review.finished_at = "stale", datetime.now(UTC)
        await session.flush()
        return review
    try:
        validate_batch(review.snapshot, batch)
    except ValueError:
        return await fail_review(
            session,
            review_id,
            "invalid_references",
            model=model,
            attempts=attempts,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost=cost,
        )
    # A savepoint also prevents partial publication if a flush fails and the caller catches it.
    async with session.begin_nested():
        claims = {c["claim_id"]: c for c in review.snapshot["claims"]}
        evidence = {e["ref"]: e for e in review.snapshot["evidence"]}
        actual_ids = set(
            await session.scalars(
                select(ThesisClaim.id).where(ThesisClaim.revision_id == revision.id)
            )
        )
        if actual_ids != {c.claim_id for c in batch.claims}:
            raise ValueError("claim_revision_mismatch")
        for assessment in batch.claims:
            saved = claims[str(assessment.claim_id)]
            cited = [evidence[ref] for ref in assessment.evidence_ids]
            resolved = [
                ThesisEvidence.model_validate(
                    {k: e[k] for k in ("ref", "url", "source", "as_of", "is_rumor")}
                ).model_dump(mode="json")
                for e in cited
            ]
            proposal = ThesisClaimReviewProposal(
                review_id=review.id,
                claim_id=assessment.claim_id,
                status_at_review=saved["status"],
                last_claim_event_id_at_review=uuid.UUID(saved["last_event_id"])
                if saved["last_event_id"]
                else None,
                suggested_status=assessment.suggested_status,
                assessment=assessment.assessment,
                rationale=assessment.rationale,
                evidence=resolved,
                as_of=review.input_cutoff,
            )
            if signal_eligible(assessment.suggested_status, cited):
                signal = Signal(
                    instrument_id=thesis.instrument_id,
                    kind="thesis_break",
                    source="agent",
                    direction="down",
                    horizon="months",
                    strength=BREAK_PRIORITY,
                    confidence=None,
                    status="new",
                    is_rumor=any(e["is_rumor"] for e in cited),
                    rationale=f"Review proposal: possible thesis break. {assessment.rationale}",
                    rationale_i18n={
                        "sl": f"Predlog pregleda: možen zlom teze. {assessment.rationale}",
                        "en": f"Review proposal: possible thesis break. {assessment.rationale}",
                    },
                    evidence=[
                        {
                            "kind": "news",
                            "label": e["title"] or e["ref"],
                            "ref_id": e["ref"].split(":")[1],
                            **{
                                k: e[k]
                                for k in ("url", "source", "as_of", "is_rumor", "official", "ref")
                            },
                        }
                        for e in cited
                    ],
                    expires_at=datetime.now(UTC) + timedelta(days=30),
                )
                session.add(signal)
                await session.flush()
                proposal.signal_id = signal.id
            session.add(proposal)
        review.status, review.finished_at = "done", datetime.now(UTC)
        review.model, review.cost = model, cost
        review.attempts, review.prompt_tokens, review.completion_tokens = (
            attempts,
            prompt_tokens,
            completion_tokens,
        )
        await session.flush()
    return review


async def _proposal(
    session: AsyncSession, thesis_id: uuid.UUID, proposal_id: uuid.UUID
) -> tuple[ThesisClaimReviewProposal, ThesisRevision]:
    await theses.get_thesis(session, thesis_id, lock=True)
    proposal = await session.scalar(
        select(ThesisClaimReviewProposal)
        .join(ThesisReview, ThesisReview.id == ThesisClaimReviewProposal.review_id)
        .join(ThesisRevision, ThesisRevision.id == ThesisReview.revision_id)
        .where(ThesisClaimReviewProposal.id == proposal_id, ThesisRevision.thesis_id == thesis_id)
        .with_for_update(of=ThesisClaimReviewProposal)
        .execution_options(populate_existing=True)
    )
    if proposal is None:
        raise HTTPException(404, "review_proposal_not_found")
    review = await session.get(ThesisReview, proposal.review_id)
    assert review is not None
    revision = await theses.get_revision(session, thesis_id, review.revision_id)
    await session.refresh(revision)
    return proposal, revision


async def accept_proposal(
    session: AsyncSession, thesis_id: uuid.UUID, proposal_id: uuid.UUID, body: AcceptProposal
) -> ThesisClaimReviewProposal:
    proposal, revision = await _proposal(session, thesis_id, proposal_id)
    if proposal.state == "accepted":
        return proposal
    if (
        proposal.state != "pending"
        or proposal.suggested_status is None
        or revision.status != "active"
    ):
        raise HTTPException(409, "proposal_not_acceptable")
    claim = await session.get(ThesisClaim, proposal.claim_id, populate_existing=True)
    assert claim is not None
    latest = await _last_event(session, claim.id)
    if (
        body.expected_status != proposal.status_at_review
        or claim.status != proposal.status_at_review
        or body.expected_last_event_id != proposal.last_claim_event_id_at_review
        or latest != proposal.last_claim_event_id_at_review
    ):
        raise HTTPException(409, "claim_changed_since_review")
    change = ThesisClaimStatusChange.model_validate(
        {
            "to_status": proposal.suggested_status,
            "expected_status": body.expected_status,
            "rationale": proposal.rationale,
            "evidence": proposal.evidence,
        }
    )
    async with session.begin_nested():
        previous_ids = list(
            await session.scalars(
                select(ThesisClaimEvent.id).where(ThesisClaimEvent.claim_id == claim.id)
            )
        )
        await theses.change_claim_status(session, thesis_id, claim.id, change)
        # Locate the newly written event even when created_at ties an earlier event.
        event = await session.scalar(
            select(ThesisClaimEvent.id)
            .where(
                ThesisClaimEvent.claim_id == claim.id,
                ThesisClaimEvent.id.not_in(previous_ids),
            )
            .order_by(ThesisClaimEvent.created_at.desc(), ThesisClaimEvent.id.desc())
            .limit(1)
        )
        assert event is not None, "change_claim_status must append an event"
        proposal.accepted_event_id = event
        proposal.state, proposal.decided_at = "accepted", datetime.now(UTC)
        await session.flush()
    return proposal


async def dismiss_proposal(
    session: AsyncSession, thesis_id: uuid.UUID, proposal_id: uuid.UUID, body: DismissProposal
) -> ThesisClaimReviewProposal:
    proposal, _ = await _proposal(session, thesis_id, proposal_id)
    if proposal.state == "dismissed":
        return proposal
    if proposal.state != "pending":
        raise HTTPException(409, "proposal_already_accepted")
    if proposal.signal_id:
        signal = await session.scalar(
            select(Signal)
            .where(Signal.id == proposal.signal_id)
            .with_for_update(of=Signal)
            .execution_options(populate_existing=True)
        )
        if signal is not None and signal.status in {"new", "watching"}:
            signal.status, signal.status_reason = "dismissed", "review_proposal_dismissed"
    proposal.state, proposal.decided_at = "dismissed", datetime.now(UTC)
    proposal.dismissal_reason = body.reason
    await session.flush()
    return proposal


async def list_reviews(
    session: AsyncSession, thesis_id: uuid.UUID, limit: int = 30, offset: int = 0
) -> list[ThesisReview]:
    await theses.get_thesis(session, thesis_id)
    return list(
        await session.scalars(
            select(ThesisReview)
            .join(ThesisRevision)
            .where(ThesisRevision.thesis_id == thesis_id)
            .order_by(ThesisReview.week_start.desc(), ThesisReview.id)
            .limit(limit)
            .offset(offset)
        )
    )


async def list_proposals(
    session: AsyncSession,
    thesis_id: uuid.UUID,
    state: str | None = "pending",
    limit: int = 30,
    offset: int = 0,
) -> list[ThesisClaimReviewProposal]:
    await theses.get_thesis(session, thesis_id)
    query = (
        select(ThesisClaimReviewProposal)
        .join(ThesisReview)
        .join(ThesisRevision)
        .where(ThesisRevision.thesis_id == thesis_id)
    )
    if state:
        query = query.where(ThesisClaimReviewProposal.state == state)
    return list(
        await session.scalars(
            query.order_by(ThesisReview.week_start.desc(), ThesisClaimReviewProposal.id)
            .limit(limit)
            .offset(offset)
        )
    )
