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
