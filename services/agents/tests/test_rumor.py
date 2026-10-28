from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from preza.config import Settings
from preza.domain.radar import NewsIn
from preza_agents.deep_research.snapshot import _news, news_is_rumor
from preza_agents.worker import _fresh_inputs
from tests.test_stock_analyst import FakeRoleLlm, make_snapshot, run_stock


@pytest.mark.parametrize("kind", ["news", "social", "filing", "press_release"])
@pytest.mark.parametrize("event_flag", [None, False, True])
def test_shared_rule(kind: str, event_flag: bool | None) -> None:
    assert news_is_rumor(kind, "Company reportedly in talks", None, event_flag) == (
        bool(event_flag) or kind in {"news", "social"}
    )
    assert news_is_rumor(kind, "Company reports results", None, event_flag) == bool(event_flag)


async def test_stored_news_classification() -> None:
    now = datetime.now(UTC)
    rows = [
        (
            SimpleNamespace(
                published_at=now,
                title="Company reportedly in talks",
                summary=None,
                source="test",
                url=f"https://example.com/{kind}",
                kind=kind,
                filing_form=None,
                symbols=["AMD"],
            ),
            None,
        )
        for kind in ("news", "filing", "press_release")
    ]
    session = AsyncMock()
    session.execute.return_value = SimpleNamespace(all=lambda: rows)
    news = await _news(session, now, now, "AMD", None)
    assert [n.is_rumor for n in news] == [True, False, False]


async def test_fresh_news_classification() -> None:
    now = datetime.now(UTC)
    items = [
        NewsIn(
            published_at=now,
            title=title,
            summary=summary,
            source="finnhub",
            url=f"https://example.com/{i}",
            kind=kind,
            symbols=["AMD"],
        )
        for i, (kind, title, summary) in enumerate(
            [
                ("news", "Company reportedly in talks", None),
                ("news", "Company update", "Sources said it is exploring a sale"),
                ("news", "Company reports Q3 results", None),
                ("filing", "Company reportedly in talks", None),
                ("press_release", "Company reportedly in talks", None),
            ]
        )
    ]
    session = AsyncMock()
    session.get.return_value = SimpleNamespace(fetched_at=now)
    news_client = SimpleNamespace(company_news=AsyncMock(return_value=items))
    news = await _fresh_inputs(
        session,
        SimpleNamespace(id=1, symbol="AMD"),
        now.date(),
        Settings(finnhub_api_key="test-key"),
        news_client=news_client,
    )
    assert [n.is_rumor for n in news] == [True, True, False, False, False]


async def test_fresh_takeover_headline_gates_bullish_decision() -> None:
    snapshot = make_snapshot()
    now = datetime.now(UTC)
    snapshot.as_of = now.date()
    item = NewsIn(
        published_at=now,
        title="Acme nears deal to buy Beta",
        source="finnhub",
        url="https://example.com/takeover",
        kind="news",
        symbols=[snapshot.symbol],
    )
    session = AsyncMock()
    session.get.return_value = SimpleNamespace(fetched_at=now)
    snapshot.news = await _fresh_inputs(
        session,
        SimpleNamespace(id=1, symbol=snapshot.symbol),
        snapshot.as_of,
        Settings(finnhub_api_key="test-key"),
        news_client=SimpleNamespace(company_news=AsyncMock(return_value=[item])),
    )
    assert len(snapshot.news) == 1 and snapshot.news[0].is_rumor
    snapshot.global_news = []
    result = await run_stock(
        FakeRoleLlm(rating="Buy", evidence_ids=["N1"]),
        snapshot,
        "en",
        lambda _: None,
    )
    assert result.rating == "Hold"
    assert "rumor_unconfirmed" in result.caveats
