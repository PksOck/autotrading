import pytest

from preza.analytics.indicators import price_stats, rsi, sma


def test_sma_and_warmup() -> None:
    assert sma([1, 2, 3], 5) is None
    assert sma([1, 2, 3, 4], 2) == 3.5


def test_rsi_extremes() -> None:
    assert rsi(list(range(1, 30))) == 100.0
    assert rsi([10.0] * 5) is None
    falling = rsi([float(30 - i) for i in range(30)])
    assert falling is not None and falling < 1


def test_price_stats_drawdown() -> None:
    closes = [100.0 + i for i in range(200)] + [250.0]
    stats = price_stats(closes)
    assert stats is not None
    assert stats.high_52w == 299.0
    assert stats.drawdown_pct == pytest.approx((250 / 299 - 1) * 100)
    assert stats.distance_sma200_pct is not None
