"""Dated dividend cash and open entitlements; no inferred payment schedule or FX."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from preza.domain.dividends import Accrual, CashEvent


class DividendTotals(BaseModel):
    currency: str
    received_gross: Decimal | None = None
    received_net: Decimal | None = None
    scheduled_gross: Decimal | None = None
    scheduled_net: Decimal | None = None
    received_count: int = 0
    scheduled_count: int = 0


class DividendMonth(DividendTotals):
    month: str


class DividendYear(DividendTotals):
    year: int


class DividendCalendarEvent(BaseModel):
    id: str
    account_id: str
    symbol: str | None
    currency: str
    payment_date: date
    gross: Decimal | None
    state: Literal["received", "scheduled"]
    source: str
    as_of: datetime


class DividendCalendarIssue(BaseModel):
    id: str
    account_id: str
    symbol: str | None
    currency: str
    reason: Literal["missing_pay_date", "cash_match_requires_reconciliation"]


class DividendCalendar(BaseModel):
    months: list[DividendMonth] = Field(default_factory=list)
    years: list[DividendYear] = Field(default_factory=list)
    events: list[DividendCalendarEvent] = Field(default_factory=list)
    issues: list[DividendCalendarIssue] = Field(default_factory=list)


def _totals(cash: list[CashEvent], open_rows: list[Accrual], currency: str) -> DividendTotals:
    from preza.domain.dividends import summarize_cash

    income = [row for row in cash if row.kind != "withholding"]
    summary = summarize_cash(cash)
    return DividendTotals(
        currency=currency,
        received_gross=sum((row.amount for row in income), Decimal(0)) if income else None,
        received_net=summary[0].net if summary else None,
        scheduled_gross=sum(
            (row.gross_amount for row in open_rows if row.gross_amount is not None), Decimal(0)
        )
        if open_rows and all(row.gross_amount is not None for row in open_rows)
        else None,
        scheduled_net=sum(
            (row.net_amount for row in open_rows if row.net_amount is not None), Decimal(0)
        )
        if open_rows and all(row.net_amount is not None for row in open_rows)
        else None,
        received_count=len(income),
        scheduled_count=len(open_rows),
    )


def dividend_calendar(
    cash: list[CashEvent], accruals: list[Accrual], *, cash_evidence: list[CashEvent] | None = None
) -> DividendCalendar:
    result = DividendCalendar()

    receipts: dict[tuple[str, str, str, str], list[CashEvent]] = defaultdict(list)
    for receipt in cash if cash_evidence is None else cash_evidence:
        if receipt.kind != "withholding" and receipt.action_id:
            receipts[
                (receipt.broker, receipt.account_id, receipt.currency, receipt.action_id)
            ].append(receipt)

    def same_instrument(receipt: CashEvent, accrual: Accrual) -> bool:
        if receipt.con_id is not None and accrual.con_id is not None:
            return receipt.con_id == accrual.con_id
        if receipt.symbol and accrual.symbol:
            return receipt.symbol == accrual.symbol
        # An unidentifiable leg needs reconciliation, never another projected payment.
        return True

    scheduled: list[Accrual] = []
    for row in accruals:
        if row.status != "open":
            continue
        row_id = f"open:{row.broker}:{row.account_id}:{row.natural_key}"
        matched = any(
            same_instrument(receipt, row)
            for receipt in receipts.get(
                (row.broker, row.account_id, row.currency, row.action_id or ""), []
            )
        )
        if matched or row.pay_date is None:
            result.issues.append(
                DividendCalendarIssue(
                    id=row_id,
                    account_id=row.account_id,
                    symbol=row.symbol,
                    currency=row.currency,
                    reason="cash_match_requires_reconciliation" if matched else "missing_pay_date",
                )
            )
            continue
        scheduled.append(row)
        result.events.append(
            DividendCalendarEvent(
                id=row_id,
                account_id=row.account_id,
                symbol=row.symbol,
                currency=row.currency,
                payment_date=row.pay_date,
                gross=row.gross_amount,
                state="scheduled",
                source=row.source,
                as_of=row.as_of,
            )
        )
    for receipt in cash:
        if receipt.kind == "withholding":
            continue
        result.events.append(
            DividendCalendarEvent(
                id=f"cash:{receipt.broker}:{receipt.account_id}:{receipt.transaction_id}",
                account_id=receipt.account_id,
                symbol=receipt.symbol,
                currency=receipt.currency,
                payment_date=receipt.booking_date,
                gross=receipt.amount,
                state="received",
                source=receipt.source,
                as_of=receipt.as_of,
            )
        )
    cash_groups: dict[tuple[str, str], list[CashEvent]] = defaultdict(list)
    open_groups: dict[tuple[str, str], list[Accrual]] = defaultdict(list)
    year_cash: dict[tuple[int, str], list[CashEvent]] = defaultdict(list)
    year_open: dict[tuple[int, str], list[Accrual]] = defaultdict(list)
    for receipt in cash:
        cash_groups[(receipt.booking_date.strftime("%Y-%m"), receipt.currency)].append(receipt)
        year_cash[(receipt.booking_date.year, receipt.currency)].append(receipt)
    for entry in scheduled:
        assert entry.pay_date is not None
        open_groups[(entry.pay_date.strftime("%Y-%m"), entry.currency)].append(entry)
        year_open[(entry.pay_date.year, entry.currency)].append(entry)
    for month, currency in sorted(cash_groups.keys() | open_groups.keys()):
        totals = _totals(cash_groups[(month, currency)], open_groups[(month, currency)], currency)
        result.months.append(DividendMonth(month=month, **totals.model_dump()))
    for year, currency in sorted(year_cash.keys() | year_open.keys()):
        totals = _totals(year_cash[(year, currency)], year_open[(year, currency)], currency)
        result.years.append(DividendYear(year=year, **totals.model_dump()))
    result.events.sort(key=lambda row: (row.payment_date, row.account_id, row.id))
    return result
