from datetime import UTC, datetime
from typing import Any

import pytest

from preza import automation_worker, db
from preza.models_automation import AutomationControl, ProcessPolicy
from preza.services import automation

pytestmark = pytest.mark.db


async def test_manual_legacy_entrypoint_runs_after_schedule_change_while_automatic_paused(
    api: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    from preza import worker  # noqa: F401

    monkeypatch.setattr(automation_worker, "HANDLERS", dict(automation_worker.HANDLERS))
    async with db.get_sessionmaker()() as session:
        await automation.ensure_policies(session)
        policy = await session.get(ProcessPolicy, "refresh_bars")
        assert policy is not None
        policy.config = {**policy.config, "schedule_kind": "daily"}
        control = await session.get(AutomationControl, 1)
        assert control is not None
        control.paused = True
        await session.commit()
    called = []

    async def fake(ctx: dict[str, Any]) -> str:
        called.append("run")
        return "done"

    fake.__name__ = "refresh_bars"
    decorated = automation_worker.managed(fake)
    assert await decorated({"job_id": "refresh_bars:manual"}) == "done"
    assert called == ["run"]
    assert await decorated({"job_id": "cron:refresh_bars:123"}) == "managed_schedule"
    assert called == ["run"]
    assert await decorated({}) == "managed_schedule"
    assert called == ["run"]
    assert await decorated({"job_id": "entries:manual"}) == "managed_schedule"
    assert await decorated({"job_id": "arbitrary"}) == "managed_schedule"
    assert called == ["run"]


async def test_managed_batch_preserves_explicit_outside_window_override(
    api: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    from preza.domain.automation import BatchPreview

    async with db.get_sessionmaker()() as session:
        await automation.ensure_policies(session)
        policy = await session.get(ProcessPolicy, "batch_analyses")
        assert policy is not None
        policy.enabled = True
        execution_id = await automation.materialize(
            session, "batch_analyses", datetime.now(UTC), origin="manual", outside_window=True
        )
        await session.commit()
    bodies = []

    async def fake_run(session: Any, settings: Any, body: Any, execution_id: Any) -> BatchPreview:
        bodies.append(body)
        return BatchPreview(
            items=[], quota_used=0, quota_limit=6, policy_revision=0, resets_at=datetime.now(UTC)
        )

    monkeypatch.setattr(automation, "run_batch", fake_run)
    assert await automation_worker.execute_process({}, str(execution_id)) == "done"
    assert bodies[0].outside_window is True
