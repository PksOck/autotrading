"""Compare reported entitlements with signed gross payments only on explicit identity links."""

from decimal import Decimal

from preza.domain.dividends import Accrual, CashEvent, DividendReconciliation


def reconcile_dividends(
    accruals: list[Accrual], cash: list[CashEvent]
) -> list[DividendReconciliation]:
    latest: dict[tuple[str, str, str, tuple[str, int | str]], Accrual] = {}

    def identity(row: Accrual | CashEvent) -> tuple[str, int | str] | None:
        if row.con_id is not None:
            return "con_id", row.con_id
        return ("symbol", row.symbol) if row.symbol else None

    for accrual in accruals:
        instrument = identity(accrual)
        if not accrual.action_id or instrument is None or accrual.gross_amount is None:
            continue
        key = (accrual.account_id, accrual.currency, accrual.action_id, instrument)
        previous = latest.get(key)
        if previous is None or (accrual.as_of, accrual.snapshot_version) > (
            previous.as_of,
            previous.snapshot_version,
        ):
            latest[key] = accrual
    results = []
    for key, accrual in sorted(latest.items()):
        rows = [
            row
            for row in cash
            if row.kind == "dividend"
            and row.action_id is not None
            and (row.account_id, row.currency, row.action_id, identity(row)) == key
        ]
        expected = accrual.gross_amount
        assert expected is not None and accrual.action_id is not None
        received = sum((row.amount for row in rows), Decimal(0)) if rows else None
        difference = received - expected if received is not None else None
        results.append(
            DividendReconciliation(
                account_id=accrual.account_id,
                symbol=accrual.symbol,
                currency=accrual.currency,
                action_id=accrual.action_id,
                expected_gross=expected,
                received_gross=received,
                difference=difference,
                status="awaiting_payment"
                if received is None
                else "confirmed"
                if difference == 0
                else "changed",
                as_of=max([accrual.as_of, *(row.as_of for row in rows)]),
            )
        )
    return results
