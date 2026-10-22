"""arq worker: background jobs (ingest, radar, agents) are registered here from M1 on."""

from datetime import UTC, datetime
from typing import Any, ClassVar

from arq import cron
from arq.connections import RedisSettings

from preza.config import get_settings


async def heartbeat(ctx: dict[str, Any]) -> str:
    """Proves the scheduler runs; replaced by real jobs in later milestones."""
    return datetime.now(UTC).isoformat()


class WorkerSettings:
    functions: ClassVar[list[Any]] = [heartbeat]
    cron_jobs: ClassVar[list[Any]] = [cron(heartbeat, minute={0, 15, 30, 45})]
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
