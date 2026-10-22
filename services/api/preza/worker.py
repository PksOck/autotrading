"""arq worker: scheduled data pulls (BL-022, BL-024). Times are UTC."""

import logging
import time
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, ClassVar

import httpx
from arq import cron
from arq.connections import RedisSettings
from sqlalchemy import select

from preza.broker.flex import FlexClient, FlexError
from preza.config import get_settings
from preza.db import get_sessionmaker
from preza.deps import get_bars_service
from preza.domain.market import InstrumentKind
from preza.entries.service import rebuild_entries
from preza.fundamentals.finnhub import FinnhubFundamentals, FundamentalsUnavailableError
from preza.ingest.edgar import parse_company_tickers
from preza.ingest.factory import build_sources
from preza.llm.client import LiteLlmClient, LlmUnavailableError
from preza.models import AnalysisRun, Instrument, Position, Proposal, WatchlistItem
from preza.notify.service import morning_digest, notify_new_signals
from preza.notify.telegram import TelegramClient
from preza.proposals.analyze import analyze_proposal
from preza.radar.pipeline import run_radar
from preza.services.analyses import new_run, queue_run
from preza.services.fundamentals import refresh_fundamentals
from preza.services.instruments import find_by_symbol, get_or_create
from preza.services.outcomes import compute_outcomes
from preza.services.portfolio import record_sync, store_statement
from preza.services.radar_views import user_symbols

SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"

log = logging.getLogger(__name__)


async def sync_flex(ctx: dict[str, Any]) -> str:
    settings = get_settings()
    if not (settings.ibkr_flex_token and settings.ibkr_flex_query_id):
        return "unconfigured"
    async with get_sessionmaker()() as session:
        try:
            statement = await FlexClient(
                settings.ibkr_flex_token, settings.ibkr_flex_query_id
            ).fetch()
        except FlexError as exc:
            await record_sync(session, "flex", "failed", str(exc))
            await session.commit()
            raise
        counts = await store_statement(session, statement)
        await record_sync(session, "flex", "ok", ", ".join(f"{k}={v}" for k, v in counts.items()))
        await session.commit()
    await refresh_bars(ctx)
    return "ok"


async def refresh_bars(ctx: dict[str, Any]) -> str:
    """Tops up daily bars for everything the user holds or watches."""
    service = get_bars_service()
    async with get_sessionmaker()() as session:
        held = select(Position.instrument_id)
        watched = select(WatchlistItem.instrument_id)
        targets = list(
            await session.scalars(select(Instrument).where(Instrument.id.in_(held.union(watched))))
        )
        ok = 0
        for instrument in targets:
            ok += await service.refresh(session, instrument)
            await session.commit()
    return f"{ok}/{len(targets)}"


def llm_client() -> LiteLlmClient:
    settings = get_settings()
    return LiteLlmClient(settings.litellm_base_url, settings.litellm_master_key)


async def _cik_map(ctx: dict[str, Any]) -> dict[str, str] | None:
    """SEC CIK → ticker, refreshed once a day; Radar works without it (filings lack tickers)."""
    settings = get_settings()
    cached = ctx.get("cik_map")
    if cached and time.monotonic() - ctx.get("cik_map_at", 0) < 86_400:
        return dict(cached)
    if not settings.sec_edgar_user_agent:
        return None
    try:
        async with httpx.AsyncClient(
            timeout=30, headers={"User-Agent": settings.sec_edgar_user_agent}
        ) as client:
            response = await client.get(SEC_TICKERS_URL)
            response.raise_for_status()
        ctx["cik_map"], ctx["cik_map_at"] = parse_company_tickers(response.json()), time.monotonic()
    except (httpx.HTTPError, ValueError) as exc:
        log.warning("SEC ticker map unavailable: %s", exc)
    return ctx.get("cik_map")


async def radar(ctx: dict[str, Any]) -> str:
    settings = get_settings()
    async with get_sessionmaker()() as session:
        held, watched = await user_symbols(session)
        sources = build_sources(settings, sorted(held | watched), await _cik_map(ctx))
        result = await run_radar(
            session,
            sources,
            llm_client(),
            settings.radar_signal_threshold,
            locale=settings.default_locale,
        )
        await session.commit()
    return (
        f"new={result.new_items} events={result.events} signals={result.signals} "
        f"translated={result.translated} errors={result.errors}"
    )


async def sweep_proposals(ctx: dict[str, Any]) -> int:
    """Re-queues proposals that were stored while the queue was down."""
    cutoff = datetime.now(UTC) - timedelta(minutes=2)
    async with get_sessionmaker()() as session:
        stuck = list(
            await session.scalars(
                select(Proposal.id).where(Proposal.status == "queued", Proposal.created_at < cutoff)
            )
        )
    redis = ctx.get("redis")
    for proposal_id in stuck:
        if redis is not None:
            await redis.enqueue_job(
                "analyze_proposal_job", str(proposal_id), _job_id=f"proposal:{proposal_id}"
            )
    return len(stuck)


async def analyze_proposal_job(ctx: dict[str, Any], proposal_id: str) -> str:
    async with get_sessionmaker()() as session:
        proposal = await session.get(Proposal, uuid.UUID(proposal_id))
        if proposal is None:
            return "missing"
        if proposal.status != "queued":
            return proposal.status  # already handled (API enqueue and sweep may overlap)
        try:
            await analyze_proposal(
                session, proposal, llm_client(), get_bars_service(), get_settings().default_locale
            )
        except LlmUnavailableError as exc:
            proposal.status = "failed"
            proposal.verdict = f'{{"summary": "llm_unavailable: {str(exc)[:120]}"}}'
        run_id = await _deep_run(session, proposal) if proposal.depth == "deep" else None
        await session.commit()
    if run_id is not None:
        await queue_run(get_settings(), run_id)
    return proposal.status


async def _deep_run(session: Any, proposal: Proposal) -> uuid.UUID | None:
    """A deep proposal also gets the full agent analysis, with the hypothesis to test (BL-090).

    The quick verdict above stays: it arrives in seconds, the agents take minutes.
    """
    instrument = await find_by_symbol(session, proposal.symbols[0])
    if instrument is None:
        return None
    existing = await session.scalar(
        select(AnalysisRun.id).where(AnalysisRun.proposal_id == proposal.id)
    )
    if existing is not None:
        return None
    run = await new_run(
        session,
        instrument,
        get_settings(),
        hypothesis=proposal.hypothesis or None,
        proposal_id=proposal.id,
    )
    return run.id


async def _benchmark_bars(session: Any) -> None:
    """The benchmark is reference data only, not something the user can trade (UCITS)."""
    symbol = get_settings().benchmark_symbol
    benchmark = await find_by_symbol(session, symbol)
    if benchmark is None:
        benchmark = await get_or_create(
            session, symbol=symbol, source="benchmark", kind=InstrumentKind.ETF
        )
        benchmark.tradable_for_user = False
    await get_bars_service().refresh(session, benchmark)


async def entries(ctx: dict[str, Any]) -> str:
    """Entry candidates after the US close and the bars refresh (M3)."""
    settings = get_settings()
    async with get_sessionmaker()() as session:
        await _benchmark_bars(session)
        run = await rebuild_entries(
            session, llm_client(), settings.default_locale, settings.benchmark_symbol
        )
        await record_sync(
            session,
            "entries",
            "failed" if run.errors and not run.evaluated else "ok",
            f"evaluated={run.evaluated} active={run.active} analyzed={run.analyzed} "
            f"signals={run.signals} errors={run.errors}",
        )
        await session.commit()
    return f"evaluated={run.evaluated} active={run.active} signals={run.signals}"


async def fundamentals(ctx: dict[str, Any]) -> str:
    """Weekly valuation metrics for held and watched stocks (BL-061)."""
    settings = get_settings()
    if not settings.finnhub_api_key:
        return "unconfigured"
    client = FinnhubFundamentals(settings.finnhub_api_key)
    ok = failed = 0
    async with get_sessionmaker()() as session:
        held, watched = await user_symbols(session)
        for symbol in sorted(held | watched):
            instrument = await find_by_symbol(session, symbol)
            if instrument is None:
                continue
            try:
                ok += await refresh_fundamentals(session, instrument, client) is not None
            except FundamentalsUnavailableError as exc:
                failed += 1
                log.warning("fundamentals %s: %s", symbol, exc)
            await session.commit()
    return f"ok={ok} failed={failed}"


async def outcomes(ctx: dict[str, Any]) -> str:
    async with get_sessionmaker()() as session:
        inserted = await compute_outcomes(session, get_settings().benchmark_symbol)
        await session.commit()
    return f"inserted={inserted}"


async def _telegram_job(job: Any) -> str:
    settings = get_settings()
    if not (settings.telegram_bot_token and settings.telegram_chat_id):
        return "unconfigured"
    client = TelegramClient(settings.telegram_bot_token)
    try:
        async with get_sessionmaker()() as session:
            count = await job(session, client, settings.telegram_chat_id, settings)
            await session.commit()
    finally:
        await client.aclose()
    return f"sent={count}"


async def notify(ctx: dict[str, Any]) -> str:
    return await _telegram_job(notify_new_signals)


async def digest(ctx: dict[str, Any]) -> str:
    return await _telegram_job(morning_digest)


class WorkerSettings:
    functions: ClassVar[list[Any]] = [
        sync_flex,
        refresh_bars,
        radar,
        analyze_proposal_job,
        sweep_proposals,
        notify,
        digest,
        entries,
        fundamentals,
        outcomes,
    ]
    cron_jobs: ClassVar[list[Any]] = [
        cron(sync_flex, hour={5}, minute={15}),  # after IBKR prepares the previous day (~07:15 CET)
        cron(refresh_bars, weekday={0, 1, 2, 3, 4}, hour={21}, minute={30}),  # after US close
        cron(radar, minute={2, 17, 32, 47}),  # every 15 minutes
        cron(sweep_proposals, minute={5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 0}),
        cron(notify, minute=set(range(0, 60, 5))),  # every 5 minutes
        cron(digest, hour={5}, minute={30}),  # 07:30 Ljubljana in summer, 06:30 in winter
        cron(entries, weekday={0, 1, 2, 3, 4}, hour={22}, minute={0}),  # after refresh_bars
        cron(outcomes, weekday={0, 1, 2, 3, 4}, hour={22}, minute={40}),
        cron(fundamentals, weekday={6}, hour={6}, minute={10}),  # Sundays
    ]
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
