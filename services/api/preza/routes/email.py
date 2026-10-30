"""Read and save non-secret notification preferences; deliberately no test-send endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from preza.config import Settings, get_settings
from preza.db import get_session
from preza.domain.email import EmailPreferencesInput, EmailPreferencesOut
from preza.services.email import preferences, save_preferences

router = APIRouter(prefix="/notifications/email", tags=["notifications"])
Session = Annotated[AsyncSession, Depends(get_session)]
Config = Annotated[Settings, Depends(get_settings)]


@router.get("", response_model=EmailPreferencesOut)
async def get_preferences(session: Session, settings: Config) -> EmailPreferencesOut:
    return await preferences(session, settings)


@router.patch("", response_model=EmailPreferencesOut)
async def patch_preferences(
    body: EmailPreferencesInput, session: Session, settings: Config
) -> EmailPreferencesOut:
    return await save_preferences(session, settings, body)
