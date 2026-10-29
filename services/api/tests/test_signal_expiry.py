"""Signal expiry must be applied before status filters and pagination."""

from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal
from uuid import UUID

import httpx
import pytest
from sqlalchemy import select

from preza.db import get_sessionmaker
from preza.models import Signal
from preza.services.instruments import get_or_create
from tests.conftest import FakeRouter

pytestmark = pytest.mark.db


async def seed_signals(status: str) -> tuple[str, str]:
    now = datetime.now(UTC)
    async with get_sessionmaker()() as session:
        instrument = await get_or_create(session, symbol="MSFT", source="test")
        rows = [
            Signal(
                instrument_id=instrument.id,
                kind="catalyst",
                source="manual",
                direction="up",
                horizon="months",
                strength=Decimal("0.5"),
                rationale="Test evidence",
                evidence=[],
                status=status,
                created_at=now - timedelta(minutes=index),
                expires_at=now + timedelta(days=days),
            )
            for index, days in enumerate((-1, 1))
        ]
        session.add_all(rows)
        await session.commit()
        return str(rows[0].id), str(rows[1].id)


@pytest.mark.parametrize("status", ["new", "watching"])
async def test_active_filter_excludes_expired_before_limit(
    api: tuple[httpx.AsyncClient, FakeRouter], status: str
) -> None:
    client, _ = api
    _, active_id = await seed_signals(status)

    response = await client.get("/signals", params={"status": status, "limit": 1})

    assert response.status_code == 200
    assert [(row["id"], row["status"]) for row in response.json()] == [(active_id, status)]


@pytest.mark.parametrize("status", ["new", "watching"])
async def test_expired_filter_finds_newly_expired_without_prior_read(
    api: tuple[httpx.AsyncClient, FakeRouter], status: str
) -> None:
    client, _ = api
    expired_id, _ = await seed_signals(status)

    response = await client.get("/signals", params={"status": "expired"})

    assert response.status_code == 200
    assert [(row["id"], row["status"]) for row in response.json()] == [(expired_id, "expired")]
    async with get_sessionmaker()() as session:
        stored = await session.get(Signal, UUID(expired_id))
        assert stored is not None and stored.status == "expired"


@pytest.mark.parametrize("status", ["accepted", "dismissed"])
async def test_expiry_preserves_user_decisions(
    api: tuple[httpx.AsyncClient, FakeRouter], status: str
) -> None:
    client, _ = api
    expired_id, active_id = await seed_signals(status)

    response = await client.get("/signals", params={"status": status})

    assert response.status_code == 200
    assert [(row["id"], row["status"]) for row in response.json()] == [
        (expired_id, status),
        (active_id, status),
    ]


async def test_unfiltered_read_expires_only_open_signals_and_persists(
    api: tuple[httpx.AsyncClient, FakeRouter],
) -> None:
    client, _ = api
    expired_id, active_id = await seed_signals("new")
    first = (await client.get("/signals")).json()
    second = (await client.get("/signals")).json()
    expected = [(expired_id, "expired"), (active_id, "new")]
    assert [(row["id"], row["status"]) for row in first] == expected
    assert [(row["id"], row["status"]) for row in second] == expected
    async with get_sessionmaker()() as session:
        stored = await session.get(Signal, UUID(expired_id))
        assert stored is not None and stored.status == "expired"


@pytest.mark.parametrize("offset", [None, -1, 0, 1])
async def test_expiry_boundary_uses_one_request_time(
    api: tuple[httpx.AsyncClient, FakeRouter], monkeypatch: pytest.MonkeyPatch, offset: int | None
) -> None:
    from preza.routes import signals

    client, _ = api
    now = datetime(2026, 10, 29, 12, tzinfo=UTC)

    class FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz: tzinfo | None = None) -> datetime:
            return now.astimezone(tz)

    expired_id, _ = await seed_signals("new")
    async with get_sessionmaker()() as session:
        stored = await session.get(Signal, UUID(expired_id))
        assert stored is not None
        stored.expires_at = None if offset is None else now + timedelta(seconds=offset)
        await session.commit()
    monkeypatch.setattr(signals, "datetime", FrozenDatetime)
    rows = (await client.get("/signals")).json()
    assert next(row for row in rows if row["id"] == expired_id)["status"] == (
        "expired" if offset == -1 else "new"
    )


async def test_kind_filter_does_not_hide_expiry_from_subsequent_query(
    api: tuple[httpx.AsyncClient, FakeRouter],
) -> None:
    client, _ = api
    expired_id, active_id = await seed_signals("watching")
    async with get_sessionmaker()() as session:
        stored = await session.get(Signal, UUID(expired_id))
        assert stored is not None
        stored.kind = "entry"
        await session.commit()
    rows = (await client.get("/signals", params={"kind": "catalyst", "limit": 1})).json()
    assert [row["id"] for row in rows] == [active_id]
    expired = (await client.get("/signals", params={"status": "expired", "kind": "entry"})).json()
    assert [row["id"] for row in expired] == [expired_id]


async def test_identical_creation_times_have_stable_descending_id_order(
    api: tuple[httpx.AsyncClient, FakeRouter],
) -> None:
    client, _ = api
    await seed_signals("accepted")
    async with get_sessionmaker()() as session:
        rows = list(await session.scalars(select(Signal).order_by(Signal.created_at.desc())))
        for row in rows:
            row.created_at = datetime(2026, 10, 29, tzinfo=UTC)
        await session.commit()
        expected = sorted((str(row.id) for row in rows), reverse=True)
    assert [row["id"] for row in (await client.get("/signals")).json()] == expected
