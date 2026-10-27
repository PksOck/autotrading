from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from preza.config import Settings, get_settings
from preza.db import get_session
from preza.domain.outcome import HORIZONS
from preza.domain.track_record import TrackRecordOut
from preza.services.track_record import load_track_record

router = APIRouter(prefix="/track-record", tags=["track-record"])
Session = Annotated[AsyncSession, Depends(get_session)]


@router.get("", response_model=TrackRecordOut)
async def track_record(
    session: Session,
    settings: Annotated[Settings, Depends(get_settings)],
    horizon_days: int = 20,
) -> TrackRecordOut:
    if horizon_days not in HORIZONS:
        raise HTTPException(422, detail="unsupported_horizon")
    return await load_track_record(session, horizon_days, settings.benchmark_symbol)
