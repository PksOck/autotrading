"""API shapes for entry candidates (SCR-03, M3)."""

from datetime import date, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from preza.domain.types import Num


class EntryView(StrEnum):
    ALL = "all"
    PORTFOLIO = "portfolio"
    WATCHLIST = "watchlist"


class RuleHitOut(BaseModel):
    rule: str
    values: dict[str, float]


class LadderLevelOut(BaseModel):
    price: Num
    weight: Num


class EntryOut(BaseModel):
    symbol: str
    name: str | None
    kind: str
    currency: str | None
    held: bool
    watched: bool
    as_of: date
    price: Num
    state: str | None
    anchor: str | None
    rules: list[RuleHitOut]
    zone_low: Num | None
    zone_high: Num | None
    stop: Num | None
    atr: Num | None
    distance_atr: Num | None
    drawdown_pct: Num | None
    valuation: dict[str, Any] = Field(default_factory=dict)
    ladder: list[LadderLevelOut] = Field(default_factory=list)
    cause: str | None
    thesis_intact: bool | None
    dip_rationale: str | None
    dip_evidence: list[dict[str, Any]] = Field(default_factory=list)
    dip_model: str | None
    analyzed_at: datetime | None
    signal_id: UUID | None
    source: str
    updated_at: datetime
