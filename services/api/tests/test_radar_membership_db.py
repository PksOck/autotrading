"""Real PostgreSQL regressions for Radar membership before the result limit (BL-221)."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any

import httpx
import pytest
from sqlalchemy import event as sql_event
from sqlalchemy.engine import Connection

from preza.db import get_engine, get_sessionmaker
from preza.domain.radar import RadarView
from preza.models import AccountSnapshot, Event, Instrument, NewsItem, Position, WatchlistItem
from preza.services.radar_views import list_events
from tests.conftest import FakeRouter

pytestmark = pytest.mark.db


def radar_event(
    title: str,
    symbols: list[str],
    *,
    score: str | None = "0.5",
    seen: datetime | None = None,
    status: str = "new",
) -> Event:
    return Event(
        title=title,
        symbols=symbols,
        score=Decimal(score) if score is not None else None,
        first_seen_at=seen or datetime.now(UTC),
        last_seen_at=seen or datetime.now(UTC),
        status=status,
    )


async def seed_membership() -> None:
    async with get_sessionmaker()() as session:
        held = Instrument(symbol="HELD", source="test")
        watched = Instrument(symbol="WATCHED", source="test")
        removed = Instrument(symbol="REMOVED", source="test")
        zero = Instrument(symbol="ZERO", source="test")
        old = Instrument(symbol="OLD", source="test")
        session.add_all([held, watched, removed, zero, old])
        await session.flush()
        for instrument, quantity, account, report in [
            (held, "1", "holding", date(2026, 10, 29)),
            (zero, "0", "holding", date(2026, 10, 29)),
            (old, "1", "emptied", date(2026, 10, 28)),
        ]:
            session.add(
                Position(
                    instrument_id=instrument.id,
                    account_id=account,
                    report_date=report,
                    quantity=Decimal(quantity),
                    currency="USD",
                    source="test",
                )
            )
        session.add_all(
            [
                AccountSnapshot(
                    account_id="emptied",
                    report_date=date(2026, 10, 29),
                    positions_complete=True,
                    source="test",
                ),
                WatchlistItem(instrument_id=watched.id),
                WatchlistItem(instrument_id=removed.id, removed_at=datetime.now(UTC)),
            ]
        )
        await session.commit()


@pytest.mark.parametrize(
    ("view", "foreign", "eligible"),
    [
        (RadarView.PORTFOLIO, ["OTHER"], ["HELD"]),
        (RadarView.WATCHLIST, ["OTHER"], ["WATCHED"]),
        (RadarView.DISCOVER, ["HELD", "WATCHED"], ["OTHER"]),
    ],
)
async def test_membership_precedes_limit_despite_more_than_triple_foreign_events(
    api: tuple[httpx.AsyncClient, FakeRouter],
    view: RadarView,
    foreign: list[str],
    eligible: list[str],
) -> None:
    await seed_membership()
    async with get_sessionmaker()() as session:
        session.add_all([radar_event(f"foreign {i}", foreign, score="0.9") for i in range(7)])
        session.add(radar_event("eligible", eligible))
        await session.commit()
        result = await list_events(session, view, limit=2)
    assert [row.title for row in result] == ["eligible"]


@pytest.mark.parametrize(
    ("view", "expected"),
    [
        (RadarView.PORTFOLIO, []),
        (RadarView.WATCHLIST, []),
        (RadarView.DISCOVER, ["unclassified", "other"]),
    ],
)
async def test_empty_membership_includes_unclassified_events_only_in_discover(
    api: tuple[httpx.AsyncClient, FakeRouter], view: RadarView, expected: list[str]
) -> None:
    async with get_sessionmaker()() as session:
        session.add_all(
            [radar_event("unclassified", [], score="0.8"), radar_event("other", ["OTHER"])]
        )
        await session.commit()
        result = await list_events(session, view)
    assert [row.title for row in result] == expected


@pytest.mark.parametrize(
    ("view", "expected"),
    [
        (RadarView.PORTFOLIO, ["mixed"]),
        (RadarView.WATCHLIST, ["mixed"]),
        (RadarView.DISCOVER, ["removed", "zero", "old", "unclassified"]),
    ],
)
async def test_membership_preserves_active_symbols_and_existing_filters(
    api: tuple[httpx.AsyncClient, FakeRouter], view: RadarView, expected: list[str]
) -> None:
    await seed_membership()
    now = datetime.now(UTC)
    async with get_sessionmaker()() as session:
        session.add_all(
            [
                radar_event("mixed", ["HELD", "WATCHED", "OTHER", "HELD"], score="0.9"),
                radar_event("removed", ["REMOVED"], score="0.8"),
                radar_event("zero", ["ZERO"], score="0.7"),
                radar_event("old", ["OLD"], score="0.6"),
                radar_event("unclassified", [], score="0.5"),
                radar_event("low", ["HELD", "WATCHED", "OTHER"], score="0.49"),
                radar_event("dismissed", ["HELD", "WATCHED"], status="dismissed"),
                radar_event("dismissed other", ["OTHER"], status="dismissed"),
                radar_event("stale", ["HELD", "WATCHED"], seen=now - timedelta(days=8)),
                radar_event("stale other", ["OTHER"], seen=now - timedelta(days=8)),
                radar_event("null score", ["HELD", "WATCHED", "OTHER"], score=None),
            ]
        )
        await session.commit()
        result = await list_events(session, view, min_score=0.5)
    assert [row.title for row in result] == expected


async def test_order_is_score_then_recency_then_id_with_nulls_last_and_zero_limit(
    api: tuple[httpx.AsyncClient, FakeRouter],
) -> None:
    now = datetime.now(UTC)
    async with get_sessionmaker()() as session:
        for title, score, seen in [
            ("null first", None, now),
            ("null second", None, now),
            ("zero", "0", now),
            ("older high", "0.9", now - timedelta(hours=1)),
            ("tie first", "0.9", now),
            ("tie second", "0.9", now),
        ]:
            session.add(radar_event(title, ["OTHER"], score=score, seen=seen))
            await session.flush()
        await session.commit()
        result = await list_events(session, RadarView.DISCOVER)
        assert [row.title for row in result] == [
            "tie second",
            "tie first",
            "older high",
            "zero",
            "null second",
            "null first",
        ]
        assert await list_events(session, RadarView.DISCOVER, limit=0) == []


async def test_sql_membership_and_limit_bound_event_and_source_loading(
    api: tuple[httpx.AsyncClient, FakeRouter],
) -> None:
    await seed_membership()
    async with get_sessionmaker()() as session:
        for i in range(12):
            row = radar_event(f"event {i}", ["HELD"] if i < 4 else ["OTHER"])
            session.add(row)
            await session.flush()
            session.add(
                NewsItem(
                    event_id=row.id,
                    source="test",
                    url=f"https://fixture.test/{i}",
                    title=f"source {i}",
                    kind="news",
                    published_at=datetime.now(UTC),
                )
            )
        await session.commit()
    statements: list[tuple[str, Any]] = []

    def capture(
        conn: Connection,
        cursor: Any,
        statement: str,
        parameters: Any,
        context: Any,
        executemany: bool,
    ) -> None:
        statements.append((statement, parameters))

    engine = get_engine().sync_engine
    sql_event.listen(engine, "before_cursor_execute", capture)
    try:
        async with get_sessionmaker()() as session:
            result = await list_events(session, RadarView.PORTFOLIO, limit=2)
    finally:
        sql_event.remove(engine, "before_cursor_execute", capture)
    assert len(result) == 2 and all(len(row.sources) == 1 for row in result)
    assert len(statements) == 4  # positions, watchlist, bounded events, batched sources
    event_query, parameters = next(s for s in statements if s[0].startswith("SELECT event.id"))
    assert "event.symbols &&" in event_query and "LIMIT" in event_query
    assert parameters[-1] == 2
    source_queries = [s for s in statements if "FROM news_item" in s[0]]
    assert len(source_queries) == 1 and len(source_queries[0][1]) == 2
    assert api[1].calls == []
