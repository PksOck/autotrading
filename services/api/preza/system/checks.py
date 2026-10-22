"""Health probes for the services Preža depends on.

Each probe is bounded by a timeout and never raises: failures become a DOWN
status with a short detail, so one broken dependency cannot break the page.
"""

import asyncio
import time
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

import httpx
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from preza.config import Settings
from preza.domain.system import ServiceId, ServiceState, ServiceStatus, SystemStatus

Probe = Callable[[Settings], Awaitable[ServiceStatus]]


async def _timed(service: ServiceId, settings: Settings, call: Awaitable[None]) -> ServiceStatus:
    start = time.perf_counter()
    try:
        await asyncio.wait_for(call, timeout=settings.status_timeout_s)
    except TimeoutError:
        return ServiceStatus(id=service, state=ServiceState.DOWN, detail="timeout")
    except Exception as exc:  # probes must never raise
        return ServiceStatus(id=service, state=ServiceState.DOWN, detail=type(exc).__name__)
    latency = round((time.perf_counter() - start) * 1000, 1)
    return ServiceStatus(id=service, state=ServiceState.UP, latency_ms=latency)


async def probe_postgres(settings: Settings) -> ServiceStatus:
    async def call() -> None:
        engine = create_async_engine(settings.database_url, pool_pre_ping=False)
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        finally:
            await engine.dispose()

    return await _timed(ServiceId.POSTGRES, settings, call())


async def probe_redis(settings: Settings) -> ServiceStatus:
    async def call() -> None:
        client = Redis.from_url(settings.redis_url)
        try:
            await client.ping()
        finally:
            await client.aclose()

    return await _timed(ServiceId.REDIS, settings, call())


async def _http_get(url: str, headers: dict[str, str] | None = None) -> None:
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()


async def probe_litellm(settings: Settings) -> ServiceStatus:
    url = f"{settings.litellm_base_url}/health/liveliness"
    return await _timed(ServiceId.LITELLM, settings, _http_get(url))


async def probe_ollama(settings: Settings) -> ServiceStatus:
    url = f"{settings.ollama_base_url}/api/tags"
    return await _timed(ServiceId.OLLAMA, settings, _http_get(url))


async def probe_ib_gateway(settings: Settings) -> ServiceStatus:
    async def call() -> None:
        _, writer = await asyncio.open_connection(
            settings.ib_gateway_host, settings.ib_gateway_port
        )
        writer.close()
        await writer.wait_closed()

    return await _timed(ServiceId.IB_GATEWAY, settings, call())


async def probe_flex(settings: Settings) -> ServiceStatus:
    # Flex is a scheduled pull, not a live connection: configured is enough here.
    # Sync freshness is reported by the portfolio module once it exists (M1).
    if settings.ibkr_flex_token and settings.ibkr_flex_query_id:
        return ServiceStatus(id=ServiceId.IBKR_FLEX, state=ServiceState.UP, detail="configured")
    return ServiceStatus(id=ServiceId.IBKR_FLEX, state=ServiceState.UNCONFIGURED)


async def probe_telegram(settings: Settings) -> ServiceStatus:
    if settings.telegram_bot_token:
        return ServiceStatus(id=ServiceId.TELEGRAM, state=ServiceState.UP, detail="configured")
    return ServiceStatus(id=ServiceId.TELEGRAM, state=ServiceState.UNCONFIGURED)


DEFAULT_PROBES: tuple[Probe, ...] = (
    probe_postgres,
    probe_redis,
    probe_litellm,
    probe_ollama,
    probe_ib_gateway,
    probe_flex,
    probe_telegram,
)


async def collect_status(
    settings: Settings, probes: tuple[Probe, ...] = DEFAULT_PROBES
) -> SystemStatus:
    services = await asyncio.gather(*(probe(settings) for probe in probes))
    return SystemStatus(as_of=datetime.now(UTC), services=list(services))
