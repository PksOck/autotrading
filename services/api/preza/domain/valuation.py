# Prirejeno iz: PksOck/autotrading (legacy)/src/domain/valuation.ts (lastna koda)
"""Valuation bands against own history and a two-stage DCF (BL-061).

Pure functions, no I/O. All numbers are computed here, never by an LLM (AGENTS.md §3).
Floats are used for the model internals; outputs are rounded for display.
"""

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import date
from typing import Any

# --- Valuation bands ----------------------------------------------------------------------

MIN_HISTORY_POINTS = 8
HISTORY_YEARS = 5
BAND_METRICS = ("pe", "ev_ebit", "fcf_yield")
# Multiples where a loss makes the value meaningless.
POSITIVE_ONLY = frozenset({"pe", "ev_ebit"})
# Higher value means cheaper (yield); for multiples, lower means cheaper.
HIGHER_IS_CHEAPER = frozenset({"fcf_yield"})


@dataclass(frozen=True)
class ValuationBand:
    metric: str
    current: float
    median: float
    p20: float
    p80: float
    percentile: float  # 0..100, share of history at or below current (ties count half)
    cheap: bool | None
    n: int
    as_of: date


def _quantile(sorted_values: Sequence[float], q: float) -> float:
    """Linear-interpolated quantile of an already sorted, non-empty sequence."""
    if len(sorted_values) == 1:
        return sorted_values[0]
    pos = q * (len(sorted_values) - 1)
    lo = math.floor(pos)
    hi = math.ceil(pos)
    frac = pos - lo
    return sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * frac


def _five_years_ago(as_of: date) -> date:
    try:
        return as_of.replace(year=as_of.year - HISTORY_YEARS)
    except ValueError:  # 29 Feb
        return as_of.replace(year=as_of.year - HISTORY_YEARS, day=28)


def _usable(metric: str, value: float | None) -> bool:
    if value is None or not math.isfinite(value):
        return False
    return not (metric in POSITIVE_ONLY and value <= 0)


def valuation_band(
    metric: str,
    current: float | None,
    history: Sequence[tuple[date, float]],
    as_of: date,
) -> ValuationBand | None:
    if not _usable(metric, current):
        return None
    assert current is not None
    start = _five_years_ago(as_of)
    values = sorted(v for d, v in history if start < d <= as_of and _usable(metric, v))
    if len(values) < MIN_HISTORY_POINTS:
        return None
    median = _quantile(values, 0.5)
    below = sum(1 for v in values if v < current)
    equal = sum(1 for v in values if v == current)
    percentile = 100.0 * (below + 0.5 * equal) / len(values)
    if current == median:
        cheap: bool | None = None
    elif metric in HIGHER_IS_CHEAPER:
        cheap = current > median
    else:
        cheap = current < median
    return ValuationBand(
        metric=metric,
        current=current,
        median=median,
        p20=_quantile(values, 0.2),
        p80=_quantile(values, 0.8),
        percentile=percentile,
        cheap=cheap,
        n=len(values),
        as_of=as_of,
    )


def valuation_bands(
    current: Mapping[str, float | None],
    history: Mapping[str, Sequence[tuple[date, float]]],
    as_of: date,
) -> dict[str, ValuationBand]:
    bands: dict[str, ValuationBand] = {}
    for metric in BAND_METRICS:
        band = valuation_band(metric, current.get(metric), history.get(metric, ()), as_of)
        if band is not None:
            bands[metric] = band
    return bands


def summary_score(bands: Mapping[str, ValuationBand]) -> float | None:
    """Fraction (0..1) of available bands that are cheap; None without any band."""
    if not bands:
        return None
    return sum(1 for b in bands.values() if b.cheap) / len(bands)


# --- DCF ----------------------------------------------------------------------------------


@dataclass(frozen=True)
class ValuationAssumptions:
    normalized_fcf: float
    growth_rate: float
    explicit_years: int
    terminal_growth_rate: float
    discount_rate: float
    net_debt: float
    diluted_shares: float


@dataclass(frozen=True)
class ValuationBreakdown:
    explicit_period_value: float
    terminal_value_present_value: float
    enterprise_value: float
    equity_value: float
    per_share_value: float


@dataclass(frozen=True)
class ValidationResult:
    errors: list[str]
    warnings: list[str]


@dataclass(frozen=True)
class ScenarioPreset:
    id: str
    label: str
    growth_rate: float
    explicit_years: int
    terminal_growth_rate: float
    discount_rate: float


VALUATION_SCENARIOS: tuple[ScenarioPreset, ...] = (
    ScenarioPreset("conservative", "Conservative", 0.04, 5, 0.015, 0.12),
    ScenarioPreset("base", "Base", 0.08, 5, 0.02, 0.10),
    ScenarioPreset("optimistic", "Optimistic", 0.12, 5, 0.025, 0.09),
)


class InvalidAssumptionsError(ValueError):
    pass


def _finite(x: Any) -> bool:
    return isinstance(x, int | float) and math.isfinite(x)


def validate_assumptions(a: ValuationAssumptions) -> ValidationResult:
    errors: list[str] = []
    for name in ("normalized_fcf", "growth_rate", "terminal_growth_rate", "net_debt"):
        if not _finite(getattr(a, name)):
            errors.append(f"{name}: must be a finite number")
    if not _finite(a.discount_rate) or a.discount_rate <= 0:
        errors.append("discount_rate: must be a positive finite number")
    if not _finite(a.diluted_shares) or a.diluted_shares <= 0:
        errors.append("diluted_shares: must be a positive finite number")
    years_ok = isinstance(a.explicit_years, int) and 1 <= a.explicit_years <= 20
    if not years_ok:
        errors.append("explicit_years: must be an integer between 1 and 20")
    if (
        _finite(a.terminal_growth_rate)
        and _finite(a.discount_rate)
        and a.terminal_growth_rate >= a.discount_rate
    ):
        errors.append("terminal_growth_rate: Terminal growth must stay below the discount rate")

    warnings: list[str] = []
    if _finite(a.growth_rate) and a.growth_rate > 0.15:
        warnings.append("Growth above 15% is unusually aggressive for a mature business")
    if _finite(a.discount_rate) and (a.discount_rate < 0.06 or a.discount_rate > 0.2):
        warnings.append("Discount rate outside 6-20% deserves a second look")
    if _finite(a.terminal_growth_rate) and a.terminal_growth_rate > 0.04:
        warnings.append("Terminal growth above 4% exceeds most long-run economic growth")
    if years_ok and a.explicit_years > 10:
        warnings.append("Explicit horizons beyond 10 years carry high forecast uncertainty")
    return ValidationResult(errors, warnings)


def calculate_dcf(a: ValuationAssumptions, *, ndigits: int | None = 4) -> ValuationBreakdown:
    """Two-stage DCF: explicit growth period, then Gordon-growth terminal value."""
    validation = validate_assumptions(a)
    if validation.errors:
        raise InvalidAssumptionsError(
            "Invalid valuation assumptions: " + "; ".join(validation.errors)
        )

    explicit = 0.0
    year_fcf = a.normalized_fcf
    for year in range(1, a.explicit_years + 1):
        year_fcf *= 1 + a.growth_rate
        explicit += year_fcf / (1 + a.discount_rate) ** year

    terminal = year_fcf * (1 + a.terminal_growth_rate) / (a.discount_rate - a.terminal_growth_rate)
    terminal_pv = terminal / (1 + a.discount_rate) ** a.explicit_years
    ev = explicit + terminal_pv
    equity = ev - a.net_debt
    per_share = equity / a.diluted_shares

    def r(x: float) -> float:
        return x if ndigits is None else round(x, ndigits)

    return ValuationBreakdown(r(explicit), r(terminal_pv), r(ev), r(equity), r(per_share))


def dcf_scenarios(
    normalized_fcf: float, net_debt: float, diluted_shares: float
) -> dict[str, ValuationBreakdown]:
    """Conservative / base / optimistic DCF for the same cash flow and balance sheet."""
    base = ValuationAssumptions(
        normalized_fcf=normalized_fcf,
        growth_rate=0.0,
        explicit_years=1,
        terminal_growth_rate=0.0,
        discount_rate=0.1,
        net_debt=net_debt,
        diluted_shares=diluted_shares,
    )
    return {
        s.id: calculate_dcf(
            replace(
                base,
                growth_rate=s.growth_rate,
                explicit_years=s.explicit_years,
                terminal_growth_rate=s.terminal_growth_rate,
                discount_rate=s.discount_rate,
            )
        )
        for s in VALUATION_SCENARIOS
    }
