"""Direct links address a signal independently of the inbox page or filter."""

from uuid import uuid4

import httpx
import pytest

from tests.conftest import FakeRouter
from tests.test_signal_expiry import seed_signals

pytestmark = pytest.mark.db


async def test_signal_detail_reads_beyond_default_page(
    api: tuple[httpx.AsyncClient, FakeRouter],
) -> None:
    from datetime import UTC, datetime, timedelta
    from decimal import Decimal
    from uuid import UUID

    from preza.db import get_sessionmaker
    from preza.models import Signal

    client, _ = api
    _, signal_id = await seed_signals("accepted")
    async with get_sessionmaker()() as session:
        original = await session.get(Signal, UUID(signal_id))
        assert original is not None
        session.add_all(
            [
                Signal(
                    instrument_id=original.instrument_id,
                    kind="catalyst",
                    source="manual",
                    direction="up",
                    horizon="months",
                    strength=Decimal("0.5"),
                    rationale="Newer fixture",
                    evidence=[],
                    status="accepted",
                    created_at=datetime.now(UTC) + timedelta(seconds=index),
                )
                for index in range(101)
            ]
        )
        await session.commit()
    listed = (await client.get("/signals")).json()
    assert len(listed) == 100
    assert signal_id not in [row["id"] for row in listed]
    detail = await client.get(f"/signals/{signal_id}")
    assert detail.status_code == 200
    assert detail.json()["id"] == signal_id


@pytest.mark.parametrize("status", ["accepted", "dismissed", "expired"])
async def test_signal_detail_ignores_inbox_status(
    api: tuple[httpx.AsyncClient, FakeRouter], status: str
) -> None:
    client, _ = api
    signal_id, _ = await seed_signals(status)
    assert (await client.get("/signals", params={"status": "new"})).json() == []
    response = await client.get(f"/signals/{signal_id}")
    assert response.status_code == 200
    assert response.json()["id"] == signal_id
    assert response.json()["status"] == status


async def test_signal_detail_normalizes_expiry_like_list(
    api: tuple[httpx.AsyncClient, FakeRouter],
) -> None:
    client, _ = api
    signal_id, _ = await seed_signals("watching")
    response = await client.get(f"/signals/{signal_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "expired"
    listed = (await client.get("/signals", params={"status": "expired"})).json()
    assert listed == [response.json()]


async def test_signal_detail_preserves_rumor_evidence_without_accepting(
    api: tuple[httpx.AsyncClient, FakeRouter],
) -> None:
    from uuid import UUID

    from preza.db import get_sessionmaker
    from preza.models import Signal

    client, _ = api
    _, signal_id = await seed_signals("watching")
    evidence = [{"kind": "news", "label": "Original source", "url": "https://example.test/news"}]
    async with get_sessionmaker()() as session:
        signal = await session.get(Signal, UUID(signal_id))
        assert signal is not None
        signal.is_rumor = True
        signal.evidence = evidence
        await session.commit()
    response = await client.get(f"/signals/{signal_id}")
    assert response.status_code == 200
    assert response.json()["is_rumor"] is True
    assert response.json()["status"] == "watching"
    assert response.json()["evidence"][0]["url"] == evidence[0]["url"]


async def test_signal_detail_reports_missing_and_malformed_id(
    api: tuple[httpx.AsyncClient, FakeRouter],
) -> None:
    client, _ = api
    missing = await client.get(f"/signals/{uuid4()}")
    assert missing.status_code == 404
    assert missing.json()["detail"] == "signal_not_found"
    assert (await client.get("/signals/not-a-uuid")).status_code == 422
