from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from preza.routes import portfolio

XML = (Path(__file__).parent / "fixtures" / "flex_statement.xml").read_bytes()


@pytest.mark.db
async def test_import_statement(api, monkeypatch):  # type: ignore[no-untyped-def]
    client, _ = api
    queue = AsyncMock(return_value=None)
    monkeypatch.setattr(portfolio, "enqueue", queue)
    response = await client.post(
        "/portfolio/import", content=XML, headers={"Content-Type": "application/xml"}
    )
    assert response.status_code == 200
    counts = response.json()["counts"]
    assert {key: counts[key] for key in ("positions", "trades", "cash")} == {
        "positions": 2,
        "trades": 1,
        "cash": 2,
    }
    assert counts["dividend_coverage"] == 4
    result = (await client.get("/portfolio")).json()
    assert {p["symbol"] for p in result["positions"]} == {"MSFT", "VWRA"}
    assert result["last_sync"]["detail"].startswith("file:")
    assert result["last_sync"]["status"] == "ok"
    assert response.json()["as_of"] == result["as_of"]
    queue.assert_awaited_once()
    assert queue.call_args.args[1] == "refresh_bars"


@pytest.mark.db
@pytest.mark.parametrize(
    ("body", "status", "detail"),
    [
        (b"<broken", 422, "flex_invalid"),
        (b"\xff", 422, "flex_invalid"),
        (b"", 400, "flex_empty"),
        (b"x" * (10 * 1024 * 1024 + 1), 413, "flex_too_large"),
        (
            b'<!DOCTYPE x [<!ENTITY a "secret"><!ENTITY b "&a;&a;">]><x>&b;</x>',
            422,
            "flex_invalid",
        ),
    ],
    ids=["malformed", "encoding", "empty", "oversized", "entities"],
)
async def test_invalid_import(api, body, status, detail):  # type: ignore[no-untyped-def]
    client, _ = api
    response = await client.post(
        "/portfolio/import", content=body, headers={"Content-Type": "text/xml"}
    )
    assert response.status_code == status
    assert response.json() == {"detail": detail}
    result = (await client.get("/portfolio")).json()
    assert result["positions"] == []
    assert result["cash"] == []
    if status == 422:
        assert result["last_sync"]["status"] == "failed"
        assert result["last_sync"]["detail"] == "flex_invalid"


@pytest.mark.parametrize(
    ("body", "status"),
    [
        (b"<broken", 422),
        (b"\xff", 422),
        (b"<unrelated/>", 422),
        (b"", 400),
        (b"x" * (10 * 1024 * 1024 + 1), 413),
        (b'<!DOCTYPE x [<!ENTITY a "secret">]><x>&a;</x>', 422),
    ],
    ids=["malformed", "encoding", "unrelated", "empty", "oversized", "entities"],
)
async def test_rejected_before_storage(body, status, monkeypatch):  # type: ignore[no-untyped-def]
    from fastapi import HTTPException
    from starlette.requests import Request

    async def receive():  # type: ignore[no-untyped-def]
        return {"type": "http.request", "body": body}

    request = Request({"type": "http", "headers": [(b"content-type", b"application/xml")]}, receive)
    session = AsyncMock()
    store = AsyncMock()
    audit = AsyncMock()
    monkeypatch.setattr(portfolio, "store_statement", store)
    monkeypatch.setattr(portfolio, "record_sync", audit)
    with pytest.raises(HTTPException) as exc:
        await portfolio.import_statement(request, session, AsyncMock())
    assert exc.value.status_code == status
    store.assert_not_awaited()
    if status == 422:
        assert exc.value.detail == "flex_invalid"
        audit.assert_awaited_once_with(session, "flex", "failed", "flex_invalid")
        session.commit.assert_awaited_once()


@pytest.mark.parametrize("content_type", [b"text/xml", b"application/xml", b"application/json"])
async def test_success_commits_before_optional_queue(monkeypatch, content_type):  # type: ignore[no-untyped-def]
    from starlette.requests import Request

    async def receive():  # type: ignore[no-untyped-def]
        return {"type": "http.request", "body": XML}

    session = AsyncMock()
    store = AsyncMock(return_value={"positions": 2, "trades": 1, "cash": 2})
    audit = AsyncMock()

    async def unavailable_queue(settings, job, **kwargs):  # type: ignore[no-untyped-def]
        session.commit.assert_awaited_once()
        assert job == "refresh_bars"
        assert kwargs["job_id"].startswith("refresh_bars:manual:")
        return None

    monkeypatch.setattr(portfolio, "store_statement", store)
    monkeypatch.setattr(portfolio, "record_sync", audit)
    monkeypatch.setattr(portfolio, "enqueue", unavailable_queue)
    request = Request({"type": "http", "headers": [(b"content-type", content_type)]}, receive)
    result = await portfolio.import_statement(request, session, AsyncMock())
    assert result.counts == {"positions": 2, "trades": 1, "cash": 2}
    assert result.as_of is not None
    audit.assert_awaited_once_with(session, "flex", "ok", "file: positions=2, trades=1, cash=2")


async def test_streamed_oversized_body_stops_early(monkeypatch):  # type: ignore[no-untyped-def]
    from fastapi import HTTPException
    from starlette.requests import Request

    chunk = b"x" * (4 * 1024 * 1024)
    sent = 0

    async def receive():  # type: ignore[no-untyped-def]
        nonlocal sent
        sent += 1
        return {"type": "http.request", "body": chunk, "more_body": sent < 10}

    store = AsyncMock()
    monkeypatch.setattr(portfolio, "store_statement", store)
    request = Request({"type": "http", "headers": []}, receive)
    with pytest.raises(HTTPException) as exc:
        await portfolio.import_statement(request, AsyncMock(), AsyncMock())
    assert exc.value.status_code == 413
    assert sent == 3
    store.assert_not_awaited()


async def test_declared_oversized_length_is_rejected_unread():  # type: ignore[no-untyped-def]
    from fastapi import HTTPException
    from starlette.requests import Request

    async def receive():  # type: ignore[no-untyped-def]
        pytest.fail("body must not be read")

    headers = [(b"content-length", str(10 * 1024 * 1024 + 1).encode())]
    with pytest.raises(HTTPException) as exc:
        await portfolio.import_statement(
            Request({"type": "http", "headers": headers}, receive), AsyncMock(), AsyncMock()
        )
    assert exc.value.status_code == 413


@pytest.mark.db
async def test_reimport_does_not_duplicate(api, monkeypatch):  # type: ignore[no-untyped-def]
    client, _ = api
    monkeypatch.setattr(portfolio, "enqueue", AsyncMock(return_value=None))
    headers = {"Content-Type": "application/xml"}
    first = await client.post("/portfolio/import", content=XML, headers=headers)
    second = await client.post("/portfolio/import", content=XML, headers=headers)
    assert first.status_code == second.status_code == 200
    assert second.json()["counts"]["trades"] == 0
    positions = (await client.get("/portfolio")).json()["positions"]
    assert sorted(p["symbol"] for p in positions) == ["MSFT", "VWRA"]


@pytest.mark.db
async def test_entity_inside_statement_rejected(api):  # type: ignore[no-untyped-def]
    client, _ = api
    doctype = '<!DOCTYPE FlexQueryResponse [<!ENTITY s "MSFT">]>\n'
    payload = doctype + XML.decode().replace('symbol="MSFT"', 'symbol="&s;"', 1)
    response = await client.post(
        "/portfolio/import", content=payload.encode(), headers={"Content-Type": "text/xml"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "flex_invalid"}
    assert (await client.get("/portfolio")).json()["positions"] == []
