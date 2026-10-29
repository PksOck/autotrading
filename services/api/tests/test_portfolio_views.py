from datetime import date
from decimal import Decimal

import httpx
import pytest

from preza.db import get_sessionmaker
from preza.models import Instrument, Position
from tests.conftest import FakeRouter

pytestmark = pytest.mark.db


async def test_portfolio_keeps_each_accounts_latest_positions(
    api: tuple[httpx.AsyncClient, FakeRouter],
) -> None:
    client, _ = api
    async with get_sessionmaker()() as session:
        for account, symbol, day in [("TEST-A", "MSFT", 27), ("TEST-B", "AAPL", 28)]:
            instrument = Instrument(symbol=symbol, kind="stock", currency="USD", source="test")
            session.add(instrument)
            await session.flush()
            session.add(
                Position(
                    account_id=account,
                    instrument_id=instrument.id,
                    report_date=date(2026, 10, day),
                    quantity=Decimal("0.125"),
                    currency="USD",
                    market_value=Decimal("10"),
                    source="test",
                )
            )
        await session.commit()
    response = await client.get("/portfolio")
    assert response.status_code == 200
    assert {row["symbol"] for row in response.json()["positions"]} == {"MSFT", "AAPL"}


async def test_watchlist_exposes_unknown_currency_without_guessing(
    api: tuple[httpx.AsyncClient, FakeRouter],
) -> None:
    client, _ = api
    response = await client.post("/watchlist", json={"symbol": "UNKNOWN"})
    assert response.status_code == 201
    row = response.json()
    assert "currency" in row and row["currency"] is None
    assert row["identity_status"] == "unresolved"
    assert row["metrics"]["forward_pe"]["meta"]["availability"] == "missing"


async def test_empty_complete_snapshot_does_not_revive_old_positions(
    api: tuple[httpx.AsyncClient, FakeRouter],
) -> None:
    from preza.domain.portfolio import AccountSnapshotIn, FlexStatement, PositionIn
    from preza.services.portfolio import store_statement

    client, _ = api
    async with get_sessionmaker()() as session:
        await store_statement(
            session,
            FlexStatement(
                positions=[
                    PositionIn(
                        account_id="EMPTY",
                        symbol="MSFT",
                        quantity=Decimal("0.125"),
                        currency="USD",
                        report_date=date(2026, 10, 27),
                    )
                ],
                cash=[],
                trades=[],
            ),
        )
        await store_statement(
            session,
            FlexStatement(
                positions=[],
                cash=[],
                trades=[],
                snapshots=[
                    AccountSnapshotIn(
                        account_id="EMPTY", report_date=date(2026, 10, 28), positions_complete=True
                    )
                ],
            ),
        )
        await session.commit()
    response = (await client.get("/portfolio", params={"account_id": "EMPTY"})).json()
    assert response["positions"] == []
    assert response["as_of"] == "2026-10-28"
    assert response["accounts"] == ["EMPTY"]


async def test_undo_restores_original_watchlist_identity_and_basis(
    api: tuple[httpx.AsyncClient, FakeRouter],
) -> None:
    client, _ = api
    original = (
        await client.post(
            "/watchlist",
            json={
                "symbol": "MSFT",
                "tags": ["long-term"],
                "alert_below": 120,
                "note": "Keep evidence",
            },
        )
    ).json()
    assert (
        await client.delete(f"/watchlist/{original['id']}?revision={original['revision']}")
    ).status_code == 204
    assert (await client.get("/watchlist")).json() == []
    restored = await client.post(
        f"/watchlist/{original['id']}/restore", json={"expected_revision": original["revision"] + 1}
    )
    assert restored.status_code == 200
    for field in ("id", "added_at", "added_price", "tags", "note", "alert_below"):
        assert restored.json()[field] == original[field]
    assert (
        await client.post(
            f"/watchlist/{original['id']}/restore",
            json={"expected_revision": original["revision"] + 1},
        )
    ).status_code == 409
