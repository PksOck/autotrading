"""Backend indicators (pure Python). Same definitions as apps/web/lib/indicators.ts; TA-Lib
replaces this module in M3 together with the parity test (BL-060)."""

from collections.abc import Sequence
from dataclasses import dataclass
from itertools import pairwise


def sma(values: Sequence[float], period: int) -> float | None:
    return sum(values[-period:]) / period if len(values) >= period else None


def rsi(closes: Sequence[float], period: int = 14) -> float | None:
    """Wilder's RSI."""
    if len(closes) <= period:
        return None
    gains = [max(b - a, 0.0) for a, b in pairwise(closes)]
    losses = [max(a - b, 0.0) for a, b in pairwise(closes)]
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for g, loss in zip(gains[period:], losses[period:], strict=True):
        avg_gain = (avg_gain * (period - 1) + g) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period
    if avg_loss == 0:
        return 100.0
    return 100 - 100 / (1 + avg_gain / avg_loss)


@dataclass(frozen=True)
class PriceStats:
    last: float
    change_1d_pct: float | None
    change_1m_pct: float | None
    high_52w: float
    low_52w: float
    drawdown_pct: float
    sma50: float | None
    sma200: float | None
    distance_sma200_pct: float | None
    rsi14: float | None


def price_stats(closes: Sequence[float]) -> PriceStats | None:
    if len(closes) < 2:
        return None
    last = closes[-1]
    year = closes[-252:]
    s200 = sma(closes, 200)
    return PriceStats(
        last=last,
        change_1d_pct=(last / closes[-2] - 1) * 100,
        change_1m_pct=(last / closes[-22] - 1) * 100 if len(closes) >= 22 else None,
        high_52w=max(year),
        low_52w=min(year),
        drawdown_pct=(last / max(year) - 1) * 100,
        sma50=sma(closes, 50),
        sma200=s200,
        distance_sma200_pct=(last / s200 - 1) * 100 if s200 else None,
        rsi14=rsi(closes),
    )
