from datetime import UTC, datetime
from decimal import Decimal

from preza.domain.track_record import MIN_SAMPLE, OutcomeRow, origin_of, track_record


def _row(
    ret: str,
    strength: str = "0.5",
    *,
    origin: str = "system",
    kind: str = "entry",
    source: str = "rule",
    alpha: str | None = None,
) -> OutcomeRow:
    return OutcomeRow(
        kind=kind,
        source=source,
        origin=origin,  # type: ignore[arg-type]
        strength=Decimal(strength),
        return_pct=Decimal(ret),
        alpha_pct=None if alpha is None else Decimal(alpha),
    )


def test_origin_separates_user_proposals() -> None:
    assert origin_of("manual", None) == "user"
    assert origin_of("agent", "proposal-id") == "user"
    assert origin_of("rule", None) == "system"


def test_aggregates_hit_rate_alpha_and_pending() -> None:
    rows = [
        _row("4", alpha="1"),
        _row("-2", alpha="-3"),
        _row("0"),
        _row("6", origin="user", kind="catalyst", source="manual", alpha="2"),
    ]
    out = track_record(
        rows, horizon_days=20, signals_total=7, benchmark="SPY", as_of=datetime.now(UTC)
    )
    assert (out.measured, out.pending, out.horizons) == (4, 3, [1, 5, 20, 60])
    # A flat return is not a hit.
    assert out.overall.hit_rate == Decimal("0.5000")
    assert out.overall.avg_return_pct == Decimal("2.0000")
    assert out.overall.avg_alpha_pct == Decimal("0.0000")
    assert out.overall.low_sample and MIN_SAMPLE > 4
    origins = {o.origin: o for o in out.by_origin}
    assert origins["user"].count == 1 and origins["user"].hit_rate == Decimal("1.0000")
    assert origins["system"].count == 3
    assert [(g.kind, g.source, g.count) for g in out.by_group] == [
        ("catalyst", "manual", 1),
        ("entry", "rule", 3),
    ]


def test_calibration_buckets_include_edges() -> None:
    rows = [_row("1", "0"), _row("1", "0.2"), _row("-1", "0.79"), _row("1", "1")]
    out = track_record(rows, horizon_days=5, signals_total=4, benchmark=None, as_of=None)
    assert [b.count for b in out.calibration] == [1, 1, 0, 1, 1]
    assert out.calibration[0].strength_low == 0 and out.calibration[-1].strength_high == 1
    empty = out.calibration[2]
    assert empty.hit_rate is None and empty.avg_strength is None and empty.low_sample
    assert out.calibration[3].hit_rate == Decimal("0.0000")


def test_empty_track_record() -> None:
    out = track_record([], horizon_days=1, signals_total=0, benchmark="SPY", as_of=None)
    assert out.measured == 0 and out.overall.hit_rate is None
    assert [o.count for o in out.by_origin] == [0, 0] and out.by_group == []
