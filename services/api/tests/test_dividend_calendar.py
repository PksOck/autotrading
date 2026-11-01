from datetime import UTC, date, datetime
from decimal import Decimal as D

from preza.domain.dividend_calendar import dividend_calendar
from preza.domain.dividends import Accrual, CashEvent

NOW = datetime(2026, 11, 1, tzinfo=UTC)


def cash(**changes):
    return CashEvent(
        **(
            dict(
                account_id="TEST",
                transaction_id="paid",
                symbol="ABC",
                action_id="A",
                kind="dividend",
                amount=D("10"),
                currency="USD",
                booking_date=date(2026, 10, 15),
                as_of=NOW,
            )
            | changes
        )
    )


def accrual(**changes):
    return Accrual(
        **(
            dict(
                account_id="TEST",
                natural_key="open",
                symbol="ABC",
                action_id="B",
                currency="USD",
                ex_date=date(2026, 10, 25),
                pay_date=date(2026, 11, 15),
                gross_amount=D("12"),
                net_amount=None,
                status="open",
                as_of=NOW,
            )
            | changes
        )
    )


def test_month_and_year_keep_currency_and_received_separate_from_scheduled():
    result = dividend_calendar(
        [cash(), cash(transaction_id="eur", currency="EUR", amount=D("20"))], [accrual()]
    )
    usd = next(row for row in result.years if row.currency == "USD")
    assert usd.received_gross == D("10") and usd.scheduled_gross == D("12")
    assert usd.received_net is None
    assert len(result.months) == 3
    assert {row.state for row in result.events} == {"received", "scheduled"}


def test_missing_dates_amounts_and_cash_matches_never_fake_income():
    result = dividend_calendar(
        [cash()],
        [
            accrual(natural_key="paid", action_id="A"),
            accrual(natural_key="undated", pay_date=None),
            accrual(natural_key="unknown", gross_amount=None),
        ],
    )
    assert {row.reason for row in result.issues} == {
        "cash_match_requires_reconciliation",
        "missing_pay_date",
    }
    month = next(row for row in result.months if row.month == "2026-11")
    assert month.scheduled_gross is None and month.scheduled_count == 1
    assert result.years[0].received_gross == D("10")


def test_booked_corrections_are_signed_and_tax_requires_evidence():
    result = dividend_calendar(
        [
            cash(),
            cash(transaction_id="correction", amount=D("-2")),
            cash(transaction_id="tax", kind="withholding", amount=D("-1")),
        ],
        [],
    )
    assert result.months[0].received_gross == D("8")
    assert result.months[0].received_net == D("7")


def test_a_cash_receipt_with_a_conid_cannot_be_counted_again_as_a_symbol_only_accrual():
    result = dividend_calendar([cash(con_id=123)], [accrual(action_id="A")])
    assert len(result.issues) == 1
    assert not any(event.state == "scheduled" for event in result.events)


def test_receipt_outside_the_selected_period_still_prevents_double_counting():
    result = dividend_calendar([], [accrual(action_id="A")], cash_evidence=[cash()])
    assert result.issues[0].reason == "cash_match_requires_reconciliation"
    assert not result.events and not result.months
