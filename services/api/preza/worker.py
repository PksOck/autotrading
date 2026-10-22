"""arq worker: scheduled data pulls (BL-022, BL-024). Times are UTC."""

import logging
from typing import Any, ClassVar

from arq import cron
from arq.connections import RedisSettings
from sqlalchemy import select

from preza.broker.flex import FlexClient, FlexError
from preza.config import get_settings
from preza.db import get_sessionmaker
from preza.deps import get_bars_service
from preza.models import Instrument, Position, WatchlistItem
from preza.services.portfolio import record_sync, store_statement

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


class WorkerSettings:
    functions: ClassVar[list[Any]] = [sync_flex, refresh_bars]
    cron_jobs: ClassVar[list[Any]] = [
        cron(sync_flex, hour={5}, minute={15}),  # after IBKR prepares the previous day (~07:15 CET)
        cron(refresh_bars, weekday={0, 1, 2, 3, 4}, hour={21}, minute={30}),  # after US close
    ]
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
