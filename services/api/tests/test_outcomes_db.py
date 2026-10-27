from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest

from preza import db
from preza.models import Bar, Instrument, Signal
from preza.services.outcomes import compute_outcomes, outcome_stats

pytestmark = pytest.mark.db


def _days(n: int) -> list[date]:
    out: list[date] = []
    d = date(2026, 3, 2)
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def _instrument(symbol: str) -> Instrument:
    return Instrument(symbol=symbol, exchange="X", kind="stock", source="test")


def _bars(inst_id: int, closes: list[int]) -> list[Bar]:
    return [
        Bar(
            instrument_id=inst_id,
            interval="1d",
            day=d,
            open=Decimal(c),
            high=Decimal(c + 1),
            low=Decimal(c - 1),
            close=Decimal(c),
            source="test",
        )
        for d, c in zip(_days(len(closes)), closes, strict=True)
    ]


async def test_compute_and_stats(api) -> None:  # type: ignore[no-untyped-def]
    async with db.get_sessionmaker()() as s:
        aapl, spy = _instrument("AAPL"), _instrument("SPY")
        s.add_all([aapl, spy])
        await s.flush()
        s.add_all(_bars(aapl.id, [100, 102, 104, 106, 108, 110, 112]))
        s.add_all(_bars(spy.id, [400, 400, 400, 400, 400, 400, 404]))
        s.add(
            Signal(
                instrument_id=aapl.id,
                kind="technical",
                source="rule",
                direction="up",
                horizon="swing",
                strength=Decimal("0.7"),
                rationale="test",
                evidence=[],
                status="new",
                created_at=datetime(2026, 3, 2, 15, 0, tzinfo=UTC),
            )
        )
        await s.commit()

    async with db.get_sessionmaker()() as s:
        assert await compute_outcomes(s) == 2  # horizons 1 and 5 available
        await s.commit()
    async with db.get_sessionmaker()() as s:
        assert await compute_outcomes(s) == 0
        stats = await outcome_stats(s)

    assert [(x["horizon_days"], x["count"]) for x in stats] == [(1, 1), (5, 1)]
    h5 = stats[1]
    assert h5["hit_rate"] == Decimal("1.0000")
    assert h5["avg_return_pct"] == Decimal("10.0000")
    assert h5["avg_alpha_pct"] == Decimal("10.0000")


async def test_track_record_endpoint_separates_proposals(api) -> None:  # type: ignore[no-untyped-def]
    client, _ = api
    async with db.get_sessionmaker()() as s:
        aapl, spy = _instrument("AAPL"), _instrument("SPY")
        s.add_all([aapl, spy])
        await s.flush()
        s.add_all(_bars(aapl.id, [100, 102, 104, 106, 108, 110, 112]))
        s.add_all(_bars(spy.id, [400, 400, 400, 400, 400, 400, 404]))
        created = datetime(2026, 3, 2, 15, 0, tzinfo=UTC)
        for source, direction, strength in (("rule", "up", "0.7"), ("manual", "down", "0.3")):
            s.add(
                Signal(
                    instrument_id=aapl.id,
                    kind="entry",
                    source=source,
                    direction=direction,
                    horizon="weeks",
                    strength=Decimal(strength),
                    rationale="test",
                    evidence=[],
                    status="new",
                    created_at=created,
                )
            )
        await s.commit()
    async with db.get_sessionmaker()() as s:
        await compute_outcomes(s)
        await s.commit()

    assert (await client.get("/track-record?horizon_days=3")).status_code == 422
    body = (await client.get("/track-record?horizon_days=5")).json()
    assert (body["measured"], body["pending"], body["benchmark"]) == (2, 0, "SPY")
    origins = {o["origin"]: o for o in body["by_origin"]}
    assert origins["system"]["hit_rate"] == "1.0000"
    assert origins["user"]["hit_rate"] == "0.0000"
    assert body["as_of"] and body["overall"]["low_sample"]
    later = (await client.get("/track-record?horizon_days=60")).json()
    assert (later["measured"], later["pending"], later["as_of"]) == (0, 2, None)
