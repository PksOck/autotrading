"""The worker against a real Postgres: snapshot from the database, steps and result stored."""

from __future__ import annotations

import os
import subprocess
from collections.abc import AsyncIterator
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import select, text

from preza import db
from preza.config import get_settings
from preza.models import AnalysisRun, AnalysisStep, Bar, Instrument, NewsItem
from preza_agents import worker
from tests.conftest import make_snapshot
from tests.fake_llm import FakeChat, FakeClient
from tests.fake_role_llm import FakeRoleLlm

API_ROOT = Path(__file__).parents[2] / "api"
TEST_DB = os.environ.get("TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not TEST_DB, reason="TEST_DATABASE_URL not set")


@pytest.fixture(scope="module")
def migrated() -> str:
    assert TEST_DB
    env = {**os.environ, "DATABASE_URL": TEST_DB}
    subprocess.run(
        ["alembic", "upgrade", "head"], cwd=API_ROOT, env=env, check=True, capture_output=True
    )
    return TEST_DB


@pytest.fixture
async def session(
    migrated: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> AsyncIterator[object]:
    assert TEST_DB
    monkeypatch.setenv("DATABASE_URL", TEST_DB)
    monkeypatch.setenv("AGENTS_HOME", str(tmp_path))
    get_settings.cache_clear()
    db.get_engine.cache_clear()
    db.get_sessionmaker.cache_clear()
    async with db.get_engine().begin() as conn:
        await conn.execute(text("TRUNCATE news_item, bar, instrument RESTART IDENTITY CASCADE"))
    async with db.get_sessionmaker()() as s:
        yield s
    await db.get_engine().dispose()


async def test_deep_analysis_job(session, monkeypatch: pytest.MonkeyPatch) -> None:  # type: ignore[no-untyped-def]
    from tradingagents.graph import trading_graph

    llm = FakeChat(rating="Hold", seen_tool_output=[])
    monkeypatch.setattr(trading_graph, "create_tier_client", lambda *a, **k: FakeClient(llm))

    fixture = make_snapshot()
    instrument = Instrument(
        symbol="ASML",
        name="ASML Holding N.V.",
        kind="stock",
        exchange="NASDAQ",
        currency="USD",
        source="test",
    )
    session.add(instrument)
    await session.flush()
    for bar in fixture.bars:
        session.add(
            Bar(
                instrument_id=instrument.id,
                day=bar.day,
                open=bar.open,
                high=bar.high,
                low=bar.low,
                close=bar.close,
                volume=bar.volume,
                source="ibkr",
            )
        )
    session.add(
        NewsItem(
            source="press_release",
            url="https://example.com/n1",
            title="ASML wins a large order",
            kind="press_release",
            symbols=["ASML"],
            published_at=datetime(2026, 10, 19, 8, tzinfo=UTC),
        )
    )
    run = AnalysisRun(
        instrument_id=instrument.id,
        engine="tradingagents",
        trade_date=date(2026, 10, 20),
        locale="sl",
    )
    session.add(run)
    await session.commit()

    assert await worker.deep_analysis({}, str(run.id)) == "done"

    await session.refresh(run)
    assert run.rating == "Hold"
    assert run.snapshot is not None and run.snapshot["bars"][-1]["day"] == "2026-10-20"
    assert Decimal(run.snapshot["bars"][-1]["close"]) == fixture.bars[-2].close
    assert "no_fundamentals" in run.caveats
    steps = list(
        await session.scalars(
            select(AnalysisStep).where(AnalysisStep.run_id == run.id).order_by(AnalysisStep.seq)
        )
    )
    assert [s.seq for s in steps] == list(range(1, len(steps) + 1))
    assert steps[0].title == "started" and steps[-1].title == "done"
    assert any(s.kind == "decision" for s in steps)
    assert any("ASML wins a large order" in out for out in llm.seen_tool_output)

    # A finished run is not run again.
    assert await worker.deep_analysis({}, str(run.id)) == "done"


async def test_etf_analysis_job(session) -> None:  # type: ignore[no-untyped-def]
    fixture = make_snapshot()
    instrument = Instrument(
        symbol="SEMI",
        name="iShares MSCI Global Semiconductors UCITS ETF (Acc)",
        kind="etf",
        exchange="LSEETF",
        currency="USD",
        source="test",
    )
    session.add(instrument)
    await session.flush()
    for bar in fixture.bars:
        session.add(
            Bar(
                instrument_id=instrument.id,
                day=bar.day,
                open=bar.open,
                high=bar.high,
                low=bar.low,
                close=bar.close,
                volume=bar.volume,
                source="ibkr",
            )
        )
    run = AnalysisRun(
        instrument_id=instrument.id, engine="etf", trade_date=date(2026, 10, 20), locale="sl"
    )
    session.add(run)
    await session.commit()

    llm = FakeRoleLlm(rating="Hold")
    assert await worker.deep_analysis({"llm": llm}, str(run.id)) == "done"

    await session.refresh(run)
    assert run.rating == "Hold"
    assert "no_profile" in run.caveats and "no_fundamentals" not in run.caveats
    assert len(llm.calls) == 2
    titles = list(
        await session.scalars(
            select(AnalysisStep.title)
            .where(AnalysisStep.run_id == run.id)
            .order_by(AnalysisStep.seq)
        )
    )
    assert titles[0] == "started" and titles[-1] == "done"
