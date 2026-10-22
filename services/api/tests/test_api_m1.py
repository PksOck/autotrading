from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import httpx
import pytest

from preza.broker.flex import parse_statement
from preza.domain.market import BarIn
from tests.conftest import FakeRouter

pytestmark = pytest.mark.db
FLEX_XML = (Path(__file__).parent / "fixtures" / "flex_statement.xml").read_text()


async def store_fixture_statement() -> None:
    from preza.db import get_sessionmaker
    from preza.services.portfolio import store_statement

    async with get_sessionmaker()() as session:
        await store_statement(session, parse_statement(FLEX_XML))
        await session.commit()


def bars_until_today(n: int, close: float = 100.0) -> list[BarIn]:
    """n weekday bars ending today, closes rising by 1 per day."""
    days: list[date] = []
    day = date.today()
    while len(days) < n:
        if day.weekday() < 5:
            days.append(day)
        day -= timedelta(days=1)
    out = []
    for i, d in enumerate(reversed(days)):
        c = Decimal(str(close + i))
        out.append(BarIn(day=d, open=c, high=c + 1, low=c - 1, close=c, volume=1000))
    return out


async def test_flex_statement_becomes_portfolio_and_is_idempotent(
    api: tuple[httpx.AsyncClient, FakeRouter],
) -> None:
    client, _ = api
    await store_fixture_statement()
    await store_fixture_statement()  # same statement again: no duplicates

    body = (await client.get("/portfolio")).json()
    assert body["as_of"] == "2026-10-21"
    assert [p["symbol"] for p in body["positions"]] == ["VWRA", "MSFT"]
    assert body["positions"][0]["kind"] == "etf"

    found = (await client.get("/instruments", params={"q": "vwr"})).json()
    assert found[0]["symbol"] == "VWRA" and found[0]["ucits"] is True


async def test_bars_are_fetched_once_and_served_from_db(
    api: tuple[httpx.AsyncClient, FakeRouter],
) -> None:
    client, router = api
    await store_fixture_statement()
    router.bars = bars_until_today(30)

    first = (await client.get("/instruments/MSFT/bars", params={"range": "1m"})).json()
    assert first["provenance"]["source"] == "fake"
    assert len(first["bars"]) >= 20
    second = await client.get("/instruments/MSFT/bars", params={"range": "1m"})
    assert second.status_code == 200
    assert len(router.calls) == 1, "fresh bars must not trigger another provider call"

    detail = (await client.get("/instruments/MSFT")).json()
    assert detail["last_close"] == first["bars"][-1]["close"]
    last, prev = first["bars"][-1]["close"], first["bars"][-2]["close"]
    assert detail["change_pct"] == pytest.approx((last / prev - 1) * 100)


async def test_failed_refresh_still_answers_and_is_audited(
    api: tuple[httpx.AsyncClient, FakeRouter],
) -> None:
    client, router = api
    await store_fixture_statement()
    router.bars = []
    response = await client.get("/instruments/VWRA/bars")
    assert response.status_code == 200 and response.json()["bars"] == []
    assert (await client.get("/instruments/NOPE/bars")).status_code == 404


async def test_watchlist_crud_and_since_added(api: tuple[httpx.AsyncClient, FakeRouter]) -> None:
    client, _ = api
    created = await client.post(
        "/watchlist", json={"symbol": "orcl", "tier": "reserve", "tags": ["ai", " "]}
    )
    assert created.status_code == 201
    item = created.json()
    assert item["symbol"] == "ORCL" and item["tags"] == ["ai"] and item["added_price"] is None
    assert (await client.post("/watchlist", json={"symbol": "ORCL"})).status_code == 409

    patched = await client.patch(
        f"/watchlist/{item['id']}", json={"tier": "active", "reviewed": True, "alert_below": 140}
    )
    assert (
        patched.json()["tier"] == "active"
        and patched.json()["reviewed_at"]
        and patched.json()["alert_below"] == 140
    )

    assert len((await client.get("/watchlist")).json()) == 1
    assert (await client.delete(f"/watchlist/{item['id']}")).status_code == 204
    assert (await client.get("/watchlist")).json() == []


async def test_sync_requires_flex_configuration(api: tuple[httpx.AsyncClient, FakeRouter]) -> None:
    client, _ = api
    response = await client.post("/portfolio/sync")
    assert response.status_code == 409 and response.json()["detail"] == "flex_unconfigured"
