"""Cash, accrual and projection contracts; money serializes as decimal strings."""

from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CashEvent(BaseModel):
    broker: str = "ibkr"
    account_id: str
    transaction_id: str
    symbol: str | None = None
    con_id: int | None = None
    action_id: str | None = None
    kind: Literal["dividend", "payment_in_lieu", "withholding"]
    amount: Decimal
    currency: str
    booking_date: date
    settlement_date: date | None = None
    fx_rate_to_base: Decimal | None = None
    fx_basis: str | None = None
    base_currency: str | None = None
    source: str = "ibkr_flex"
    as_of: datetime
    as_of_basis: str = "statement_report_date_utc_boundary"


class Accrual(BaseModel):
    broker: str = "ibkr"
    account_id: str
    natural_key: str
    symbol: str | None = None
    con_id: int | None = None
    action_id: str | None = None
    currency: str
    ex_date: date
    pay_date: date | None = None
    quantity: Decimal | None = None
    gross_rate: Decimal | None = None
    gross_amount: Decimal | None = None
    tax: Decimal | None = None
    net_amount: Decimal | None = None
    fx_rate_to_base: Decimal | None = None
    status: str
    source: str = "ibkr_flex"
    as_of: datetime
    as_of_basis: str = "statement_report_date_utc_boundary"
    snapshot_version: str = ""


class ImportCoverage(BaseModel):
    account_id: str
    section: str
    from_date: date
    to_date: date
    status: Literal["missing", "partial", "complete"]
    gaps: list[str] = Field(default_factory=list)
    source: str = "ibkr_flex"
    as_of: datetime
    as_of_basis: str = "statement_report_date_utc_boundary"
    snapshot_version: str = ""
    row_keys: list[str] = Field(default_factory=list)


class DividendStatement(BaseModel):
    cash_events: list[CashEvent] = Field(default_factory=list)
    accruals: list[Accrual] = Field(default_factory=list)
    coverage: list[ImportCoverage] = Field(default_factory=list)


class ProjectionBasis(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)
    symbol: str
    currency: str
    annual_per_share: Decimal | None = None
    basis: Literal["indicated_annual", "verified_ttm", "accumulating_share_class"]
    source: str = Field(min_length=1)
    as_of: datetime
    includes_special: bool = False


class DividendProjection(BaseModel):
    account_id: str | None = None
    symbol: str
    quantity: Decimal
    currency: str
    annual_gross: Decimal | None
    annual_per_share: Decimal | None
    basis: str | None
    reason: str | None
    source: str | None
    as_of: datetime | None
    includes_special: bool = False


def project_dividend(
    symbol: str, quantity: Decimal, currency: str, basis: ProjectionBasis | None
) -> DividendProjection:
    valid = basis is not None and basis.symbol == symbol and basis.currency == currency
    accumulating = valid and basis is not None and basis.basis == "accumulating_share_class"
    amount = None
    if accumulating:
        amount = Decimal(0)
    elif valid and basis is not None and basis.annual_per_share is not None:
        amount = quantity * basis.annual_per_share
    return DividendProjection(
        symbol=symbol,
        quantity=quantity,
        currency=currency,
        annual_gross=amount,
        annual_per_share=basis.annual_per_share if valid and basis else None,
        basis=basis.basis if valid and basis else None,
        reason="accumulating_share_class"
        if accumulating
        else ("incomplete_history" if amount is None else None),
        source=basis.source if valid and basis else None,
        as_of=basis.as_of if valid and basis else None,
        includes_special=basis.includes_special if valid and basis else False,
    )


class CashSummary(BaseModel):
    currency: str
    gross: Decimal
    payment_in_lieu: Decimal
    withholding: Decimal | None
    unresolved_withholding: Decimal | None
    net: Decimal | None
    base_amount: Decimal | None
    base_currency: str | None = None
    fx_complete: bool


def summarize_cash(events: list[CashEvent]) -> list[CashSummary]:
    grouped: dict[str, list[CashEvent]] = defaultdict(list)
    for event in events:
        grouped[event.currency].append(event)
    results = []
    for currency, rows in sorted(grouped.items()):
        income = [r for r in rows if r.kind != "withholding"]
        taxes = [r for r in rows if r.kind == "withholding"]

        # Only explicit same-account corporate-action + instrument links qualify.
        def key(row: CashEvent) -> tuple[str, str | None, int | None, str | None]:
            return row.account_id, row.action_id, row.con_id, row.symbol

        linked_keys = {key(r) for r in income if r.action_id}
        linked = [r for r in taxes if r.action_id and key(r) in linked_keys]
        unresolved = [r for r in taxes if r not in linked]
        tax_complete = (
            bool(income)
            and all(r.action_id and any(key(t) == key(r) for t in linked) for r in income)
            and not unresolved
        )
        gross = sum((r.amount for r in income), Decimal(0))
        withholding = sum((r.amount for r in linked), Decimal(0)) if linked else None
        net = gross + (withholding or Decimal(0)) if tax_complete else None
        bases = {r.base_currency for r in rows}
        base_currency = next(iter(bases)) if len(bases) == 1 else None
        fx_complete = base_currency is not None and all(r.fx_rate_to_base is not None for r in rows)
        results.append(
            CashSummary(
                currency=currency,
                gross=gross,
                payment_in_lieu=sum(
                    (r.amount for r in income if r.kind == "payment_in_lieu"), Decimal(0)
                ),
                withholding=withholding,
                unresolved_withholding=sum((r.amount for r in unresolved), Decimal(0))
                if unresolved
                else None,
                net=net,
                base_amount=sum(
                    (r.amount * r.fx_rate_to_base for r in rows if r.fx_rate_to_base is not None),
                    Decimal(0),
                )
                if fx_complete and tax_complete
                else None,
                fx_complete=fx_complete,
                base_currency=base_currency,
            )
        )
    return results


class DividendsOut(BaseModel):
    cash_events: list[CashEvent]
    received: list[CashSummary]
    accruals: list[Accrual]
    projections: list[DividendProjection]
    coverage: list[ImportCoverage]
    accounts: list[str]
    currencies: list[str]
    source: str = "ibkr_flex"
    as_of: datetime | None
    contract_status: str = "synthetic_contract_not_live_validated"
