"""Overview visualizations keep missing market data and cohort scope honest."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import httpx
import pytest

from preza.db import get_sessionmaker
from preza.models import Bar, Event, NewsItem, Signal
from preza.routes.overview import market_strip
from preza.services.instruments import get_or_create
from tests.conftest import FakeRouter


def test_missing_market_inputs_never_become_sample_values() -> None:
    rows = market_strip([])
    assert [row.key for row in rows] == ["spy", "vix", "us10y", "dxy"]
    assert all(row.value is None and row.source is None and row.as_of is None for row in rows)


def test_spy_requires_200_closes_and_uses_decimal_sma() -> None:
    bars = [Bar(day=date(2026, 10, 28), close=Decimal("100"), source="test") for _ in range(200)]
    bars[0].close = Decimal("110")
    assert market_strip(bars[:199])[0].value is None
    spy = market_strip(bars)[0]
    assert spy.value == (Decimal("110") / Decimal("100.05") - 1) * 100
    assert spy.source == "test" and spy.as_of == date(2026, 10, 28)


@pytest.mark.db
async def test_overview_cohort_dedupes_events_and_timeline_uses_first_detection(
    api: tuple[httpx.AsyncClient, FakeRouter],
) -> None:
    client, _ = api
    now = datetime.now(UTC)
    async with get_sessionmaker()() as session:
        instrument = await get_or_create(session, symbol="MSFT", source="test")
        recent = Event(
            title="Recent",
            symbols=["MSFT"],
            first_seen_at=now - timedelta(days=2),
            last_seen_at=now,
            triaged_at=now,
        )
        refreshed_old = Event(
            title="Old refreshed",
            symbols=["MSFT"],
            first_seen_at=now - timedelta(days=40),
            last_seen_at=now,
        )
        session.add_all([recent, refreshed_old])
        await session.flush()
        session.add_all(
            [
                NewsItem(
                    title=f"News {i}",
                    source="test",
                    url=f"https://example.test/{i}",
                    kind="news",
                    published_at=now - timedelta(days=40),
                    fetched_at=now - timedelta(days=1),
                    event_id=recent.id,
                )
                for i in range(2)
            ]
        )
        session.add(
            NewsItem(
                title="Outside cohort",
                source="test",
                url="https://example.test/old",
                kind="news",
                published_at=now - timedelta(days=40),
                fetched_at=now - timedelta(days=40),
                event_id=refreshed_old.id,
            )
        )
        session.add_all(
            [
                Signal(
                    instrument_id=instrument.id,
                    event_id=recent.id,
                    kind="catalyst",
                    source="radar",
                    direction="up",
                    horizon="months",
                    strength=Decimal("0.6"),
                    rationale="Evidence",
                    evidence=[],
                    status="dismissed",
                )
                for _ in range(2)
            ]
        )
        await session.commit()
        event_id = recent.id

    response = await client.get("/overview")
    assert response.status_code == 200
    data = response.json()
    assert data["funnel30d"] | {"since": None} == {
        "since": None,
        "news": 2,
        "events": 1,
        "triaged": 1,
        "signalled": 1,
    }
    assert data["timeline7d"]["total"] == 1
    assert [row["id"] for row in data["timeline7d"]["events"]] == [event_id]
    assert len(data["timeline7d"]["events"][0]["sources"]) == 2
    assert all(row["value"] is None for row in data["market_strip"])
