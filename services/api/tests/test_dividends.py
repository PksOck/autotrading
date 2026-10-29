"""Synthetic contract fixtures only: no customer statement or authentic amounts."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from preza.broker.dividends import parse_dividend_statement
from preza.domain.dividends import ProjectionBasis, project_dividend, summarize_cash


def xml(cash: str = "", accrual: str = "") -> str:
    return (
        '<FlexQueryResponse><FlexStatements><FlexStatement accountId="SYNTH-A" '
        'fromDate="20260101" toDate="20261028" whenGenerated="20261029;080000">'
        f"{cash}{accrual}</FlexStatement></FlexStatements></FlexQueryResponse>"
    )


def event(identifier: str, amount: str, kind: str = "Dividends", action: str = "A1") -> str:
    return (
        f'<CashTransaction transactionID="{identifier}" type="{kind}" amount="{amount}" '
        f'currency="USD" dateTime="20261001;120000" symbol="SYNTH" conid="90001" '
        f'actionID="{action}" />'
    )


def test_signed_cash_tax_and_accrual_are_separate() -> None:
    parsed = parse_dividend_statement(
        xml(
            "<CashTransactions>"
            + event("1", "100")
            + event("2", "-15", "Withholding Tax")
            + event("3", "-20")
            + "</CashTransactions>",
            '<OpenDividendAccruals><OpenDividendAccrual conid="90001" symbol="SYNTH" '
            'currency="USD" exDate="20261020" payDate="20261101" quantity="10" '
            'grossRate="2" grossAmount="20" /></OpenDividendAccruals>',
        )
    )
    summary = summarize_cash(parsed.cash_events)[0]
    assert summary.gross == Decimal("80")
    assert summary.withholding == Decimal("-15")
    assert summary.net == Decimal("65")
    assert len(parsed.accruals) == 1
    assert parsed.accruals[0].net_amount is None
    assert summary.base_amount is None


def test_missing_tax_is_unknown_unlinked_tax_remains_unresolved() -> None:
    parsed = parse_dividend_statement(
        xml(
            "<CashTransactions>"
            + event("1", "100")
            + event("2", "-15", "Withholding Tax", "OTHER")
            + "</CashTransactions>"
        )
    )
    summary = summarize_cash(parsed.cash_events)[0]
    assert summary.net is None
    assert summary.unresolved_withholding == Decimal("-15")


def test_absent_section_differs_from_explicit_empty() -> None:
    absent = parse_dividend_statement(xml())
    empty = parse_dividend_statement(xml("<CashTransactions />"))
    assert absent.coverage[0].status == "missing"
    assert empty.coverage[0].status == "complete"
    assert not empty.cash_events


def test_missing_transaction_id_is_coverage_gap_not_fabricated_identity() -> None:
    parsed = parse_dividend_statement(
        xml(
            "<CashTransactions><CashTransaction "
            'type="Dividends" amount="10" currency="USD" dateTime="20261001" />'
            "</CashTransactions>"
        )
    )
    assert not parsed.cash_events
    assert parsed.coverage[0].status == "partial"
    assert "missing_transaction_id" in parsed.coverage[0].gaps


def test_change_reversal_never_proves_cash_received() -> None:
    parsed = parse_dividend_statement(
        xml(
            accrual="<ChangeInDividendAccruals>"
            '<ChangeInDividendAccrual conid="90001" symbol="SYNTH" currency="USD" '
            'exDate="20261020" payDate="20261101" quantity="10" grossAmount="-20" '
            'code="Re" /></ChangeInDividendAccruals>'
        )
    )
    assert not parsed.cash_events
    assert parsed.accruals[0].status == "change:Re"


def test_payment_in_lieu_is_distinct_and_nonfinite_money_is_rejected() -> None:
    parsed = parse_dividend_statement(
        xml(
            "<CashTransactions>"
            + event("1", "8", "Payment In Lieu Of Dividends")
            + event("2", "NaN")
            + "</CashTransactions>"
        )
    )
    assert parsed.cash_events[0].kind == "payment_in_lieu"
    assert len(parsed.cash_events) == 1
    assert parsed.coverage[0].status == "partial"


def test_projection_uses_verified_per_share_basis_or_explicit_gap() -> None:
    basis = ProjectionBasis(
        symbol="SYNTH",
        currency="USD",
        annual_per_share=Decimal("4"),
        basis="indicated_annual",
        source="synthetic_issuer",
        as_of=datetime.now(UTC),
    )
    assert project_dividend("SYNTH", Decimal("25"), "USD", basis).annual_gross == 100
    assert project_dividend("SYNTH", Decimal("25"), "USD", None).reason == "incomplete_history"
    acc = basis.model_copy(update={"basis": "accumulating_share_class", "annual_per_share": None})
    result = project_dividend("SYNTH", Decimal("25"), "USD", acc)
    assert result.annual_gross == 0
    assert result.reason == "accumulating_share_class"


def test_invalid_statement_period_is_rejected() -> None:
    with pytest.raises(ValueError):
        parse_dividend_statement(xml().replace("20260101", "20270101"))
