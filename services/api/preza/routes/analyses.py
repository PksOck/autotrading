"""Deep analysis runs (M4: BL-080, BL-082, SCR-06).

The agents service does the work; this API queues runs and streams their steps.
The stream reads the steps table, so a reconnecting browser replays from
`Last-Event-ID` and nothing depends on the worker being reachable.
"""

import asyncio
import json
import uuid
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from preza.config import Settings, get_settings
from preza.db import get_session, get_sessionmaker
from preza.domain.analysis import (
    AnalysisCreate,
    AnalysisOut,
    AnalysisStatus,
    AnalysisStepOut,
    AnalysisSummary,
)
from preza.models import AnalysisRun, AnalysisStep, Instrument
from preza.services.analyses import new_run, queue_run
from preza.services.instruments import find_by_symbol

router = APIRouter(prefix="/analyses", tags=["analyses"])
Session = Annotated[AsyncSession, Depends(get_session)]

POLL_S = 1.0
HEARTBEAT_S = 15.0
FINISHED = {AnalysisStatus.DONE, AnalysisStatus.FAILED}


def summary(run: AnalysisRun) -> AnalysisSummary:
    return AnalysisSummary(
        id=run.id,
        symbol=run.instrument.symbol,
        name=run.instrument.name,
        engine=run.engine,
        trade_date=run.trade_date,
        status=AnalysisStatus(run.status),
        rating=run.rating,
        caveats=list(run.caveats or []),
        created_at=run.created_at,
        finished_at=run.finished_at,
    )


def step_out(step: AnalysisStep) -> AnalysisStepOut:
    return AnalysisStepOut(
        seq=step.seq,
        agent=step.agent,
        kind=step.kind,
        title=step.title,
        content=step.content,
        created_at=step.created_at,
    )


def _sources(run: AnalysisRun) -> dict[str, str | None]:
    snap = run.snapshot or {}
    return {
        "bars": snap.get("bars_source"),
        "fundamentals": snap.get("fundamentals_source"),
        "fundamentals_as_of": snap.get("fundamentals_as_of"),
        "as_of": snap.get("as_of"),
    }


async def _get(session: AsyncSession, run_id: uuid.UUID) -> AnalysisRun:
    run = await session.get(AnalysisRun, run_id)
    if run is None:
        raise HTTPException(404, detail="analysis_not_found")
    return run


@router.post("", response_model=AnalysisSummary, status_code=202)
async def create_analysis(
    body: AnalysisCreate,
    session: Session,
    settings: Annotated[Settings, Depends(get_settings)],
) -> AnalysisSummary:
    instrument = await find_by_symbol(session, body.symbol.upper())
    if instrument is None:
        raise HTTPException(404, detail="instrument_not_found")
    run = await new_run(
        session, instrument, settings, trade_date=body.trade_date, hypothesis=body.hypothesis
    )
    await session.refresh(run, ["instrument"])
    out = summary(run)
    await session.commit()
    await queue_run(settings, run.id)
    return out


@router.get("", response_model=list[AnalysisSummary])
async def list_analyses(
    session: Session, symbol: str | None = None, limit: int = 30
) -> list[AnalysisSummary]:
    query = select(AnalysisRun).order_by(AnalysisRun.created_at.desc()).limit(min(limit, 100))
    if symbol:
        query = query.join(Instrument).where(Instrument.symbol == symbol.upper())
    return [summary(r) for r in await session.scalars(query)]


@router.get("/{run_id}", response_model=AnalysisOut)
async def get_analysis(run_id: uuid.UUID, session: Session) -> AnalysisOut:
    run = await _get(session, run_id)
    steps = await session.scalars(
        select(AnalysisStep).where(AnalysisStep.run_id == run.id).order_by(AnalysisStep.seq)
    )
    return AnalysisOut(
        **summary(run).model_dump(),
        locale=run.locale,
        hypothesis=run.hypothesis,
        decision=run.decision,
        reports=dict(run.reports or {}),
        models=dict(run.models or {}),
        error=run.error,
        started_at=run.started_at,
        data_sources=_sources(run),
        steps=[step_out(s) for s in steps],
    )


def _event(name: str, data: str, event_id: int | None = None) -> str:
    head = f"id: {event_id}\n" if event_id is not None else ""
    return f"{head}event: {name}\ndata: {data}\n\n"


async def run_events(
    run_id: uuid.UUID, after: int, is_disconnected: object = None
) -> AsyncIterator[str]:
    """Steps after `after`, then `end` once the run is finished. One short session per poll."""
    idle = 0.0
    while True:
        async with get_sessionmaker()() as session:
            run = await session.get(AnalysisRun, run_id)
            if run is None:
                yield _event("end", json.dumps({"status": "missing"}))
                return
            steps = list(
                await session.scalars(
                    select(AnalysisStep)
                    .where(AnalysisStep.run_id == run_id, AnalysisStep.seq > after)
                    .order_by(AnalysisStep.seq)
                )
            )
            status = run.status
        for step in steps:
            after = step.seq
            yield _event("step", step_out(step).model_dump_json(), step.seq)
        if status in FINISHED:
            yield _event("end", json.dumps({"status": status}))
            return
        if steps:
            idle = 0.0
        else:
            idle += POLL_S
            if idle >= HEARTBEAT_S:
                idle = 0.0
                yield ": keep-alive\n\n"
        if callable(is_disconnected) and await is_disconnected():
            return
        await asyncio.sleep(POLL_S)


@router.get("/{run_id}/events")
async def analysis_events(
    run_id: uuid.UUID,
    request: Request,
    session: Session,
    last_event_id: Annotated[str | None, Header(alias="Last-Event-ID")] = None,
    after: int = 0,
) -> StreamingResponse:
    await _get(session, run_id)
    start = int(last_event_id) if last_event_id and last_event_id.isdigit() else after
    return StreamingResponse(
        run_events(run_id, start, request.is_disconnected),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
