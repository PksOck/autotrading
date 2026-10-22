import re
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pytest
from pydantic import BaseModel
from sqlalchemy import func, select

from preza.broker.flex import parse_statement
from preza.domain.radar import (
    EventType,
    NewsIn,
    TimeSensitivity,
    TranslatedText,
    TranslationBatch,
    TriageResult,
)
from preza.llm.client import LlmResult, LlmUnavailableError
from preza.models import Event, NewsItem, Signal
from tests.conftest import FakeRouter

pytestmark = pytest.mark.db
FLEX_XML = (Path(__file__).parent / "fixtures" / "flex_statement.xml").read_text()
NOW = datetime.now(UTC)


class FakeSource:
    def __init__(self, name: str, items: list[NewsIn]):
        self.name = name
        self.items = items

    async def fetch(self, since: datetime) -> list[NewsIn]:
        return [i for i in self.items if i.published_at >= since]


class FakeLlm:
    """Deterministic triage: rumor if the text says so, materiality from keywords."""

    def __init__(self) -> None:
        self.calls = 0

    async def embed(self, texts: list[str]) -> list[list[float]]:
        raise LlmUnavailableError("embed offline")  # exercises the word-overlap fallback

    async def complete_json(self, role, system, user, schema: type[BaseModel]):  # type: ignore[no-untyped-def]
        self.calls += 1
        if schema is TranslationBatch:
            ids = [int(i) for i in re.findall(r"^\[(\d+)\]", user, re.MULTILINE)]
            batch = TranslationBatch(items=[TranslatedText(id=i, text=f"SL #{i}") for i in ids])
            return LlmResult(value=batch, model="fake-local", prompt_tokens=1, completion_tokens=1)
        text = user.lower()
        rumor = "rumor" in text or "reddit" in text
        value = TriageResult(
            tickers=["MSFT"] if "microsoft" in text else [],
            event_type=EventType.RUMOR if rumor else EventType.GUIDANCE,
            is_rumor=rumor,
            sentiment=0.6,
            materiality=0.9,
            novelty=0.9,
            time_sensitivity=TimeSensitivity.DAYS,
            summary="Microsoft raised full-year cloud guidance.",
        )
        return LlmResult(value=value, model="fake-local", prompt_tokens=10, completion_tokens=10)


def news(
    title: str,
    url: str,
    minutes_ago: int,
    kind: str = "press_release",
    symbols: list[str] | None = None,
) -> NewsIn:
    return NewsIn(
        source="rss:test" if kind != "social" else "reddit",
        url=url,
        title=title,
        summary=title,
        published_at=NOW - timedelta(minutes=minutes_ago),
        symbols=symbols if symbols is not None else ["MSFT"],
        kind=kind,  # type: ignore[arg-type]
    )


async def seed_portfolio() -> None:
    from preza.db import get_sessionmaker
    from preza.services.portfolio import store_statement

    async with get_sessionmaker()() as session:
        await store_statement(session, parse_statement(FLEX_XML))
        await session.commit()


async def run(
    sources: list[FakeSource], llm: FakeLlm, threshold: float = 0.3, locale: str = "en"
) -> dict[str, int]:
    from preza.db import get_sessionmaker
    from preza.radar.pipeline import run_radar

    async with get_sessionmaker()() as session:
        result = await run_radar(session, sources, llm, threshold=threshold, locale=locale)  # type: ignore[arg-type]
        await session.commit()
    return {"new": result.new_items, "events": result.events, "signals": result.signals}


async def test_similar_news_form_one_event_and_a_signal(
    api: tuple[httpx.AsyncClient, FakeRouter],
) -> None:
    from preza.db import get_sessionmaker

    await seed_portfolio()
    llm = FakeLlm()
    source = FakeSource(
        "test",
        [
            news(
                "Microsoft raises full-year cloud revenue guidance",
                "https://x.test/a?utm_source=rss",
                30,
            ),
            news("Microsoft raises cloud revenue guidance for the year", "https://y.test/b", 20),
        ],
    )
    first = await run([source], llm)
    assert first == {"new": 2, "events": 1, "signals": 1}

    again = await run([source], llm)  # same items again: nothing new, no duplicate signal
    assert again["new"] == 0

    async with get_sessionmaker()() as session:
        assert await session.scalar(select(func.count()).select_from(NewsItem)) == 2
        event = await session.scalar(select(Event))
        assert event is not None and event.symbols == ["MSFT"] and float(event.score or 0) > 0.3
        signal = await session.scalar(select(Signal))
        assert signal is not None and signal.status == "new" and signal.direction == "up"
        assert len(signal.evidence) == 2 and signal.rationale.startswith("Microsoft")


async def test_rumor_is_watched_until_an_official_source_confirms(
    api: tuple[httpx.AsyncClient, FakeRouter],
) -> None:
    from preza.db import get_sessionmaker

    await seed_portfolio()
    llm = FakeLlm()
    rumor = news(
        "Reddit rumor: Microsoft raises cloud guidance soon",
        "https://reddit.test/1",
        50,
        kind="social",
    )
    # Rumors carry a 0.6 penalty (score ~0.24 here), so this test uses a low threshold.
    await run([FakeSource("reddit", [rumor])], llm, threshold=0.2)

    async with get_sessionmaker()() as session:
        signal = await session.scalar(select(Signal))
        assert signal is not None and signal.is_rumor and signal.status == "watching"

    official = news("Microsoft raises cloud guidance", "https://ir.test/pr", 10)
    await run([FakeSource("test", [official])], llm, threshold=0.2)
    async with get_sessionmaker()() as session:
        signal = await session.scalar(select(Signal))
        event = await session.scalar(select(Event))
        assert event is not None and not event.is_rumor and len(event.items) == 2
        assert signal is not None and not signal.is_rumor and signal.status == "new"


async def test_without_local_model_events_wait_instead_of_scoring_blind(
    api: tuple[httpx.AsyncClient, FakeRouter],
) -> None:
    from preza.db import get_sessionmaker

    await seed_portfolio()
    await run(
        [FakeSource("test", [news("Microsoft opens new data center", "https://z.test/1", 5)])], None
    )  # type: ignore[arg-type]
    async with get_sessionmaker()() as session:
        event = await session.scalar(select(Event))
        assert event is not None and event.score is None and event.triaged_at is None
        assert await session.scalar(select(func.count()).select_from(Signal)) == 0


async def test_summaries_are_translated_for_the_user_locale(
    api: tuple[httpx.AsyncClient, FakeRouter],
) -> None:
    from preza.db import get_sessionmaker

    client, _ = api
    await seed_portfolio()
    llm = FakeLlm()
    source = FakeSource("test", [news("Microsoft raises cloud guidance", "https://x/t1", 30)])
    await run([source], llm, locale="sl")

    async with get_sessionmaker()() as session:
        event = (await session.scalars(select(Event))).one()
        signal = (await session.scalars(select(Signal))).one()
    assert event.summary == "Microsoft raised full-year cloud guidance."
    assert event.summary_i18n == {"sl": f"SL #{event.id}"}
    assert signal.rationale_i18n == {"sl": f"SL #{event.id}"}

    calls = llm.calls
    await run([source], llm, locale="sl")
    assert llm.calls == calls  # already translated: no second call

    body = (await client.get("/signals")).json()
    assert body[0]["rationale_translations"] == {"sl": f"SL #{event.id}"}


async def test_english_locale_skips_translation(api: tuple[httpx.AsyncClient, FakeRouter]) -> None:
    from preza.db import get_sessionmaker

    await seed_portfolio()
    llm = FakeLlm()
    await run([FakeSource("test", [news("Microsoft raises guidance", "https://x/t2", 30)])], llm)
    async with get_sessionmaker()() as session:
        event = (await session.scalars(select(Event))).one()
    assert event.summary_i18n == {}
    assert llm.calls == 1
