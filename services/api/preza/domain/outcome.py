"""Signal outcome maths (BL-065): what happened N trading days after a signal.

Pure functions, no I/O. All money maths in Decimal, percentages quantized to 4 places.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from pydantic import BaseModel

HORIZONS: tuple[int, ...] = (1, 5, 20, 60)

_Q = Decimal("0.0001")
_HUNDRED = Decimal(100)
_ZERO = Decimal(0)


@dataclass(frozen=True)
class DayBar:
    day: date
    high: Decimal
    low: Decimal
    close: Decimal


@dataclass(frozen=True)
class Outcome:
    horizon_days: int
    start_day: date
    end_day: date
    start_price: Decimal
    end_price: Decimal
    return_pct: Decimal
    benchmark_return_pct: Decimal | None
    alpha_pct: Decimal | None
    mfe_pct: Decimal
    mae_pct: Decimal


class OutcomeStat(BaseModel):
    kind: str
    source: str
    horizon_days: int
    count: int
    hit_rate: Decimal
    avg_return_pct: Decimal
    avg_alpha_pct: Decimal | None


def _q(value: Decimal) -> Decimal:
    return value.quantize(_Q)


def _close_on_or_before(bars: Sequence[DayBar], day: date) -> Decimal | None:
    found: Decimal | None = None
    for bar in bars:
        if bar.day <= day:
            found = bar.close
        else:
            break
    return found


def compute_outcome(
    bars: Sequence[DayBar],
    signal_day: date,
    horizon: int,
    direction: str,
    benchmark: Sequence[DayBar] | None,
) -> Outcome | None:
    """Return of a signal `horizon` trading bars after its start bar, or None if not yet known."""
    ordered = sorted(bars, key=lambda b: b.day)
    start_idx = next((i for i, b in enumerate(ordered) if b.day >= signal_day), None)
    if start_idx is None:
        return None
    end_idx = start_idx + horizon
    if horizon < 1 or end_idx >= len(ordered):
        return None

    start, end = ordered[start_idx], ordered[end_idx]
    if start.close <= 0:
        return None
    sign = Decimal(-1) if direction == "down" else Decimal(1)
    window = ordered[start_idx + 1 : end_idx + 1]

    raw_return = (end.close / start.close - 1) * _HUNDRED
    ret = sign * raw_return

    max_high = max(b.high for b in window)
    min_low = min(b.low for b in window)
    up_excursion = (max_high / start.close - 1) * _HUNDRED
    down_excursion = (min_low / start.close - 1) * _HUNDRED
    if sign > 0:
        mfe, mae = max(_ZERO, up_excursion), min(_ZERO, down_excursion)
    else:
        mfe, mae = max(_ZERO, -down_excursion), min(_ZERO, -up_excursion)

    bench_ret: Decimal | None = None
    alpha: Decimal | None = None
    if benchmark:
        bench = sorted(benchmark, key=lambda b: b.day)
        b_start = _close_on_or_before(bench, start.day)
        b_end = _close_on_or_before(bench, end.day)
        if b_start is not None and b_end is not None and b_start > 0:
            bench_ret = sign * (b_end / b_start - 1) * _HUNDRED
            alpha = _q(ret) - _q(bench_ret)

    return Outcome(
        horizon_days=horizon,
        start_day=start.day,
        end_day=end.day,
        start_price=start.close,
        end_price=end.close,
        return_pct=_q(ret),
        benchmark_return_pct=None if bench_ret is None else _q(bench_ret),
        alpha_pct=None if alpha is None else _q(alpha),
        mfe_pct=_q(mfe),
        mae_pct=_q(mae),
    )
