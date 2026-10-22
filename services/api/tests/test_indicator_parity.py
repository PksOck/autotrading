"""TA-Lib (backend) and trading-signals (web) must agree (BL-060).

Fixture: `pnpm --dir apps/web gen:indicator-fixture`.
"""

import json
import math
from pathlib import Path

import pytest

from preza.entries.indicators import compute

# ATR seeds differently (trading-signals counts the first bar's high-low, TA-Lib starts one bar
# later); Wilder smoothing makes the difference vanish, so ATR is compared after warm-up.
WARMUP = {"atr14": 100}
FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "indicator_parity.json").read_text())


@pytest.mark.parametrize("name", ["sma50", "sma200", "rsi14", "atr14"])
def test_matches_trading_signals(name: str) -> None:
    bars = FIXTURE["bars"]
    series = compute(
        [b["high"] for b in bars], [b["low"] for b in bars], [b["close"] for b in bars]
    )
    ours = getattr(series, name)
    theirs = FIXTURE[name]
    compared = 0
    for i, expected in enumerate(theirs):
        got = float(ours[i])
        if expected is None or math.isnan(got) or i < WARMUP.get(name, 0):
            continue
        assert got == pytest.approx(expected, rel=1e-4), f"{name}[{i}]"
        compared += 1
    assert compared >= 100
