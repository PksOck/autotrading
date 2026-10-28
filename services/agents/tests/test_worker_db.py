"""The worker against a real Postgres: snapshot from the database, steps and result stored."""

from __future__ import annotations

import os
import subprocess
from collections.abc import AsyncIterator
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import select, text

from preza import db
from preza.config import get_settings
from preza.domain.radar import NewsIn
from preza.fundamentals.finnhub import FundamentalsSnapshot
from preza.ingest.base import SourceUnavailableError
from preza.models import AnalysisRun, AnalysisStep, Bar, Fundamentals, Instrument, NewsItem
from preza_agents import worker
from tests.conftest import make_snapshot
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
        await conn.execute(
            text("TRUNCATE news_item, bar, fundamentals, instrument RESTART IDENTITY CASCADE")
        )
    async with db.get_sessionmaker()() as s:
        yield s
    await db.get_engine().dispose()


async def test_deep_analysis_job(session, monkeypatch: pytest.MonkeyPatch) -> None:  # type: ignore[no-untyped-def]
    llm = FakeRoleLlm()

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
        hypothesis="Rast naročil.",
    )
    session.add(run)
    await session.commit()

    assert (
        await worker.deep_analysis({"llm": llm, "statement_fetcher": lambda *_: {}}, str(run.id))
        == "done"
    )

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
    assert any("ASML wins a large order" in s.content for s in steps if s.kind == "report")
    assert len(llm.calls) == 6
    assert len(run.models["usage"]["calls"]) == 6
    assert all(c["input_token_estimate"] <= 12_000 for c in run.models["usage"]["calls"])
    assert [c["max_output_tokens"] for c in run.models["usage"]["calls"]] == [6000] * 5 + [10_000]
    assert "### Sources" in run.decision and "as_of:" in run.decision
    assert run.card["conviction"] == 6
    assert "delno potrjena" in run.reports["hypothesis_check"]
    assert run.models["hypothesis"] == run.models["deep"]

    # A finished run is not run again.
    assert await worker.deep_analysis({}, str(run.id)) == "done"

    second = AnalysisRun(
        instrument_id=instrument.id,
        engine="tradingagents",
        trade_date=run.trade_date,
        locale="sl",
    )
    session.add(second)
    await session.commit()
    next_llm = FakeRoleLlm(rating="Overweight")
    assert (
        await worker.deep_analysis(
            {"llm": next_llm, "statement_fetcher": lambda *_: {}}, str(second.id)
        )
        == "done"
    )
    await session.refresh(second)
    assert second.card["previous"]["id"] == str(run.id)
    assert second.card["delta_note"]
    assert len(next_llm.calls) == 6


async def test_invalid_stock_decision_uses_worker_failure_path(session) -> None:  # type: ignore[no-untyped-def]
    instrument = Instrument(symbol="FAIL", kind="stock", currency="USD", source="test")
    session.add(instrument)
    await session.flush()
    run = AnalysisRun(
        instrument_id=instrument.id,
        engine="tradingagents",
        trade_date=date(2026, 10, 20),
        locale="en",
    )
    session.add(run)
    await session.commit()
    llm = FakeRoleLlm(decision_fails=True)
    assert (
        await worker.deep_analysis({"llm": llm, "statement_fetcher": lambda *_: {}}, str(run.id))
        == "failed"
    )
    await session.refresh(run)
    assert run.rating is None and run.decision is None and run.card is None
    assert "invalid structured output" in run.error
    assert run.models["usage"]["calls"][-1]["status"] == "failed"
    kinds = list(
        await session.scalars(select(AnalysisStep.kind).where(AnalysisStep.run_id == run.id))
    )
    assert "decision" not in kinds


async def _etf_run(session, hypothesis: str | None = None) -> AnalysisRun:  # type: ignore[no-untyped-def]
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
        instrument_id=instrument.id,
        engine="etf",
        trade_date=date(2026, 10, 20),
        locale="sl",
        hypothesis=hypothesis,
    )
    session.add(run)
    await session.commit()
    return run


async def test_etf_analysis_job(session) -> None:  # type: ignore[no-untyped-def]
    run = await _etf_run(session)
    llm = FakeRoleLlm(rating="Hold")
    assert await worker.deep_analysis({"llm": llm}, str(run.id)) == "done"

    await session.refresh(run)
    assert run.rating == "Hold"
    assert "no_profile" in run.caveats and "no_fundamentals" not in run.caveats
    assert len(llm.calls) == 3  # theme, decision, card
    assert run.card is not None and run.card["conviction"] == 6
    assert run.card["control"]["components"]["valuation"] is None  # a fund has no P/E
    assert run.card["previous"] is None and run.card["delta_note"] is None
    titles = list(
        await session.scalars(
            select(AnalysisStep.title)
            .where(AnalysisStep.run_id == run.id)
            .order_by(AnalysisStep.seq)
        )
    )
    assert titles[0] == "started" and titles[-1] == "done"


async def test_hypothesis_is_checked_after_the_run(session) -> None:  # type: ignore[no-untyped-def]
    run = await _etf_run(session, hypothesis="Polprevodniki bodo rasli z AI.")
    llm = FakeRoleLlm(rating="Overweight")
    assert await worker.deep_analysis({"llm": llm}, str(run.id)) == "done"

    await session.refresh(run)
    assert len(llm.calls) == 4 and "Polprevodniki bodo rasli" in llm.calls[2][2]
    assert llm.calls[2][0] == "cloud-deep"
    assert "delno potrjena" in run.reports["hypothesis_check"]
    assert run.models["hypothesis"] == "fake-cloud-deep"
    titles = list(
        await session.scalars(
            select(AnalysisStep.title)
            .where(AnalysisStep.run_id == run.id)
            .order_by(AnalysisStep.seq)
        )
    )
    assert titles[-2:] == ["hypothesis_check", "done"]


async def test_failed_hypothesis_check_keeps_the_run(session) -> None:  # type: ignore[no-untyped-def]
    run = await _etf_run(session, hypothesis="Polprevodniki bodo rasli z AI.")
    llm = FakeRoleLlm(check_fails=True)
    assert await worker.deep_analysis({"llm": llm}, str(run.id)) == "done"

    await session.refresh(run)
    assert run.rating == "Hold" and "hypothesis_check" not in run.reports
    assert "hypothesis_unchecked" in run.caveats


async def test_card_compares_with_the_previous_run(session) -> None:  # type: ignore[no-untyped-def]
    first = await _etf_run(session)
    assert await worker.deep_analysis({"llm": FakeRoleLlm()}, str(first.id)) == "done"
    second = AnalysisRun(
        instrument_id=first.instrument_id,
        engine="etf",
        trade_date=date(2026, 10, 20),
        locale="sl",
    )
    session.add(second)
    await session.commit()
    llm = FakeRoleLlm(rating="Overweight", conviction=9)
    assert await worker.deep_analysis({"llm": llm}, str(second.id)) == "done"

    await session.refresh(second)
    card = second.card
    assert card is not None
    assert card["previous"] == {"id": str(first.id), "trade_date": "2026-10-20", "rating": "Hold"}
    assert card["delta_note"] and '"rating": "Hold"' in llm.calls[-1][2]
    assert card["size_class"] in ("increased", "small")  # small only when the control disagrees
    assert ("control_disagrees" in second.caveats) == (card["size_class"] == "small")


class _FakeFundamentals:
    def __init__(self) -> None:
        self.calls = 0

    async def fetch(self, symbol: str) -> FundamentalsSnapshot:
        self.calls += 1
        return FundamentalsSnapshot(symbol=symbol, as_of=date.today(), metrics={"pe_ttm": 30.0})


class _FakeNews:
    def __init__(self, fail: bool = False, error: Exception | None = None) -> None:
        self.error = error or (SourceUnavailableError("finnhub: ReadTimeout") if fail else None)

    async def company_news(self, symbol: str, start: str, end: str) -> list[NewsIn]:
        if self.error:
            raise self.error
        now = datetime.now(UTC)
        return [
            NewsIn(
                source="finnhub",
                url="https://example.com/amd",
                title="AMD launches a chip",
                published_at=now,
                symbols=[symbol],
                kind="news",
            )
        ]


async def test_fresh_inputs_fill_gaps_for_an_unwatched_symbol(  # type: ignore[no-untyped-def]
    session, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FINNHUB_API_KEY", "test-key")
    get_settings.cache_clear()
    instrument = Instrument(symbol="AMD", kind="unknown", source="manual")
    session.add(instrument)
    await session.commit()
    funds = _FakeFundamentals()
    today = datetime.now(UTC).date()

    news = await worker._fresh_inputs(
        session, instrument, today, get_settings(), funds, _FakeNews()
    )
    assert [n.title for n in news] == ["AMD launches a chip"]
    assert news[0].symbols == ["AMD"] and news[0].source == "finnhub"
    row = await session.get(Fundamentals, instrument.id)
    assert row is not None and row.metrics == {"pe_ttm": 30.0}
    # News is not stored, so a later radar run still sees the URL as new.
    assert not list(await session.scalars(select(NewsItem)))

    # Fresh fundamentals are kept; a news outage only drops the news.
    assert not await worker._fresh_inputs(
        session, instrument, today, get_settings(), funds, _FakeNews(fail=True)
    )
    assert funds.calls == 1

    # A past run never sees data fetched today.
    past = today - timedelta(days=10)
    assert not await worker._fresh_inputs(
        session, instrument, past, get_settings(), _FakeFundamentals(), _FakeNews()
    )


class _BrokenFundamentals:
    async def fetch(self, symbol: str) -> FundamentalsSnapshot:
        raise RuntimeError("unexpected payload")


async def test_fresh_input_failures_leave_the_run_usable(  # type: ignore[no-untyped-def]
    session, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FINNHUB_API_KEY", "test-key")
    get_settings.cache_clear()
    instrument = Instrument(symbol="AMD", kind="unknown", source="manual")
    session.add(instrument)
    await session.commit()
    instrument.name = "Pending change"  # stands in for the run row marked running

    news = await worker._fresh_inputs(
        session,
        instrument,
        datetime.now(UTC).date(),
        get_settings(),
        _BrokenFundamentals(),
        _FakeNews(error=OverflowError("timestamp out of range")),
    )
    assert news == []
    assert await session.get(Fundamentals, instrument.id) is None
    await session.commit()  # the savepoint rolled back only the failed write
    assert instrument.name == "Pending change"
