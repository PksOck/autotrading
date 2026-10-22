from datetime import date, timedelta
from decimal import Decimal

from preza.domain.outcome import DayBar, compute_outcome


def _bars(closes: list[str], start: date = date(2026, 3, 2)) -> list[DayBar]:
    """Mon-Fri bars; high = close + 1, low = close - 1."""
    out: list[DayBar] = []
    day = start
    for c in closes:
        while day.weekday() >= 5:
            day += timedelta(days=1)
        close = Decimal(c)
        out.append(DayBar(day, close + 1, close - 1, close))
        day += timedelta(days=1)
    return out


def test_up_return_mfe_mae() -> None:
    bars = _bars(["100", "110", "90", "120"])
    o = compute_outcome(bars, date(2026, 3, 2), 3, "up", None)
    assert o is not None
    assert o.return_pct == Decimal("20.0000")
    assert o.mfe_pct == Decimal("21.0000")  # high 121
    assert o.mae_pct == Decimal("-11.0000")  # low 89
    assert o.benchmark_return_pct is None and o.alpha_pct is None


def test_down_inverts() -> None:
    bars = _bars(["100", "110", "90", "80"])
    o = compute_outcome(bars, date(2026, 3, 2), 3, "down", None)
    assert o is not None
    assert o.return_pct == Decimal("20.0000")
    assert o.mfe_pct == Decimal("21.0000")  # low 79
    assert o.mae_pct == Decimal("-11.0000")  # high 111


def test_neutral_as_up() -> None:
    bars = _bars(["100", "110"])
    o = compute_outcome(bars, date(2026, 3, 2), 1, "neutral", None)
    assert o is not None and o.return_pct == Decimal("10.0000")


def test_horizon_not_reached() -> None:
    assert compute_outcome(_bars(["100", "101"]), date(2026, 3, 2), 5, "up", None) is None


def test_signal_after_last_bar() -> None:
    assert compute_outcome(_bars(["100", "101"]), date(2026, 4, 1), 1, "up", None) is None


def test_weekend_signal_starts_next_trading_day() -> None:
    bars = _bars(["100", "102", "104"], start=date(2026, 3, 6))  # Fri, Mon, Tue
    o = compute_outcome(bars, date(2026, 3, 7), 1, "up", None)  # Saturday
    assert o is not None
    assert o.start_day == date(2026, 3, 9)
    assert o.start_price == Decimal(102)
    assert o.end_day == date(2026, 3, 10)


def test_benchmark_alpha() -> None:
    bars = _bars(["100", "110"])
    bench = _bars(["400", "408"])
    o = compute_outcome(bars, date(2026, 3, 2), 1, "up", bench)
    assert o is not None
    assert o.benchmark_return_pct == Decimal("2.0000")
    assert o.alpha_pct == Decimal("8.0000")
    d = compute_outcome(bars, date(2026, 3, 2), 1, "down", bench)
    assert d is not None
    assert d.return_pct == Decimal("-10.0000")
    assert d.benchmark_return_pct == Decimal("-2.0000")
    assert d.alpha_pct == Decimal("-8.0000")


def test_benchmark_missing_data() -> None:
    bars = _bars(["100", "110"])
    late = _bars(["400", "408"], start=date(2026, 3, 20))
    o = compute_outcome(bars, date(2026, 3, 2), 1, "up", late)
    assert o is not None and o.alpha_pct is None
