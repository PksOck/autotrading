"""Bounded, restart-safe delivery of durable automation intents."""

import asyncio
import os
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from preza import db
from preza.config import Settings
from preza.domain.automation import PolicyInput
from preza.models_automation import AutomationControl, ProcessExecution, ProcessPolicy
from preza.services import automation

pytestmark = pytest.mark.db


@pytest.fixture
async def outbox(api: Any) -> None:
    async with db.get_sessionmaker()() as session:
        await automation.ensure_policies(session)
        # The dedicated DB fixture may outlive an individual delivery cursor.
        if await session.scalar(text("SELECT to_regclass('automation_outbox_cursor')")):
            await session.execute(text("DELETE FROM automation_outbox_cursor"))
        await session.commit()


def policy(key: str, **kwargs: Any) -> ProcessPolicy:
    config = PolicyInput(enabled=True, **kwargs)
    return ProcessPolicy(
        process_key=key,
        enabled=config.enabled,
        revision=0,
        config=config.model_dump(exclude={"enabled", "revision"}),
    )


def execution(
    key: str,
    slot: datetime,
    *,
    revision: int = 0,
    origin: str = "automatic",
    outside_window: bool = False,
    number: int | None = None,
) -> ProcessExecution:
    execution_id = uuid.UUID(int=number) if number is not None else uuid.uuid4()
    return ProcessExecution(
        id=execution_id,
        process_key=key,
        policy_revision=revision,
        scheduled_for=slot,
        origin=origin,
        outside_window=outside_window,
        state="pending",
        job_id=f"process:{execution_id}",
        counts={},
    )


async def tick() -> int:
    async with db.get_sessionmaker()() as session:
        result = await automation.deliver_pending(session, Settings(database_url="unused"))
        await session.commit()
        return result


async def test_deliver_pending_passes_100_blocked_rows(
    outbox: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    now = datetime.now(UTC) - timedelta(hours=1)
    async with db.get_sessionmaker()() as session:
        blocked = await session.get(ProcessPolicy, "entries")
        assert blocked is not None
        blocked.enabled = False
        session.add_all(
            execution("entries", now + timedelta(microseconds=index)) for index in range(100)
        )
        allowed = execution("radar", now + timedelta(seconds=1))
        session.add(allowed)
        await session.commit()

    delivered: list[str] = []

    async def enqueue(settings: Settings, job: str, *args: Any, **kwargs: Any) -> str:
        assert job == "execute_process"
        delivered.append(str(args[0]))
        return str(kwargs["job_id"])

    monkeypatch.setattr(automation, "enqueue", enqueue)
    assert await tick() == 1
    assert delivered == [str(allowed.id)]


async def test_stale_revision_is_skipped_without_queueing(
    outbox: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    async with db.get_sessionmaker()() as session:
        stale = execution("radar", datetime.now(UTC) - timedelta(minutes=1), revision=99)
        session.add(stale)
        await session.commit()

    async def forbidden(*args: Any, **kwargs: Any) -> None:
        pytest.fail("A stale policy revision must not reach Redis")

    monkeypatch.setattr(automation, "enqueue", forbidden)
    assert await tick() == 0
    async with db.get_sessionmaker()() as session:
        row = await session.get(ProcessExecution, stale.id)
        assert row is not None
        assert (row.state, row.reason) == ("skipped", "policy_changed")
        assert row.finished_at is not None


async def test_stale_delivery_cannot_overwrite_a_concurrent_running_claim(
    outbox: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    async with db.get_sessionmaker()() as session:
        pending = execution("radar", datetime.now(UTC) - timedelta(minutes=1))
        session.add(pending)
        await session.commit()

    candidate_read, policy_changed = asyncio.Event(), asyncio.Event()
    original_get = AsyncSession.get
    async with (
        db.get_sessionmaker()() as delivery_session,
        db.get_sessionmaker()() as claimant,
        db.get_sessionmaker()() as observer,
    ):
        delivery_pid = await delivery_session.scalar(text("SELECT pg_backend_pid()"))
        claimant_pid = await claimant.scalar(text("SELECT pg_backend_pid()"))

        async def get_after_policy_change(
            session: AsyncSession, entity: Any, *args: Any, **kwargs: Any
        ) -> Any:
            if session is delivery_session and entity is ProcessPolicy:
                candidate_read.set()
                await policy_changed.wait()
            return await original_get(session, entity, *args, **kwargs)

        async def deliver() -> int:
            result = await automation.deliver_pending(
                delivery_session, Settings(database_url="unused")
            )
            await delivery_session.commit()
            return result

        async def forbidden(*args: Any, **kwargs: Any) -> None:
            pytest.fail("A candidate whose policy changed must not be enqueued")

        monkeypatch.setattr(AsyncSession, "get", get_after_policy_change)
        monkeypatch.setattr(automation, "enqueue", forbidden)
        delivery = asyncio.create_task(deliver())
        try:
            await asyncio.wait_for(candidate_read.wait(), timeout=5)
            claimed = await automation.claim(claimant, pending.id)
            assert claimed is not None and claimed.state == "running"
            await claimant.flush()
            await observer.execute(
                update(ProcessPolicy).where(ProcessPolicy.process_key == "radar").values(revision=1)
            )
            await observer.commit()
            policy_changed.set()
            # The real SQL write waits for the real claim lock, not a fake barrier.
            async with asyncio.timeout(5):
                while True:
                    blocking = await observer.scalar(
                        text("SELECT pg_blocking_pids(:pid)"), {"pid": delivery_pid}
                    )
                    if claimant_pid in blocking:
                        break
                    await asyncio.sleep(0.01)
        finally:
            policy_changed.set()
            await claimant.commit()
            assert await asyncio.wait_for(delivery, timeout=5) == 0

    async with db.get_sessionmaker()() as session:
        row = await session.get(ProcessExecution, pending.id)
        assert row is not None
        assert row.state == "running"
        assert row.reason is None and row.finished_at is None
        assert row.started_at is not None and row.heartbeat_at is not None


async def test_deduplicated_prefix_advances_after_restart_with_bounded_work(
    outbox: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    slot = datetime.now(UTC) - timedelta(hours=1)
    async with db.get_sessionmaker()() as session:
        # Equal timestamps require the ID tie breaker across the persisted cursor.
        for number in range(1, 1003):
            key = f"equal-{number}"
            session.add(policy(key))
        await session.flush()
        session.add_all(
            execution(f"equal-{number}", slot, number=number) for number in range(1, 1003)
        )
        await session.commit()

    calls: list[int] = []

    async def deduplicate(settings: Settings, job: str, *args: Any, **kwargs: Any) -> str | None:
        number = uuid.UUID(str(args[0])).int
        calls.append(number)
        return str(kwargs["job_id"]) if number == 1002 else None

    monkeypatch.setattr(automation, "enqueue", deduplicate)
    assert await tick() == 0
    assert calls == list(range(1, 1001))
    # Fresh engine/session models a worker restart; no in-memory continuation survives.
    await db.get_engine().dispose()
    db.get_engine.cache_clear()
    db.get_sessionmaker.cache_clear()
    calls.clear()
    assert await tick() == 1
    assert calls == [1001, 1002]
    calls.clear()
    assert await tick() == 0
    assert calls == list(range(1, 1001))


async def test_successful_deliveries_stop_at_100_and_resume_tail(
    outbox: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    slot = datetime.now(UTC) - timedelta(hours=1)
    async with db.get_sessionmaker()() as session:
        session.add_all(
            execution("radar", slot + timedelta(microseconds=number), number=number)
            for number in range(1, 106)
        )
        await session.commit()
    calls: list[int] = []
    queued: set[int] = set()

    async def enqueue(settings: Settings, job: str, *args: Any, **kwargs: Any) -> str | None:
        number = uuid.UUID(str(args[0])).int
        calls.append(number)
        if number in queued:
            return None
        queued.add(number)
        return str(kwargs["job_id"])

    monkeypatch.setattr(automation, "enqueue", enqueue)
    assert await tick() == 100
    assert calls == list(range(1, 101))
    calls.clear()
    assert await tick() == 5
    assert calls == [101, 102, 103, 104, 105]


@pytest.mark.parametrize("block", ["disabled", "paused", "analyses_disabled", "outside_window"])
async def test_temporary_blocks_retain_pending_and_resume(
    outbox: None, monkeypatch: pytest.MonkeyPatch, block: str
) -> None:
    async with db.get_sessionmaker()() as session:
        row = await session.get(ProcessPolicy, "entries")
        control = await session.get(AutomationControl, 1)
        assert row is not None and control is not None
        if block == "disabled":
            row.enabled = False
        elif block == "paused":
            control.paused = True
        elif block == "analyses_disabled":
            control.automatic_analyses_enabled = False
        else:
            day = datetime.now(UTC).weekday()
            row.config = {**row.config, "weekdays": [(day + 1) % 7]}
        pending = execution("entries", datetime.now(UTC) - timedelta(minutes=1))
        session.add(pending)
        await session.commit()
        assert await automation.claim(session, pending.id) is None
        await session.commit()
        assert pending.state == "pending"

    calls: list[str] = []

    async def enqueue(settings: Settings, job: str, *args: Any, **kwargs: Any) -> str:
        calls.append(str(args[0]))
        return str(kwargs["job_id"])

    monkeypatch.setattr(automation, "enqueue", enqueue)
    assert await tick() == 0
    assert calls == []
    async with db.get_sessionmaker()() as session:
        row = await session.get(ProcessPolicy, "entries")
        control = await session.get(AutomationControl, 1)
        assert row is not None and control is not None
        row.enabled = True
        row.config = {**row.config, "weekdays": list(range(7))}
        control.paused = False
        control.automatic_analyses_enabled = True
        await session.commit()
    assert await tick() == 1
    assert calls == [str(pending.id)]


async def test_manual_override_respects_due_time_and_routes_agents(
    outbox: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    async with db.get_sessionmaker()() as session:
        row = await session.get(ProcessPolicy, "discover_thesis_reviews")
        control = await session.get(AutomationControl, 1)
        assert row is not None and control is not None
        row.config = {**row.config, "weekdays": [(datetime.now(UTC).weekday() + 1) % 7]}
        control.paused = True
        control.automatic_analyses_enabled = False
        due = execution(
            row.process_key,
            datetime.now(UTC) - timedelta(minutes=1),
            origin="manual",
            outside_window=True,
        )
        session.add_all(
            [
                due,
                execution(
                    row.process_key,
                    datetime.now(UTC) + timedelta(days=1),
                    origin="manual",
                    outside_window=True,
                ),
                execution(row.process_key, datetime.now(UTC) - timedelta(minutes=2)),
            ]
        )
        await session.commit()
    calls: list[str] = []

    async def enqueue(settings: Settings, job: str, *args: Any, **kwargs: Any) -> str:
        assert kwargs["queue_name"] == "arq:agents"
        assert kwargs["job_id"] == due.job_id
        calls.append(str(args[0]))
        return str(kwargs["job_id"])

    monkeypatch.setattr(automation, "enqueue", enqueue)
    assert await tick() == 1
    assert calls == [str(due.id)]


async def test_redis_outage_wraps_and_recovers_durable_pending(
    outbox: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    async with db.get_sessionmaker()() as session:
        pending = execution("radar", datetime.now(UTC) - timedelta(minutes=1))
        session.add(pending)
        await session.commit()

    async def offline(*args: Any, **kwargs: Any) -> None:
        return None

    monkeypatch.setattr(automation, "enqueue", offline)
    assert await tick() == 0
    async with db.get_sessionmaker()() as session:
        row = await session.get(ProcessExecution, pending.id)
        assert row is not None and row.state == "pending"

    async def online(settings: Settings, job: str, *args: Any, **kwargs: Any) -> str:
        return str(kwargs["job_id"])

    monkeypatch.setattr(automation, "enqueue", online)
    assert await tick() == 1


async def test_two_schedulers_and_two_claims_dispatch_once(
    outbox: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    async with db.get_sessionmaker()() as session:
        pending = execution("radar", datetime.now(UTC) - timedelta(minutes=1))
        session.add(pending)
        await session.commit()

    entered, release = asyncio.Event(), asyncio.Event()
    calls: list[str] = []

    async def enqueue(settings: Settings, job: str, *args: Any, **kwargs: Any) -> str:
        calls.append(str(args[0]))
        entered.set()
        await release.wait()
        return str(kwargs["job_id"])

    monkeypatch.setattr(automation, "enqueue", enqueue)
    first = asyncio.create_task(tick())
    try:
        await asyncio.wait_for(entered.wait(), timeout=5)
        assert await asyncio.wait_for(tick(), timeout=5) == 0
    finally:
        release.set()
        assert await asyncio.wait_for(first, timeout=5) == 1
    assert calls == [str(pending.id)]
    async with db.get_sessionmaker()() as first_session, db.get_sessionmaker()() as second_session:
        assert await automation.claim(first_session, pending.id) is not None
        assert await automation.claim(second_session, pending.id) is None
        await first_session.commit()
        await second_session.commit()
    async with db.get_sessionmaker()() as session:
        states = list(await session.scalars(select(ProcessExecution.state)))
        assert states == ["running"]


@pytest.mark.skipif(not os.getenv("TEST_REDIS_URL"), reason="isolated TEST_REDIS_URL not set")
async def test_configured_arq_worker_allows_same_job_id_after_blocked_claim(
    outbox: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    from arq.connections import RedisSettings
    from arq.worker import Function, Worker

    from preza import automation_worker, worker
    from preza.queue import enqueue

    redis_url = os.environ["TEST_REDIS_URL"]
    queue_name = f"test:outbox:{uuid.uuid4()}"
    registration = next(
        item
        for item in worker.WorkerSettings.functions
        if isinstance(item, Function) and item.coroutine is automation_worker.execute_process
    )
    async with db.get_sessionmaker()() as session:
        control = await session.get(AutomationControl, 1)
        assert control is not None
        control.paused = True
        pending = execution("radar", datetime.now(UTC) - timedelta(minutes=1))
        session.add(pending)
        await session.commit()

    called: list[str] = []

    async def handler(ctx: dict[str, Any]) -> str:
        called.append(str(ctx["process_execution_id"]))
        return "done"

    monkeypatch.setitem(automation_worker.HANDLERS, "radar", handler)
    settings = Settings(redis_url=redis_url, database_url="unused")

    async def deliver_and_execute() -> None:
        assert (
            await enqueue(
                settings,
                "execute_process",
                str(pending.id),
                job_id=pending.job_id,
                queue_name=queue_name,
            )
            == pending.job_id
        )
        runner = Worker(
            functions=[registration],
            redis_settings=RedisSettings.from_dsn(redis_url),
            queue_name=queue_name,
            burst=True,
            handle_signals=False,
            poll_delay=0.01,
        )
        try:
            await runner.async_run()
            assert runner.jobs_complete == 1
            assert runner.jobs_failed == 0
        finally:
            await runner.pool.delete(runner.health_check_key)
            await runner.pool.aclose()

    await deliver_and_execute()
    assert called == []
    async with db.get_sessionmaker()() as session:
        row = await session.get(ProcessExecution, pending.id)
        control = await session.get(AutomationControl, 1)
        assert row is not None and control is not None
        assert (row.state, row.reason) == ("pending", "paused")
        control.paused = False
        await session.commit()
    # The configured zero result retention must release this identical identity.
    await deliver_and_execute()
    assert called == [str(pending.id)]
    async with db.get_sessionmaker()() as session:
        row = await session.get(ProcessExecution, pending.id)
        assert row is not None and row.state == "done"
