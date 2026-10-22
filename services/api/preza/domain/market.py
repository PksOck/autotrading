"""Instruments and daily bars (M1)."""

from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from preza.domain.types import Num


class InstrumentKind(StrEnum):
    STOCK = "stock"
    ETF = "etf"
    UNKNOWN = "unknown"


class InstrumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    symbol: str
    name: str | None
    kind: InstrumentKind
    exchange: str | None
    currency: str | None
    isin: str | None
    ucits: bool
    tradable_for_user: bool


class BarIn(BaseModel):
    """A daily bar as returned by a provider, before it is stored."""

    day: date
    open: Num
    high: Num
    low: Num
    close: Num
    volume: int | None = Field(default=None, ge=0)


class BarOut(BarIn):
    model_config = ConfigDict(from_attributes=True)


class Provenance(BaseModel):
    source: str
    as_of: datetime
    stale: bool = False


class InstrumentDetail(InstrumentOut):
    last_close: Num | None = None
    change_pct: Num | None = None
    provenance: Provenance | None = None


class BarsOut(BaseModel):
    symbol: str
    bars: list[BarOut]
    provenance: Provenance | None
