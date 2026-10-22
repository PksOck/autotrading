"""Daily indicator series with TA-Lib (BL-060). Same definitions as trading-signals in the web
app; `tests/test_indicator_parity.py` checks both against a shared fixture."""

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import talib


@dataclass(frozen=True)
class Series:
    close: np.ndarray
    high: np.ndarray
    low: np.ndarray
    sma50: np.ndarray
    sma200: np.ndarray
    rsi14: np.ndarray
    atr14: np.ndarray


def compute(high: Sequence[float], low: Sequence[float], close: Sequence[float]) -> Series:
    h = np.asarray(high, dtype=np.float64)
    lo = np.asarray(low, dtype=np.float64)
    c = np.asarray(close, dtype=np.float64)
    return Series(
        close=c,
        high=h,
        low=lo,
        sma50=talib.SMA(c, timeperiod=50),
        sma200=talib.SMA(c, timeperiod=200),
        rsi14=talib.RSI(c, timeperiod=14),
        atr14=talib.ATR(h, lo, c, timeperiod=14),
    )


def last(values: np.ndarray, back: int = 0) -> float | None:
    """Value `back` bars before the latest, or None while the indicator is not stable."""
    if len(values) <= back:
        return None
    v = float(values[-1 - back])
    return None if np.isnan(v) else v
