"""Weight calibration (BL-103). Weights change only on an explicit user confirmation."""

import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from preza.db import get_session
from preza.domain.outcome import HORIZONS
from preza.services import calibration
from preza.services.calibration import CalibrationOut, WeightSetOut

router = APIRouter(prefix="/calibration", tags=["calibration"])
Session = Annotated[AsyncSession, Depends(get_session)]


class ConfirmWeights(BaseModel):
    confirm: Literal[True]


@router.get("", response_model=CalibrationOut)
async def get_calibration(session: Session) -> CalibrationOut:
    return await calibration.load_calibration(session)


@router.post("/proposals", response_model=WeightSetOut, status_code=201)
async def create_proposal(session: Session, horizon_days: int = 20) -> WeightSetOut:
    if horizon_days not in HORIZONS:
        raise HTTPException(422, detail="unsupported_horizon")
    return await calibration.create_proposal(session, horizon_days)


@router.post("/{set_id}/confirm", response_model=WeightSetOut)
async def confirm(set_id: uuid.UUID, body: ConfirmWeights, session: Session) -> WeightSetOut:
    return await calibration.confirm_proposal(session, set_id)


@router.post("/{set_id}/reject", response_model=WeightSetOut)
async def reject(set_id: uuid.UUID, session: Session) -> WeightSetOut:
    return await calibration.reject_proposal(session, set_id)
