"""arq worker for agent runs (M4). Its own queue, one run at a time.

Run with `arq preza_agents.worker.WorkerSettings`. The run itself is blocking
(LangGraph, worker threads); it runs in a thread while this loop writes its steps
to the database every half second, which is what the timeline streams (BL-082).
"""

from __future__ import annotations

import asyncio
import functools
import logging
import os
import queue
import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, ClassVar, cast

from arq import cron
from arq.connections import RedisSettings
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from preza.config import Settings, get_settings
from preza.db import get_sessionmaker
from preza.domain.analysis import DecisionCard, PreviousRun
from preza.llm.client import LiteLlmClient, Llm, Role
from preza.models import AnalysisRun, AnalysisStep
from preza.queue import AGENTS_QUEUE
from preza_agents.decision_card import build_card, control_score, draft_card
from preza_agents.deep_research import adapter
from preza_agents.deep_research.snapshot import DataSnapshot, build_snapshot
from preza_agents.deep_research.timeline import Step
from preza_agents.etf_analyst.analyst import run_etf
from preza_agents.etf_analyst.context import build_etf_facts
from preza_agents.etf_analyst.profile import fetch_profile, store_profile, user_etfs
from preza_agents.hypothesis import check_hypothesis, check_md

log = logging.getLogger(__name__)

FLUSH_S = 0.5
MAX_CONTENT = 20_000
RUN_TIMEOUT_S = 3 * 60 * 60


def deep_settings(settings: Settings) -> adapter.DeepSettings:
    return adapter.DeepSettings(
        litellm_base_url=settings.litellm_base_url,
        quick_role=settings.deep_quick_role,
        deep_role=settings.deep_deep_role,
        debate_rounds=settings.deep_debate_rounds,
        home=Path(settings.agents_home),
        benchmark=settings.benchmark_symbol,
    )


def _utcnow() -> datetime:
    return datetime.now(UTC)


async def _next_seq(session: AsyncSession, run_id: uuid.UUID) -> int:
    last = await session.scalar(
        select(func.max(AnalysisStep.seq)).where(AnalysisStep.run_id == run_id)
    )
    return (last or 0) + 1


async def _flush(
    session: AsyncSession, run_id: uuid.UUID, steps: queue.SimpleQueue[Step], seq: int
) -> int:
    added = False
    while True:
        try:
            step = steps.get_nowait()
        except queue.Empty:
            break
        session.add(
            AnalysisStep(
                run_id=run_id,
                seq=seq,
                agent=step.agent,
                kind=step.kind,
                title=step.title,
                content=step.content[:MAX_CONTENT],
            )
        )
        seq += 1
        added = True
    if added:
        await session.commit()
    return seq


async def deep_analysis(
    ctx: dict[str, Any], run_id: str, graph_factory: Callable[..., Any] | None = None
) -> str:
    settings = get_settings()
    async with get_sessionmaker()() as session:
        run = await session.get(AnalysisRun, uuid.UUID(run_id))
        if run is None:
            return "missing"
        if run.status in ("done", "failed"):
            return run.status
        run.status = "running"
        run.started_at = run.started_at or _utcnow()
        snapshot = await build_snapshot(session, run.instrument, run.trade_date)
        run.snapshot = snapshot.model_dump(mode="json")
        seq = await _next_seq(session, run.id)
        await session.commit()

        steps: queue.SimpleQueue[Step] = queue.SimpleQueue()
        steps.put(Step(agent="system", kind="status", title="started"))
        deep = deep_settings(settings)
        extra: list[str] = []
        work: Awaitable[adapter.DeepResult]
        llm = ctx.get("llm") or LiteLlmClient(
            settings.litellm_base_url, settings.litellm_master_key
        )
        if run.engine == "etf":
            facts = await build_etf_facts(session, run.instrument, snapshot, settings.base_currency)
            if facts.profile is None:
                extra.append("no_profile")
            work = run_etf(
                llm,
                facts,
                run.locale,
                steps.put,
                cast(Role, deep.quick_role),
                cast(Role, deep.deep_role),
            )
        else:
            config = adapter.build_config(deep, run.locale)
            run_deep = (
                functools.partial(adapter.run_deep, graph_factory=graph_factory)
                if graph_factory
                else adapter.run_deep
            )
            work = asyncio.to_thread(run_deep, snapshot, config, steps.put)
        task = asyncio.ensure_future(work)
        while not task.done():
            seq = await _flush(session, run.id, steps, seq)
            await asyncio.wait({task}, timeout=FLUSH_S)
        try:
            result = task.result()
        except Exception as exc:  # a failed run is a row with its reason, not a crashed worker
            log.exception("deep analysis %s failed", run_id)
            steps.put(Step(agent="system", kind="status", title="failed", content=str(exc)[:500]))
            await _flush(session, run.id, steps, seq)
            run.status = "failed"
            run.error = f"{type(exc).__name__}: {str(exc)[:500]}"
            run.finished_at = _utcnow()
            await session.commit()
            return run.status
        if run.hypothesis:
            try:
                check, model = await check_hypothesis(
                    llm,
                    run.hypothesis,
                    result.reports,
                    result.rating,
                    run.locale,
                    cast(Role, deep.deep_role),
                )
            except Exception:  # the run stands without the check; the caveat says so
                log.warning("hypothesis check for %s failed", run_id, exc_info=True)
                extra.append("hypothesis_unchecked")
            else:
                text = check_md(run.hypothesis, check, run.locale)
                result.reports["hypothesis_check"] = text
                result.models["hypothesis"] = model
                steps.put(
                    Step(agent="hypothesis", kind="report", title="hypothesis_check", content=text)
                )
        card, card_model = await _card(session, run, snapshot, result, llm, deep)
        if card_model is None:
            extra.append("card_incomplete")
        if card.confidence == "low":
            extra.append("control_disagrees")
        steps.put(Step(agent="system", kind="status", title="done"))
        await _flush(session, run.id, steps, seq)
        run.card = card.model_dump(mode="json")
        if card_model is not None:
            result.models["card"] = card_model
        run.rating = result.rating
        run.decision = result.decision
        run.reports = result.reports
        run.models = result.models
        found = adapter.caveats(snapshot, result.rating)
        if run.engine == "etf":  # a fund has no company fundamentals to miss
            found = [c for c in found if c != "no_fundamentals"]
        run.caveats = found + extra
        run.status = "done"
        run.finished_at = _utcnow()
        await session.commit()
        return run.status


async def _card(
    session: AsyncSession,
    run: AnalysisRun,
    snapshot: DataSnapshot,
    result: adapter.DeepResult,
    llm: Llm,
    deep: adapter.DeepSettings,
) -> tuple[DecisionCard, str | None]:
    """The decision card; without the model's half it still carries the control score."""
    before = await session.scalar(
        select(AnalysisRun)
        .where(
            AnalysisRun.instrument_id == run.instrument_id,
            AnalysisRun.status == "done",
            AnalysisRun.id != run.id,
            AnalysisRun.created_at < run.created_at,
        )
        .order_by(AnalysisRun.created_at.desc())
        .limit(1)
    )
    previous = (
        PreviousRun(id=before.id, trade_date=before.trade_date, rating=before.rating)
        if before is not None
        else None
    )
    draft, model = None, None
    try:
        draft, model = await draft_card(
            llm,
            result.rating,
            result.decision,
            result.reports,
            None
            if before is None
            else {
                "trade_date": before.trade_date.isoformat(),
                "rating": before.rating,
                "decision": (before.decision or "")[:3000],
            },
            run.locale,
            cast(Role, deep.quick_role),
        )
    except Exception:
        log.warning("decision card for %s failed", run.id, exc_info=True)
    return build_card(result.rating, control_score(snapshot), draft, previous), model


async def sweep_runs(ctx: dict[str, Any]) -> int:
    """Queue runs stored while Redis was down; arq's job id keeps this from doubling a run."""
    cutoff = _utcnow() - timedelta(minutes=2)
    async with get_sessionmaker()() as session:
        stuck = list(
            await session.scalars(
                select(AnalysisRun.id).where(
                    AnalysisRun.status == "queued", AnalysisRun.created_at < cutoff
                )
            )
        )
    for run_id in stuck:
        await ctx["redis"].enqueue_job(
            "deep_analysis", str(run_id), _job_id=f"analysis:{run_id}", _queue_name=AGENTS_QUEUE
        )
    return len(stuck)


async def refresh_etf_profiles(ctx: dict[str, Any]) -> int:
    """Weekly fund profiles (TER, holdings, sectors) for held and watched ETFs."""
    if not get_settings().yahoo_enabled:
        return 0
    today = _utcnow().date()
    stored = 0
    async with get_sessionmaker()() as session:
        for instrument in await user_etfs(session):
            try:
                profile = await asyncio.to_thread(fetch_profile, instrument, today)
            except Exception:  # one fund without data must not stop the others
                log.warning("etf profile %s failed", instrument.symbol, exc_info=True)
                continue
            await store_profile(session, instrument, profile)
            stored += 1
        await session.commit()
    return stored


async def startup(ctx: dict[str, Any]) -> None:
    settings = get_settings()
    # TradingAgents' OpenAI-compatible client reads its key from this variable.
    if settings.litellm_master_key:
        os.environ.setdefault("OPENAI_COMPATIBLE_API_KEY", settings.litellm_master_key)
    await asyncio.to_thread(Path(settings.agents_home).mkdir, parents=True, exist_ok=True)
    ctx["llm"] = LiteLlmClient(settings.litellm_base_url, settings.litellm_master_key)


class WorkerSettings:
    functions: ClassVar[list[Any]] = [deep_analysis, sweep_runs, refresh_etf_profiles]
    cron_jobs: ClassVar[list[Any]] = [
        cron(sweep_runs, minute=set(range(0, 60, 5))),
        cron(refresh_etf_profiles, weekday="sun", hour=5, minute=17),
    ]
    on_startup = startup
    queue_name = AGENTS_QUEUE
    max_jobs = 1  # one GPU and two subscriptions: runs queue up instead of competing
    job_timeout = RUN_TIMEOUT_S
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
