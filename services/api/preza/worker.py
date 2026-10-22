"""arq worker: scheduled data pulls (BL-022, BL-024). Times are UTC."""

import logging
import time
import uuid
from typing import Any, ClassVar

import httpx
from arq import cron
from arq.connections import RedisSettings
from sqlalchemy import select

from preza.broker.flex import FlexClient, FlexError
from preza.config import get_settings
from preza.db import get_sessionmaker
from preza.deps import get_bars_service
from preza.ingest.edgar import parse_company_tickers
from preza.ingest.factory import build_sources
from preza.llm.client import LiteLlmClient, LlmUnavailableError
from preza.models import Instrument, Position, Proposal, WatchlistItem
from preza.proposals.analyze import analyze_proposal
from preza.radar.pipeline import run_radar
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
        result = await run_radar(session, sources, llm_client(), settings.radar_signal_threshold)
        await session.commit()
    return (
        f"new={result.new_items} events={result.events} signals={result.signals} "
        f"errors={result.errors}"
    )


async def analyze_proposal_job(ctx: dict[str, Any], proposal_id: str) -> str:
    async with get_sessionmaker()() as session:
        proposal = await session.get(Proposal, uuid.UUID(proposal_id))
        if proposal is None:
            return "missing"
        try:
            await analyze_proposal(
                session, proposal, llm_client(), get_bars_service(), get_settings().default_locale
            )
        except LlmUnavailableError as exc:
            proposal.status = "failed"
            proposal.verdict = f'{{"summary": "llm_unavailable: {str(exc)[:120]}"}}'
        await session.commit()
        return proposal.status


class WorkerSettings:
    functions: ClassVar[list[Any]] = [sync_flex, refresh_bars, radar, analyze_proposal_job]
    cron_jobs: ClassVar[list[Any]] = [
        cron(sync_flex, hour={5}, minute={15}),  # after IBKR prepares the previous day (~07:15 CET)
        cron(refresh_bars, weekday={0, 1, 2, 3, 4}, hour={21}, minute={30}),  # after US close
        cron(radar, minute={2, 17, 32, 47}),  # every 15 minutes
    ]
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
