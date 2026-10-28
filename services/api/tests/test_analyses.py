"""Deep analysis API: queue a run, read it back, stream its steps (BL-080, BL-082)."""

import uuid
from datetime import date
from typing import Any

import pytest
from sqlalchemy import select

from preza import db
from preza.models import AnalysisRun, AnalysisStep, Instrument
from preza.services import analyses as analyses_service

pytestmark = pytest.mark.db


async def _instrument(symbol: str, kind: str = "stock") -> None:
    async with db.get_sessionmaker()() as session:
        session.add(Instrument(symbol=symbol, name=f"{symbol} Inc", kind=kind, source="test"))
        await session.commit()


async def test_create_list_and_get(api: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    client, _ = api
    queued: list[tuple[str, str | None, str | None]] = []

    async def fake_enqueue(settings, job, *args, job_id=None, queue_name=None):  # type: ignore[no-untyped-def]
        queued.append((job, job_id, queue_name))
        return job_id

    monkeypatch.setattr(analyses_service, "enqueue", fake_enqueue)
    await _instrument("ASML")
    await _instrument("VWRA", kind="etf")

    resp = await client.post("/analyses", json={"symbol": "asml", "trade_date": "2026-10-20"})
    assert resp.status_code == 202
    run = resp.json()
    assert run["symbol"] == "ASML" and run["status"] == "queued"
    assert queued == [("deep_analysis", f"analysis:{run['id']}", "arq:agents")]

    etf = await client.post("/analyses", json={"symbol": "VWRA"})
    assert etf.status_code == 202 and etf.json()["engine"] == "etf"
    assert (await client.post("/analyses", json={"symbol": "NOPE"})).status_code == 404

    listed = (await client.get("/analyses", params={"symbol": "ASML"})).json()
    assert [r["id"] for r in listed] == [run["id"]]

    detail = (await client.get(f"/analyses/{run['id']}")).json()
    assert detail["steps"] == [] and detail["reports"] == {}
    assert detail["trade_date"] == "2026-10-20"


async def test_events_replay_and_end(api: Any) -> None:
    client, _ = api
    await _instrument("ASML")
    async with db.get_sessionmaker()() as session:
        instrument_id = await session.scalar(select(Instrument.id))
        run = AnalysisRun(
            instrument_id=instrument_id,
            engine="tradingagents",
            trade_date=date(2026, 10, 20),
            status="done",
            rating="Hold",
        )
        session.add(run)
        await session.flush()
        for seq, (agent, kind) in enumerate(
            [("system", "status"), ("market", "tool"), ("portfolio_manager", "decision")], 1
        ):
            session.add(AnalysisStep(run_id=run.id, seq=seq, agent=agent, kind=kind, content=""))
        await session.commit()
        run_id = run.id

    resp = await client.get(f"/analyses/{run_id}/events", headers={"Last-Event-ID": "1"})
    assert resp.headers["content-type"].startswith("text/event-stream")
    body = resp.text
    assert "id: 1\n" not in body
    assert "id: 2\nevent: step" in body and "id: 3\nevent: step" in body
    assert body.rstrip().endswith('data: {"status": "done"}')


async def test_deep_proposal_queues_an_agent_run(api: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    from preza import worker
    from preza.models import Proposal
    from tests.test_api_m2 import VerdictLlm

    client, _ = api
    queued: list[Any] = []

    async def fake_queue_run(settings: Any, run_id: Any) -> None:
        queued.append(run_id)

    llm = VerdictLlm()
    monkeypatch.setattr(worker, "llm_client", lambda: llm)
    monkeypatch.setattr(worker, "get_bars_service", lambda: None)
    monkeypatch.setattr(worker, "queue_run", fake_queue_run)
    await _instrument("ORCL")
    async with db.get_sessionmaker()() as session:
        proposal = Proposal(symbols=["ORCL"], hypothesis="Cloud backlog grows.", depth="deep")
        session.add(proposal)
        await session.commit()
        proposal_id = proposal.id

    assert await worker.analyze_proposal_job({}, str(proposal_id)) == "done"
    assert llm.roles == ["cloud-deep"]  # the quick verdict still comes first
    async with db.get_sessionmaker()() as session:
        run = await session.scalar(select(AnalysisRun))
        assert run is not None and queued == [run.id]
        assert run.hypothesis == "Cloud backlog grows." and run.proposal_id == proposal_id
        assert run.engine == "tradingagents" and run.status == "queued"

    out = (await client.get(f"/proposals/{proposal_id}")).json()
    assert out["analysis_id"] == str(run.id)


async def test_detail_carries_the_decision_card(api: Any) -> None:
    from preza.cli.seed_demo_analysis import CARD

    client, _ = api
    await _instrument("ASML")
    async with db.get_sessionmaker()() as session:
        run = AnalysisRun(
            instrument_id=await session.scalar(select(Instrument.id)),
            engine="tradingagents",
            trade_date=date(2026, 10, 20),
            status="done",
            rating="Overweight",
            card=CARD,
            models={"quick": "m-quick", "usage": {"calls": [], "prompt_tokens": 120}},
        )
        session.add(run)
        await session.commit()
    detail = (await client.get(f"/analyses/{run.id}")).json()
    card = detail["card"]
    assert card["size_class"] == "normal" and card["control"]["implied_rating"] == "Overweight"
    assert len(card["upgrade_if"]) == 2
    assert detail["models"]["usage"]["prompt_tokens"] == 120


async def test_daily_limit(api: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    from preza.config import get_settings

    client, _ = api

    async def fake_enqueue(*args: Any, **kwargs: Any) -> None:
        return None

    monkeypatch.setattr(analyses_service, "enqueue", fake_enqueue)
    monkeypatch.setenv("DEEP_DAILY_LIMIT", "2")
    get_settings.cache_clear()
    try:
        await _instrument("ASML")
        assert (await client.post("/analyses", json={"symbol": "ASML"})).status_code == 202
        first_id = (await client.get("/analyses")).json()[0]["id"]
        assert (await client.post("/analyses", json={"symbol": "ASML"})).status_code == 202
        over = await client.post("/analyses", json={"symbol": "ASML"})
        assert over.status_code == 429 and over.json()["detail"] == "daily_limit_reached"
        assert (await client.get("/analyses/quota")).json() == {"limit": 2, "used": 2}

        async with db.get_sessionmaker()() as session:  # a failed run gives its slot back
            run = await session.get(AnalysisRun, uuid.UUID(first_id))
            assert run is not None
            run.status = "failed"
            await session.commit()
        assert (await client.post("/analyses", json={"symbol": "ASML"})).status_code == 202
    finally:
        get_settings.cache_clear()
