"""arq worker for agent runs (M4). Its own queue, one run at a time.

Run with `arq preza_agents.worker.WorkerSettings`. Stock and ETF role calls are
sequential and asynchronous; blocking SEC fetches run in a thread. The loop writes
steps every half second for the streamed timeline (BL-082).
"""

from __future__ import annotations

import asyncio
import logging
import os
import queue
import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any, ClassVar, cast

from arq import cron
from arq.connections import RedisSettings
from arq.jobs import Job, JobStatus
from arq.worker import func as arq_func
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from preza.config import Settings, get_settings
from preza.db import get_sessionmaker
from preza.domain.analysis import DecisionCard, PreviousRun
from preza.fundamentals.finnhub import FinnhubFundamentals
from preza.ingest.finnhub import FinnhubSource
from preza.llm.client import LiteLlmClient, Llm, Role
from preza.models import (
    AnalysisRun,
    AnalysisStep,
    Fundamentals,
    Instrument,
    ThesisReview,
    ThesisRevision,
)
from preza.queue import AGENTS_QUEUE
from preza.services.fundamentals import refresh_fundamentals
from preza.services.thesis_reviews import week_start
from preza_agents.budget import UsageLlm
from preza_agents.decision_card import build_card, control_score, draft_card
from preza_agents.deep_research import adapter
from preza_agents.deep_research.snapshot import (
    NEWS_DAYS,
    DataSnapshot,
    NewsRow,
    build_snapshot,
    news_is_rumor,
)
from preza_agents.deep_research.timeline import Step
from preza_agents.etf_analyst.analyst import run_etf
from preza_agents.etf_analyst.context import build_etf_facts
from preza_agents.etf_analyst.profile import fetch_profile, store_profile, user_etfs
from preza_agents.hypothesis import check_hypothesis, check_md
from preza_agents.stock_analyst.analyst import StockResult, run_stock
from preza_agents.thesis_tracker.runner import thesis_review

log = logging.getLogger(__name__)

FLUSH_S = 0.5
MAX_CONTENT = 20_000
RUN_TIMEOUT_S = 3 * 60 * 60
# Only close runs this old when arq has no queued, deferred or in-progress job.
STALE_RUN_S = RUN_TIMEOUT_S + 15 * 60


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


def _fetch_stock_statements(snapshot: DataSnapshot, settings: Settings) -> dict[str, str]:
    """Blocking SEC adapter, called only in a worker thread with a configured contact."""
    if not settings.sec_edgar_user_agent:
        raise ValueError("SEC EDGAR contact is not configured")
    from tradingagents.dataflows.config import run_config
    from tradingagents.dataflows.vendors import sec_edgar

    os.environ.setdefault("SEC_EDGAR_USER_AGENT", settings.sec_edgar_user_agent)
    with run_config({"data_cache_dir": str(Path(settings.agents_home) / "cache")}):
        return {
            name: fetch(snapshot.symbol, "quarterly", snapshot.as_of.isoformat())
            for name, fetch in (
                ("income_statement", sec_edgar.get_income_statement),
                ("balance_sheet", sec_edgar.get_balance_sheet),
                ("cashflow", sec_edgar.get_cashflow),
            )
        }


FUNDAMENTALS_MAX_AGE = timedelta(days=7)
FRESH_WINDOW = timedelta(days=3)


async def _fresh_inputs(
    session: AsyncSession,
    instrument: Instrument,
    as_of: date,
    settings: Settings,
    fundamentals_client: Any = None,
    news_client: Any = None,
) -> list[NewsRow]:
    """Fetch what the scheduled jobs skip for symbols that are neither held nor watched.

    Fundamentals are stored like the weekly job stores them. Company news only enters this
    run's snapshot: storing it would hide the URLs from a later radar triage.
    """
    if not settings.finnhub_api_key or as_of < _utcnow().date() - FRESH_WINDOW:
        return []  # a past run must not see data fetched today
    row = await session.get(Fundamentals, instrument.id)
    if row is None or row.fetched_at < _utcnow() - FUNDAMENTALS_MAX_AGE:
        # A savepoint keeps a failed write from rolling back the run row with it.
        try:
            async with session.begin_nested():
                await refresh_fundamentals(
                    session,
                    instrument,
                    fundamentals_client or FinnhubFundamentals(settings.finnhub_api_key),
                )
        except Exception as exc:  # the analysis runs without them, flagged no_fundamentals
            log.warning("fundamentals %s: %s", instrument.symbol, exc)
    client = news_client or FinnhubSource(settings.finnhub_api_key, [instrument.symbol])
    start = (as_of - timedelta(days=NEWS_DAYS)).isoformat()
    try:
        items = await client.company_news(instrument.symbol, start, as_of.isoformat())
    except Exception as exc:  # outages and unparseable rows alike
        log.warning("company news %s: %s", instrument.symbol, exc)
        return []
    return [
        NewsRow(
            published_at=item.published_at,
            title=item.title,
            summary=item.summary,
            source=item.source,
            url=item.url,
            kind=item.kind,
            is_rumor=news_is_rumor(item.kind, item.title, item.summary),
            symbols=item.symbols,
        )
        for item in items
        if item.published_at.date() <= as_of
    ]


async def _stock_work(
    ctx: dict[str, Any],
    settings: Settings,
    llm: Llm,
    snapshot: DataSnapshot,
    locale: str,
    on_step: Callable[[Step], None],
    hypothesis: str | None,
    previous: dict[str, str | None] | None,
) -> StockResult:
    # Tests inject a pure fetcher. Neither model code nor digests can perform I/O.
    fetcher = ctx.get("statement_fetcher", _fetch_stock_statements)
    unavailable = False
    try:
        statements = await asyncio.to_thread(fetcher, snapshot, settings)
        if not isinstance(statements, dict) or not all(
            isinstance(k, str) and isinstance(v, str) for k, v in statements.items()
        ):
            raise ValueError("SEC statement fetcher must return a text mapping")
        unavailable = not bool(statements)
    except Exception:
        log.warning("SEC statements unavailable for %s", snapshot.symbol)
        statements = None
        unavailable = True
    result = await run_stock(
        llm,
        snapshot,
        locale,
        on_step,
        cast(Role, settings.deep_quick_role),
        cast(Role, settings.deep_deep_role),
        cast(Role | None, settings.deep_compose_role),
        hypothesis,
        previous,
        statements,
    )
    if unavailable:
        result.caveats.append("statements_unavailable")
    return result


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
        fresh: list[NewsRow] = []
        if run.engine != "etf":
            fetch_fresh = ctx.get("fresh_inputs", _fresh_inputs)
            fresh = await fetch_fresh(session, run.instrument, run.trade_date, settings)
        snapshot = await build_snapshot(session, run.instrument, run.trade_date)
        seen = {n.url for n in snapshot.news}  # stored rows win over fresh ones
        added: list[NewsRow] = []
        for n in fresh:
            if n.url not in seen:
                seen.add(n.url)
                added.append(n)
        snapshot.news = sorted([*snapshot.news, *added], key=lambda n: n.published_at, reverse=True)
        run.snapshot = snapshot.model_dump(mode="json")
        seq = await _next_seq(session, run.id)
        await session.commit()

        steps: queue.SimpleQueue[Step] = queue.SimpleQueue()
        steps.put(Step(agent="system", kind="status", title="started"))
        deep = deep_settings(settings)
        extra: list[str] = []
        work: Awaitable[adapter.DeepResult]
        llm = UsageLlm(
            ctx.get("llm") or LiteLlmClient(settings.litellm_base_url, settings.litellm_master_key)
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
            before = await _previous_run(session, run)
            previous = (
                None
                if before is None
                else {
                    "trade_date": before.trade_date.isoformat(),
                    "rating": before.rating,
                    "decision": (before.decision or "")[:3000],
                }
            )
            work = _stock_work(
                ctx,
                settings,
                llm,
                snapshot,
                run.locale,
                steps.put,
                run.hypothesis,
                previous,
            )
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
            failed_models: dict[str, Any] = {**(run.models or {}), "usage": llm.usage()}
            run.models = failed_models
            run.finished_at = _utcnow()
            await session.commit()
            return run.status
        if isinstance(result, StockResult):
            extra.extend(result.caveats)
        if run.hypothesis and isinstance(result, StockResult):
            if result.hypothesis_check is not None:
                text = check_md(run.hypothesis, result.hypothesis_check, run.locale)
                if sources := result.reports.get("evidence_sources"):
                    text += "\n\n" + sources
                result.reports["hypothesis_check"] = text
                steps.put(
                    Step(agent="hypothesis", kind="report", title="hypothesis_check", content=text)
                )
        elif run.hypothesis:
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
        result.models["usage"] = llm.usage()  # type: ignore[assignment]
        run.models = result.models
        found = adapter.caveats(snapshot, result.rating)
        if run.engine == "etf":  # a fund has no company fundamentals to miss
            found = [c for c in found if c != "no_fundamentals"]
        run.caveats = list(dict.fromkeys(found + extra))
        run.status = "done"
        run.finished_at = _utcnow()
        await session.commit()
        return run.status


async def _previous_run(session: AsyncSession, run: AnalysisRun) -> AnalysisRun | None:
    return await session.scalar(
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


async def _card(
    session: AsyncSession,
    run: AnalysisRun,
    snapshot: DataSnapshot,
    result: adapter.DeepResult,
    llm: Llm,
    deep: adapter.DeepSettings,
) -> tuple[DecisionCard, str | None]:
    """The decision card; without the model's half it still carries the control score."""
    before = await _previous_run(session, run)
    previous = (
        PreviousRun(id=before.id, trade_date=before.trade_date, rating=before.rating)
        if before is not None
        else None
    )
    draft, model = None, None
    if isinstance(result, StockResult):
        return build_card(
            result.rating, control_score(snapshot), result.card_draft, previous
        ), result.models.get("deep")
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


async def _job_alive(redis: Any, run_id: uuid.UUID) -> bool:
    status = await Job(f"analysis:{run_id}", redis, _queue_name=AGENTS_QUEUE).status()
    return status in (JobStatus.deferred, JobStatus.queued, JobStatus.in_progress)


async def sweep_runs(ctx: dict[str, Any]) -> int:
    """Fail stale runs without live arq jobs; re-queue queued runs with deduplicated IDs."""
    now = _utcnow()
    cutoff = now - timedelta(minutes=2)
    async with get_sessionmaker()() as session:
        candidates = list(
            await session.scalars(
                select(AnalysisRun.id).where(
                    AnalysisRun.status == "running",
                    AnalysisRun.started_at < now - timedelta(seconds=STALE_RUN_S),
                )
            )
        )
        abandoned = [run_id for run_id in candidates if not await _job_alive(ctx["redis"], run_id)]
        closed = []
        if abandoned:
            closed = list(
                await session.scalars(
                    update(AnalysisRun)
                    .where(AnalysisRun.id.in_(abandoned), AnalysisRun.status == "running")
                    .values(
                        status="failed",
                        finished_at=now,
                        error="interrupted: no result within the job timeout",
                    )
                    .returning(AnalysisRun.id)
                )
            )
        stuck = list(
            await session.scalars(
                select(AnalysisRun.id).where(
                    AnalysisRun.status == "queued", AnalysisRun.created_at < cutoff
                )
            )
        )
        await session.commit()
    if closed:
        log.warning("closed %d interrupted analysis runs", len(closed))
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


async def discover_thesis_reviews(ctx: dict[str, Any]) -> int:
    """Find missing reviews and recover interrupted reservations without redispatch."""
    monday = week_start(_utcnow())
    async with get_sessionmaker()() as session:
        revisions = list(
            await session.scalars(
                select(ThesisRevision.id)
                .outerjoin(
                    ThesisReview,
                    (ThesisReview.revision_id == ThesisRevision.id)
                    & (ThesisReview.week_start == monday),
                )
                .where(
                    ThesisRevision.status == "active",
                    (ThesisReview.id.is_(None)) | ThesisReview.status.in_(("queued", "running")),
                )
                .order_by(ThesisRevision.id)
            )
        )
    for revision_id in revisions:
        await ctx["redis"].enqueue_job(
            "thesis_review",
            str(revision_id),
            monday.isoformat(),
            _job_id=f"thesis-review:{revision_id}:{monday.isoformat()}",
            _queue_name=AGENTS_QUEUE,
        )
    return len(revisions)


class WorkerSettings:
    functions: ClassVar[list[Any]] = [
        deep_analysis,
        sweep_runs,
        refresh_etf_profiles,
        arq_func(thesis_review, max_tries=1),
    ]
    cron_jobs: ClassVar[list[Any]] = [
        cron(sweep_runs, minute=set(range(0, 60, 5))),
        cron(refresh_etf_profiles, weekday="sun", hour=5, minute=17),
        cron(
            discover_thesis_reviews, name="thesis-review-weekly", weekday="sun", hour=6, minute=15
        ),
        cron(discover_thesis_reviews, name="thesis-review-catchup", hour=6, minute=20),
    ]
    on_startup = startup
    queue_name = AGENTS_QUEUE
    max_jobs = 1  # one GPU and two subscriptions: runs queue up instead of competing
    timezone = UTC
    job_timeout = RUN_TIMEOUT_S
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
