"""Business quality score from reported ratios (BL-088). Pure, no I/O.

Each ratio maps to -1..1 by fixed steps; the score is their mean. It is a coarse
check for the control score next to the agents' rating, not a ranking. Banks and
insurers carry debt by design, so debt is only scored for other companies.
"""

from collections.abc import Mapping

MIN_RATIOS = 2

# (metric, [(threshold, score), ...] checked from the top, score below all thresholds)
STEPS: dict[str, tuple[list[tuple[float, float]], float]] = {
    "roe_pct": ([(20, 1.0), (10, 0.5), (0, 0.0)], -1.0),
    "net_margin_pct": ([(15, 1.0), (5, 0.5), (0, 0.0)], -1.0),
    "revenue_growth_pct": ([(10, 1.0), (3, 0.5), (-3, 0.0)], -1.0),
}
DEBT_STEPS = [(0.5, 1.0), (1.0, 0.5), (2.0, 0.0)]  # lower is better
FINANCIAL_SECTORS = frozenset({"financials", "financial services", "banks", "insurance"})


def _step(value: float, steps: list[tuple[float, float]], below: float) -> float:
    for threshold, score in steps:
        if value >= threshold:
            return score
    return below


def quality_parts(metrics: Mapping[str, object], sector: str | None = None) -> dict[str, float]:
    parts: dict[str, float] = {}
    for metric, (steps, below) in STEPS.items():
        value = metrics.get(metric)
        if isinstance(value, int | float):
            parts[metric] = _step(float(value), steps, below)
    debt = metrics.get("debt_to_equity")
    if isinstance(debt, int | float) and (sector or "").lower() not in FINANCIAL_SECTORS:
        if debt < 0:
            parts["debt_to_equity"] = -1.0  # negative equity
        else:
            parts["debt_to_equity"] = next(
                (score for limit, score in DEBT_STEPS if debt <= limit), -1.0
            )
    return parts


def quality_score(metrics: Mapping[str, object], sector: str | None = None) -> float | None:
    parts = quality_parts(metrics, sector)
    if len(parts) < MIN_RATIOS:
        return None
    return sum(parts.values()) / len(parts)
