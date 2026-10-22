"""SQLAlchemy tables. Every row carries its source and time (AGENTS.md §3.5)."""

from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from preza.db import Base

PRICE = Numeric(20, 6)
QTY = Numeric(20, 6)


def utcnow() -> datetime:
    return datetime.now(UTC)


class Instrument(Base):
    __tablename__ = "instrument"
    # NULLS NOT DISTINCT: a symbol without a known exchange may exist only once.
    __table_args__ = (
        UniqueConstraint(
            "symbol",
            "exchange",
            name="uq_instrument_symbol_exchange",
            postgresql_nulls_not_distinct=True,
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(20), index=True)
    exchange: Mapped[str | None] = mapped_column(String(20))
    name: Mapped[str | None] = mapped_column(String(200))
    kind: Mapped[str] = mapped_column(String(10), default="unknown")
    currency: Mapped[str | None] = mapped_column(String(3))
    isin: Mapped[str | None] = mapped_column(String(12))
    ib_con_id: Mapped[int | None] = mapped_column(BigInteger, unique=True)
    ucits: Mapped[bool] = mapped_column(Boolean, default=False)
    domicile: Mapped[str | None] = mapped_column(String(2))
    tradable_for_user: Mapped[bool] = mapped_column(Boolean, default=True)
    source: Mapped[str] = mapped_column(String(32))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Bar(Base):
    __tablename__ = "bar"

    instrument_id: Mapped[int] = mapped_column(
        ForeignKey("instrument.id", ondelete="CASCADE"), primary_key=True
    )
    interval: Mapped[str] = mapped_column(String(4), primary_key=True, default="1d")
    day: Mapped[date] = mapped_column(Date, primary_key=True)
    open: Mapped[Decimal] = mapped_column(PRICE)
    high: Mapped[Decimal] = mapped_column(PRICE)
    low: Mapped[Decimal] = mapped_column(PRICE)
    close: Mapped[Decimal] = mapped_column(PRICE)
    volume: Mapped[int | None] = mapped_column(BigInteger)
    source: Mapped[str] = mapped_column(String(32))
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Position(Base):
    """Snapshot rows: one set per account and report date."""

    __tablename__ = "position"
    __table_args__ = (
        UniqueConstraint("account_id", "instrument_id", "report_date", name="uq_position_snapshot"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[str] = mapped_column(String(32), index=True)
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instrument.id"))
    report_date: Mapped[date] = mapped_column(Date, index=True)
    quantity: Mapped[Decimal] = mapped_column(QTY)
    avg_cost: Mapped[Decimal | None] = mapped_column(PRICE)
    market_price: Mapped[Decimal | None] = mapped_column(PRICE)
    market_value: Mapped[Decimal | None] = mapped_column(PRICE)
    unrealized_pnl: Mapped[Decimal | None] = mapped_column(PRICE)
    fx_rate_to_base: Mapped[Decimal | None] = mapped_column(Numeric(20, 10))
    currency: Mapped[str] = mapped_column(String(3))
    source: Mapped[str] = mapped_column(String(32))
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    instrument: Mapped[Instrument] = relationship(lazy="joined")


class Trade(Base):
    __tablename__ = "trade"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[str] = mapped_column(String(32), index=True)
    ib_trade_id: Mapped[str] = mapped_column(String(64), unique=True)
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instrument.id"))
    trade_date: Mapped[date] = mapped_column(Date)
    side: Mapped[str] = mapped_column(String(8))
    quantity: Mapped[Decimal] = mapped_column(QTY)
    price: Mapped[Decimal] = mapped_column(PRICE)
    currency: Mapped[str] = mapped_column(String(3))
    commission: Mapped[Decimal | None] = mapped_column(PRICE)
    source: Mapped[str] = mapped_column(String(32))


class CashBalance(Base):
    __tablename__ = "cash_balance"

    account_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    currency: Mapped[str] = mapped_column(String(3), primary_key=True)
    report_date: Mapped[date] = mapped_column(Date, primary_key=True)
    amount: Mapped[Decimal] = mapped_column(PRICE)
    source: Mapped[str] = mapped_column(String(32))


class WatchlistItem(Base):
    __tablename__ = "watchlist_item"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instrument.id"), unique=True)
    tier: Mapped[str] = mapped_column(String(10), default="active")
    source: Mapped[str] = mapped_column(String(64), default="manual")
    tags: Mapped[list[str]] = mapped_column(ARRAY(String(40)), default=list)
    note: Mapped[str | None] = mapped_column(Text)
    target_price: Mapped[Decimal | None] = mapped_column(PRICE)
    alert_below: Mapped[Decimal | None] = mapped_column(PRICE)
    alert_above: Mapped[Decimal | None] = mapped_column(PRICE)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    added_price: Mapped[Decimal | None] = mapped_column(PRICE)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    instrument: Mapped[Instrument] = relationship(lazy="joined")


class SyncRun(Base):
    """Audit of every data pull: what ran, when, and how it ended (freshness in the UI)."""

    __tablename__ = "sync_run"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kind: Mapped[str] = mapped_column(String(32), index=True)
    status: Mapped[str] = mapped_column(String(16))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    detail: Mapped[str | None] = mapped_column(Text)
