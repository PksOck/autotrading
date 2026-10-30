"""Saved-record event study: availability, direction, costs and incomplete history."""

from datetime import UTC, date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import event

from preza.db import get_sessionmaker
from preza.domain.backtest import BacktestRequest
from preza.models import AnalysisRun, Bar, Signal
from preza.services.backtest import evaluate_record, opinion_direction
from preza.services.instruments import get_or_create
from tests.conftest import FakeRouter


def bars() -> list[Bar]:
    return [
        Bar(day=date(2026, 10, day), close=Decimal(price), source="test")
        for day, price in [(23, "80"), (26, "100"), (27, "110")]
    ]


def test_entry_is_strictly_after_availability_day_and_costs_apply_to_both_notionals() -> None:
    result = evaluate_record(
        available_at=datetime(2026, 10, 23, 8, tzinfo=UTC),
        direction="up",
        bars=bars(),
        horizon=1,
        cost_bps=Decimal("10"),
    )
    assert result.entry_date == date(2026, 10, 26)
    assert result.exit_date == date(2026, 10, 27)
    assert result.gross_return_pct == Decimal("10")
    assert result.net_return_pct == Decimal("9.79")


def test_short_direction_and_neutral_skip() -> None:
    result = evaluate_record(
        available_at=datetime(2026, 10, 23, tzinfo=UTC),
        direction="down",
        bars=bars(),
        horizon=1,
        cost_bps=Decimal(0),
    )
    assert result.net_return_pct == Decimal("-10")
    neutral = evaluate_record(
        available_at=datetime(2026, 10, 23, tzinfo=UTC),
        direction="neutral",
        bars=bars(),
        horizon=1,
        cost_bps=Decimal(0),
    )
    assert neutral.skip_reason == "neutral_or_unknown_direction"


def test_partial_history_and_nonpositive_prices_are_explicit_skips() -> None:
    result = evaluate_record(
        available_at=datetime(2026, 10, 23, tzinfo=UTC),
        direction="up",
        bars=bars(),
        horizon=5,
        cost_bps=Decimal(0),
    )
    assert result.skip_reason == "insufficient_future_sessions"
    assert result.entry_date == date(2026, 10, 26)
    invalid = bars()
    invalid[1].close = Decimal(0)
    result = evaluate_record(
        available_at=datetime(2026, 10, 23, tzinfo=UTC),
        direction="up",
        bars=invalid,
        horizon=1,
        cost_bps=Decimal(0),
    )
    assert result.skip_reason == "invalid_price"


def test_utc_availability_and_unknown_opinion_are_not_guessed() -> None:
    # Local Monday 00:30 is still Sunday UTC: Monday's close can be the entry.
    result = evaluate_record(
        available_at=datetime(2026, 10, 26, 0, 30, tzinfo=timezone(timedelta(hours=2))),
        direction="up",
        bars=bars(),
        horizon=1,
        cost_bps=Decimal(0),
    )
    assert result.entry_date == date(2026, 10, 26)
    assert opinion_direction("Buy") == "up"
    assert opinion_direction("Underweight") == "down"
    assert opinion_direction("strong conviction") == "neutral"
    assert opinion_direction("Hold") == "neutral"
    assert opinion_direction(None) == "neutral"


def test_request_rejects_reversed_dates_and_out_of_range_cost() -> None:
    with pytest.raises(ValueError):
        BacktestRequest(available_from=date(2026, 10, 28), available_to=date(2026, 10, 1))
    with pytest.raises(ValueError):
        BacktestRequest(cost_bps=Decimal("-1"))


@pytest.mark.db
async def test_saved_record_filters_counts_and_incomplete_opinions(
    api: tuple[httpx.AsyncClient, FakeRouter],
) -> None:
    client, _ = api
    now = datetime.now(UTC)
    available = now - timedelta(days=10)
    async with get_sessionmaker()() as session:
        instrument = await get_or_create(session, symbol="MSFT", source="test")
        for strength, status in [("0.8", "accepted"), ("0.2", "dismissed")]:
            session.add(
                Signal(
                    instrument_id=instrument.id,
                    kind="catalyst",
                    source="radar",
                    direction="up",
                    horizon="months",
                    strength=Decimal(strength),
                    rationale="Evidence",
                    evidence=[],
                    status=status,
                    created_at=available,
                )
            )
        for status, finished_at, rating in [("done", available, "Buy"), ("running", None, None)]:
            session.add(
                AnalysisRun(
                    instrument_id=instrument.id,
                    engine="stock",
                    trade_date=available.date(),
                    status=status,
                    finished_at=finished_at,
                    rating=rating,
                )
            )
        for offset, price in [(1, "100"), (2, "110"), (10, "999"), (11, "999")]:
            session.add(
                Bar(
                    instrument_id=instrument.id,
                    interval="1d",
                    day=available.date() + timedelta(days=offset),
                    open=Decimal(price),
                    high=Decimal(price),
                    low=Decimal(price),
                    close=Decimal(price),
                    source="test",
                )
            )
        await session.commit()

    response = await client.post(
        "/backtest", json={"horizon_sessions": 1, "cost_bps": "0", "limit": 1}
    )
    assert response.status_code == 200
    limited = response.json()
    assert limited["total_matching"] == 3 and limited["evaluated"] == 1
    assert limited["truncated"] is True
    response = await client.post(
        "/backtest",
        json={
            "horizon_sessions": 1,
            "cost_bps": "0",
            "source": "signal",
            "min_strength": "0.5",
            "signal_status": "accepted",
            "available_from": available.date().isoformat(),
            "available_to": available.date().isoformat(),
        },
    )
    data = response.json()
    assert data["total_matching"] == data["completed"] == 1
    assert data["rows"][0]["record_status"] == "accepted"
    assert Decimal(data["mean_net_return_pct"]) == Decimal("10")
    assert data["rows"][0]["entry_source"] == "test"
    assert data["rows"][0]["entry_date"] == (available.date() + timedelta(days=1)).isoformat()
    response = await client.post("/backtest", json={"source": "analysis", "horizon_sessions": 60})
    data = response.json()
    assert data["total_matching"] == data["skipped"] == 1
    assert data["rows"][0]["skip_reason"] == "insufficient_future_sessions"
    async with get_sessionmaker()() as session:
        session.add(
            AnalysisRun(
                instrument_id=instrument.id,
                engine="stock",
                trade_date=now.date() - timedelta(days=1),
                status="done",
                finished_at=now - timedelta(days=1),
                rating="Buy",
            )
        )
        await session.commit()
    response = await client.post(
        "/backtest",
        json={
            "source": "analysis",
            "horizon_sessions": 1,
            "available_from": (now.date() - timedelta(days=1)).isoformat(),
        },
    )
    assert response.json()["rows"][0]["skip_reason"] == "no_entry_bar"


@pytest.mark.db
async def test_history_loading_is_bounded_per_record_not_by_full_instrument_history(
    api: tuple[httpx.AsyncClient, FakeRouter],
) -> None:
    client, _ = api
    now = datetime.now(UTC)
    available = now - timedelta(days=400)
    async with get_sessionmaker()() as session:
        instrument = await get_or_create(session, symbol="MSFT", source="test")
        shared_id = uuid4()
        session.add(
            Signal(
                id=shared_id,
                instrument_id=instrument.id,
                kind="catalyst",
                source="radar",
                direction="up",
                horizon="months",
                strength=Decimal("0.8"),
                rationale="Evidence",
                evidence=[],
                status="accepted",
                created_at=available,
            )
        )
        session.add(
            AnalysisRun(
                id=shared_id,
                instrument_id=instrument.id,
                engine="stock",
                status="done",
                rating="Buy",
                trade_date=available.date() + timedelta(days=100),
                finished_at=available + timedelta(days=100),
            )
        )
        for offset in range(1, 350):
            session.add(
                Bar(
                    instrument_id=instrument.id,
                    interval="1d",
                    day=available.date() + timedelta(days=offset),
                    open=Decimal(100),
                    high=Decimal(100),
                    low=Decimal(100),
                    close=Decimal(100),
                    source="test",
                )
            )
        await session.commit()
    loaded: list[Bar] = []

    def remember_bar(target: Bar, context: object) -> None:
        loaded.append(target)

    event.listen(Bar, "load", remember_bar)
    try:
        response = await client.post("/backtest", json={"source": "all", "horizon_sessions": 1})
    finally:
        event.remove(Bar, "load", remember_bar)
    assert response.status_code == 200
    assert response.json()["completed"] == 2
    assert len(loaded) == 4
    assert [row["entry_date"] for row in response.json()["rows"]] == [
        (available.date() + timedelta(days=1)).isoformat(),
        (available.date() + timedelta(days=101)).isoformat(),
    ]
