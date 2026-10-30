"""Short scheduler ticks, durable outbox recovery and atomic worker claims."""

import asyncio
import contextlib
import functools
import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from sqlalchemy import update

from preza.config import get_settings
from preza.db import get_sessionmaker
from preza.domain.automation import BatchInput
from preza.models_automation import ProcessExecution, ProcessPolicy
from preza.services import automation
from preza.services.analyses import queue_run

HANDLERS: dict[str, Callable[..., Awaitable[Any]]] = {}


def managed[F: Callable[..., Awaitable[Any]]](function: F) -> F:
    """Existing UTC cron remains the trigger until its policy explicitly changes."""

    HANDLERS[function.__name__] = function

    @functools.wraps(function)
    async def wrapped(ctx: dict[str, Any], *args: Any, **kwargs: Any) -> Any:
        async with get_sessionmaker()() as session:
            await automation.ensure_policies(session)
            row = await session.get(ProcessPolicy, function.__name__)
            assert row is not None
            # Explicit API routes own these function-specific manual job markers.
            # Unknown and missing IDs must never turn scheduled work into manual work.
            marker = f"{function.__name__}:manual"
            job_id = str(ctx.get("job_id", ""))
            automatic = not (job_id == marker or job_id.startswith(marker + ":"))
            if automatic and row.config.get("schedule_kind") != "legacy":
                await session.commit()
                return "managed_schedule"
            reason = await automation.gate(session, function.__name__, automatic=automatic)
            if reason:
                await session.commit()
                return reason
            slot = datetime.now(UTC)
            if automatic:
                slot = slot.replace(second=0, microsecond=0)
            execution_id = await automation.materialize(
                session, function.__name__, slot, origin="automatic" if automatic else "manual"
            )
            await session.commit()
        return await execute_process(ctx, str(execution_id))

    return cast(F, wrapped)


async def _heartbeat(execution_id: uuid.UUID) -> None:
    while True:
        await asyncio.sleep(30)
        async with get_sessionmaker()() as session:
            await session.execute(
                update(ProcessExecution)
                .where(ProcessExecution.id == execution_id, ProcessExecution.state == "running")
                .values(heartbeat_at=datetime.now(UTC))
            )
            await session.commit()


async def execute_process(ctx: dict[str, Any], execution_id: str) -> str:
    from preza import worker

    run_ids: list[str] = []
    async with get_sessionmaker()() as session:
        execution = await automation.claim(session, uuid.UUID(execution_id))
        await session.commit()
        if execution is None:
            return "not_claimed"
        key = execution.process_key
    heartbeat = asyncio.create_task(_heartbeat(execution.id))
    try:
        if key == "batch_analyses":
            async with get_sessionmaker()() as session:
                policy = await session.get(ProcessPolicy, key)
                assert policy is not None
                config = automation.policy_input(policy)
                # Attempt cap is per logical execution; failures are never retried automatically.
                result = await automation.run_batch(
                    session,
                    get_settings(),
                    BatchInput(
                        scope=config.scope, cap=config.cap, outside_window=execution.outside_window
                    ),
                    execution.id,
                )
                run_ids = result.run_ids
                counts: dict[str, Any] = {"accepted": len(run_ids), "considered": len(result.items)}
                await session.commit()
            for run_id in run_ids:
                await queue_run(get_settings(), uuid.UUID(run_id))
        else:
            function = HANDLERS.get(key) or getattr(worker, key)
            raw = getattr(function, "__wrapped__", function)
            result_text = await raw(
                {
                    **ctx,
                    "process_origin": execution.origin,
                    "process_execution_id": str(execution.id),
                }
            )
            counts = {"result": str(result_text)[:120]}
        async with get_sessionmaker()() as session:
            current_execution = await session.get(
                ProcessExecution, execution.id, populate_existing=True, with_for_update=True
            )
            if current_execution is not None:
                counts = {**current_execution.counts, **counts}
            await session.execute(
                update(ProcessExecution)
                .where(ProcessExecution.id == execution.id, ProcessExecution.state == "running")
                .values(
                    state="done",
                    counts=counts,
                    finished_at=datetime.now(UTC),
                    heartbeat_at=datetime.now(UTC),
                )
            )
            await session.commit()
        return "done"
    except Exception:
        async with get_sessionmaker()() as session:
            await session.execute(
                update(ProcessExecution)
                .where(ProcessExecution.id == execution.id)
                .values(state="failed", reason="process_failed", finished_at=datetime.now(UTC))
            )
            await session.commit()
        raise
    finally:
        heartbeat.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await heartbeat


async def automation_tick(ctx: dict[str, Any]) -> int:
    now = datetime.now(UTC)
    async with get_sessionmaker()() as session:
        # An expired lease has unknown side effects. Report it; do not blindly replay it.
        await session.execute(
            update(ProcessExecution)
            .where(
                ProcessExecution.state == "running",
                ProcessExecution.heartbeat_at < now - timedelta(minutes=10),
            )
            .values(state="interrupted", reason="heartbeat_expired", finished_at=now)
        )
        await automation.schedule_due(session, now)
        await session.commit()
        return await automation.deliver_pending(session, get_settings())
