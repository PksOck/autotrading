from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from preza import __version__
from preza.config import Settings, get_settings
from preza.domain.system import SystemStatus
from preza.system.checks import collect_status

router = APIRouter(tags=["system"])


class Health(BaseModel):
    status: str
    version: str


@router.get("/health", response_model=Health)
async def health() -> Health:
    """Liveness only: the process is up. Dependencies are in /system/status."""
    return Health(status="ok", version=__version__)


@router.get("/system/status", response_model=SystemStatus)
async def system_status(settings: Annotated[Settings, Depends(get_settings)]) -> SystemStatus:
    return await collect_status(settings)
