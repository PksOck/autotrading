from datetime import UTC, date, datetime
from decimal import Decimal

from preza.domain.dividends import Accrual, CashEvent
from preza.services.dividend_controls import reconcile_dividends


def test_reconciliation_uses_explicit_same_account_action_and_signed_gross() -> None:
    stamp = datetime(2026, 10, 29, tzinfo=UTC)
    accrual = Accrual(
        account_id="DEMO",
        natural_key="a",
        symbol="MSFT",
        action_id="A",
        currency="USD",
        ex_date=date(2026, 10, 1),
        gross_amount=Decimal(20),
        status="open",
        as_of=stamp,
    )

    def cash(tx: str, amount: int, account: str = "DEMO", kind: str = "dividend") -> CashEvent:
        return CashEvent(
            transaction_id=tx,
            account_id=account,
            symbol="MSFT",
            action_id="A",
            currency="USD",
            booking_date=date(2026, 10, 20),
            kind=kind,
            amount=Decimal(amount),
            as_of=stamp,
        )

    rows = reconcile_dividends(
        [accrual],
        [
            cash("one", 25),
            cash("reverse", -5),
            cash("tax", -3, kind="withholding"),
            cash("other", 999, account="OTHER"),
        ],
    )
    assert rows[0].status == "confirmed"
    assert rows[0].received_gross == Decimal(20)
    changed = reconcile_dividends([accrual], [cash("one", 25)])[0]
    assert changed.status == "changed" and changed.difference == Decimal(5)
    assert (
        reconcile_dividends([accrual], [cash("other", 999, account="OTHER")])[0].status
        == "awaiting_payment"
    )
    accrual.action_id = None
    assert reconcile_dividends([accrual], [cash("one", 25)]) == []
