from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from preza.config import Settings
from preza.domain.email import EmailPreferencesInput
from preza.models_automation import AutomationControl, ProcessPolicy
from preza.services.automation import gate
from preza.services.email import configured


@pytest.mark.parametrize("address", ["bad", "a@", "a\nb@example.com", "Name <a@example.com>"])
def test_email_rejects_invalid_recipient(address: str) -> None:
    with pytest.raises(ValidationError):
        EmailPreferencesInput(recipients=[address])


def test_email_normalizes_and_deduplicates_recipients() -> None:
    preferences = EmailPreferencesInput(
        recipients=[" user@example.com ", "user@example.com", "two@example.org"]
    )
    assert preferences.recipients == ["user@example.com", "two@example.org"]


@pytest.mark.parametrize(
    "key,automatic,expected",
    [
        ("entries", True, "analyses_disabled"),
        ("entries", False, None),
        ("refresh_bars", True, None),
        ("batch_analyses", True, "analyses_disabled"),
        ("discover_thesis_reviews", True, "analyses_disabled"),
    ],
)
async def test_analysis_switch_preserves_manual_runs_and_sync(
    key: str, automatic: bool, expected: str | None
) -> None:
    policy = ProcessPolicy(process_key=key, enabled=True, revision=0, config={})
    control = AutomationControl(id=1, paused=False, automatic_analyses_enabled=False)
    session = AsyncMock()
    session.get.side_effect = [policy, control]
    assert await gate(session, key, automatic=automatic) == expected


def test_email_cannot_enable_with_missing_or_insecure_transport() -> None:
    assert not configured(Settings())
    assert not configured(
        Settings(smtp_host="smtp.example.org", smtp_from="a@example.org", smtp_security="none")
    )
    assert configured(Settings(smtp_host="smtp.example.org", smtp_from="a@example.org"))


async def test_explicit_portfolio_actions_own_unique_manual_job_markers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from preza.routes import portfolio

    enqueue = AsyncMock(return_value="queued")
    monkeypatch.setattr(portfolio, "enqueue", enqueue)
    settings = Settings(ibkr_flex_token="test", ibkr_flex_query_id="test")
    await portfolio.sync(settings)
    first = enqueue.call_args.kwargs["job_id"]
    assert first.startswith("sync_flex:manual:")
    await portfolio.sync(settings)
    assert enqueue.call_args.kwargs["job_id"] != first
    monkeypatch.setattr(portfolio, "_read_capped", AsyncMock(return_value=b"<FlexStatement/>"))
    monkeypatch.setattr(
        portfolio, "parse_statement", lambda _: SimpleNamespace(positions=[], cash=[])
    )
    monkeypatch.setattr(portfolio, "store_statement", AsyncMock(return_value={}))
    monkeypatch.setattr(portfolio, "record_sync", AsyncMock())
    await portfolio.import_statement(AsyncMock(), AsyncMock(), settings)
    assert enqueue.call_args.kwargs["job_id"].startswith("refresh_bars:manual:")


async def test_delivery_rechecks_global_pause_before_any_smtp(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from preza.services import email

    sender = AsyncMock()
    monkeypatch.setattr(email, "send_message", sender)
    session = AsyncMock()
    session.get.return_value = AutomationControl(id=1, paused=True)
    assert not await email.deliver_one(session, Settings())
    sender.assert_not_called()
    session.scalar.assert_not_called()


async def test_delivery_rechecks_pause_after_claim_before_smtp(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from preza.domain.email import EmailPreferencesOut
    from preza.services import email

    sender = AsyncMock()
    monkeypatch.setattr(email, "send_message", sender)
    monkeypatch.setattr(
        email,
        "preferences",
        AsyncMock(
            return_value=EmailPreferencesOut(
                configured=True, enabled=True, recipients=["one@example.org"], kinds=["signals"]
            )
        ),
    )
    session = AsyncMock()
    session.get.side_effect = [
        AutomationControl(id=1, paused=False),
        AutomationControl(id=1, paused=True),
    ]
    session.scalar.return_value = SimpleNamespace(
        recipient="one@example.org", kind="signals", state="pending"
    )
    assert not await email.deliver_one(session, Settings())
    sender.assert_not_called()
    session.commit.assert_not_called()


async def test_automatic_model_rechecks_switch_on_every_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from contextlib import asynccontextmanager

    from pydantic import BaseModel

    from preza.llm import automatic
    from preza.llm.client import LlmUnavailableError

    control = AutomationControl(id=1, paused=False, automatic_analyses_enabled=True)
    session = AsyncMock()
    session.get.return_value = control

    @asynccontextmanager
    async def sessions():
        yield session

    monkeypatch.setattr(automatic, "get_sessionmaker", lambda: sessions)
    inner = AsyncMock()
    llm = automatic.AutomaticLlm(inner)
    await llm.complete_json("cloud-deep", "system", "user", BaseModel, max_output_tokens=100)
    assert inner.complete_json.await_count == 1
    assert inner.complete_json.call_args.kwargs == {"max_output_tokens": 100}
    control.automatic_analyses_enabled = False
    with pytest.raises(LlmUnavailableError):
        await llm.complete_json("cloud-deep", "system", "user", BaseModel, max_output_tokens=100)
    assert inner.complete_json.await_count == 1


@pytest.mark.parametrize("origin,expected", [("manual", None), ("automatic", "paused")])
async def test_review_child_uses_persisted_origin_and_window_override(
    origin: str, expected: str | None
) -> None:
    import uuid

    from preza.models_automation import ProcessExecution
    from preza.services.automation import review_gate

    revision_id, execution_id = uuid.uuid4(), uuid.uuid4()
    policy = ProcessPolicy(
        process_key="discover_thesis_reviews", enabled=True, revision=2, config={"weekdays": [0]}
    )
    execution = ProcessExecution(
        id=execution_id,
        process_key=policy.process_key,
        policy_revision=2,
        origin=origin,
        outside_window=True,
        state="done",
        counts={"revision_ids": str(revision_id)},
    )
    control = AutomationControl(id=1, paused=True, automatic_analyses_enabled=False)
    session = AsyncMock()
    session.get.side_effect = [execution, policy, policy, control]
    assert await review_gate(session, revision_id, str(execution_id)) == expected


async def test_review_child_cannot_borrow_another_revision_manual_origin() -> None:
    import uuid

    from preza.models_automation import ProcessExecution
    from preza.services.automation import review_gate

    execution_id = uuid.uuid4()
    session = AsyncMock()
    session.get.return_value = ProcessExecution(
        id=execution_id,
        process_key="discover_thesis_reviews",
        origin="manual",
        state="done",
        counts={"revision_ids": str(uuid.uuid4())},
    )
    assert await review_gate(session, uuid.uuid4(), str(execution_id)) == "execution_missing"
