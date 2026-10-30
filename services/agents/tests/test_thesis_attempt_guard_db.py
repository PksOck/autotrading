"""Real dispatch locks plus recorded HTTP, always on an isolated test database."""

import asyncio
import json
import os
import subprocess
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import httpx
import pytest
from sqlalchemy import text

from preza import db
from preza.config import get_settings
from preza.llm.client import LiteLlmClient
from preza.models import (
    AnalysisRun,
    Instrument,
    NewsItem,
    Thesis,
    ThesisClaim,
    ThesisReview,
    ThesisRevision,
)
from preza.models_automation import AutomationControl, ProcessExecution, ProcessPolicy
from preza.services import thesis_reviews as reviews
from preza_agents.thesis_tracker import runner

pytestmark = [
    pytest.mark.db,
    pytest.mark.skipif(not os.getenv("TEST_DATABASE_URL"), reason="isolated database required"),
]


@pytest.fixture(scope="module")
def migrated_guard_db():
    url = os.environ["TEST_DATABASE_URL"]
    # Match the repository TEST_DATABASE_URL contract, with a test-name sanity check.
    assert "test" in url.rsplit("/", 1)[1].lower()
    api = Path(__file__).resolve().parents[2] / "api"
    env = {**os.environ, "DATABASE_URL": url}
    for step in (["downgrade", "base"], ["upgrade", "head"]):
        subprocess.run(["alembic", *step], cwd=api, env=env, check=True, capture_output=True)
    return url


@pytest.fixture
async def review_case(migrated_guard_db, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", migrated_guard_db)
    get_settings.cache_clear()
    db.get_engine.cache_clear()
    db.get_sessionmaker.cache_clear()
    now = datetime.now(UTC)
    async with db.get_engine().begin() as conn:
        await conn.execute(
            text("TRUNCATE instrument, news_item, automation_control, process_policy CASCADE")
        )
    async with db.get_sessionmaker()() as session:
        instrument = Instrument(symbol="GUARD", source="recorded", kind="stock")
        session.add(instrument)
        await session.flush()
        run = AnalysisRun(instrument_id=instrument.id, engine="stock", trade_date=now.date())
        thesis = Thesis(instrument_id=instrument.id, source="recorded", as_of=now)
        session.add_all([run, thesis])
        await session.flush()
        revision = ThesisRevision(
            thesis_id=thesis.id,
            analysis_run_id=run.id,
            version=1,
            status="active",
            source="recorded",
            as_of=now,
        )
        session.add(revision)
        await session.flush()
        claim = ThesisClaim(
            revision_id=revision.id,
            ordinal=1,
            trigger_kind="upgrade",
            trigger_index=0,
            original_text="License renewed",
            statement="License remains valid",
            source="recorded",
            as_of=now,
        )
        news = NewsItem(
            source="edgar",
            url="https://www.sec.gov/Archives/guard",
            title="License renewed",
            summary="The license remains valid.",
            kind="filing",
            published_at=now - timedelta(hours=1),
            fetched_at=now - timedelta(minutes=30),
            symbols=["GUARD"],
        )
        session.add_all([claim, news])
        policy = ProcessPolicy(
            process_key="discover_thesis_reviews", enabled=True, revision=2, config={}
        )
        control = AutomationControl(id=1, paused=False, automatic_analyses_enabled=True)
        session.add_all([policy, control])
        await session.flush()
        review, _ = await reviews.reserve_review(session, revision.id, cutoff=now)
        assert review.status == "queued"
        execution = ProcessExecution(
            process_key=policy.process_key,
            policy_revision=2,
            scheduled_for=now,
            state="done",
            origin="automatic",
            job_id="recorded-review",
            counts={"revision_ids": str(revision.id), "review_week": review.week_start.isoformat()},
        )
        session.add(execution)
        await session.commit()
        case = {
            "review_id": review.id,
            "revision_id": revision.id,
            "execution_id": execution.id,
            "claim_id": claim.id,
            "week": review.week_start.isoformat(),
        }
    yield case
    await db.get_engine().dispose()
    db.get_sessionmaker.cache_clear()
    db.get_engine.cache_clear()
    get_settings.cache_clear()


def response(case, invalid=False):
    content = (
        {}
        if invalid
        else {
            "claims": [
                {
                    "claim_id": str(case["claim_id"]),
                    "assessment": "insufficient",
                    "suggested_status": None,
                    "rationale": "Recorded evidence remains inconclusive.",
                    "evidence_ids": [],
                }
            ]
        }
    )
    return httpx.Response(
        200,
        json={
            "choices": [{"message": {"content": json.dumps(content)}}],
            "usage": {"prompt_tokens": 7, "completion_tokens": 3},
        },
        headers={"x-litellm-response-cost": "0.01"},
    )


async def run(case, llm, **ctx):
    return await runner.thesis_review(
        {"llm": llm, **ctx}, str(case["revision_id"]), case["week"], str(case["execution_id"])
    )


async def stored(case):
    async with db.get_sessionmaker()() as session:
        return await session.get(ThesisReview, case["review_id"])


async def wait_for_database_lock(pid):
    async with asyncio.timeout(5):
        while True:
            async with db.get_sessionmaker()() as session:
                if await session.scalar(
                    text("SELECT cardinality(pg_blocking_pids(:pid)) > 0"), {"pid": pid}
                ):
                    return
            await asyncio.sleep(0.01)


async def test_switch_off_during_actual_mark_dispatched_lock_prevents_http(
    review_case, monkeypatch
):
    case = review_case
    entered = asyncio.Future()
    mark = reviews.mark_dispatched

    async def dispatch(session, review_id):
        entered.set_result(await session.scalar(text("SELECT pg_backend_pid()")))
        return await mark(session, review_id)

    monkeypatch.setattr(reviews, "mark_dispatched", dispatch)
    calls = []
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: (calls.append(request), response(case))[1])
    ) as http:
        async with db.get_sessionmaker()() as lock:
            await lock.get(ThesisReview, case["review_id"], with_for_update=True)
            task = asyncio.create_task(run(case, LiteLlmClient("http://proxy", None, http)))
            try:
                pid = await asyncio.wait_for(entered, 5)
                await wait_for_database_lock(pid)
                async with db.get_sessionmaker()() as switch:
                    control = await switch.get(AutomationControl, 1)
                    control.automatic_analyses_enabled = False
                    await switch.commit()
            finally:
                await lock.rollback()
            outcome = await asyncio.wait_for(task, 5)
    assert calls == []
    assert outcome == "failed"
    review = await stored(case)
    assert review.status == "failed" and review.error_code == "automatic_analyses_disabled"
    assert review.attempts == review.prompt_tokens == review.completion_tokens == 0
    assert review.cost == Decimal("0")
    assert review.finished_at is not None


async def test_automatic_review_repair_rechecks_control_and_keeps_usage(review_case):
    case = review_case
    calls = []

    async def handler(request):
        calls.append(request)
        async with db.get_sessionmaker()() as session:
            control = await session.get(AutomationControl, 1)
            control.automatic_analyses_enabled = False
            await session.commit()
        return response(case, invalid=len(calls) == 1)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        assert await run(case, LiteLlmClient("http://proxy", None, http)) == "failed"
    assert len(calls) == 1
    review = await stored(case)
    assert review.error_code == "automatic_analyses_disabled"
    assert (review.attempts, review.prompt_tokens, review.completion_tokens, review.cost) == (
        1,
        7,
        3,
        Decimal("0.01"),
    )


async def test_manual_durable_origin_and_window_override_allow_repair(review_case):
    case = review_case
    async with db.get_sessionmaker()() as session:
        execution = await session.get(ProcessExecution, case["execution_id"])
        execution.origin, execution.outside_window = "manual", True
        control = await session.get(AutomationControl, 1)
        control.paused, control.automatic_analyses_enabled = True, False
        policy = await session.get(ProcessPolicy, execution.process_key)
        policy.config = {"weekdays": [(datetime.now(UTC).weekday() + 1) % 7]}
        await session.commit()
    calls = []

    def handler(request):
        calls.append(request)
        return response(case, invalid=len(calls) == 1)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        assert await run(case, LiteLlmClient("http://proxy", None, http)) == "done"
    assert len(calls) == 2


async def test_automatic_outside_window_cannot_borrow_context_manual_flag(review_case):
    case = review_case
    async with db.get_sessionmaker()() as session:
        policy = await session.get(ProcessPolicy, "discover_thesis_reviews")
        policy.config = {"weekdays": [(datetime.now(UTC).weekday() + 1) % 7]}
        await session.commit()
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: pytest.fail("unexpected HTTP"))
    ) as http:
        assert (
            await run(case, LiteLlmClient("http://proxy", None, http), manual=True)
            == "outside_window"
        )
    assert (await stored(case)).status == "queued"


@pytest.mark.parametrize("invalid", ["membership", "revision", "week"])
async def test_invalid_durable_execution_cannot_borrow_manual_permission(review_case, invalid):
    case = review_case
    async with db.get_sessionmaker()() as session:
        execution = await session.get(ProcessExecution, case["execution_id"])
        execution.origin, execution.outside_window = "manual", True
        if invalid == "membership":
            execution.counts = {**execution.counts, "revision_ids": str(uuid.uuid4())}
        elif invalid == "revision":
            execution.policy_revision = 1
        else:
            execution.counts = {**execution.counts, "review_week": "2020-01-06"}
        await session.commit()
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: pytest.fail("unexpected HTTP"))
    ) as http:
        assert await run(case, LiteLlmClient("http://proxy", None, http), manual=True) == (
            "policy_changed" if invalid == "revision" else "execution_missing"
        )
    assert (await stored(case)).status == "queued"


async def test_another_dispatch_owner_wins_actual_lock_without_being_failed(
    review_case, monkeypatch
):
    case = review_case
    entered = asyncio.Future()
    mark = reviews.mark_dispatched

    async def dispatch(session, review_id):
        entered.set_result(await session.scalar(text("SELECT pg_backend_pid()")))
        return await mark(session, review_id)

    monkeypatch.setattr(reviews, "mark_dispatched", dispatch)
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: pytest.fail("unexpected HTTP"))
    ) as http:
        async with db.get_sessionmaker()() as owner:
            review = await owner.get(ThesisReview, case["review_id"], with_for_update=True)
            task = asyncio.create_task(run(case, LiteLlmClient("http://proxy", None, http)))
            try:
                pid = await asyncio.wait_for(entered, 5)
                await wait_for_database_lock(pid)
                review.status, review.dispatch_at = "running", datetime.now(UTC)
                await owner.commit()
            finally:
                await owner.rollback()
            assert await asyncio.wait_for(task, 5) == "conflict"
    review = await stored(case)
    assert review.status == "running" and review.error_code is None
