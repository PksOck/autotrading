from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select, update

from preza.config import get_settings
from preza.db import get_sessionmaker
from preza.models_auth import OwnerSession
from preza.services.owner_access import hash_password

pytestmark = pytest.mark.db
ORIGIN = "https://preza.example.test"
PASSWORD = "synthetic owner testing password"


def configure(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("APP_BASE_URL", ORIGIN)
    monkeypatch.setenv("OWNER_PASSWORD_HASH", hash_password(PASSWORD))
    get_settings.cache_clear()


async def test_direct_api_login_origin_logout_and_opaque_storage(api, monkeypatch):
    client, _ = api
    configure(monkeypatch)
    assert (await client.get("/portfolio")).status_code == 401
    assert (await client.get("/docs")).status_code == 401
    assert (
        await client.get("/analyses/00000000-0000-0000-0000-000000000000/events")
    ).status_code == 401
    assert (await client.get("/auth/session")).json()["authenticated"] is False
    body = {"username": "owner", "password": PASSWORD}
    for origin in [None, "https://evil.example", ORIGIN + ".evil"]:
        assert (
            await client.post(
                "/auth/login", json=body, headers={"Origin": origin} if origin else {}
            )
        ).status_code == 403
    response = await client.post("/auth/login", json=body, headers={"Origin": ORIGIN})
    assert response.status_code == 200
    cookie = response.headers["set-cookie"]
    assert "HttpOnly" in cookie and "Secure" in cookie and "SameSite=strict" in cookie
    token = response.cookies.get("__Host-preza_session")
    # httpx uses an HTTP test URL; forward the secure cookie explicitly.
    client.headers["Cookie"] = f"__Host-preza_session={token}"
    async with get_sessionmaker()() as db:
        row = await db.scalar(select(OwnerSession))
        assert row is not None and row.token_hash != token and PASSWORD not in row.token_hash
    assert (await client.get("/portfolio")).status_code == 200
    assert (await client.post("/auth/logout")).status_code == 403
    assert (await client.post("/auth/logout", headers={"Origin": ORIGIN})).status_code == 204
    assert (await client.get("/portfolio")).status_code == 401


@pytest.mark.parametrize("reason", ["absolute", "idle", "rotation"])
async def test_session_expiry_and_credential_rotation(api, monkeypatch, reason):
    client, _ = api
    configure(monkeypatch)
    response = await client.post(
        "/auth/login", json={"username": "owner", "password": PASSWORD}, headers={"Origin": ORIGIN}
    )
    client.headers["Cookie"] = (
        f"__Host-preza_session={response.cookies.get('__Host-preza_session')}"
    )
    async with get_sessionmaker()() as db:
        if reason == "absolute":
            await db.execute(
                update(OwnerSession).values(expires_at=datetime.now(UTC) - timedelta(seconds=1))
            )
        elif reason == "idle":
            await db.execute(
                update(OwnerSession).values(last_seen_at=datetime.now(UTC) - timedelta(hours=1))
            )
        await db.commit()
    if reason == "rotation":
        monkeypatch.setenv("OWNER_PASSWORD_HASH", hash_password(PASSWORD + "changed"))
        get_settings.cache_clear()
    assert (await client.get("/portfolio")).status_code == 401


async def test_global_throttle_cannot_be_bypassed_by_forwarded_ip(api, monkeypatch):
    client, _ = api
    configure(monkeypatch)
    for i in range(6):
        response = await client.post(
            "/auth/login",
            json={"username": "owner", "password": "wrong"},
            headers={"Origin": ORIGIN, "X-Forwarded-For": f"192.0.2.{i}"},
        )
        assert response.status_code == (401 if i < 5 else 429)


async def test_production_cannot_disable_auth_or_use_missing_secrets(api, monkeypatch):
    client, _ = api
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("AUTH_ENABLED", "false")
    monkeypatch.delenv("OWNER_PASSWORD_HASH", raising=False)
    get_settings.cache_clear()
    assert (await client.get("/portfolio")).status_code == 503
    assert (await client.get("/health")).status_code == 200


async def test_parallel_attempt_reservations_are_globally_bounded(api):
    import asyncio

    from preza.services.owner_access import reserve_attempt

    assert sum(await asyncio.gather(*(reserve_attempt() for _ in range(12)))) == 5


async def test_background_polls_do_not_extend_idle_but_explicit_activity_does(api, monkeypatch):
    client, _ = api
    configure(monkeypatch)
    response = await client.post(
        "/auth/login", json={"username": "owner", "password": PASSWORD}, headers={"Origin": ORIGIN}
    )
    client.headers["Cookie"] = (
        f"__Host-preza_session={response.cookies.get('__Host-preza_session')}"
    )
    past = datetime.now(UTC) - timedelta(minutes=20)
    async with get_sessionmaker()() as db:
        await db.execute(update(OwnerSession).values(last_seen_at=past))
        await db.commit()
    for path in ["/auth/session", "/portfolio"]:
        assert (await client.get(path)).status_code == 200
    async with get_sessionmaker()() as db:
        assert (await db.scalar(select(OwnerSession))).last_seen_at == past
    assert (await client.post("/auth/activity", headers={"Origin": ORIGIN})).status_code == 204
    async with get_sessionmaker()() as db:
        assert (await db.scalar(select(OwnerSession))).last_seen_at > past
