from datetime import date, timedelta
from typing import Any

from preza.domain.outlook import brief, compute_outlook

AS_OF = date(2026, 10, 23)


def _bars(closes: list[float], *, spread: float = 0.01) -> list[dict[str, Any]]:
    start = AS_OF - timedelta(days=len(closes) - 1)
    return [
        {
            "day": (start + timedelta(days=i)).isoformat(),
            "open": str(c),
            "high": str(round(c * (1 + spread), 4)),
            "low": str(round(c * (1 - spread), 4)),
            "close": str(c),
            "volume": 1000,
        }
        for i, c in enumerate(closes)
    ]


def _snapshot(closes: list[float], **extra: Any) -> dict[str, Any]:
    return {"as_of": AS_OF.isoformat(), "bars": _bars(closes), "bars_source": "yahoo", **extra}


def _horizon(outlook: Any, name: str) -> Any:
    return next(h for h in outlook.horizons if h.horizon == name)


def test_uptrend_supports_short_and_medium() -> None:
    closes = [100 * 1.0015**i for i in range(800)]
    outlook = compute_outlook(_snapshot(closes))
    assert outlook is not None
    assert [h.horizon for h in outlook.horizons] == ["short", "medium", "long"]
    short = {e.key: e.stance for e in _horizon(outlook, "short").evidence}
    # A smooth rise is overbought, so RSI counts against growth.
    assert short == {
        "trend_sma50": "pro",
        "rsi14": "contra",
        "return_1m": "pro",
        "volatility_atr": "neutral",
    }
    assert _horizon(outlook, "short").verdict == "mixed"
    medium = _horizon(outlook, "medium")
    assert medium.verdict == "supports"
    assert {e.key for e in medium.evidence} == {"trend_sma200", "cross_50_200", "momentum_12_1"}
    trend = next(e for e in medium.evidence if e.key == "trend_sma200")
    assert trend.stance == "pro" and trend.source == "yahoo" and trend.as_of == AS_OF
    long = _horizon(outlook, "long")
    assert "valuation" in long.missing and "quality.roe_pct" in long.missing
    assert [e.key for e in long.evidence] == ["return_3y_cagr"]
    assert long.verdict == "insufficient"


def test_downtrend_is_against() -> None:
    closes = [300 * 0.9985**i for i in range(800)]
    outlook = compute_outlook(_snapshot(closes))
    assert outlook is not None
    assert _horizon(outlook, "medium").verdict == "against"
    assert _horizon(outlook, "short").contra >= 2


def test_too_few_bars_is_insufficient() -> None:
    outlook = compute_outlook(_snapshot([100.0 + i for i in range(30)]))
    assert outlook is not None
    medium = _horizon(outlook, "medium")
    assert medium.verdict == "insufficient" and medium.balance is None
    assert {"trend_sma200", "cross_50_200", "momentum_12_1"} <= set(medium.missing)


def test_quality_mix_and_fundamental_provenance() -> None:
    closes = [100 * 1.0005**i for i in range(800)]
    snap = _snapshot(
        closes,
        fundamentals={
            "roe_pct": 32.0,
            "net_margin_pct": 2.0,
            "revenue_growth_pct": -8.0,
            "debt_to_equity": 0.3,
        },
        fundamentals_source="fmp",
        fundamentals_as_of="2026-09-30",
    )
    outlook = compute_outlook(snap)
    assert outlook is not None
    long = {e.key: e for e in _horizon(outlook, "long").evidence}
    assert long["quality.roe_pct"].stance == "pro"
    assert long["quality.net_margin_pct"].stance == "neutral"
    assert long["quality.revenue_growth_pct"].stance == "contra"
    assert long["quality.debt_to_equity"].stance == "pro"
    assert long["quality.debt_to_equity"].unit == "ratio"
    assert long["quality.roe_pct"].source == "fmp"
    assert long["quality.roe_pct"].as_of == date(2026, 9, 30)


def test_valuation_counts_once_in_brief() -> None:
    closes = [100 * 1.0015**i for i in range(800)]
    history = [[(AS_OF - timedelta(days=90 * i)).isoformat(), 30.0 + i % 5] for i in range(12)]
    snap = _snapshot(
        closes,
        fundamentals={"pe": 20.0},
        fundamentals_history={"pe": history},
        fundamentals_as_of=AS_OF.isoformat(),
    )
    outlook = compute_outlook(snap)
    assert outlook is not None
    medium = {e.key: e for e in _horizon(outlook, "medium").evidence}
    assert medium["valuation"].stance == "pro"  # far below its own history
    summary = brief(outlook)
    assert summary is not None
    total_pro = sum(h.pro for h in outlook.horizons)
    assert summary.pro == total_pro - 1


def test_bars_after_as_of_are_ignored() -> None:
    closes = [100 * 1.0015**i for i in range(800)]
    snap = _snapshot(closes)
    later = AS_OF + timedelta(days=1)
    snap["bars"].append(
        {"day": later.isoformat(), "high": "1", "low": "1", "close": "1", "open": "1"}
    )
    outlook = compute_outlook(snap)
    assert outlook is not None
    short = _horizon(outlook, "short")
    assert short.evidence[0].as_of == AS_OF
    assert {e.key: e.stance for e in short.evidence}["trend_sma50"] == "pro"


def test_empty_or_broken_snapshot() -> None:
    assert compute_outlook(None) is None
    assert compute_outlook({}) is None
    assert compute_outlook({"as_of": AS_OF.isoformat(), "bars": []}) is None
    assert compute_outlook({"as_of": "nope", "bars": _bars([1.0, 2.0])}) is None
    assert brief(None) is None
