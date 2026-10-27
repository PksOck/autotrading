"""Track record (SCR-10, BL-102): hit rate, alpha and strength calibration from outcomes.

Pure aggregation over `signal_outcome` rows, no I/O. Every number shown on the screen
comes from here; the UI only formats it (AGENTS.md rule 3).
"""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import AwareDatetime, BaseModel, Field

from preza.domain.outcome import HORIZONS

# Below this many outcomes a rate is still shown, but flagged as too little data.
MIN_SAMPLE = 10
STRENGTH_EDGES: tuple[Decimal, ...] = tuple(Decimal(x) / 5 for x in range(6))

_Q = Decimal("0.0001")

Origin = Literal["user", "system"]


@dataclass(frozen=True)
class OutcomeRow:
    kind: str
    source: str
    origin: Origin
    strength: Decimal
    return_pct: Decimal
    alpha_pct: Decimal | None


class TrackStat(BaseModel):
    count: int
    hit_rate: Decimal | None = Field(
        description="Share of outcomes that moved in the signal direction, 0..1."
    )
    avg_return_pct: Decimal | None
    avg_alpha_pct: Decimal | None
    low_sample: bool = Field(description=f"Fewer than {MIN_SAMPLE} outcomes.")


class TrackGroup(TrackStat):
    kind: str
    source: str


class TrackOrigin(TrackStat):
    origin: Origin


class CalibrationBucket(TrackStat):
    strength_low: Decimal
    strength_high: Decimal
    avg_strength: Decimal | None


class TrackRecordOut(BaseModel):
    horizon_days: int
    horizons: list[int]
    benchmark: str | None
    source: str = "signal_outcome"
    as_of: AwareDatetime | None = Field(description="Latest outcome computation time.")
    min_sample: int = MIN_SAMPLE
    signals_total: int
    measured: int
    pending: int = Field(description="Signals without an outcome at this horizon yet.")
    overall: TrackStat
    by_origin: list[TrackOrigin]
    by_group: list[TrackGroup]
    calibration: list[CalibrationBucket]


def origin_of(source: str, proposal_id: object | None) -> Origin:
    """Your proposals are measured apart from system signals (DESIGN §11)."""
    return "user" if source == "manual" or proposal_id is not None else "system"


def _avg(values: Sequence[Decimal]) -> Decimal | None:
    return (sum(values, Decimal(0)) / len(values)).quantize(_Q) if values else None


def stat(rows: Sequence[OutcomeRow]) -> TrackStat:
    alphas = [r.alpha_pct for r in rows if r.alpha_pct is not None]
    hits = [Decimal(1) if r.return_pct > 0 else Decimal(0) for r in rows]
    return TrackStat(
        count=len(rows),
        hit_rate=_avg(hits),
        avg_return_pct=_avg([r.return_pct for r in rows]),
        avg_alpha_pct=_avg(alphas),
        low_sample=len(rows) < MIN_SAMPLE,
    )


def _bucket(strength: Decimal) -> int:
    # The top bucket includes 1.0.
    for i in range(len(STRENGTH_EDGES) - 2, -1, -1):
        if strength >= STRENGTH_EDGES[i]:
            return i
    return 0


def track_record(
    rows: Iterable[OutcomeRow],
    *,
    horizon_days: int,
    signals_total: int,
    benchmark: str | None,
    as_of: datetime | None,
) -> TrackRecordOut:
    items = list(rows)
    origins: dict[Origin, list[OutcomeRow]] = {"user": [], "system": []}
    groups: dict[tuple[str, str], list[OutcomeRow]] = {}
    buckets: list[list[OutcomeRow]] = [[] for _ in STRENGTH_EDGES[:-1]]
    for row in items:
        origins[row.origin].append(row)
        groups.setdefault((row.kind, row.source), []).append(row)
        buckets[_bucket(row.strength)].append(row)
    return TrackRecordOut(
        horizon_days=horizon_days,
        horizons=list(HORIZONS),
        benchmark=benchmark,
        as_of=as_of,
        signals_total=signals_total,
        measured=len(items),
        pending=max(signals_total - len(items), 0),
        overall=stat(items),
        by_origin=[
            TrackOrigin(origin=origin, **stat(group).model_dump())
            for origin, group in origins.items()
        ],
        by_group=[
            TrackGroup(kind=kind, source=source, **stat(group).model_dump())
            for (kind, source), group in sorted(groups.items())
        ],
        calibration=[
            CalibrationBucket(
                strength_low=STRENGTH_EDGES[i],
                strength_high=STRENGTH_EDGES[i + 1],
                avg_strength=_avg([r.strength for r in bucket]),
                **stat(bucket).model_dump(),
            )
            for i, bucket in enumerate(buckets)
        ],
    )
