"""Identity enrichment is explicit, listing-safe and never invents security facts."""

from datetime import UTC, datetime

import httpx
import pytest

from preza import db
from preza.models import Fundamentals, Instrument

pytestmark = pytest.mark.db


async def seed() -> int:
    async with db.get_sessionmaker()() as session:
        row = Instrument(symbol="SYNTH", kind="unknown", source="test")
        session.add(row)
        await session.flush()
        session.add(
            Fundamentals(
                instrument_id=row.id,
                as_of=datetime.now(UTC).date(),
                source="synthetic",
                metrics={"pe": "12.5"},
                metrics_meta={"pe": {"basis": "TTM", "source_field": "peTTM"}},
            )
        )
        await session.commit()
        return row.id


async def test_detail_exposes_stored_metrics_and_identity_without_provider_fetch(api):
    client, bars = api
    identity = await seed()
    response = await client.get("/instruments/SYNTH")
    assert response.status_code == 200
    data = response.json()
    assert data["instrument_id"] == identity
    assert data["identity_status"] == "unresolved"
    assert data["metrics"]["pe"]["value"] == "12.5"
    assert data["metrics"]["pe"]["meta"]["source_field"] == "peTTM"
    assert data["currency"] is None and data["kind"] == "unknown"
    assert not bars.calls


async def test_explicit_enrichment_matches_ticker_and_preserves_unproven_fields(api, monkeypatch):
    from preza.services import identity

    client, _ = api
    instrument_id = await seed()
    calls = []

    async def profile(symbol, settings):
        calls.append(symbol)
        return identity.CompanyProfile(
            ticker="SYNTH", name="Synthetic Company", currency="USD", exchange="XNAS"
        )

    monkeypatch.setattr(identity, "fetch_profile", profile)
    before = (await client.get("/instruments/SYNTH")).json()
    response = await client.post(
        "/instruments/SYNTH/identity/enrich",
        json={
            "instrument_id": instrument_id,
            "expected_updated_at": before["identity_updated_at"],
        },
    )
    assert response.status_code == 200, response.text
    after = (await client.get("/instruments/SYNTH")).json()
    assert calls == ["SYNTH"]
    assert after["name"] == "Synthetic Company" and after["exchange"] == "XNAS"
    assert after["currency"] is None and after["kind"] == "unknown"
    assert after["identity_source"] == "finnhub_profile2"
    assert after["identity_updated_at"] != before["identity_updated_at"]
    stale = await client.post(
        "/instruments/SYNTH/identity/enrich",
        json={
            "instrument_id": instrument_id,
            "expected_updated_at": before["identity_updated_at"],
        },
    )
    assert stale.status_code == 409
    assert calls == ["SYNTH"]


async def test_mismatch_and_duplicate_listings_do_not_mutate(api, monkeypatch):
    from preza.services import identity

    client, _ = api
    instrument_id = await seed()

    async def profile(symbol, settings):
        return identity.CompanyProfile(ticker="OTHER", name="Wrong issuer", exchange="XNAS")

    monkeypatch.setattr(identity, "fetch_profile", profile)
    before = (await client.get("/instruments/SYNTH")).json()
    body = {"instrument_id": instrument_id, "expected_updated_at": before["identity_updated_at"]}
    response = await client.post("/instruments/SYNTH/identity/enrich", json=body)
    assert response.status_code == 409 and response.json()["detail"] == "identity_symbol_mismatch"
    assert (await client.get("/instruments/SYNTH")).json() == before
    async with db.get_sessionmaker()() as session:
        session.add(Instrument(symbol="SYNTH", exchange="OTHER", kind="stock", source="test"))
        await session.commit()
    response = await client.post("/instruments/SYNTH/identity/enrich", json=body)
    assert response.status_code == 409 and response.json()["detail"] == "identity_ambiguous"


async def test_long_exchange_is_not_truncated_and_noop_preserves_provenance(api, monkeypatch):
    from preza.services import identity

    client, _ = api
    instrument_id = await seed()

    async def profile(symbol, settings):
        return identity.CompanyProfile(
            ticker="SYNTH", exchange="NASDAQ NMS - GLOBAL MARKET", currency="USD"
        )

    monkeypatch.setattr(identity, "fetch_profile", profile)
    before = (await client.get("/instruments/SYNTH")).json()
    response = await client.post(
        "/instruments/SYNTH/identity/enrich",
        json={
            "instrument_id": instrument_id,
            "expected_updated_at": before["identity_updated_at"],
        },
    )
    assert response.status_code == 200
    assert response.json()["changed_fields"] == []
    assert "exchange_label_requires_mapping" in response.json()["gaps"]
    assert (await client.get("/instruments/SYNTH")).json() == before


async def test_missing_connection_returns_explicit_error_without_mutation(api, monkeypatch):
    from preza.config import get_settings

    client, _ = api
    instrument_id = await seed()
    monkeypatch.setattr(get_settings(), "finnhub_api_key", "")
    before = (await client.get("/instruments/SYNTH")).json()
    response = await client.post(
        "/instruments/SYNTH/identity/enrich",
        json={
            "instrument_id": instrument_id,
            "expected_updated_at": before["identity_updated_at"],
        },
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "identity_unconfigured"
    assert (await client.get("/instruments/SYNTH")).json() == before


@pytest.mark.parametrize("status", [401, 429, 500])
async def test_provider_errors_are_safe(status):
    from preza.config import Settings
    from preza.services.identity import IdentityError, fetch_profile

    async def handler(request):
        assert "token" not in request.url.query.decode()
        return httpx.Response(status, json={"error": "secret-provider-body"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(IdentityError) as caught:
            await fetch_profile("SYNTH", Settings(finnhub_api_key="private"), client=client)
    assert "secret" not in str(caught.value) and "private" not in str(caught.value)
