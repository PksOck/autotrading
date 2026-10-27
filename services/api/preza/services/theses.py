"""Deterministic thesis lifecycle. Mutations share a thesis lock and request transaction."""

import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from preza.domain.analysis import DecisionCard
from preza.domain.thesis import (
    ClaimStatus,
    ThesisClaimEventOut,
    ThesisClaimOut,
    ThesisClaimStatusChange,
    ThesisInstrument,
    ThesisOut,
    ThesisRevisionOut,
    ThesisRevisionPatch,
    ThesisSummary,
)
from preza.models import (
    AnalysisRun,
    Instrument,
    Thesis,
    ThesisClaim,
    ThesisClaimEvent,
    ThesisRevision,
)


async def get_thesis(session: AsyncSession, thesis_id: uuid.UUID, *, lock: bool = False) -> Thesis:
    query = select(Thesis).where(Thesis.id == thesis_id)
    if lock:
        query = query.with_for_update(of=Thesis)
    thesis = await session.scalar(query)
    if thesis is None:
        raise HTTPException(404, detail="thesis_not_found")
    return thesis


async def get_revision(
    session: AsyncSession, thesis_id: uuid.UUID, revision_id: uuid.UUID
) -> ThesisRevision:
    revision = await session.scalar(
        select(ThesisRevision).where(
            ThesisRevision.id == revision_id, ThesisRevision.thesis_id == thesis_id
        )
    )
    if revision is None:
        raise HTTPException(404, detail="thesis_revision_not_found")
    return revision


async def revision_out(session: AsyncSession, revision: ThesisRevision) -> ThesisRevisionOut:
    claims = list(
        await session.scalars(
            select(ThesisClaim)
            .where(ThesisClaim.revision_id == revision.id)
            .order_by(ThesisClaim.ordinal)
        )
    )
    events = await session.scalars(
        select(ThesisClaimEvent)
        .where(ThesisClaimEvent.claim_id.in_([claim.id for claim in claims]))
        .order_by(ThesisClaimEvent.created_at, ThesisClaimEvent.id)
    )
    by_claim: dict[uuid.UUID, list[ThesisClaimEventOut]] = {}
    for event in events:
        by_claim.setdefault(event.claim_id, []).append(ThesisClaimEventOut.model_validate(event))
    out = ThesisRevisionOut.model_validate(revision)
    for claim in claims:
        item = ThesisClaimOut.model_validate(claim)
        item.events = by_claim.get(claim.id, [])
        out.claims.append(item)
    return out


async def create_draft(session: AsyncSession, run_id: uuid.UUID) -> tuple[ThesisRevision, bool]:
    run = await session.get(AnalysisRun, run_id)
    if run is None:
        raise HTTPException(404, detail="analysis_not_found")
    if run.status != "done" or run.finished_at is None or not run.card:
        raise HTTPException(409, detail="analysis_not_finished_with_card")
    card = DecisionCard.model_validate(run.card)
    triggers = [
        (kind, index, text)
        for kind, texts in (("upgrade", card.upgrade_if), ("downgrade", card.downgrade_if))
        for index, text in enumerate(texts)
        if text.strip()
    ]
    if not triggers:
        raise HTTPException(409, detail="analysis_has_no_triggers")
    # Lock the stable parent even before a thesis exists, serializing first creation.
    await session.scalar(
        select(Instrument.id).where(Instrument.id == run.instrument_id).with_for_update()
    )
    thesis = await session.scalar(select(Thesis).where(Thesis.instrument_id == run.instrument_id))
    source = f"analysis_card:{run.id}"
    if thesis is None:
        thesis = Thesis(instrument_id=run.instrument_id, source=source, as_of=run.finished_at)
        session.add(thesis)
        await session.flush()
    else:
        thesis = await get_thesis(session, thesis.id, lock=True)
    existing = await session.scalar(
        select(ThesisRevision).where(
            ThesisRevision.thesis_id == thesis.id, ThesisRevision.analysis_run_id == run.id
        )
    )
    if existing is not None:
        return existing, False
    version = await session.scalar(
        select(func.max(ThesisRevision.version)).where(ThesisRevision.thesis_id == thesis.id)
    )
    revision = ThesisRevision(
        thesis_id=thesis.id,
        version=(version or 0) + 1,
        analysis_run_id=run.id,
        status="draft",
        locale=run.locale,
        delta_note=card.delta_note,
        source=source,
        as_of=run.finished_at,
    )
    session.add(revision)
    await session.flush()
    for ordinal, (kind, index, text) in enumerate(triggers):
        session.add(
            ThesisClaim(
                revision_id=revision.id,
                ordinal=ordinal,
                trigger_kind=kind,
                trigger_index=index,
                original_text=text,
                statement=text,
                status="open",
                source=source,
                as_of=run.finished_at,
            )
        )
    await session.flush()
    return revision, True


async def patch_revision(
    session: AsyncSession,
    thesis_id: uuid.UUID,
    revision_id: uuid.UUID,
    body: ThesisRevisionPatch,
) -> ThesisRevision:
    await get_thesis(session, thesis_id, lock=True)
    revision = await get_revision(session, thesis_id, revision_id)
    if revision.status != "draft":
        raise HTTPException(409, detail="revision_not_draft")
    if body.expected_version is not None and body.expected_version != revision.version:
        raise HTTPException(409, detail="revision_version_conflict")
    if body.expected_edit_count is not None and body.expected_edit_count != revision.edit_count:
        raise HTTPException(409, detail="revision_edit_conflict")
    claims = {
        c.id: c
        for c in await session.scalars(
            select(ThesisClaim).where(ThesisClaim.revision_id == revision.id)
        )
    }
    if any(patch.id not in claims for patch in body.claims):
        raise HTTPException(404, detail="thesis_claim_not_found")
    for patch in body.claims:
        claim = claims[patch.id]
        if "statement" in patch.model_fields_set and patch.statement is not None:
            claim.statement = patch.statement
        if "invalidated_if" in patch.model_fields_set:
            claim.invalidated_if = patch.invalidated_if
        if "expires_at" in patch.model_fields_set:
            claim.expires_at = patch.expires_at
    revision.edit_count += 1
    revision.edited_at = datetime.now(UTC)
    await session.flush()
    return revision


async def confirm_revision(
    session: AsyncSession, thesis_id: uuid.UUID, revision_id: uuid.UUID
) -> ThesisRevision:
    await get_thesis(session, thesis_id, lock=True)
    revision = await get_revision(session, thesis_id, revision_id)
    if revision.status != "draft":
        raise HTTPException(409, detail="revision_not_draft")
    active = await session.scalar(
        select(ThesisRevision).where(
            ThesisRevision.thesis_id == thesis_id, ThesisRevision.status == "active"
        )
    )
    if active is not None:
        active.status = "superseded"
        # Release the partial unique index before activating the replacement.
        await session.flush()
    revision.status = "active"
    revision.confirmed_at = datetime.now(UTC)
    await session.flush()
    return revision


async def change_claim_status(
    session: AsyncSession,
    thesis_id: uuid.UUID,
    claim_id: uuid.UUID,
    body: ThesisClaimStatusChange,
) -> ThesisClaim:
    await get_thesis(session, thesis_id, lock=True)
    claim = await session.scalar(
        select(ThesisClaim)
        .join(ThesisRevision, ThesisRevision.id == ThesisClaim.revision_id)
        .where(ThesisClaim.id == claim_id, ThesisRevision.thesis_id == thesis_id)
    )
    if claim is None:
        raise HTTPException(404, detail="thesis_claim_not_found")
    revision = await get_revision(session, thesis_id, claim.revision_id)
    if revision.status != "active":
        raise HTTPException(409, detail="claim_revision_not_active")
    if claim.status != body.expected_status:
        raise HTTPException(409, detail="claim_status_conflict")
    session.add(
        ThesisClaimEvent(
            claim_id=claim.id,
            from_status=claim.status,
            to_status=body.to_status,
            actor="user",
            rationale=body.rationale,
            evidence=[e.model_dump(mode="json") for e in body.evidence],
            source="user",
            as_of=datetime.now(UTC),
        )
    )
    claim.status = body.to_status
    await session.flush()
    return claim


async def detail(session: AsyncSession, thesis: Thesis) -> ThesisOut:
    revisions = await session.scalars(
        select(ThesisRevision)
        .where(ThesisRevision.thesis_id == thesis.id)
        .order_by(ThesisRevision.version.desc())
    )
    items = [await revision_out(session, r) for r in revisions]
    times = [thesis.created_at]
    for revision in items:
        times.append(revision.created_at)
        if revision.confirmed_at:
            times.append(revision.confirmed_at)
        if revision.edited_at:
            times.append(revision.edited_at)
        for claim in revision.claims:
            times.extend(event.created_at for event in claim.events)
    return ThesisOut(
        id=thesis.id,
        instrument=ThesisInstrument(
            id=thesis.instrument_id, symbol=thesis.instrument.symbol, name=thesis.instrument.name
        ),
        source=thesis.source,
        as_of=thesis.as_of,
        created_at=thesis.created_at,
        updated_at=max(times),
        revisions=items,
    )


async def list_theses(
    session: AsyncSession, symbol: str | None, limit: int, offset: int
) -> list[ThesisSummary]:
    query = select(Thesis).order_by(Thesis.created_at.desc(), Thesis.id).limit(limit).offset(offset)
    if symbol:
        query = query.join(Instrument).where(Instrument.symbol == symbol.upper())
    page = list(await session.scalars(query))
    if not page:
        return []
    thesis_ids = [thesis.id for thesis in page]
    revisions = await session.scalars(
        select(ThesisRevision)
        .where(ThesisRevision.thesis_id.in_(thesis_ids))
        .order_by(ThesisRevision.version.desc())
    )
    by_thesis: dict[uuid.UUID, list[ThesisRevision]] = {}
    updated = {thesis.id: thesis.created_at for thesis in page}
    for revision in revisions:
        by_thesis.setdefault(revision.thesis_id, []).append(revision)
        updated[revision.thesis_id] = max(
            updated[revision.thesis_id],
            revision.created_at,
            revision.confirmed_at or revision.created_at,
            revision.edited_at or revision.created_at,
        )
    # Summaries never load claim bodies or the potentially large audit payloads.
    count_rows = await session.execute(
        select(ThesisRevision.thesis_id, ThesisClaim.status, func.count(ThesisClaim.id))
        .join(ThesisClaim, ThesisClaim.revision_id == ThesisRevision.id)
        .where(ThesisRevision.thesis_id.in_(thesis_ids), ThesisRevision.status == "active")
        .group_by(ThesisRevision.thesis_id, ThesisClaim.status)
    )
    counts_by_thesis: dict[uuid.UUID, dict[str, int]] = {}
    for thesis_id, status, count in count_rows:
        counts_by_thesis.setdefault(thesis_id, {})[status] = count
    event_rows = await session.execute(
        select(ThesisRevision.thesis_id, func.max(ThesisClaimEvent.created_at))
        .join(ThesisClaim, ThesisClaim.revision_id == ThesisRevision.id)
        .join(ThesisClaimEvent, ThesisClaimEvent.claim_id == ThesisClaim.id)
        .where(ThesisRevision.thesis_id.in_(thesis_ids))
        .group_by(ThesisRevision.thesis_id)
    )
    for thesis_id, event_time in event_rows:
        updated[thesis_id] = max(updated[thesis_id], event_time)
    result = []
    for thesis in page:
        items = by_thesis.get(thesis.id, [])
        active = next((r for r in items if r.status == "active"), None)
        draft = next((r for r in items if r.status == "draft"), None)
        counts: dict[ClaimStatus, int] = {
            "open": 0,
            "confirmed": 0,
            "weakening": 0,
            "broken": 0,
            "expired": 0,
        }
        for status in counts:
            counts[status] = counts_by_thesis.get(thesis.id, {}).get(status, 0)
        result.append(
            ThesisSummary(
                id=thesis.id,
                instrument=ThesisInstrument(
                    id=thesis.instrument_id,
                    symbol=thesis.instrument.symbol,
                    name=thesis.instrument.name,
                ),
                active_revision_version=active.version if active else None,
                claim_status_counts=counts,
                latest_draft_id=draft.id if draft else None,
                updated_at=updated[thesis.id],
            )
        )
    return result
