"""Portfolio snapshot and watchlist (M1, BL-022, BL-028, BL-032)."""

from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from preza.domain.dividends import DividendStatement
from preza.domain.market import InstrumentKind
from preza.domain.metadata import DataMeta, MetricValue
from preza.domain.types import Num


class PositionIn(BaseModel):
    """A position parsed from IBKR (Flex or Gateway), before it is stored."""

    account_id: str
    symbol: str
    con_id: int | None = None
    name: str | None = None
    kind: InstrumentKind = InstrumentKind.UNKNOWN
    exchange: str | None = None
    currency: str
    isin: str | None = None
    quantity: Num
    avg_cost: Num | None = None
    market_price: Num | None = None
    market_value: Num | None = None
    unrealized_pnl: Num | None = None
    fx_rate_to_base: Num | None = None
    report_date: date


class TradeIn(BaseModel):
    account_id: str
    ib_trade_id: str
    symbol: str
    con_id: int | None = None
    trade_date: date
    side: str
    quantity: Num
    price: Num
    currency: str
    commission: Num | None = None


class CashIn(BaseModel):
    account_id: str
    currency: str
    amount: Num
    report_date: date


class AccountSnapshotIn(BaseModel):
    account_id: str
    report_date: date
    positions_complete: bool = False
    cash_complete: bool = False


class FlexStatement(BaseModel):
    positions: list[PositionIn]
    trades: list[TradeIn]
    cash: list[CashIn]
    snapshots: list[AccountSnapshotIn] = Field(default_factory=list)
    dividends: DividendStatement | None = None


class PositionOut(BaseModel):
    instrument_id: int | None = None
    account_id: str | None = None
    report_date: date | None = None
    exchange: str | None = None
    identity_status: str = "unresolved"
    latest_close: str | None = None
    price_meta: DataMeta = Field(default_factory=DataMeta)
    metrics: dict[str, MetricValue] = Field(default_factory=dict)
    symbol: str
    name: str | None
    kind: InstrumentKind
    currency: str
    quantity: Num
    avg_cost: Num | None
    market_price: Num | None
    market_value: Num | None
    unrealized_pnl: Num | None
    weight_pct: Num | None
    change_pct: Num | None = None


class SyncInfo(BaseModel):
    kind: str
    status: str
    finished_at: datetime | None
    detail: str | None


class PortfolioOut(BaseModel):
    accounts: list[str] = Field(default_factory=list)
    selected_account: str | None = None
    valuation_meta: DataMeta = Field(default_factory=DataMeta)
    as_of: date | None
    base_currency: str
    total_value: Num | None
    positions: list[PositionOut]
    cash: list[CashIn]
    last_sync: SyncInfo | None
    source: str | None


class WatchTier(StrEnum):
    ACTIVE = "active"
    RESERVE = "reserve"


class WatchlistCreate(BaseModel):
    symbol: str = Field(min_length=1, max_length=20)
    tier: WatchTier = WatchTier.ACTIVE
    source: str = Field(default="manual", max_length=64)
    tags: list[str] = Field(default_factory=list, max_length=12)
    note: str | None = Field(default=None, max_length=4000)
    target_price: Num | None = None
    alert_below: Num | None = None
    alert_above: Num | None = None


class WatchlistUpdate(BaseModel):
    tier: WatchTier | None = None
    tags: list[str] | None = None
    note: str | None = None
    target_price: Num | None = None
    alert_below: Num | None = None
    alert_above: Num | None = None
    reviewed: bool | None = None


class WatchlistOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    instrument_id: int | None = None
    exchange: str | None = None
    currency: str | None = None
    identity_status: str = "unresolved"
    change_pct: Num | None = None
    price_meta: DataMeta = Field(default_factory=DataMeta)
    metrics: dict[str, MetricValue] = Field(default_factory=dict)
    revision: int = 1
    symbol: str
    name: str | None
    kind: InstrumentKind
    tier: WatchTier
    source: str
    tags: list[str]
    note: str | None
    target_price: Num | None
    alert_below: Num | None
    alert_above: Num | None
    added_at: datetime
    added_price: Num | None
    last_close: Num | None
    since_added_pct: Num | None
    reviewed_at: datetime | None
