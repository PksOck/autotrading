"""Isolated PostgreSQL tests; all accounts and figures below are synthetic."""

from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import delete, func, select

from preza.domain.dividends import ProjectionBasis
from preza.models import Instrument, Position
from preza.models_dividends import (
    DividendAccrualSnapshot,
    DividendCashEvent,
    DividendImportCoverage,
    DividendProjectionBasis,
)
from preza.services.dividends import get_dividends, import_dividend_statement
from tests.test_dividends import event, xml

pytestmark = pytest.mark.db


@pytest.fixture
async def session(api):
    from preza.db import get_sessionmaker

    async with get_sessionmaker()() as connection:
        for model in (
            DividendCashEvent,
            DividendAccrualSnapshot,
            DividendImportCoverage,
            DividendProjectionBasis,
        ):
            await connection.execute(delete(model))
        await connection.commit()
        yield connection
        await connection.rollback()


async def test_cash_idempotency_and_conflict_preserve_signed_ledger(session):
    payload = xml(
        "<CashTransactions>" + event("1", "100") + event("2", "-25") + "</CashTransactions>"
    )
    first = await import_dividend_statement(session, payload)
    second = await import_dividend_statement(session, payload)
    assert first["dividend_cash"] == 2
    assert second["dividend_cash"] == 0
    assert await session.scalar(select(func.count()).select_from(DividendCashEvent)) == 2
    await session.commit()
    with pytest.raises(ValueError, match="dividend_transaction_conflict"):
        await import_dividend_statement(session, payload.replace('amount="100"', 'amount="101"'))
    await session.rollback()
    result = await get_dividends(session)
    assert result.received[0].gross == 75
    assert result.received[0].net is None


async def test_same_transaction_id_in_different_account_is_distinct(session):
    payload = xml("<CashTransactions>" + event("1", "100") + "</CashTransactions>")
    await import_dividend_statement(session, payload)
    await import_dividend_statement(session, payload.replace("SYNTH-A", "SYNTH-B"))
    result = await get_dividends(session, account_id="SYNTH-B")
    assert len(result.cash_events) == 1
    assert result.accounts == ["SYNTH-A", "SYNTH-B"]


async def test_empty_new_open_snapshot_clears_old_entitlements(session):
    payload = xml(
        accrual='<OpenDividendAccruals><OpenDividendAccrual conid="90001" '
        'symbol="SYNTH" currency="USD" exDate="20261020" payDate="20261101" '
        'grossAmount="20" /></OpenDividendAccruals>'
    )
    await import_dividend_statement(session, payload)
    assert len((await get_dividends(session)).accruals) == 1
    await import_dividend_statement(
        session,
        xml(accrual="<OpenDividendAccruals />")
        .replace("20261029;080000", "20261030;080000")
        .replace('toDate="20261028"', 'toDate="20261029"'),
    )
    result = await get_dividends(session)
    assert not result.accruals
    assert not result.cash_events
    assert await session.scalar(select(func.count()).select_from(DividendAccrualSnapshot)) == 1


async def test_new_intraday_empty_snapshot_clears_rows_and_older_reimport_cannot_revive(session):
    payload = xml(
        accrual='<OpenDividendAccruals><OpenDividendAccrual conid="90001" '
        'symbol="SYNTH" currency="USD" exDate="20261020" payDate="20261101" '
        'grossAmount="20" /></OpenDividendAccruals>'
    )
    await import_dividend_statement(session, payload)
    assert len((await get_dividends(session)).accruals) == 1
    await import_dividend_statement(
        session,
        xml(accrual="<OpenDividendAccruals />").replace("20261029;080000", "20261029;090000"),
    )
    assert not (await get_dividends(session)).accruals


async def test_newer_empty_export_with_different_period_keeps_accruals_empty(session):
    old = xml(
        accrual=(
            '<OpenDividendAccruals><OpenDividendAccrual conid="90001" '
            'symbol="SYNTH" currency="USD" exDate="20261020" '
            'payDate="20261101" grossAmount="20" /></OpenDividendAccruals>'
        )
    )
    await import_dividend_statement(session, old)
    newer = (
        xml(accrual="<OpenDividendAccruals />")
        .replace('fromDate="20260101"', 'fromDate="20261001"')
        .replace("20261029;080000", "20261029;090000")
    )
    await import_dividend_statement(session, newer)
    await import_dividend_statement(session, old)
    assert not (await get_dividends(session)).accruals


async def test_sold_cash_stays_visible_and_accumulating_fund_never_gets_fake_cash(session):
    await import_dividend_statement(
        session, xml("<CashTransactions>" + event("1", "100") + "</CashTransactions>")
    )
    instrument = Instrument(symbol="SYNTH-ACC", currency="EUR", kind="etf", source="synthetic")
    session.add(instrument)
    await session.flush()
    session.add(
        Position(
            account_id="SYNTH-A",
            instrument_id=instrument.id,
            report_date=date(2026, 10, 28),
            quantity=Decimal("10"),
            currency="EUR",
            source="synthetic",
        )
    )
    basis = ProjectionBasis(
        symbol="SYNTH-ACC",
        currency="EUR",
        basis="accumulating_share_class",
        source="synthetic_issuer",
        as_of=datetime.now(UTC),
    )
    session.add(
        DividendProjectionBasis(
            symbol=basis.symbol,
            currency=basis.currency,
            annual_per_share=None,
            payload=basis.model_dump(mode="json"),
        )
    )
    await session.flush()
    result = await get_dividends(session)
    assert result.cash_events[0].symbol == "SYNTH"
    assert result.projections[0].annual_gross == 0
    assert result.projections[0].reason == "accumulating_share_class"
    filtered = await get_dividends(session, currency="EUR")
    assert not filtered.cash_events
    assert len(filtered.projections) == 1


async def test_api_returns_decimal_strings_and_rejects_conflicting_import_atomically(
    api, session, monkeypatch
):
    client, _ = api

    async def no_queue(*args, **kwargs):
        return None

    monkeypatch.setattr("preza.routes.portfolio.enqueue", no_queue)
    payload = xml("<CashTransactions>" + event("1", "100") + "</CashTransactions>")
    response = await client.post("/portfolio/import", content=payload)
    assert response.status_code == 200
    assert response.json()["counts"]["dividend_cash"] == 1
    response = await client.get("/portfolio/dividends?currency=USD&account_id=SYNTH-A")
    assert response.status_code == 200
    assert response.json()["received"][0]["gross"] == "100"
    assert response.json()["received"][0]["net"] is None
    assert response.json()["contract_status"] == "synthetic_contract_not_live_validated"
    response = await client.post(
        "/portfolio/import", content=payload.replace('amount="100"', 'amount="101"')
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "dividend_transaction_conflict"
    response = await client.get("/portfolio/dividends")
    assert response.json()["received"][0]["gross"] == "100"
    response = await client.get("/portfolio/dividends?from_date=2026-11-01&to_date=2026-01-01")
    assert response.status_code == 422
