from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from preza.config import Settings, get_settings
from preza.db import get_session
from preza.domain.outcome import HORIZONS
from preza.domain.track_record import TrackOutcomePage, TrackRecordOut
from preza.services.track_record import load_outcomes, load_track_record

router = APIRouter(prefix="/track-record", tags=["track-record"])
Session = Annotated[AsyncSession, Depends(get_session)]


@router.get("", response_model=TrackRecordOut)
async def track_record(
    session: Session,
    settings: Annotated[Settings, Depends(get_settings)],
    horizon_days: int = 20,
    created_from: date | None = None,
    created_to: date | None = None,
) -> TrackRecordOut:
    if horizon_days not in HORIZONS:
        raise HTTPException(422, detail="unsupported_horizon")
    if created_from and created_to and created_from > created_to:
        raise HTTPException(422, detail="invalid_cohort")
    return await load_track_record(
        session, horizon_days, settings.benchmark_symbol, created_from, created_to
    )


@router.get("/outcomes", response_model=TrackOutcomePage)
async def outcomes(
    session: Session,
    horizon_days: int = 20,
    created_from: date | None = None,
    created_to: date | None = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
) -> TrackOutcomePage:
    if horizon_days not in HORIZONS or (created_from and created_to and created_from > created_to):
        raise HTTPException(422, detail="invalid_cohort")
    return await load_outcomes(session, horizon_days, created_from, created_to, offset, limit)
