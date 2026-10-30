"""Watchlist: two tiers, idea source, note, alerts and performance since added (BL-032)."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from preza.domain.market import InstrumentKind
from preza.domain.portfolio import WatchlistCreate, WatchlistOut, WatchlistUpdate, WatchTier
from preza.models import Bar, WatchlistItem
from preza.services.instruments import find_by_symbol, get_or_create
from preza.services.market_context import MarketContext, identity_status, market_context


class AlreadyWatchedError(Exception):
    pass


async def _last_close(session: AsyncSession, instrument_id: int) -> Decimal | None:
    return await session.scalar(
        select(Bar.close)
        .where(Bar.instrument_id == instrument_id)
        .order_by(Bar.day.desc())
        .limit(1)
    )


async def to_out(
    session: AsyncSession, item: WatchlistItem, context: MarketContext | None = None
) -> WatchlistOut:
    context = (
        context
        if context is not None
        else (await market_context(session, [item.instrument_id]))[item.instrument_id]
    )
    last = Decimal(context["latest_close"]) if context["latest_close"] is not None else None
    since = (last / item.added_price - 1) * 100 if last is not None and item.added_price else None
    return WatchlistOut(
        id=item.id,
        instrument_id=item.instrument_id,
        exchange=item.instrument.exchange,
        currency=item.instrument.currency,
        identity_status=identity_status(item.instrument),
        revision=item.revision,
        change_pct=context["change_pct"],
        price_meta=context["price_meta"],
        metrics=context["metrics"],
        price_trend=context["price_trend"],
        symbol=item.instrument.symbol,
        name=item.instrument.name,
        kind=InstrumentKind(item.instrument.kind),
        tier=WatchTier(item.tier),
        source=item.source,
        tags=list(item.tags or []),
        note=item.note,
        target_price=item.target_price,
        alert_below=item.alert_below,
        alert_above=item.alert_above,
        added_at=item.added_at,
        added_price=item.added_price,
        last_close=last,
        since_added_pct=since,
        reviewed_at=item.reviewed_at,
    )


async def list_items(session: AsyncSession) -> list[WatchlistOut]:
    items = list(
        await session.scalars(
            select(WatchlistItem)
            .where(WatchlistItem.removed_at.is_(None))
            .order_by(WatchlistItem.tier, WatchlistItem.added_at.desc(), WatchlistItem.id)
        )
    )
    contexts = await market_context(session, [item.instrument_id for item in items])
    return [await to_out(session, item, contexts[item.instrument_id]) for item in items]


async def fill_added_price(session: AsyncSession, instrument_id: int) -> None:
    """An item added before its bars arrived takes the close of the day it was added."""
    item = await session.scalar(
        select(WatchlistItem).where(WatchlistItem.instrument_id == instrument_id)
    )
    if item is None or item.added_price is not None:
        return
    item.added_price = await session.scalar(
        select(Bar.close)
        .where(Bar.instrument_id == instrument_id, Bar.day <= item.added_at.date())
        .order_by(Bar.day.desc())
        .limit(1)
    ) or await _last_close(session, instrument_id)


async def add(session: AsyncSession, data: WatchlistCreate) -> WatchlistItem:
    instrument = await find_by_symbol(session, data.symbol) or await get_or_create(
        session, symbol=data.symbol, source="manual"
    )
    exists = await session.scalar(
        select(WatchlistItem).where(WatchlistItem.instrument_id == instrument.id)
    )
    if exists and exists.removed_at is None:
        raise AlreadyWatchedError(instrument.symbol)
    if exists:
        exists.removed_at = None
        exists.revision += 1
        exists.added_at = datetime.now(UTC)
        exists.added_price = await _last_close(session, instrument.id)
        exists.reviewed_at = None
        for key in ("tier", "source", "tags", "note", "target_price", "alert_below", "alert_above"):
            value = getattr(data, key)
            setattr(exists, key, value.value if isinstance(value, WatchTier) else value)
        await session.flush()
        return exists
    item = WatchlistItem(
        instrument_id=instrument.id,
        tier=data.tier.value,
        source=data.source,
        tags=[t.strip() for t in data.tags if t.strip()],
        note=data.note,
        target_price=data.target_price,
        alert_below=data.alert_below,
        alert_above=data.alert_above,
        added_price=await _last_close(session, instrument.id),
    )
    session.add(item)
    await session.flush()
    await session.refresh(item, ["instrument"])
    return item


async def update(
    session: AsyncSession, item: WatchlistItem, data: WatchlistUpdate
) -> WatchlistItem:
    changes = data.model_dump(exclude_unset=True)
    reviewed = changes.pop("reviewed", None)
    for key, value in changes.items():
        setattr(item, key, value.value if isinstance(value, WatchTier) else value)
    if reviewed is not None:
        item.reviewed_at = datetime.now(UTC) if reviewed else None
    item.revision += 1
    await session.flush()
    return item


def bars_since(range_key: str, today: date | None = None) -> date:
    today = today or date.today()
    days = {"1m": 31, "3m": 93, "1y": 366, "2y": 731, "5y": 1827}.get(range_key, 366)
    return today - timedelta(days=days)
