"""Weight calibration (BL-103): propose per-group strength weights from outcomes.

Pure and deterministic. A group's weight multiplies the strength of its new signals.
A change is only proposed when the group's 95 % Wilson interval for the hit rate
excludes the system baseline; the proposed weight is the shrunk hit rate over the
baseline, clamped to [WEIGHT_MIN, WEIGHT_MAX]. Nothing changes until the user confirms
(ADR-0006, ADR-0015).
"""

import math
from collections.abc import Iterable, Mapping
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

from pydantic import BaseModel, Field

from preza.domain.track_record import MIN_SAMPLE, OutcomeRow

# Opportunity groups that may be tuned. Risk warnings (exit_warning, thesis_break) and
# your own proposals are never down-weighted: missing them costs more than noise.
TUNABLE: tuple[tuple[str, str], ...] = (("catalyst", "radar"), ("entry", "rule"))
WEIGHT_MIN = Decimal("0.50")
WEIGHT_MAX = Decimal("1.50")
DEFAULT_WEIGHT = Decimal("1.00")
Z95 = 1.959964

Reason = Literal["low_sample", "not_significant", "better", "worse", "no_baseline"]


def group_key(kind: str, source: str) -> str:
    return f"{kind}:{source}"


class Interval(BaseModel):
    low: Decimal
    high: Decimal


class GroupProposal(BaseModel):
    kind: str
    source: str
    count: int
    hits: int
    hit_rate: Decimal | None
    interval: Interval | None = Field(description="95 % Wilson interval for the hit rate.")
    current_weight: Decimal
    proposed_weight: Decimal
    reason: Reason


class CalibrationProposal(BaseModel):
    horizon_days: int
    min_sample: int = MIN_SAMPLE
    baseline_hit_rate: Decimal | None = Field(
        description="Hit rate of all system signals at this horizon."
    )
    baseline_count: int
    groups: list[GroupProposal]
    changed: bool


def _q(value: float, places: str = "0.0001") -> Decimal:
    return Decimal(str(value)).quantize(Decimal(places), ROUND_HALF_UP)


def wilson(hits: int, n: int, z: float = Z95) -> tuple[float, float]:
    if n == 0:
        return 0.0, 1.0
    p = hits / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def _proposed(hits: int, n: int, base: float) -> Decimal:
    # Shrink toward the baseline with MIN_SAMPLE pseudo-outcomes, then take the ratio.
    shrunk = (hits + MIN_SAMPLE * base) / (n + MIN_SAMPLE)
    ratio = _q(shrunk / base, "0.01")
    return min(max(ratio, WEIGHT_MIN), WEIGHT_MAX)


def propose(
    rows: Iterable[OutcomeRow], *, horizon_days: int, current: Mapping[str, Decimal]
) -> CalibrationProposal:
    system = [r for r in rows if r.origin == "system"]
    base_hits = sum(1 for r in system if r.return_pct > 0)
    base = base_hits / len(system) if system else None
    groups: list[GroupProposal] = []
    for kind, source in TUNABLE:
        sample = [r for r in system if r.kind == kind and r.source == source]
        n, hits = len(sample), sum(1 for r in sample if r.return_pct > 0)
        now = current.get(group_key(kind, source), DEFAULT_WEIGHT)
        low, high = wilson(hits, n)
        reason: Reason
        if n < MIN_SAMPLE:
            reason, weight = "low_sample", now
        elif not base:
            reason, weight = "no_baseline", now
        elif low <= base <= high:
            reason, weight = "not_significant", now
        else:
            weight = _proposed(hits, n, base)
            reason = "better" if hits / n > base else "worse"
        groups.append(
            GroupProposal(
                kind=kind,
                source=source,
                count=n,
                hits=hits,
                hit_rate=_q(hits / n) if n else None,
                interval=Interval(low=_q(low), high=_q(high)) if n else None,
                current_weight=now,
                proposed_weight=weight,
                reason=reason,
            )
        )
    return CalibrationProposal(
        horizon_days=horizon_days,
        baseline_hit_rate=_q(base) if base is not None else None,
        baseline_count=len(system),
        groups=groups,
        changed=any(g.proposed_weight != g.current_weight for g in groups),
    )


def weighted_strength(raw: Decimal | float, weight: Decimal) -> Decimal:
    """Strength after the group weight, kept within 0..1."""
    value = Decimal(str(raw)) * weight
    return min(max(value, Decimal(0)), Decimal(1)).quantize(Decimal("0.0001"), ROUND_HALF_UP)
