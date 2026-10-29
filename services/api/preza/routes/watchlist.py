from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from preza.config import Settings, get_settings
from preza.db import get_session
from preza.domain.portfolio import WatchlistCreate, WatchlistOut, WatchlistUpdate
from preza.models import WatchlistItem
from preza.queue import enqueue
from preza.services import watchlist
from preza.services.table_sort import sort_rows

router = APIRouter(prefix="/watchlist", tags=["watchlist"])
Session = Annotated[AsyncSession, Depends(get_session)]


@router.get("", response_model=list[WatchlistOut])
async def list_items(
    session: Session, sort: str | None = None, direction: str = "asc", q: str | None = None
) -> list[WatchlistOut]:
    return sort_rows(await watchlist.list_items(session), sort, direction, q)


@router.post("", response_model=WatchlistOut, status_code=201)
async def add(
    session: Session, settings: Annotated[Settings, Depends(get_settings)], data: WatchlistCreate
) -> WatchlistOut:
    try:
        item = await watchlist.add(session, data)
    except watchlist.AlreadyWatchedError as exc:
        raise HTTPException(409, detail="already_watched") from exc
    out = await watchlist.to_out(session, item)
    await session.commit()  # the worker must see the new instrument
    # Prices arrive within a minute, not at the nightly refresh; no queue only delays them.
    await enqueue(settings, "refresh_instrument_bars", item.instrument_id)
    return out


async def _item_or_404(session: AsyncSession, item_id: int) -> WatchlistItem:
    item = await session.get(WatchlistItem, item_id)
    if item is None or item.removed_at is not None:
        raise HTTPException(404, detail="watchlist_item_not_found")
    return item


@router.patch("/{item_id}", response_model=WatchlistOut)
async def update(session: Session, item_id: int, data: WatchlistUpdate) -> WatchlistOut:
    item = await watchlist.update(session, await _item_or_404(session, item_id), data)
    return await watchlist.to_out(session, item)


@router.delete("/{item_id}", status_code=204)
async def remove(session: Session, item_id: int, revision: int | None = None) -> Response:
    item = await session.scalar(
        select(WatchlistItem).where(WatchlistItem.id == item_id).with_for_update(of=WatchlistItem)
    )
    if item is None or item.removed_at is not None:
        raise HTTPException(404, detail="watchlist_item_not_found")
    if revision is not None and item.revision != revision:
        raise HTTPException(409, detail="watchlist_conflict")
    item.removed_at = datetime.now(UTC)
    item.revision += 1
    return Response(status_code=204)


class RestoreWatchlist(BaseModel):
    expected_revision: int


@router.post("/{item_id}/restore", response_model=WatchlistOut)
async def restore(session: Session, item_id: int, data: RestoreWatchlist) -> WatchlistOut:
    item = await session.scalar(
        select(WatchlistItem).where(WatchlistItem.id == item_id).with_for_update(of=WatchlistItem)
    )
    if item is None:
        raise HTTPException(404, detail="watchlist_item_not_found")
    if item.removed_at is None or item.revision != data.expected_revision:
        raise HTTPException(409, detail="watchlist_conflict")
    item.removed_at = None
    item.revision += 1
    await session.flush()
    return await watchlist.to_out(session, item)
