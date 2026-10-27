"""Outlook by horizon from a stored analysis snapshot (ADR-0014, BL-165). Pure, no I/O.

Every piece of evidence is one indicator with a fixed threshold, so the same snapshot
always gives the same outlook. The agents do not take part; the web app turns the keys
into text. The thresholds are a simplification, not a forecast.
"""

from collections.abc import Callable, Mapping, Sequence
from datetime import date
from typing import Any, Literal

from pydantic import BaseModel

from preza.domain.quality import quality_parts
from preza.domain.valuation import HIGHER_IS_CHEAPER, valuation_bands
from preza.entries.indicators import compute, last

Horizon = Literal["short", "medium", "long"]
Stance = Literal["pro", "contra", "neutral"]
Verdict = Literal["supports", "mixed", "against", "insufficient"]
Unit = Literal["pct", "index", "ratio"]

HORIZONS: tuple[Horizon, ...] = ("short", "medium", "long")
MONTH_BARS = 21
YEAR_BARS = 252
THREE_YEAR_BARS = 756
RSI_OVERSOLD = 30.0
RSI_OVERBOUGHT = 70.0
RETURN_1M_PCT = 3.0
ATR_CALM_PCT = 1.5
ATR_WILD_PCT = 3.5
MOMENTUM_PCT = 5.0
VALUATION_EDGE = 0.3
CAGR_GOOD_PCT = 7.0
QUALITY_PRO = 0.5
VERDICT_EDGE = 0.34
MIN_EVIDENCE = 2
QUALITY_KEYS = ("roe_pct", "net_margin_pct", "revenue_growth_pct", "debt_to_equity")


class Evidence(BaseModel):
    key: str
    horizon: Horizon
    stance: Stance
    value: float | None
    reference: float | None
    unit: Unit
    source: str | None
    as_of: date | None


class HorizonOutlook(BaseModel):
    horizon: Horizon
    verdict: Verdict
    pro: int
    contra: int
    neutral: int
    balance: float | None
    evidence: list[Evidence]
    missing: list[str]


class Outlook(BaseModel):
    as_of: date
    horizons: list[HorizonOutlook]


class OutlookBrief(BaseModel):
    short: Verdict
    medium: Verdict
    long: Verdict
    pro: int
    contra: int


def _date(value: Any) -> date | None:
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value:
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None
    return None


def _num(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _band(value: float, low: float, high: float, *, higher_is_pro: bool = True) -> Stance:
    """pro above `high`, contra below `low` (reversed when lower is better)."""
    if value > high:
        return "pro" if higher_is_pro else "contra"
    if value < low:
        return "contra" if higher_is_pro else "pro"
    return "neutral"


def _pct(a: float, b: float) -> float:
    return (a / b - 1) * 100


def _valuation(snapshot: Mapping[str, Any], as_of: date) -> float | None:
    """Mean position against own 5-year history: +1 cheapest, -1 most expensive."""
    fundamentals = snapshot.get("fundamentals")
    if not isinstance(fundamentals, Mapping):
        return None
    current = {k: _num(v) for k, v in fundamentals.items()}
    history: dict[str, list[tuple[date, float]]] = {}
    for metric, points in (snapshot.get("fundamentals_history") or {}).items():
        rows = []
        for point in points or []:
            if isinstance(point, Sequence) and len(point) == 2:
                day, value = _date(point[0]), _num(point[1])
                if day is not None and value is not None:
                    rows.append((day, value))
        history[metric] = rows
    bands = valuation_bands(current, history, _date(snapshot.get("fundamentals_as_of")) or as_of)
    if not bands:
        return None
    scores = []
    for metric, band in bands.items():
        position = (band.percentile - 50.0) / 50.0
        scores.append(position if metric in HIGHER_IS_CHEAPER else -position)
    return max(-1.0, min(1.0, sum(scores) / len(scores)))


def _quality_stance(part: float | None) -> Stance:
    if part is None:
        return "neutral"
    if part >= QUALITY_PRO:
        return "pro"
    return "contra" if part < 0 else "neutral"


def _fixed(stance: Stance) -> Callable[[float], Stance]:
    return lambda _value: stance


def _verdict(evidence: Sequence[Evidence]) -> tuple[Verdict, float | None]:
    if len(evidence) < MIN_EVIDENCE:
        return "insufficient", None
    pro = sum(1 for e in evidence if e.stance == "pro")
    contra = sum(1 for e in evidence if e.stance == "contra")
    balance = round((pro - contra) / len(evidence), 3)
    if balance >= VERDICT_EDGE:
        return "supports", balance
    if balance <= -VERDICT_EDGE:
        return "against", balance
    return "mixed", balance


def compute_outlook(snapshot: Mapping[str, Any] | None) -> Outlook | None:
    if not snapshot:
        return None
    as_of = _date(snapshot.get("as_of"))
    if as_of is None:
        return None
    bars: list[tuple[date, float, float, float]] = []
    for bar in snapshot.get("bars") or []:
        day = _date(bar.get("day"))
        high, low, last_close = _num(bar.get("high")), _num(bar.get("low")), _num(bar.get("close"))
        if day is not None and day <= as_of and high is not None and low is not None:
            if last_close is not None:
                bars.append((day, high, low, last_close))
    if not bars:
        return None
    bars.sort(key=lambda b: b[0])
    closes = [b[3] for b in bars]
    series = compute([b[1] for b in bars], [b[2] for b in bars], closes)
    close = closes[-1]
    price_source = snapshot.get("bars_source")
    price_day = bars[-1][0]
    fund_source = snapshot.get("fundamentals_source")
    fund_day = _date(snapshot.get("fundamentals_as_of"))

    found: dict[Horizon, list[Evidence]] = {h: [] for h in HORIZONS}
    missing: dict[Horizon, list[str]] = {h: [] for h in HORIZONS}

    def add(
        horizon: Horizon,
        key: str,
        value: float | None,
        stance: Callable[[float], Stance],
        reference: float | None,
        unit: Unit = "pct",
        fundamental: bool = False,
    ) -> None:
        if value is None or close <= 0:
            missing[horizon].append(key)
            return
        found[horizon].append(
            Evidence(
                key=key,
                horizon=horizon,
                stance=stance(value),
                value=round(value, 2),
                reference=reference,
                unit=unit,
                source=fund_source if fundamental else price_source,
                as_of=fund_day if fundamental else price_day,
            )
        )

    sma50, sma200 = last(series.sma50), last(series.sma200)
    rsi, atr = last(series.rsi14), last(series.atr14)

    def back(n: int) -> float | None:
        return closes[-1 - n] if len(closes) > n and closes[-1 - n] > 0 else None

    month_ago, year_ago, three_years_ago = back(MONTH_BARS), back(YEAR_BARS), back(THREE_YEAR_BARS)

    # Short: up to three months.
    add("short", "trend_sma50", sma50 and _pct(close, sma50), lambda v: _band(v, 0, 0), 0.0)
    add(
        "short",
        "rsi14",
        rsi,
        lambda v: _band(v, RSI_OVERSOLD, RSI_OVERBOUGHT, higher_is_pro=False),
        None,
        "index",
    )
    add(
        "short",
        "return_1m",
        month_ago and _pct(close, month_ago),
        lambda v: _band(v, -RETURN_1M_PCT, RETURN_1M_PCT),
        RETURN_1M_PCT,
    )
    add(
        "short",
        "volatility_atr",
        atr and atr / close * 100,
        lambda v: _band(v, ATR_CALM_PCT, ATR_WILD_PCT, higher_is_pro=False),
        ATR_WILD_PCT,
    )

    # Medium: about one year.
    add("medium", "trend_sma200", sma200 and _pct(close, sma200), lambda v: _band(v, 0, 0), 0.0)
    add(
        "medium",
        "cross_50_200",
        sma50 and sma200 and _pct(sma50, sma200),
        lambda v: _band(v, 0, 0),
        0.0,
    )
    add(
        "medium",
        "momentum_12_1",
        year_ago and month_ago and _pct(month_ago, year_ago),
        lambda v: _band(v, -MOMENTUM_PCT, MOMENTUM_PCT),
        MOMENTUM_PCT,
    )
    valuation = _valuation(snapshot, as_of)
    valuation_horizons: tuple[Horizon, ...] = ("medium", "long")
    for horizon in valuation_horizons:
        add(
            horizon,
            "valuation",
            valuation,
            lambda v: _band(v, -VALUATION_EDGE, VALUATION_EDGE),
            VALUATION_EDGE,
            "index",
            fundamental=True,
        )

    # Long: three years and more.
    fundamentals = snapshot.get("fundamentals")
    parts = quality_parts(
        fundamentals if isinstance(fundamentals, Mapping) else {},
        snapshot.get("sector") if isinstance(snapshot.get("sector"), str) else None,
    )
    for metric in QUALITY_KEYS:
        raw = _num(fundamentals.get(metric)) if isinstance(fundamentals, Mapping) else None
        part = parts.get(metric)
        add(
            "long",
            f"quality.{metric}",
            raw if part is not None else None,
            _fixed(_quality_stance(part)),
            None,
            "ratio" if metric == "debt_to_equity" else "pct",
            fundamental=True,
        )
    cagr = three_years_ago and ((close / three_years_ago) ** (1 / 3) - 1) * 100
    add("long", "return_3y_cagr", cagr, lambda v: _band(v, 0, CAGR_GOOD_PCT), CAGR_GOOD_PCT)

    horizons = []
    for horizon in HORIZONS:
        evidence = found[horizon]
        verdict, balance = _verdict(evidence)
        horizons.append(
            HorizonOutlook(
                horizon=horizon,
                verdict=verdict,
                pro=sum(1 for e in evidence if e.stance == "pro"),
                contra=sum(1 for e in evidence if e.stance == "contra"),
                neutral=sum(1 for e in evidence if e.stance == "neutral"),
                balance=balance,
                evidence=evidence,
                missing=missing[horizon],
            )
        )
    return Outlook(as_of=as_of, horizons=horizons)


def brief(outlook: Outlook | None) -> OutlookBrief | None:
    if outlook is None:
        return None
    by = {h.horizon: h for h in outlook.horizons}
    # Valuation appears in two horizons; count each indicator once.
    stances = {e.key: e.stance for h in outlook.horizons for e in h.evidence}
    return OutlookBrief(
        short=by["short"].verdict,
        medium=by["medium"].verdict,
        long=by["long"].verdict,
        pro=sum(1 for s in stances.values() if s == "pro"),
        contra=sum(1 for s in stances.values() if s == "contra"),
    )
