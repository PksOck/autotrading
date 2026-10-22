from typing import Annotated

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from preza.config import Settings, get_settings
from preza.db import get_session
from preza.domain.portfolio import PortfolioOut
from preza.services.portfolio import get_portfolio

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


class Queued(BaseModel):
    job_id: str


@router.get("", response_model=PortfolioOut)
async def portfolio(
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> PortfolioOut:
    return await get_portfolio(session, settings.base_currency)


@router.post("/sync", response_model=Queued, status_code=202)
async def sync(settings: Annotated[Settings, Depends(get_settings)]) -> Queued:
    if not (settings.ibkr_flex_token and settings.ibkr_flex_query_id):
        raise HTTPException(409, detail="flex_unconfigured")
    try:
        pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    except (OSError, ConnectionError) as exc:
        raise HTTPException(503, detail="queue_unavailable") from exc
    job = await pool.enqueue_job("sync_flex")
    await pool.aclose()
    if job is None:
        raise HTTPException(409, detail="sync_already_queued")
    return Queued(job_id=job.job_id)
