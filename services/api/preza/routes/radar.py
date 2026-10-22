from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from preza.db import get_session
from preza.domain.radar import EventOut, RadarView
from preza.models import Event
from preza.services.radar_views import event_out, list_events

router = APIRouter(prefix="/radar", tags=["radar"])
Session = Annotated[AsyncSession, Depends(get_session)]


@router.get("/events", response_model=list[EventOut])
async def events(
    session: Session,
    view: RadarView = RadarView.DISCOVER,
    min_score: Annotated[float, Query(ge=0, le=1)] = 0.0,
    days: Annotated[int, Query(ge=1, le=60)] = 7,
) -> list[EventOut]:
    return await list_events(session, view, min_score, days)


@router.get("/events/{event_id}", response_model=EventOut)
async def event(session: Session, event_id: int) -> EventOut:
    found = await session.get(Event, event_id)
    if found is None:
        raise HTTPException(404, detail="event_not_found")
    return event_out(found)
