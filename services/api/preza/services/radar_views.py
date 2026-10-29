"""Radar views: Discover / Watchlist / Portfolio (BRAND §4, BL-049)."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from preza.domain.radar import EventOut, EventSource, EventStatus, EventType, RadarView
from preza.models import Event, Instrument, WatchlistItem


async def user_symbols(session: AsyncSession) -> tuple[set[str], set[str]]:
    from preza.services.portfolio import latest_positions

    held = {p.instrument.symbol for p in await latest_positions(session)}
    watched = set(
        await session.scalars(
            select(Instrument.symbol).join(WatchlistItem).where(WatchlistItem.removed_at.is_(None))
        )
    )
    return held, watched


def event_out(event: Event) -> EventOut:
    return EventOut(
        id=event.id,
        title=event.title,
        summary=event.summary,
        summary_translations=dict(event.summary_i18n or {}),
        symbols=list(event.symbols),
        event_type=EventType(event.event_type) if event.event_type else None,
        is_rumor=event.is_rumor,
        sentiment=event.sentiment,
        materiality=event.materiality,
        novelty=event.novelty,
        attention=event.attention,
        reaction_z=event.reaction_z,
        score=event.score,
        status=EventStatus(event.status),
        first_seen_at=event.first_seen_at,
        last_seen_at=event.last_seen_at,
        sources=[
            EventSource(
                title=i.title, url=i.url, source=i.source, published_at=i.published_at, kind=i.kind
            )
            for i in sorted(event.items, key=lambda i: i.published_at, reverse=True)
        ],
    )


async def list_events(
    session: AsyncSession, view: RadarView, min_score: float = 0.0, days: int = 7, limit: int = 100
) -> list[EventOut]:
    held, watched = await user_symbols(session)
    since = datetime.now(UTC) - timedelta(days=days)
    query = (
        select(Event)
        .where(Event.last_seen_at >= since, Event.status != EventStatus.DISMISSED.value)
        .order_by(Event.score.desc().nulls_last(), Event.last_seen_at.desc())
        .limit(limit * 3)
    )
    if min_score > 0:
        query = query.where(Event.score >= min_score)
    out: list[EventOut] = []
    for event in await session.scalars(query):
        symbols = set(event.symbols)
        in_view = {
            RadarView.PORTFOLIO: bool(symbols & held),
            RadarView.WATCHLIST: bool(symbols & watched),
            RadarView.DISCOVER: not symbols & (held | watched),
        }[view]
        if in_view:
            out.append(event_out(event))
        if len(out) >= limit:
            break
    return out
