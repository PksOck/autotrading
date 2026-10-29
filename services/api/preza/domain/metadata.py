"""Additive provenance, distinct from request/transport state."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class DataMeta(BaseModel):
    source: str | None = None
    as_of: datetime | None = None
    market_date: date | None = None
    fetched_at: datetime | None = None
    availability: Literal["available", "missing", "not_applicable", "partial"] = "missing"
    reason_code: str | None = "no_observation"
    stale: bool = False
    basis: str | None = None
    source_field: str | None = None


class MetricValue(BaseModel):
    value: str | None = None
    unit: str | None = None
    meta: DataMeta = Field(default_factory=DataMeta)
