"""Price-only estimate for unchanged imported holdings, never account NAV performance."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from preza.domain.types import Num


@dataclass(frozen=True)
class DailyHolding:
    quantity: Decimal
    currency: str
    fx: Decimal | None
    close: Decimal | None
    previous: Decimal | None
    day: date | None
    previous_day: date | None
    report_date: date
    source: str | None
    resolved: bool
    stale: bool = False
    fx_base_currency: str | None = None


class DailyMove(BaseModel):
    amount: Num | None = None
    percent: Num | None = None
    market_date: date | None = None
    previous_market_date: date | None = None
    holdings_dates: list[date] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    basis: str = "held_positions_constant_reported_fx"
    reason: str | None = "no_positions"


class CurrencyDailyMove(DailyMove):
    currency: str
    position_count: int


def native_daily_moves(holdings: list[DailyHolding]) -> list[CurrencyDailyMove]:
    currencies = sorted({row.currency for row in holdings if row.quantity != 0})
    result = []
    for currency in currencies:
        rows = [row for row in holdings if row.currency == currency and row.quantity != 0]
        result.append(
            CurrencyDailyMove(
                **daily_move(rows, currency).model_dump(),
                currency=currency,
                position_count=len(rows),
            )
        )
    return result


def daily_move(holdings: list[DailyHolding], base_currency: str) -> DailyMove:
    rows = [row for row in holdings if not row.quantity.is_finite() or row.quantity != 0]
    result = DailyMove(
        holdings_dates=sorted({row.report_date for row in rows}),
        sources=sorted({row.source for row in rows if row.source}),
    )
    if not rows:
        return result
    dates = {(row.day, row.previous_day) for row in rows}
    if len(dates) != 1:
        result.reason = "mixed_market_dates"
        return result
    amount, previous_value = Decimal(0), Decimal(0)
    for row in rows:
        fx = Decimal(1) if row.currency == base_currency else row.fx
        if any(
            value is not None and not value.is_finite()
            for value in (row.quantity, fx, row.close, row.previous)
        ):
            result.reason = "invalid_price"
            return result
        reason = (
            "unresolved_identity"
            if not row.resolved
            else "short_position"
            if row.quantity < 0
            else "stale_prices"
            if row.stale
            else "missing_price"
            if row.close is None
            or row.previous is None
            or row.day is None
            or row.previous_day is None
            else "invalid_price"
            if row.close <= 0 or row.previous <= 0 or row.day <= row.previous_day
            else "missing_fx"
            if fx is None or fx <= 0
            else "unverified_fx_target"
            if row.currency != base_currency and row.fx_base_currency != base_currency
            else None
        )
        if reason:
            result.reason = reason
            return result
        assert row.close is not None and row.previous is not None and fx is not None
        amount += row.quantity * (row.close - row.previous) * fx
        previous_value += row.quantity * row.previous * fx
    if previous_value <= 0:
        result.reason = "invalid_price"
        return result
    result.amount = amount
    result.percent = amount / previous_value * 100
    result.market_date, result.previous_market_date = next(iter(dates))
    result.reason = None
    return result
