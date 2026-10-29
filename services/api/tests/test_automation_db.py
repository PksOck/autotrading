"""Automation transaction/recovery integration cases (isolated database only)."""

import asyncio
import uuid
from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi import HTTPException
from sqlalchemy import delete, select

from preza import db
from preza.config import Settings
from preza.domain.automation import PolicyInput
from preza.models import AnalysisRun, Instrument
from preza.models_automation import AutomationControl, ProcessExecution, ProcessPolicy
from preza.services import automation
from preza.services.analyses import new_run

pytestmark = pytest.mark.db


@pytest.fixture
async def clean_automation(api: Any) -> Any:
    async with db.get_sessionmaker()() as session:
        await session.execute(delete(ProcessExecution))
        await session.execute(delete(ProcessPolicy))
        await session.execute(delete(AutomationControl))
        await automation.ensure_policies(session)
        await session.commit()
    return api


async def test_revision_guard_and_new_schedule_disabled(clean_automation: Any) -> None:
    client, _ = clean_automation
    rows = (await client.get("/automation/policies")).json()
    batch = next(row for row in rows if row["process_key"] == "batch_analyses")
    assert batch["enabled"] is False
    body = PolicyInput(enabled=True).model_dump()
    assert (await client.patch("/automation/policies/batch_analyses", json=body)).status_code == 200
    assert (await client.patch("/automation/policies/batch_analyses", json=body)).status_code == 409


async def test_shared_quota_serializes_concurrent_acceptance(clean_automation: Any) -> None:
    async with db.get_sessionmaker()() as session:
        instruments = [Instrument(symbol=s, source="test", kind="stock") for s in ("AAA", "BBB")]
        session.add_all(instruments)
        await session.commit()
        ids = [row.id for row in instruments]

    async def accept(instrument_id: int) -> int:
        async with db.get_sessionmaker()() as session:
            instrument = await session.get(Instrument, instrument_id)
            assert instrument is not None
            try:
                await new_run(session, instrument, Settings(deep_daily_limit=1))
                await session.commit()
                return 202
            except HTTPException as exc:
                await session.rollback()
                return exc.status_code

    assert sorted(await asyncio.gather(*(accept(i) for i in ids))) == [202, 429]


async def test_active_duplicate_prevented(clean_automation: Any) -> None:
    async with db.get_sessionmaker()() as session:
        instrument = Instrument(symbol="ACTIVE", source="test", kind="stock")
        session.add(instrument)
        await session.flush()
        await new_run(session, instrument, Settings(deep_daily_limit=20))
        with pytest.raises(HTTPException) as exc:
            await new_run(session, instrument, Settings(deep_daily_limit=20))
        assert exc.value.status_code == 409


async def test_single_claim_and_pending_outbox_survives_redis(
    clean_automation: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    async with db.get_sessionmaker()() as session:
        slot = datetime.now(UTC)
        first = await automation.materialize(session, "radar", slot)
        assert await automation.materialize(session, "radar", slot) == first
        await session.commit()

    async def offline(*args: Any, **kwargs: Any) -> None:
        return None

    monkeypatch.setattr(automation, "enqueue", offline)
    async with db.get_sessionmaker()() as session:
        assert await automation.deliver_pending(session, Settings()) == 0
        execution = await session.get(ProcessExecution, first)
        assert execution is not None and execution.state == "pending"
    async with db.get_sessionmaker()() as one, db.get_sessionmaker()() as two:
        assert await automation.claim(one, first) is not None
        assert await automation.claim(two, first) is None
        await one.commit()
    async with db.get_sessionmaker()() as session:
        assert await automation.claim(session, first) is None


async def test_policy_disable_and_pause_rechecked_before_start(clean_automation: Any) -> None:
    async with db.get_sessionmaker()() as session:
        execution_id = await automation.materialize(session, "radar", datetime.now(UTC))
        control = await session.get(AutomationControl, 1)
        assert control is not None
        control.paused = True
        await session.commit()
        assert await automation.claim(session, execution_id) is None
        execution = await session.get(ProcessExecution, execution_id)
        assert (
            execution is not None and execution.state == "pending" and execution.reason == "paused"
        )
        control.paused = False
        policy = await session.get(ProcessPolicy, "radar")
        assert policy is not None
        policy.enabled = False
        await session.commit()
        assert await automation.claim(session, execution_id) is None
        assert execution.state == "skipped"
        assert not list(await session.scalars(select(AnalysisRun)))


async def test_batch_preview_scope_cap_active_and_explicit_enable(
    clean_automation: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    from datetime import date
    from decimal import Decimal

    from preza.models import AccountSnapshot, Position, WatchlistItem
    from preza.services import analyses as analysis_service

    client, _ = clean_automation

    async def offline(*args: Any, **kwargs: Any) -> None:
        return None

    monkeypatch.setattr(analysis_service, "enqueue", offline)
    async with db.get_sessionmaker()() as session:
        instruments = [
            Instrument(symbol=s, source="test", kind="stock")
            for s in ("ACTIVE", "READY", "SOLD", "WATCH", "REMOVED")
        ]
        session.add_all(instruments)
        await session.flush()
        for account, index, day in (("A", 0, 20), ("A", 1, 20), ("B", 2, 19)):
            session.add(
                Position(
                    account_id=account,
                    instrument_id=instruments[index].id,
                    report_date=date(2026, 10, day),
                    quantity=Decimal(1),
                    currency="EUR",
                    source="test",
                )
            )
        session.add(
            AccountSnapshot(
                account_id="B",
                report_date=date(2026, 10, 20),
                positions_complete=True,
                source="test",
            )
        )
        session.add(WatchlistItem(instrument_id=instruments[3].id))
        session.add(WatchlistItem(instrument_id=instruments[4].id, removed_at=datetime.now(UTC)))
        await new_run(session, instruments[0], Settings(deep_daily_limit=20))
        await session.commit()
    response = await client.post("/automation/batch/preview", json={"scope": "both", "cap": 1})
    data = response.json()
    assert {row["symbol"] for row in data["items"]} == {"ACTIVE", "READY", "WATCH"}
    assert data["blocked_reason"] == "disabled"
    assert (
        await client.post("/automation/batch/run", json={"scope": "both", "cap": 1, "revision": 0})
    ).status_code == 409
    assert (
        await client.patch(
            "/automation/policies/batch_analyses", json=PolicyInput(enabled=True).model_dump()
        )
    ).status_code == 200
    data = (await client.post("/automation/batch/preview", json={"scope": "both", "cap": 1})).json()
    assert {row["symbol"]: row["reason"] for row in data["items"]} == {
        "ACTIVE": "active",
        "READY": "ready",
        "WATCH": "cap",
    }
    result = await client.post(
        "/automation/batch/run",
        json={"scope": "both", "cap": 1, "revision": data["policy_revision"]},
    )
    assert result.status_code == 202 and len(result.json()["run_ids"]) == 1
    selected = (
        await client.post(
            "/automation/batch/preview", json={"scope": "portfolio", "account_id": "B"}
        )
    ).json()
    assert selected["items"] == []


async def test_recovery_keeps_only_latest_due_occurrence(clean_automation: Any) -> None:
    from datetime import timedelta

    async with db.get_sessionmaker()() as session:
        now = datetime(2026, 10, 29, 12, tzinfo=UTC)
        row = await session.get(ProcessPolicy, "batch_analyses")
        assert row is not None
        row.enabled = True
        row.config = PolicyInput(
            enabled=True, schedule_kind="interval", interval_minutes=5
        ).model_dump(exclude={"enabled", "revision"})
        row.updated_at = now - timedelta(days=3)
        await automation.materialize(session, row.process_key, now - timedelta(days=2))
        await session.flush()
        await automation.schedule_due(session, now)
        pending = list(
            await session.scalars(
                select(ProcessExecution).where(ProcessExecution.state == "pending")
            )
        )
        assert len(pending) == 1
        assert pending[0].scheduled_for == now


async def test_worker_claim_executes_handler_once(
    clean_automation: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    from preza import automation_worker

    calls = []

    async def fake_handler(ctx: Any) -> str:
        calls.append("called")
        return "ok"

    monkeypatch.setitem(automation_worker.HANDLERS, "radar", fake_handler)
    async with db.get_sessionmaker()() as session:
        execution_id = await automation.materialize(session, "radar", datetime.now(UTC))
        await session.commit()
    assert await automation_worker.execute_process({}, str(execution_id)) == "done"
    assert await automation_worker.execute_process({}, str(execution_id)) == "not_claimed"
    assert calls == ["called"]


async def test_automatic_failed_attempts_cannot_repeat_without_bound(clean_automation: Any) -> None:
    from preza.domain.automation import BatchInput
    from preza.models import WatchlistItem

    async with db.get_sessionmaker()() as session:
        policy = await session.get(ProcessPolicy, "batch_analyses")
        assert policy is not None
        policy.enabled = True
        instrument = Instrument(symbol="ATTEMPT", source="test", kind="stock")
        session.add(instrument)
        await session.flush()
        session.add(WatchlistItem(instrument_id=instrument.id))
        first = await automation.materialize(session, policy.process_key, datetime.now(UTC))
        result = await automation.run_batch(
            session, Settings(deep_daily_limit=10), BatchInput(scope="watchlist", cap=1), first
        )
        assert len(result.run_ids) == 1
        run = await session.get(AnalysisRun, uuid.UUID(result.run_ids[0]))
        assert run is not None
        run.status = "failed"
        await session.flush()
        second = await automation.materialize(session, policy.process_key, datetime.now(UTC))
        second_result = await automation.run_batch(
            session, Settings(deep_daily_limit=10), BatchInput(scope="watchlist", cap=1), second
        )
        assert second_result.run_ids == []
        assert second_result.items[0].reason == "cap"
