"""Research read contracts, filtering before pagination and safe proposal output."""

import uuid
from datetime import UTC, date, datetime, timedelta
from typing import Any

import pytest

from preza import db
from preza.models import AnalysisRun, Instrument, Proposal

pytestmark = pytest.mark.db


async def test_latest_success_precedes_partition_and_limit(api: Any) -> None:
    client, _ = api
    now = datetime.now(UTC)
    async with db.get_sessionmaker()() as session:
        instrument = Instrument(symbol="ASML", source="test", kind="stock")
        other = Instrument(symbol="VWRA", source="test", kind="etf")
        session.add_all([instrument, other])
        await session.flush()
        success = AnalysisRun(
            instrument_id=instrument.id,
            engine="stock",
            trade_date=date.today(),
            status="done",
            created_at=now - timedelta(days=2),
        )
        session.add(success)
        session.add_all(
            AnalysisRun(
                instrument_id=instrument.id,
                engine="stock",
                trade_date=date.today(),
                status="failed",
                created_at=now - timedelta(minutes=i),
            )
            for i in range(105)
        )
        session.add(
            AnalysisRun(
                instrument_id=other.id,
                engine="etf",
                trade_date=date.today(),
                status="done",
                created_at=now - timedelta(days=1),
            )
        )
        await session.commit()
        success_id = str(success.id)
    rows = (await client.get("/analyses?status=done&latest_per_instrument=true&limit=100")).json()
    assert [r["symbol"] for r in rows] == ["VWRA", "ASML"]
    assert rows[1]["id"] == success_id
    assert len((await client.get("/analyses?latest_per_instrument=true")).json()) == 2
    assert (await client.get("/analyses?limit=0")).status_code == 422


async def test_analysis_stable_tie_order(api: Any) -> None:
    client, _ = api
    now = datetime.now(UTC)
    ids = [uuid.UUID(int=i) for i in (1, 2, 3)]
    async with db.get_sessionmaker()() as session:
        instrument = Instrument(symbol="ASML", source="test", kind="stock")
        session.add(instrument)
        await session.flush()
        session.add_all(
            AnalysisRun(
                id=i,
                instrument_id=instrument.id,
                engine="stock",
                trade_date=date.today(),
                status="done",
                created_at=now,
            )
            for i in ids
        )
        await session.commit()
    rows = (await client.get("/analyses?limit=2")).json()
    assert [r["id"] for r in rows] == [str(i) for i in reversed(ids[1:])]


@pytest.mark.parametrize(
    "status,verdict",
    [
        ("failed", '{"summary":"llm_unavailable: private provider body token=secret"}'),
        ("done", "not JSON private traceback"),
        ("done", '{"summary":"looks valid but lacks verdict"}'),
    ],
)
async def test_proposal_errors_are_never_results(api: Any, status: str, verdict: str) -> None:
    client, _ = api
    async with db.get_sessionmaker()() as session:
        proposal = Proposal(symbols=["ASML"], status=status, verdict=verdict)
        session.add(proposal)
        await session.commit()
        proposal_id = str(proposal.id)
    body = (await client.get(f"/proposals/{proposal_id}")).json()
    assert body["verdict"] is None
    assert body["verdict_result"] is None
    assert body["error_code"] in {"analysis_failed", "invalid_result"}
    assert "private" not in str(body)


async def test_proposal_request_id_and_retry_are_idempotent(api: Any, monkeypatch: Any) -> None:
    from preza.routes import proposals

    client, _ = api
    queued = []

    async def enqueue(*args: Any, **kwargs: Any) -> None:
        queued.append(args)

    monkeypatch.setattr(proposals, "enqueue", enqueue)
    request_id = str(uuid.uuid4())
    payload = {"symbols": ["asml"], "hypothesis": "Growth", "request_id": request_id}
    first = await client.post("/proposals", json=payload)
    second = await client.post("/proposals", json=payload)
    assert first.status_code == second.status_code == 202
    assert first.json()["id"] == second.json()["id"] == request_id
    assert len(queued) == 1
    assert (
        await client.post("/proposals", json={**payload, "hypothesis": "Changed"})
    ).status_code == 409
    async with db.get_sessionmaker()() as session:
        proposal = await session.get(Proposal, uuid.UUID(request_id))
        proposal.status = "failed"
        await session.commit()
    assert (await client.post(f"/proposals/{request_id}/retry")).json()["status"] == "queued"
    assert (await client.post(f"/proposals/{request_id}/retry")).json()["status"] == "queued"
    assert len(queued) == 2


async def test_performance_cohort_is_signal_creation_not_outcome_date(api: Any) -> None:
    from decimal import Decimal

    from preza.models import Signal, SignalOutcome

    client, _ = api
    async with db.get_sessionmaker()() as session:
        instrument = Instrument(symbol="ASML", source="test", kind="stock")
        session.add(instrument)
        await session.flush()
        for day, ret in [(1, "4"), (15, "-2")]:
            signal = Signal(
                instrument_id=instrument.id,
                kind="entry",
                source="rule",
                direction="up",
                horizon="weeks",
                strength=Decimal("0.5"),
                rationale="test",
                created_at=datetime(2026, 10, day, tzinfo=UTC),
            )
            session.add(signal)
            await session.flush()
            session.add(
                SignalOutcome(
                    signal_id=signal.id,
                    horizon_days=5,
                    start_day=date(2026, 10, 20),
                    end_day=date(2026, 10, 27),
                    start_price=100,
                    end_price=104,
                    return_pct=Decimal(ret),
                    alpha_pct=None,
                    mfe_pct=5,
                    mae_pct=-3,
                )
            )
        await session.commit()
    query = "horizon_days=5&created_from=2026-10-10&created_to=2026-10-20"
    summary = (await client.get(f"/track-record?{query}")).json()
    assert summary["signals_total"] == summary["measured"] == 1
    assert Decimal(summary["overall"]["avg_return_pct"]) == -2
    drilldown = (await client.get(f"/track-record/outcomes?{query}")).json()
    assert drilldown["total"] == 1
    assert len(drilldown["items"]) == 1
    assert Decimal(drilldown["items"][0]["return_pct"]) == -2
