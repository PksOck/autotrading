"""Durable idempotent dividend import and read model; never places broker orders."""

from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from preza.broker.dividends import parse_dividend_statement
from preza.domain.dividends import (
    Accrual,
    CashEvent,
    DividendsOut,
    DividendStatement,
    ImportCoverage,
    ProjectionBasis,
    project_dividend,
    summarize_cash,
)
from preza.models_dividends import (
    DividendAccrualSnapshot,
    DividendCashEvent,
    DividendImportCoverage,
    DividendProjectionBasis,
)
from preza.services.dividend_controls import reconcile_dividends


def _cash_content(payload: dict[str, Any]) -> dict[str, Any]:
    # Re-exporting the same immutable booking in a later statement is not a conflict.
    return {key: value for key, value in payload.items() if key != "as_of"}


async def store_dividend_data(session: AsyncSession, parsed: DividendStatement) -> dict[str, int]:
    cash_count = 0
    for event in parsed.cash_events:
        payload = event.model_dump(mode="json")
        result = await session.execute(
            insert(DividendCashEvent)
            .values(
                broker=event.broker,
                account_id=event.account_id,
                transaction_id=event.transaction_id,
                booking_date=event.booking_date,
                amount=event.amount,
                currency=event.currency,
                payload=payload,
            )
            .on_conflict_do_nothing(constraint="uq_dividend_cash_identity")
            .returning(DividendCashEvent.id)
        )
        if result.scalar_one_or_none() is not None:
            cash_count += 1
        else:
            existing = await session.scalar(
                select(DividendCashEvent).where(
                    DividendCashEvent.broker == event.broker,
                    DividendCashEvent.account_id == event.account_id,
                    DividendCashEvent.transaction_id == event.transaction_id,
                )
            )
            if existing is None or _cash_content(existing.payload) != _cash_content(payload):
                raise ValueError("dividend_transaction_conflict")
    for accrual in parsed.accruals:
        payload = accrual.model_dump(mode="json")
        stmt = insert(DividendAccrualSnapshot).values(
            account_id=accrual.account_id,
            natural_key=accrual.natural_key,
            as_of=accrual.as_of,
            gross_amount=accrual.gross_amount,
            net_amount=accrual.net_amount,
            tax=accrual.tax,
            currency=accrual.currency,
            payload=payload,
        )
        result = await session.execute(
            stmt.on_conflict_do_nothing(constraint="uq_dividend_accrual_snapshot").returning(
                DividendAccrualSnapshot.id
            )
        )
        if result.scalar_one_or_none() is None:
            existing_accrual = await session.scalar(
                select(DividendAccrualSnapshot).where(
                    DividendAccrualSnapshot.account_id == accrual.account_id,
                    DividendAccrualSnapshot.natural_key == accrual.natural_key,
                    DividendAccrualSnapshot.as_of == accrual.as_of,
                )
            )
            if existing_accrual is None or existing_accrual.payload != payload:
                raise ValueError("dividend_accrual_conflict")
    for coverage in parsed.coverage:
        stmt = insert(DividendImportCoverage).values(
            account_id=coverage.account_id,
            section=coverage.section,
            from_date=coverage.from_date,
            to_date=coverage.to_date,
            as_of=coverage.as_of,
            payload=coverage.model_dump(mode="json"),
        )
        await session.execute(
            stmt.on_conflict_do_update(
                constraint="uq_dividend_coverage",
                set_={"payload": stmt.excluded.payload},
                where=DividendImportCoverage.payload["snapshot_version"].astext
                <= stmt.excluded.payload["snapshot_version"].astext,
            )
        )
    await session.flush()
    return {
        "dividend_cash": cash_count,
        "dividend_accruals": len(parsed.accruals),
        "dividend_coverage": len(parsed.coverage),
    }


async def import_dividend_statement(session: AsyncSession, xml: str) -> dict[str, int]:
    return await store_dividend_data(session, parse_dividend_statement(xml))


async def get_dividends(
    session: AsyncSession,
    account_id: str | None = None,
    currency: str | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
) -> DividendsOut:
    from preza.services.portfolio import latest_positions

    cash_rows = list(
        await session.scalars(
            select(DividendCashEvent).order_by(
                DividendCashEvent.booking_date.desc(), DividendCashEvent.id.desc()
            )
        )
    )
    all_cash = [CashEvent.model_validate(r.payload) for r in cash_rows]
    coverage_rows = list(
        await session.scalars(
            select(DividendImportCoverage).order_by(
                DividendImportCoverage.to_date.desc(),
                DividendImportCoverage.as_of.desc(),
                DividendImportCoverage.payload["snapshot_version"].astext.desc(),
            )
        )
    )
    all_coverage = [ImportCoverage.model_validate(r.payload) for r in coverage_rows]
    accounts = sorted({r.account_id for r in all_cash} | {r.account_id for r in all_coverage})
    cash = [
        r
        for r in all_cash
        if (not account_id or r.account_id == account_id)
        and (not currency or r.currency == currency)
        and (not from_date or r.booking_date >= from_date)
        and (not to_date or r.booking_date <= to_date)
    ]
    coverage = [
        r
        for r in all_coverage
        if (not account_id or r.account_id == account_id)
        and (not from_date or r.to_date >= from_date)
        and (not to_date or r.from_date <= to_date)
    ]
    # Keep all coverage periods visible. For open accruals, only the newest reported
    # snapshot per account is authoritative, including an explicit empty section.
    latest_open: dict[str, ImportCoverage] = {}
    for row in all_coverage:
        if row.section == "OpenDividendAccruals" and row.status != "missing":
            latest_open.setdefault(row.account_id, row)
    accrual_rows = list(await session.scalars(select(DividendAccrualSnapshot)))
    accruals = [Accrual.model_validate(r.payload) for r in accrual_rows]
    historical_accruals = list(accruals)
    accruals = [
        r
        for r in accruals
        if r.status == "open"
        and r.account_id in latest_open
        and r.as_of == latest_open[r.account_id].as_of
        and r.natural_key in latest_open[r.account_id].row_keys
        and (not account_id or r.account_id == account_id)
        and (not currency or r.currency == currency)
        and (not from_date or (r.pay_date or r.ex_date) >= from_date)
        and (not to_date or (r.pay_date or r.ex_date) <= to_date)
    ]
    bases = {
        (r.symbol, r.currency): ProjectionBasis.model_validate(r.payload)
        for r in await session.scalars(select(DividendProjectionBasis))
    }
    positions = await latest_positions(session)
    projections = []
    for position in positions:
        if (
            (account_id and position.account_id != account_id)
            or (currency and position.currency != currency)
            or position.quantity == 0
        ):
            continue
        result = project_dividend(
            position.instrument.symbol,
            position.quantity,
            position.currency,
            bases.get((position.instrument.symbol, position.currency)),
        )
        result.account_id = position.account_id
        result.position_as_of = position.report_date
        projections.append(result)
    currencies = sorted(
        {r.currency for r in all_cash}
        | {r.currency for r in accruals}
        | {r.currency for r in projections}
    )
    return DividendsOut(
        cash_events=cash,
        received=summarize_cash(cash),
        accruals=accruals,
        projections=projections,
        coverage=coverage,
        accounts=accounts,
        currencies=currencies,
        as_of=max((r.as_of for r in coverage), default=None),
        reconciliation=[
            row
            for row in reconcile_dividends(historical_accruals, all_cash)
            if (not account_id or row.account_id == account_id)
            and (not currency or row.currency == currency)
        ],
    )
