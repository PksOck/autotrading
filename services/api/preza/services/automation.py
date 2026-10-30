"""Durable process policy, outbox and shared-quota batch acceptance."""

import uuid
from datetime import UTC, datetime, time, timedelta
from typing import Literal

from fastapi import HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from preza.config import Settings
from preza.domain.automation import (
    BatchInput,
    BatchItem,
    BatchPreview,
    PolicyInput,
    PolicyOut,
    in_window,
    next_slots,
)
from preza.models import AnalysisRun, Instrument, WatchlistItem
from preza.models_automation import (
    AutomationControl,
    ProcessAnalysis,
    ProcessExecution,
    ProcessPolicy,
)
from preza.queue import enqueue
from preza.services.analyses import lock_quota, new_run, used_today

LEGACY_PROCESSES = (
    "sync_flex",
    "refresh_bars",
    "radar",
    "entries",
    "fundamentals",
    "outcomes",
    "notify",
    "digest",
    "refresh_etf_profiles",
    "discover_thesis_reviews",
)
AGENT_PROCESSES = {"refresh_etf_profiles", "discover_thesis_reviews"}
ANALYSIS_PROCESSES = {"entries", "discover_thesis_reviews", "batch_analyses"}
PROCESS_KEYS = (*LEGACY_PROCESSES, "batch_analyses")


async def ensure_policies(session: AsyncSession) -> None:
    await session.execute(
        insert(AutomationControl).values(id=1, paused=False, revision=0).on_conflict_do_nothing()
    )
    for key in PROCESS_KEYS:
        default = PolicyInput(
            enabled=key in LEGACY_PROCESSES,
            schedule_kind="legacy" if key in LEGACY_PROCESSES else "manual",
        )
        await session.execute(
            insert(ProcessPolicy)
            .values(
                process_key=key,
                enabled=default.enabled,
                revision=0,
                config=default.model_dump(exclude={"enabled", "revision"}),
                updated_at=datetime.now(UTC),
            )
            .on_conflict_do_nothing()
        )


def policy_input(row: ProcessPolicy) -> PolicyInput:
    return PolicyInput(**row.config, enabled=row.enabled, revision=row.revision)


def policy_out(row: ProcessPolicy) -> PolicyOut:
    policy = policy_input(row)
    return PolicyOut(
        **policy.model_dump(),
        process_key=row.process_key,
        next_runs=next_slots(policy, datetime.now(UTC)),
    )


async def update_policy(session: AsyncSession, key: str, body: PolicyInput) -> PolicyOut:
    await ensure_policies(session)
    if key == "batch_analyses" and body.schedule_kind == "legacy":
        raise HTTPException(422, "no_legacy_batch_schedule")
    result = await session.execute(
        update(ProcessPolicy)
        .where(ProcessPolicy.process_key == key, ProcessPolicy.revision == body.revision)
        .values(
            enabled=body.enabled,
            revision=body.revision + 1,
            config=body.model_dump(exclude={"enabled", "revision"}),
            updated_at=datetime.now(UTC),
        )
        .returning(ProcessPolicy)
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(
            409 if key in PROCESS_KEYS else 404,
            "revision_conflict" if key in PROCESS_KEYS else "process_not_found",
        )
    return policy_out(row)


async def gate(
    session: AsyncSession,
    key: str,
    *,
    automatic: bool = True,
    outside_window: bool = False,
    now: datetime | None = None,
) -> str | None:
    policy = await session.get(ProcessPolicy, key, populate_existing=True)
    if policy is None:
        return None if key in LEGACY_PROCESSES else "disabled"
    control = await session.get(AutomationControl, 1, populate_existing=True)
    if not policy.enabled:
        return "disabled"
    if automatic and control is not None and control.paused:
        return "paused"
    if (
        automatic
        and key in ANALYSIS_PROCESSES
        and control is not None
        and not control.automatic_analyses_enabled
    ):
        return "analyses_disabled"
    if not outside_window and not in_window(policy_input(policy), now or datetime.now(UTC)):
        return "outside_window"
    return None


async def automatic_analyses_allowed(session: AsyncSession) -> bool:
    control = await session.get(AutomationControl, 1, populate_existing=True)
    return control is None or (not control.paused and control.automatic_analyses_enabled)


async def materialize(
    session: AsyncSession,
    key: str,
    slot: datetime,
    origin: str = "automatic",
    outside_window: bool = False,
) -> uuid.UUID:
    row = await session.get(ProcessPolicy, key)
    if row is None:
        raise HTTPException(404, "process_not_found")
    execution_id = uuid.uuid4()
    await session.execute(
        insert(ProcessExecution)
        .values(
            id=execution_id,
            process_key=key,
            policy_revision=row.revision,
            scheduled_for=slot,
            origin=origin,
            outside_window=outside_window,
            state="pending",
            job_id=f"process:{execution_id}",
            counts={},
        )
        .on_conflict_do_nothing(constraint="uq_process_slot")
    )
    existing = await session.scalar(
        select(ProcessExecution.id).where(
            ProcessExecution.process_key == key, ProcessExecution.scheduled_for == slot
        )
    )
    assert existing is not None
    return existing


async def claim(session: AsyncSession, execution_id: uuid.UUID) -> ProcessExecution | None:
    execution = await session.scalar(
        select(ProcessExecution)
        .where(ProcessExecution.id == execution_id, ProcessExecution.state == "pending")
        .with_for_update(skip_locked=True)
    )
    if execution is None:
        return None
    row = await session.get(ProcessPolicy, execution.process_key, populate_existing=True)
    if row is None or row.revision != execution.policy_revision:
        execution.state, execution.reason = "skipped", "policy_changed"
        execution.finished_at = datetime.now(UTC)
        return None
    reason = await gate(
        session,
        execution.process_key,
        automatic=execution.origin == "automatic",
        outside_window=execution.outside_window,
    )
    if reason:
        execution.reason = reason
        if reason == "disabled":
            execution.state, execution.finished_at = "skipped", datetime.now(UTC)
        return None
    execution.state = "running"
    execution.reason = None
    execution.started_at = execution.heartbeat_at = datetime.now(UTC)
    return execution


async def deliver_pending(session: AsyncSession, settings: Settings) -> int:
    """Pending rows are the outbox. Delivery does not delete their durable intent."""
    rows = list(
        await session.scalars(
            select(ProcessExecution)
            .where(ProcessExecution.state == "pending")
            .order_by(ProcessExecution.scheduled_for)
            .limit(100)
        )
    )
    delivered = 0
    for row in rows:
        if await gate(
            session,
            row.process_key,
            automatic=row.origin == "automatic",
            outside_window=row.outside_window,
        ):
            continue
        job = await enqueue(
            settings,
            "execute_process",
            str(row.id),
            job_id=row.job_id,
            queue_name="arq:agents" if row.process_key in AGENT_PROCESSES else None,
        )
        delivered += job is not None
    return delivered


async def schedule_due(session: AsyncSession, now: datetime) -> int:
    await ensure_policies(session)
    control = await session.get(AutomationControl, 1)
    if control is not None and control.paused:
        return 0
    created = 0
    for row in await session.scalars(select(ProcessPolicy).where(ProcessPolicy.enabled.is_(True))):
        policy = policy_input(row)
        after = max(now - timedelta(days=8), row.updated_at)
        slots = next_slots(policy, after, count=2500)
        due = [slot for slot in slots if slot <= now]
        if due:
            await materialize(session, row.process_key, due[-1])
            await session.execute(
                update(ProcessExecution)
                .where(
                    ProcessExecution.process_key == row.process_key,
                    ProcessExecution.origin == "automatic",
                    ProcessExecution.state == "pending",
                    ProcessExecution.scheduled_for < due[-1],
                )
                .values(state="skipped", reason="superseded", finished_at=now)
            )
            created += 1
    return created


async def batch_preview(
    session: AsyncSession, settings: Settings, body: BatchInput
) -> BatchPreview:
    await ensure_policies(session)
    from preza.services.portfolio import latest_positions

    ids: set[int] = set()
    if body.scope in {"portfolio", "both"}:
        ids.update(
            p.instrument_id
            for p in await latest_positions(session, body.account_id)
            if p.quantity != 0
        )
    if body.scope in {"watchlist", "both"}:
        ids.update(
            await session.scalars(
                select(WatchlistItem.instrument_id).where(WatchlistItem.removed_at.is_(None))
            )
        )
    active = set(
        await session.scalars(
            select(AnalysisRun.instrument_id).where(AnalysisRun.status.in_(("queued", "running")))
        )
    )
    used = await used_today(session)
    available = (
        max(0, settings.deep_daily_limit - used) if settings.deep_daily_limit > 0 else body.cap
    )
    count = 0
    items = []
    for instrument in await session.scalars(
        select(Instrument).where(Instrument.id.in_(ids)).order_by(Instrument.symbol, Instrument.id)
    ):
        reason: Literal["active", "cap", "quota", "ready"] = (
            "active"
            if instrument.id in active
            else "cap"
            if count >= body.cap
            else "quota"
            if count >= available
            else "ready"
        )
        items.append(
            BatchItem(instrument_id=instrument.id, symbol=instrument.symbol, reason=reason)
        )
        count += reason == "ready"
    blocked = await gate(
        session, "batch_analyses", automatic=False, outside_window=body.outside_window
    )
    if blocked in {"disabled", "outside_window"}:
        for item in items:
            if item.reason == "ready":
                item.reason = "disabled" if blocked == "disabled" else "outside_window"
    policy = await session.get(ProcessPolicy, "batch_analyses")
    assert policy is not None
    return BatchPreview(
        items=items,
        quota_used=used,
        quota_limit=settings.deep_daily_limit,
        policy_revision=policy.revision,
        blocked_reason=blocked,
        resets_at=datetime.combine(datetime.now(UTC).date() + timedelta(days=1), time.min, UTC),
    )


async def run_batch(
    session: AsyncSession,
    settings: Settings,
    body: BatchInput,
    execution_id: uuid.UUID | None = None,
) -> BatchPreview:
    await lock_quota(session)
    preview = await batch_preview(session, settings, body)
    if execution_id is not None:
        execution = await session.get(ProcessExecution, execution_id)
        if execution is not None and execution.origin == "automatic":
            start = datetime.combine(datetime.now(UTC).date(), time.min, UTC)
            attempted = (
                await session.scalar(
                    select(func.count())
                    .select_from(ProcessAnalysis)
                    .join(ProcessExecution)
                    .where(
                        ProcessExecution.process_key == "batch_analyses",
                        ProcessExecution.origin == "automatic",
                        ProcessExecution.scheduled_for >= start,
                    )
                )
                or 0
            )
            remaining = max(0, body.cap - attempted)
            for item in preview.items:
                if item.reason == "ready":
                    if remaining <= 0:
                        item.reason = "cap"
                    else:
                        remaining -= 1
    for item in preview.items:
        if item.reason == "ready":
            instrument = await session.get(Instrument, item.instrument_id)
            assert instrument is not None
            run = await new_run(session, instrument, settings)
            if execution_id is not None:
                session.add(ProcessAnalysis(run_id=run.id, execution_id=execution_id))
            preview.run_ids.append(str(run.id))
    return preview


async def analysis_gate(session: AsyncSession, run_id: uuid.UUID) -> str | None:
    """Manual runs have no policy link; automatic child runs recheck before costly work."""
    link = await session.get(ProcessAnalysis, run_id)
    if link is None:
        return None
    execution = await session.get(ProcessExecution, link.execution_id)
    if execution is None:
        return "execution_missing"
    return await gate(
        session,
        execution.process_key,
        automatic=execution.origin == "automatic",
        outside_window=execution.outside_window,
    )


async def analysis_is_automatic(session: AsyncSession, run_id: uuid.UUID) -> bool:
    origin = await session.scalar(
        select(ProcessExecution.origin)
        .join(ProcessAnalysis, ProcessAnalysis.execution_id == ProcessExecution.id)
        .where(ProcessAnalysis.run_id == run_id)
    )
    return origin == "automatic"


async def review_gate(
    session: AsyncSession,
    revision_id: uuid.UUID,
    execution_id: str | None,
    week_start: str | None = None,
) -> str | None:
    if execution_id is None:
        return await gate(session, "discover_thesis_reviews")
    execution = await session.get(ProcessExecution, uuid.UUID(execution_id), populate_existing=True)
    if (
        execution is None
        or execution.process_key != "discover_thesis_reviews"
        or execution.state not in {"running", "done"}
    ):
        return "execution_missing"
    if str(revision_id) not in str(execution.counts.get("revision_ids", "")).split(","):
        return "execution_missing"
    if week_start is not None and execution.counts.get("review_week") != week_start:
        return "execution_missing"
    policy = await session.get(ProcessPolicy, execution.process_key, populate_existing=True)
    if policy is None or policy.revision != execution.policy_revision:
        return "policy_changed"
    return await gate(
        session,
        execution.process_key,
        automatic=execution.origin == "automatic",
        outside_window=execution.outside_window,
    )


async def owns_review_dispatch(
    session: AsyncSession, review_id: uuid.UUID, execution_id: str | None
) -> bool:
    if execution_id is None:
        return False
    execution = await session.get(ProcessExecution, uuid.UUID(execution_id), populate_existing=True)
    return execution is not None and str(review_id) in str(
        execution.counts.get("dispatch_review_ids", "")
    ).split(",")


async def record_review_dispatch(
    session: AsyncSession, review_id: uuid.UUID, execution_id: str | None
) -> None:
    if execution_id is None:
        return
    execution = await session.get(
        ProcessExecution, uuid.UUID(execution_id), populate_existing=True, with_for_update=True
    )
    if execution is not None:
        ids = set(str(execution.counts.get("dispatch_review_ids", "")).split(",")) - {""}
        ids.add(str(review_id))
        execution.counts = {**execution.counts, "dispatch_review_ids": ",".join(sorted(ids))}
