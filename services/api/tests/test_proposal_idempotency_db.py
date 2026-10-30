"""Acceptance survives a lost response; workers and providers remain test doubles."""

import asyncio
import uuid
from typing import Any

import httpx
import pytest
from sqlalchemy import func, select

from preza import db, worker
from preza.models import AnalysisRun, Instrument, Proposal, Signal
from preza.routes import proposals
from tests.test_api_m2 import VerdictLlm

pytestmark = pytest.mark.db


async def test_lost_acceptance_reply_reuses_one_proposal_and_deep_analysis(
    api: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, _ = api
    accepted: list[str] = []
    analyses: list[uuid.UUID] = []
    llm = VerdictLlm()

    async def enqueue(settings: Any, job: str, proposal_id: str, **kwargs: Any) -> str:
        accepted.append(proposal_id)
        return str(kwargs["job_id"])

    async def queue_run(settings: Any, run_id: uuid.UUID) -> None:
        analyses.append(run_id)

    monkeypatch.setattr(proposals, "enqueue", enqueue)
    monkeypatch.setattr(worker, "llm_client", lambda: llm)
    monkeypatch.setattr(worker, "get_bars_service", lambda: None)
    monkeypatch.setattr(worker, "queue_run", queue_run)
    async with db.get_sessionmaker()() as session:
        session.add(Instrument(symbol="ORCL", kind="stock", currency="USD", source="synthetic"))
        await session.commit()

    request_id = str(uuid.uuid4())
    body = {
        "request_id": request_id,
        "symbols": ["ORCL"],
        "hypothesis": "Synthetic",
        "depth": "deep",
    }
    original_send = client.send
    dropped = False

    async def lose_first_reply(request: httpx.Request, **kwargs: Any) -> httpx.Response:
        nonlocal dropped
        response = await original_send(request, **kwargs)
        if request.method == "POST" and request.url.path == "/proposals" and not dropped:
            dropped = True
            assert response.status_code == 202
            raise httpx.ReadError("synthetic lost acceptance reply", request=request)
        return response

    monkeypatch.setattr(client, "send", lose_first_reply)
    with pytest.raises(httpx.ReadError, match="synthetic lost"):
        await client.post("/proposals", json=body)
    recovered = await client.get(f"/proposals/{request_id}")
    assert recovered.status_code == 200 and recovered.json()["id"] == request_id
    assert (await client.post("/proposals", json=body)).json()["id"] == request_id
    assert accepted == [request_id]
    assert await worker.analyze_proposal_job({}, request_id) == "done"
    assert (await client.post("/proposals", json=body)).json()["id"] == request_id
    assert llm.roles == ["cloud-deep"]
    assert len(analyses) == 1
    async with db.get_sessionmaker()() as session:
        assert await session.scalar(select(func.count()).select_from(Proposal)) == 1
        assert await session.scalar(select(func.count()).select_from(AnalysisRun)) == 1
        assert await session.scalar(select(func.count()).select_from(Signal)) == 1


async def test_concurrent_same_id_accepts_once_and_conflicting_body_keeps_original(
    api: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, _ = api
    queued: list[str] = []

    async def enqueue(settings: Any, job: str, proposal_id: str, **kwargs: Any) -> str:
        queued.append(proposal_id)
        return str(kwargs["job_id"])

    monkeypatch.setattr(proposals, "enqueue", enqueue)
    request_id = str(uuid.uuid4())
    body = {"request_id": request_id, "symbols": ["orcl"], "hypothesis": "Original"}
    responses = await asyncio.gather(*(client.post("/proposals", json=body) for _ in range(2)))
    assert [response.status_code for response in responses] == [202, 202]
    assert all(response.json()["id"] == request_id for response in responses)
    conflict = await client.post("/proposals", json={**body, "hypothesis": "Changed"})
    assert conflict.status_code == 409 and conflict.json()["detail"] == "idempotency_conflict"
    original = await client.get(f"/proposals/{request_id}")
    assert original.json()["hypothesis"] == "Original"
    assert queued == [request_id]
    async with db.get_sessionmaker()() as session:
        assert await session.scalar(select(func.count()).select_from(Proposal)) == 1
