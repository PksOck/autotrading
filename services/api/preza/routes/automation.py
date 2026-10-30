"""Process controls and explicit batch acceptance; no secrets or order endpoints."""

import uuid
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from preza.config import Settings, get_settings
from preza.db import get_session
from preza.domain.automation import (
    BatchInput,
    BatchPreview,
    ControlInput,
    ExecutionOut,
    PolicyInput,
    PolicyOut,
    RunInput,
)
from preza.models_automation import AutomationControl, ProcessExecution, ProcessPolicy
from preza.services import automation as service
from preza.services.analyses import queue_run

router = APIRouter(prefix="/automation", tags=["automation"])
Session = Annotated[AsyncSession, Depends(get_session)]
Config = Annotated[Settings, Depends(get_settings)]


@router.get("/policies", response_model=list[PolicyOut])
async def policies(session: Session) -> list[PolicyOut]:
    await service.ensure_policies(session)
    return [
        service.policy_out(row)
        for row in await session.scalars(select(ProcessPolicy).order_by(ProcessPolicy.process_key))
    ]


@router.patch("/policies/{key}", response_model=PolicyOut)
async def patch_policy(key: str, body: PolicyInput, session: Session) -> PolicyOut:
    return await service.update_policy(session, key, body)


@router.get("/control", response_model=ControlInput)
async def control(session: Session) -> ControlInput:
    await service.ensure_policies(session)
    row = await session.get(AutomationControl, 1)
    assert row is not None
    return ControlInput(
        revision=row.revision,
        paused=row.paused,
        automatic_analyses_enabled=row.automatic_analyses_enabled,
    )


@router.patch("/control", response_model=ControlInput)
async def patch_control(body: ControlInput, session: Session) -> ControlInput:
    await service.ensure_policies(session)
    row = await session.scalar(
        update(AutomationControl)
        .where(AutomationControl.id == 1, AutomationControl.revision == body.revision)
        .values(
            paused=body.paused,
            automatic_analyses_enabled=body.automatic_analyses_enabled,
            revision=body.revision + 1,
        )
        .returning(AutomationControl)
    )
    if row is None:
        raise HTTPException(409, "revision_conflict")
    return ControlInput(
        revision=row.revision,
        paused=row.paused,
        automatic_analyses_enabled=row.automatic_analyses_enabled,
    )


@router.get("/executions", response_model=list[ExecutionOut])
async def executions(session: Session) -> list[dict[str, Any]]:
    rows = await session.scalars(
        select(ProcessExecution).order_by(ProcessExecution.scheduled_for.desc()).limit(100)
    )
    return [
        {
            "id": str(row.id),
            "process_key": row.process_key,
            "policy_revision": row.policy_revision,
            "scheduled_for": row.scheduled_for,
            "origin": row.origin,
            "outside_window": row.outside_window,
            "state": row.state,
            "reason": row.reason,
            "started_at": row.started_at,
            "finished_at": row.finished_at,
            "heartbeat_at": row.heartbeat_at,
            "counts": row.counts,
        }
        for row in rows
    ]


@router.post("/policies/{key}/run", status_code=202)
async def run_process(
    key: str, body: RunInput, session: Session, settings: Config
) -> dict[str, str]:
    await service.ensure_policies(session)
    row = await session.get(ProcessPolicy, key)
    if row is None:
        raise HTTPException(404, "process_not_found")
    if row.revision != body.revision:
        raise HTTPException(409, "revision_conflict")
    reason = await service.gate(session, key, automatic=False, outside_window=body.outside_window)
    if reason:
        raise HTTPException(409, reason)
    execution_id = await service.materialize(
        session, key, datetime.now(UTC), origin="manual", outside_window=body.outside_window
    )
    await session.commit()
    await service.deliver_pending(session, settings)
    return {"id": str(execution_id), "state": "pending"}


@router.post("/batch/preview", response_model=BatchPreview)
async def preview_batch(body: BatchInput, session: Session, settings: Config) -> BatchPreview:
    return await service.batch_preview(session, settings, body)


@router.post("/batch/run", response_model=BatchPreview, status_code=202)
async def batch(body: BatchInput, session: Session, settings: Config) -> BatchPreview:
    await service.ensure_policies(session)
    row = await session.scalar(
        select(ProcessPolicy).where(ProcessPolicy.process_key == "batch_analyses").with_for_update()
    )
    assert row is not None
    if body.revision != row.revision:
        raise HTTPException(409, "revision_conflict")
    reason = await service.gate(
        session, "batch_analyses", automatic=False, outside_window=body.outside_window
    )
    if reason:
        raise HTTPException(409, reason)
    execution_id = await service.materialize(
        session,
        "batch_analyses",
        datetime.now(UTC),
        origin="manual",
        outside_window=body.outside_window,
    )
    result = await service.run_batch(session, settings, body, execution_id)
    execution = await session.get(ProcessExecution, execution_id)
    assert execution is not None
    execution.state = "done"
    execution.started_at = execution.finished_at = datetime.now(UTC)
    execution.counts = {"accepted": len(result.run_ids), "considered": len(result.items)}
    await session.commit()
    for run_id in result.run_ids:
        await queue_run(settings, uuid.UUID(run_id))
    return result
