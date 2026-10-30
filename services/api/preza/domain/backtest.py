"""Read-only event-study contract for saved signals and final agent opinions."""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from preza.domain.types import Num


class BacktestRequest(BaseModel):
    source: Literal["all", "signal", "analysis"] = "all"
    available_from: date | None = None
    available_to: date | None = None
    horizon_sessions: Literal[1, 5, 20, 60] = 20
    cost_bps: Decimal = Field(default=Decimal("10"), ge=0, le=1000)
    min_strength: Decimal = Field(default=Decimal(0), ge=0, le=1)
    signal_status: Literal["all", "new", "watching", "accepted", "dismissed", "expired"] = "all"
    limit: int = Field(default=1000, ge=1, le=1000)

    @model_validator(mode="after")
    def ordered_dates(self) -> "BacktestRequest":
        if self.available_from and self.available_to and self.available_from > self.available_to:
            raise ValueError("invalid_availability_range")
        return self


class EventStudyResult(BaseModel):
    entry_date: date | None = None
    exit_date: date | None = None
    entry_price: Num | None = None
    exit_price: Num | None = None
    entry_source: str | None = None
    exit_source: str | None = None
    gross_return_pct: Num | None = None
    net_return_pct: Num | None = None
    skip_reason: (
        Literal[
            "neutral_or_unknown_direction",
            "no_entry_bar",
            "insufficient_future_sessions",
            "invalid_price",
        ]
        | None
    ) = None


class BacktestRow(EventStudyResult):
    id: str
    source: Literal["signal", "analysis"]
    origin: str
    symbol: str
    currency: str | None = None
    available_at: datetime
    direction: str
    strength: Num | None
    record_status: str


class BacktestOut(BaseModel):
    as_of: datetime
    source: str = "database"
    parameters: BacktestRequest
    total_matching: int
    evaluated: int
    truncated: bool
    completed: int
    skipped: int
    mean_gross_return_pct: Num | None
    mean_net_return_pct: Num | None
    positive_share: Num | None
    rows: list[BacktestRow]
