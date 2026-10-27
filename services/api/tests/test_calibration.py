from decimal import Decimal

from preza.domain.calibration import (
    WEIGHT_MAX,
    WEIGHT_MIN,
    propose,
    weighted_strength,
    wilson,
)
from preza.domain.track_record import OutcomeRow


def _rows(kind: str, source: str, hits: int, misses: int, origin: str = "system") -> list:
    return [
        OutcomeRow(
            kind=kind,
            source=source,
            origin=origin,  # type: ignore[arg-type]
            strength=Decimal("0.5"),
            return_pct=Decimal(1 if i < hits else -1),
            alpha_pct=None,
        )
        for i in range(hits + misses)
    ]


def _groups(proposal) -> dict:  # type: ignore[no-untyped-def]
    return {f"{g.kind}:{g.source}": g for g in proposal.groups}


def test_wilson_interval() -> None:
    low, high = wilson(8, 10)
    assert round(low, 3) == 0.490 and round(high, 3) == 0.943
    assert wilson(0, 0) == (0.0, 1.0)


def test_small_or_insignificant_groups_keep_their_weight() -> None:
    rows = _rows("catalyst", "radar", 3, 2) + _rows("entry", "rule", 6, 6)
    out = propose(rows, horizon_days=20, current={"entry:rule": Decimal("1.10")})
    groups = _groups(out)
    assert groups["catalyst:radar"].reason == "low_sample"
    assert groups["entry:rule"].reason == "not_significant"
    assert groups["entry:rule"].proposed_weight == Decimal("1.10")
    assert not out.changed


def test_significant_groups_move_with_shrinkage_and_clamp() -> None:
    # Baseline over all system signals; risk warnings count there but are never tuned.
    rows = (
        _rows("catalyst", "radar", 4, 26)
        + _rows("entry", "rule", 28, 2)
        + _rows("exit_warning", "rule", 15, 15)
    )
    out = propose(rows, horizon_days=20, current={})
    assert out.baseline_hit_rate == Decimal("0.5222") and out.baseline_count == 90
    groups = _groups(out)
    assert set(groups) == {"catalyst:radar", "entry:rule"}
    radar, entry = groups["catalyst:radar"], groups["entry:rule"]
    assert radar.reason == "worse" and entry.reason == "better"
    # (4 + 10·0.5222) / 40 / 0.5222 = 0.44 → clamped to the floor
    assert radar.proposed_weight == WEIGHT_MIN
    # (28 + 10·0.5222) / 40 / 0.5222 = 1.59 → clamped to the ceiling
    assert entry.proposed_weight == WEIGHT_MAX
    assert entry.interval is not None and entry.interval.low > out.baseline_hit_rate
    assert out.changed


def test_user_proposals_do_not_set_the_baseline() -> None:
    rows = _rows("entry", "rule", 20, 10) + _rows("entry", "manual", 0, 50, origin="user")
    out = propose(rows, horizon_days=5, current={})
    assert out.baseline_count == 30 and _groups(out)["entry:rule"].reason == "not_significant"


def test_weighted_strength_stays_in_range() -> None:
    assert weighted_strength(Decimal("0.8"), Decimal("1.5")) == Decimal("1.0000")
    assert weighted_strength(0.5, Decimal("0.5")) == Decimal("0.2500")
