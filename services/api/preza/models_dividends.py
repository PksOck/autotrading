"""Separate dividend ledgers: received cash, accrual snapshots, and source coverage."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Date, DateTime, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from preza.db import Base


class DividendCashEvent(Base):
    __tablename__ = "dividend_cash_event"
    __table_args__ = (
        UniqueConstraint(
            "broker", "account_id", "transaction_id", name="uq_dividend_cash_identity"
        ),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    broker: Mapped[str] = mapped_column(String(16))
    account_id: Mapped[str] = mapped_column(String(64), index=True)
    transaction_id: Mapped[str] = mapped_column(String(128))
    booking_date: Mapped[date] = mapped_column(Date, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(28, 10))
    currency: Mapped[str] = mapped_column(String(3))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB)


class DividendAccrualSnapshot(Base):
    __tablename__ = "dividend_accrual_snapshot"
    __table_args__ = (
        UniqueConstraint("account_id", "natural_key", "as_of", name="uq_dividend_accrual_snapshot"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[str] = mapped_column(String(64), index=True)
    natural_key: Mapped[str] = mapped_column(String(256))
    as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    gross_amount: Mapped[Decimal | None] = mapped_column(Numeric(28, 10))
    net_amount: Mapped[Decimal | None] = mapped_column(Numeric(28, 10))
    tax: Mapped[Decimal | None] = mapped_column(Numeric(28, 10))
    currency: Mapped[str] = mapped_column(String(3))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB)


class DividendImportCoverage(Base):
    __tablename__ = "dividend_import_coverage"
    __table_args__ = (
        UniqueConstraint(
            "account_id", "section", "from_date", "to_date", "as_of", name="uq_dividend_coverage"
        ),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[str] = mapped_column(String(64), index=True)
    section: Mapped[str] = mapped_column(String(64))
    from_date: Mapped[date] = mapped_column(Date)
    to_date: Mapped[date] = mapped_column(Date)
    as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB)


class DividendProjectionBasis(Base):
    """Only verified per-share distributions or an explicit accumulating share class policy."""

    __tablename__ = "dividend_projection_basis"
    symbol: Mapped[str] = mapped_column(String(32), primary_key=True)
    currency: Mapped[str] = mapped_column(String(3), primary_key=True)
    annual_per_share: Mapped[Decimal | None] = mapped_column(Numeric(28, 10))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB)
