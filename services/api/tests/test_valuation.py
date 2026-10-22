from dataclasses import replace
from datetime import date, timedelta

import pytest

from preza.domain.valuation import (
    VALUATION_SCENARIOS,
    InvalidAssumptionsError,
    ValuationAssumptions,
    calculate_dcf,
    dcf_scenarios,
    summary_score,
    validate_assumptions,
    valuation_bands,
)
from preza.services.fundamentals import bands_json

AS_OF = date(2026, 10, 1)


def quarterly(values: list[float]) -> list[tuple[date, float]]:
    return [(AS_OF - timedelta(days=90 * (i + 1)), v) for i, v in enumerate(values)]


HIST = quarterly([10, 12, 14, 16, 18, 20, 22, 24, 26, 28])  # median 19


def test_pe_below_median_is_cheap_with_percentile() -> None:
    bands = valuation_bands({"pe": 15.0}, {"pe": HIST}, AS_OF)
    b = bands["pe"]
    assert b.cheap is True and b.n == 10 and b.median == 19.0
    assert b.percentile == pytest.approx(30.0)  # 10,12,14 below 15
    assert b.p20 < b.median < b.p80


def test_fcf_yield_above_median_is_cheap() -> None:
    hist = quarterly([2, 3, 4, 5, 6, 7, 8, 9])
    assert valuation_bands({"fcf_yield": 8.0}, {"fcf_yield": hist}, AS_OF)["fcf_yield"].cheap
    assert (
        valuation_bands({"fcf_yield": 3.0}, {"fcf_yield": hist}, AS_OF)["fcf_yield"].cheap is False
    )


def test_losses_are_ignored() -> None:
    assert valuation_bands({"pe": -5.0}, {"pe": HIST}, AS_OF) == {}
    assert valuation_bands({"pe": None}, {"pe": HIST}, AS_OF) == {}
    # negative history points are dropped, leaving 7 usable -> no band
    hist = quarterly([10, 12, 14, 16, 18, 20, 22, -4, -8])
    assert valuation_bands({"pe": 15.0}, {"pe": hist}, AS_OF) == {}
    # but negative FCF yields are legitimate data
    fy = quarterly([-2, -1, 0, 1, 2, 3, 4, 5])
    assert "fcf_yield" in valuation_bands({"fcf_yield": 1.0}, {"fcf_yield": fy}, AS_OF)


def test_too_few_points_and_old_points_excluded() -> None:
    assert valuation_bands({"pe": 15.0}, {"pe": HIST[:7]}, AS_OF) == {}
    old = [(AS_OF - timedelta(days=365 * 6 + i), 20.0) for i in range(10)]
    assert valuation_bands({"pe": 15.0}, {"pe": old}, AS_OF) == {}


def test_summary_score() -> None:
    hist = quarterly([10, 12, 14, 16, 18, 20, 22, 24])
    bands = valuation_bands(
        {"pe": 12.0, "ev_ebit": 30.0, "fcf_yield": 1.0},
        {"pe": hist, "ev_ebit": hist, "fcf_yield": hist},
        AS_OF,
    )
    assert summary_score(bands) == pytest.approx(1 / 3)
    assert summary_score({}) is None
    assert bands_json(bands)["summary"] == pytest.approx(1 / 3)
    assert bands_json(bands)["pe"]["as_of"] == "2026-10-01"


# --- DCF parity with the legacy TypeScript tests ------------------------------------------

BASE = ValuationAssumptions(100, 0.1, 3, 0.02, 0.1, 50, 10)


def test_dcf_hand_verified() -> None:
    b = calculate_dcf(BASE)
    assert b.explicit_period_value == pytest.approx(300, abs=1e-8)
    assert b.terminal_value_present_value == pytest.approx(1275, abs=1e-8)
    assert b.enterprise_value == pytest.approx(1575, abs=1e-8)
    assert b.equity_value == pytest.approx(1525, abs=1e-8)
    assert b.per_share_value == pytest.approx(152.5, abs=1e-8)


def test_valid_has_no_messages() -> None:
    r = validate_assumptions(BASE)
    assert r.errors == [] and r.warnings == []


@pytest.mark.parametrize(
    "change",
    [
        {"terminal_growth_rate": 0.1},
        {"terminal_growth_rate": 0.12},
        {"discount_rate": 0.0},
        {"discount_rate": -0.05},
        {"diluted_shares": 0},
        {"diluted_shares": -3},
        {"explicit_years": 0},
        {"explicit_years": 21},
        {"normalized_fcf": float("nan")},
        {"growth_rate": float("inf")},
        {"net_debt": float("nan")},
    ],
)
def test_validation_errors(change: dict[str, float]) -> None:
    assert validate_assumptions(replace(BASE, **change)).errors  # type: ignore[arg-type]
    with pytest.raises(InvalidAssumptionsError):
        calculate_dcf(replace(BASE, **change))  # type: ignore[arg-type]


def test_non_integer_years_rejected() -> None:
    assert validate_assumptions(replace(BASE, explicit_years=2.5)).errors  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "change",
    [
        {"growth_rate": 0.2},
        {"discount_rate": 0.03},
        {"discount_rate": 0.25},
        {"terminal_growth_rate": 0.05},
        {"explicit_years": 15},
    ],
)
def test_warnings(change: dict[str, float]) -> None:
    assert validate_assumptions(replace(BASE, **change)).warnings  # type: ignore[arg-type]


def test_scenarios_ordered_and_valid() -> None:
    assert [s.id for s in VALUATION_SCENARIOS] == ["conservative", "base", "optimistic"]
    res = dcf_scenarios(100, 0, 10)
    assert list(res) == ["conservative", "base", "optimistic"]
    assert (
        res["conservative"].per_share_value
        < res["base"].per_share_value
        < res["optimistic"].per_share_value
    )
