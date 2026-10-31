"""Characterize both existing methods before declaring their distinct contracts (BL-228)."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest

from preza.domain.backtest import BacktestOut, BacktestRequest
from preza.domain.outcome import DayBar, compute_outcome
from preza.domain.track_record import track_record
from preza.models import Bar
from preza.services.backtest import evaluate_record

AVAILABLE = datetime(2026, 10, 23, 22, tzinfo=UTC)


def _history(closes: list[int]) -> tuple[list[DayBar], list[Bar]]:
    day = AVAILABLE.date()
    legacy: list[DayBar] = []
    stored: list[Bar] = []
    for price in closes:
        while day.weekday() >= 5:
            day += timedelta(days=1)
        close = Decimal(price)
        legacy.append(DayBar(day, close + 1, close - 1, close))
        stored.append(Bar(day=day, close=close, source="synthetic-method-test"))
        day += timedelta(days=1)
    return legacy, stored


@pytest.mark.parametrize("direction", ["up", "down", "neutral", "unknown"])
def test_same_record_has_distinct_entry_direction_and_cost_semantics(direction: str) -> None:
    history, bars = _history([80, 100, 110])
    legacy = compute_outcome(history, AVAILABLE.date(), 1, direction, None)
    study = evaluate_record(
        available_at=AVAILABLE,
        direction=direction,
        bars=bars,
        horizon=1,
        cost_bps=Decimal("10"),
    )
    assert legacy is not None
    assert legacy.start_day == date(2026, 10, 23)
    assert legacy.return_pct == Decimal("-25" if direction == "down" else "25")
    assert legacy.alpha_pct is None
    if direction in {"neutral", "unknown"}:
        assert study.skip_reason == "neutral_or_unknown_direction"
        assert study.net_return_pct is None
    else:
        assert study.entry_date == date(2026, 10, 26)
        assert study.exit_date == date(2026, 10, 27)
        assert study.gross_return_pct == Decimal("-10" if direction == "down" else "10")
        assert study.net_return_pct == Decimal("-10.21" if direction == "down" else "9.79")


def test_twenty_saved_sessions_are_not_the_same_start_or_exit_cohort() -> None:
    history, bars = _history([80, 100, *range(101, 122)])
    legacy = compute_outcome(history, AVAILABLE.date(), 20, "up", None)
    study = evaluate_record(
        available_at=AVAILABLE, direction="up", bars=bars, horizon=20, cost_bps=Decimal("10")
    )
    assert legacy is not None
    assert legacy.start_price == Decimal("80")
    assert legacy.end_price == Decimal("119")
    assert legacy.return_pct == Decimal("48.7500")
    assert study.entry_price == Decimal("100")
    assert study.exit_price == Decimal("120")
    assert study.net_return_pct == Decimal("19.78")
    assert legacy.end_day != study.exit_date


def test_weekend_availability_can_share_an_entry_without_sharing_costs() -> None:
    history, bars = _history([80, 100, 110])
    weekend = datetime(2026, 10, 24, 10, tzinfo=UTC)
    legacy = compute_outcome(history, weekend.date(), 1, "up", None)
    study = evaluate_record(
        available_at=weekend, direction="up", bars=bars, horizon=1, cost_bps=Decimal("10")
    )
    assert legacy is not None
    assert legacy.start_day == study.entry_date == date(2026, 10, 26)
    assert legacy.return_pct == study.gross_return_pct == Decimal("10")
    assert study.net_return_pct == Decimal("9.79")


def test_unavailable_benchmark_remains_unknown() -> None:
    history, _ = _history([80, 100])
    future_benchmark = [DayBar(date(2026, 11, 1), Decimal(101), Decimal(99), Decimal(100))]
    result = compute_outcome(history, AVAILABLE.date(), 1, "up", future_benchmark)
    assert result is not None
    assert result.alpha_pct is None and result.benchmark_return_pct is None


def test_api_contract_identifies_unversioned_history_and_versioned_study() -> None:
    legacy = track_record([], horizon_days=20, signals_total=0, benchmark=None, as_of=None)
    study = BacktestOut(
        as_of=AVAILABLE,
        parameters=BacktestRequest(),
        total_matching=0,
        evaluated=0,
        truncated=False,
        completed=0,
        skipped=0,
        mean_gross_return_pct=None,
        mean_net_return_pct=None,
        positive_share=None,
        rows=[],
    )
    assert legacy.model_dump()["method_id"] == "legacy-unversioned"
    assert study.model_dump()["method_id"] == "saved-record-after-utc-close-v1"
