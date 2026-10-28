"""Worker orchestration with transaction fakes. Never connects to a database."""

import asyncio
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from preza.domain.thesis_review import ReviewBatch
from preza.llm.client import LlmResult, LlmSchemaError, LlmTruncatedError, LlmUnavailableError
from preza.services.thesis_reviews import week_start
from preza_agents import worker
from preza_agents.thesis_tracker import runner
from tests.test_thesis_review import recorded_input, recorded_output


@pytest.fixture
def harness(monkeypatch):
    review = SimpleNamespace(
        id=uuid.uuid4(), status="queued", dispatch_at=None, snapshot=recorded_input()
    )
    events = []
    active = 0

    @asynccontextmanager
    async def session():
        nonlocal active
        active += 1
        events.append("open")
        try:
            yield SimpleNamespace(commit=AsyncMock(side_effect=lambda: events.append("commit")))
        finally:
            active -= 1
            events.append("close")

    monkeypatch.setattr(runner, "get_sessionmaker", lambda: session)
    reserve = AsyncMock(return_value=(review, True))
    monkeypatch.setattr(runner.reviews, "reserve_review", reserve)

    async def dispatch(*args):
        events.append("dispatch")
        review.status, review.dispatch_at = "running", datetime.now(UTC)
        return review

    async def finalize(*args, **kwargs):
        events.append("finalize")
        review.status = "done"
        return review

    async def fail(_session, _id, code, **kwargs):
        review.status = "failed_unknown" if kwargs.get("unknown") else "failed"
        review.error_code = code
        return review

    dispatched = AsyncMock(side_effect=dispatch)
    finalized = AsyncMock(side_effect=finalize)
    failed = AsyncMock(side_effect=fail)
    monkeypatch.setattr(runner.reviews, "mark_dispatched", dispatched)
    monkeypatch.setattr(runner.reviews, "finalize_review", finalized)
    monkeypatch.setattr(runner.reviews, "fail_review", failed)
    result = LlmResult(
        value=ReviewBatch.model_validate(recorded_output()),
        model="recorded-model",
        attempts=2,
        prompt_tokens=123,
        completion_tokens=45,
        cost=Decimal("0.01"),
    )

    async def complete(*args, **kwargs):
        assert active == 0
        assert events[-3:] == ["dispatch", "commit", "close"]
        events.append("llm")
        return result

    llm = SimpleNamespace(complete_json=AsyncMock(side_effect=complete))
    return SimpleNamespace(
        review=review,
        llm=llm,
        result=result,
        events=events,
        dispatch=dispatched,
        finalize=finalized,
        fail=failed,
        reserve=reserve,
    )


async def run(h):
    return await runner.thesis_review(
        {"llm": h.llm}, str(uuid.uuid4()), week_start(datetime.now(UTC)).isoformat()
    )


async def test_one_call_committed_phases_and_usage(harness):
    h = harness
    assert await run(h) == "done"
    h.llm.complete_json.assert_awaited_once()
    args, kwargs = h.llm.complete_json.call_args
    assert args[0] == "cloud-deep" and args[3] is ReviewBatch
    assert kwargs == {"max_output_tokens": 4000}
    assert h.finalize.call_args.kwargs == runner.usage(h.result)
    assert h.events.count("commit") == 3
    h.fail.assert_not_awaited()


@pytest.mark.parametrize("status", sorted(runner.reviews.TERMINAL))
async def test_terminal_including_no_evidence_never_calls_llm(harness, status):
    harness.review.status = status
    assert await run(harness) == status
    harness.llm.complete_json.assert_not_awaited()
    harness.dispatch.assert_not_awaited()


async def test_restart_after_dispatch_fails_unknown_without_llm(harness):
    h = harness
    h.review.status, h.review.dispatch_at = "running", datetime.now(UTC)
    h.reserve.return_value = (h.review, False)
    assert await run(h) == "failed_unknown"
    assert h.fail.call_args.args[2] == "interrupted"
    assert h.fail.call_args.kwargs == {"unknown": True}
    h.llm.complete_json.assert_not_awaited()


async def test_restart_before_dispatch_can_continue(harness):
    harness.reserve.return_value = (harness.review, False)
    assert await run(harness) == "done"
    harness.llm.complete_json.assert_awaited_once()


async def test_timeout_is_bounded_and_failed(harness, monkeypatch):
    h = harness
    cancelled = asyncio.Event()

    async def hanging(*args, **kwargs):
        try:
            await asyncio.Event().wait()
        finally:
            cancelled.set()

    h.llm.complete_json.side_effect = hanging
    monkeypatch.setattr(runner, "JOB_TIMEOUT_S", 0.05)
    assert await run(h) == "failed"
    assert cancelled.is_set()
    assert h.fail.call_args.args[2] == "timeout"
    h.finalize.assert_not_awaited()
    assert h.llm.complete_json.await_count == 1


@pytest.mark.parametrize(
    ("error_type", "expected_code"),
    [
        (LlmUnavailableError, "role_unavailable"),
        (LlmTruncatedError, "output_truncated"),
        (LlmSchemaError, "schema_validation_failed"),
    ],
)
async def test_role_error_preserves_usage_without_provider_text(harness, error_type, expected_code):
    h = harness
    exc = error_type("secret provider content")
    exc.attempts, exc.prompt_tokens, exc.completion_tokens = 2, 123, 45
    exc.cost = Decimal("0.01")
    h.llm.complete_json.side_effect = exc
    assert await run(h) == "failed"
    assert h.fail.call_args.args[2] == expected_code
    assert h.fail.call_args.kwargs == runner.usage(exc)
    assert "secret" not in str(h.fail.call_args)
    h.llm.complete_json.assert_awaited_once()
    h.finalize.assert_not_awaited()


@pytest.mark.parametrize("invalid", ["schema", "references"])
async def test_invalid_result_fails_without_publication(harness, invalid):
    h = harness
    output = recorded_output()
    if invalid == "schema":
        output["claims"][0]["unexpected"] = True
        h.result.value = output
    else:
        output["claims"][0]["evidence_ids"] = ["news_item:999"]
        h.result.value = ReviewBatch.model_validate(output)
    assert await run(h) == "failed"
    assert h.fail.call_args.args[2] == (
        "invalid_output" if invalid == "schema" else "invalid_references"
    )
    assert h.fail.call_args.kwargs == runner.usage(h.result)
    h.finalize.assert_not_awaited()


async def test_superseded_before_dispatch_skips_llm(harness):
    async def stale(*args):
        harness.review.status = "stale"
        return harness.review

    harness.dispatch.side_effect = stale
    assert await run(harness) == "stale"
    harness.llm.complete_json.assert_not_awaited()


async def test_superseded_during_call_returns_finalize_state(harness):
    async def stale(*args, **kwargs):
        harness.review.status = "stale"
        return harness.review

    harness.finalize.side_effect = stale
    assert await run(harness) == "stale"
    harness.llm.complete_json.assert_awaited_once()


async def test_dispatch_compare_and_swap_conflict_never_calls_llm(harness):
    harness.dispatch.side_effect = HTTPException(409, "review_already_dispatched_or_finished")
    assert await run(harness) == "conflict"
    harness.llm.complete_json.assert_not_awaited()
    harness.finalize.assert_not_awaited()
    harness.fail.assert_not_awaited()


async def test_unexpected_error_is_safe_and_not_retried(harness):
    harness.llm.complete_json.side_effect = RuntimeError("private provider details")
    assert await run(harness) == "failed"
    assert harness.fail.call_args.args[2] == "internal_error"
    assert "private" not in str(harness.fail.call_args)
    assert await run(harness) == "failed"
    harness.llm.complete_json.assert_awaited_once()


async def test_obsolete_week_job_does_not_reserve_or_call(harness):
    assert (
        await runner.thesis_review({"llm": harness.llm}, str(uuid.uuid4()), "2020-01-06")
        == "obsolete_week"
    )
    harness.reserve.assert_not_awaited()
    harness.llm.complete_json.assert_not_awaited()


async def test_oversized_legacy_snapshot_fails_before_dispatch(harness):
    harness.review.snapshot["claims"][0]["statement"] = "x" * 40000
    assert await run(harness) == "failed"
    harness.dispatch.assert_not_awaited()
    harness.llm.complete_json.assert_not_awaited()


async def test_discovery_week_and_job_id(monkeypatch):
    now = datetime(2027, 1, 3, 6, 15, tzinfo=UTC)
    revision_id = uuid.uuid4()
    scalars = AsyncMock(return_value=[revision_id])

    @asynccontextmanager
    async def session():
        yield SimpleNamespace(scalars=scalars)

    monkeypatch.setattr(worker, "get_sessionmaker", lambda: session)
    monkeypatch.setattr(worker, "_utcnow", lambda: now)
    redis = SimpleNamespace(enqueue_job=AsyncMock())
    assert await worker.discover_thesis_reviews({"redis": redis}) == 1
    redis.enqueue_job.assert_awaited_once_with(
        "thesis_review",
        str(revision_id),
        "2026-12-28",
        _job_id=f"thesis-review:{revision_id}:2026-12-28",
        _queue_name=worker.AGENTS_QUEUE,
    )
    query = str(scalars.call_args.args[0])
    assert "LEFT OUTER JOIN thesis_review" in query
    assert "thesis_review.week_start" in query
    assert "thesis_revision.status" in query


def test_cron_schedule_utc_and_single_worker():
    settings = worker.WorkerSettings
    assert settings.timezone is UTC
    assert settings.max_jobs == 1
    jobs = {c.name: c for c in settings.cron_jobs}
    weekly, daily = jobs["thesis-review-weekly"], jobs["thesis-review-catchup"]
    assert (weekly.weekday, weekly.hour, weekly.minute) == ("sun", 6, 15)
    assert (daily.weekday, daily.hour, daily.minute) == (None, 6, 20)
    review_job = next(f for f in settings.functions if getattr(f, "name", None) == "thesis_review")
    assert review_job.max_tries == 1
    assert runner.JOB_TIMEOUT_S == 660
