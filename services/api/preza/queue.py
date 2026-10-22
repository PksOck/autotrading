"""Enqueue background jobs without letting a missing Redis break a request."""

import logging

from arq import create_pool
from arq.connections import RedisSettings
from redis.exceptions import RedisError

from preza.config import Settings

log = logging.getLogger(__name__)


async def enqueue(
    settings: Settings, job: str, *args: object, job_id: str | None = None
) -> str | None:
    """Returns the job id, or None when the queue is unreachable or the job is already queued."""
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    redis_settings.conn_retries = 0
    redis_settings.conn_timeout = 2
    try:
        pool = await create_pool(redis_settings)
    except (RedisError, OSError) as exc:
        log.warning("queue unavailable for %s: %s", job, exc)
        return None
    try:
        queued = await pool.enqueue_job(job, *args, _job_id=job_id)
    except (RedisError, OSError) as exc:
        log.warning("enqueue %s failed: %s", job, exc)
        return None
    finally:
        await pool.aclose()
    return queued.job_id if queued else None
