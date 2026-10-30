"""Read-only calculation endpoint for saved research records."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from preza.db import get_session
from preza.domain.backtest import BacktestOut, BacktestRequest
from preza.services.backtest import run_backtest

router = APIRouter(prefix="/backtest", tags=["backtest"])


@router.post("", response_model=BacktestOut)
async def backtest(
    request: BacktestRequest, session: Annotated[AsyncSession, Depends(get_session)]
) -> BacktestOut:
    return await run_backtest(session, request)
