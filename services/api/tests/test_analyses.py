"""Deep analysis API: queue a run, read it back, stream its steps (BL-080, BL-082)."""

from datetime import date
from typing import Any

import pytest
from sqlalchemy import select

from preza import db
from preza.models import AnalysisRun, AnalysisStep, Instrument
from preza.routes import analyses

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

    monkeypatch.setattr(analyses, "enqueue", fake_enqueue)
    await _instrument("ASML")
    await _instrument("VWRA", kind="etf")

    resp = await client.post("/analyses", json={"symbol": "asml", "trade_date": "2026-10-20"})
    assert resp.status_code == 202
    run = resp.json()
    assert run["symbol"] == "ASML" and run["status"] == "queued"
    assert queued == [("deep_analysis", f"analysis:{run['id']}", "arq:agents")]

    assert (await client.post("/analyses", json={"symbol": "VWRA"})).status_code == 422
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
