from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from preza.db import get_session
from preza.domain.dividends import DividendsOut
from preza.services.dividends import get_dividends

router = APIRouter(prefix="/portfolio/dividends", tags=["dividends"])


@router.get("", response_model=DividendsOut)
async def dividends(
    session: Annotated[AsyncSession, Depends(get_session)],
    account_id: str | None = None,
    currency: Annotated[str | None, Query(pattern="^[A-Z]{3}$")] = None,
    from_date: date | None = None,
    to_date: date | None = None,
) -> DividendsOut:
    if from_date and to_date and from_date > to_date:
        raise HTTPException(422, detail="invalid_date_range")
    return await get_dividends(session, account_id, currency, from_date, to_date)
