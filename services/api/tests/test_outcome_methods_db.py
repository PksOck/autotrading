"""Exercise an actual neutral producer and verify that method labeling never rewrites rows."""

from datetime import UTC, date, datetime
from decimal import Decimal

import httpx
import pytest
from sqlalchemy import select

from preza import db
from preza.models import Bar, Event, Instrument, SignalOutcome
from preza.radar.signals import upsert_signal
from preza.services.outcomes import compute_outcomes
from tests.conftest import FakeRouter

pytestmark = pytest.mark.db


async def test_neutral_radar_signal_remains_legacy_and_is_skipped_in_the_study(
    api: tuple[httpx.AsyncClient, FakeRouter],
) -> None:
    client, _ = api
    async with db.get_sessionmaker()() as session:
        instrument = Instrument(
            symbol="NEUTRAL", exchange="TEST", currency="USD", kind="stock", source="synthetic"
        )
        event = Event(
            title="Synthetic neutral event",
            symbols=["NEUTRAL"],
            sentiment=Decimal(0),
            score=Decimal("0.9"),
            materiality=Decimal("0.7"),
            event_type="other",
            is_rumor=False,
            items=[],
        )
        session.add_all([instrument, event])
        await session.flush()
        signal = await upsert_signal(session, event, instrument.id, threshold=0.1)
        assert signal is not None and signal.direction == "neutral"
        signal.created_at = datetime(2026, 10, 23, 22, tzinfo=UTC)
        signal_id = signal.id
        session.add_all(
            [
                Bar(
                    instrument_id=instrument.id,
                    interval="1d",
                    day=date(2026, 10, day),
                    open=Decimal(price),
                    high=Decimal(price + 1),
                    low=Decimal(price - 1),
                    close=Decimal(price),
                    source="synthetic",
                )
                for day, price in [(23, 80), (26, 100), (27, 110)]
            ]
        )
        await session.commit()

    async with db.get_sessionmaker()() as session:
        assert await compute_outcomes(session) == 1
        await session.commit()
        stored = (await session.scalars(select(SignalOutcome))).one()
        before = (stored.start_day, stored.end_day, stored.return_pct, stored.computed_at)
        assert stored.signal_id == signal_id
        assert stored.return_pct == Decimal("25")
        assert stored.alpha_pct is None

    legacy = (await client.get("/track-record?horizon_days=1")).json()
    assert legacy["method_id"] == "legacy-unversioned"
    assert legacy["measured"] == 1
    page = (await client.get("/track-record/outcomes?horizon_days=1")).json()
    assert page["method_id"] == "legacy-unversioned"
    assert page["items"][0]["signal_id"] == str(signal_id)
    stats = (await client.get("/entries/outcomes")).json()
    assert stats[0]["method_id"] == "legacy-unversioned"
    response = await client.post("/backtest", json={"source": "signal", "horizon_sessions": 1})
    assert response.status_code == 200
    study = response.json()
    assert study["method_id"] == "saved-record-after-utc-close-v1"
    assert (study["completed"], study["skipped"]) == (0, 1)
    assert study["rows"][0]["skip_reason"] == "neutral_or_unknown_direction"
    async with db.get_sessionmaker()() as session:
        assert await compute_outcomes(session) == 0
        stored = (await session.scalars(select(SignalOutcome))).one()
        assert (stored.start_day, stored.end_day, stored.return_pct, stored.computed_at) == before
