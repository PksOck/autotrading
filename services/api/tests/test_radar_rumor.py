from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from preza.domain.radar import EventType, SignalStatus, TimeSensitivity, TriageResult
from preza.models import Event, NewsItem, Signal
from preza.radar import signals
from preza.radar.cluster import assign_events
from preza.radar.triage import triage_event


def news(kind: str, title: str, summary: str | None = None) -> NewsItem:
    return NewsItem(
        id=1,
        kind=kind,
        title=title,
        summary=summary,
        symbols=["ACME"],
        published_at=datetime.now(UTC),
    )


def session_for(events: list[Event]) -> AsyncSession:
    session = AsyncMock(spec=AsyncSession)
    session.scalars.return_value = events
    session.add = Mock(side_effect=lambda event: setattr(event, "id", 10))
    return session


@pytest.mark.parametrize(
    ("kind", "title", "summary", "expected"),
    [
        ("news", "Acme nears deal to buy Beta - sources", None, True),
        ("news", "Acme reports quarterly update", "Sources say a deal is close", True),
        ("press_release", "Acme nears deal to buy Beta - sources", None, False),
        ("filing", "Acme nears deal to buy Beta - sources", None, False),
        ("press_release", "Acme quarterly update", "Reportedly a deal is close", False),
        ("filing", "Acme quarterly update", "Reportedly a deal is close", False),
        ("social", "Acme reports quarterly earnings", None, True),
        ("news", "Acme reports quarterly earnings", None, False),
    ],
)
async def test_new_event_classifies_rumor(
    kind: str, title: str, summary: str | None, expected: bool
) -> None:
    item = news(kind, title, summary)
    session = session_for([])

    events = await assign_events(session, [item], None)

    assert len(events) == 1
    assert events[0].is_rumor is expected
    assert item.event_id == events[0].id


@pytest.mark.parametrize(
    ("initial_flag", "kind", "title", "expected"),
    [
        (True, "press_release", "Acme agrees deal to buy Beta", True),
        (True, "filing", "Acme agrees deal to buy Beta", True),
        (True, "news", "Acme agrees deal to buy Beta", True),
        (False, "news", "Acme nears deal to buy Beta - sources", True),
        # A plain social post does not flip a news event; triage decides (only_social rule).
        (False, "social", "Acme agrees deal to buy Beta", False),
        (False, "social", "Acme reportedly agrees deal to buy Beta", True),
        (False, "press_release", "Acme nears deal to buy Beta - sources", False),
        (False, "news", "Acme agrees deal to buy Beta", False),
    ],
)
async def test_join_preserves_or_adds_rumor_flag(
    initial_flag: bool, kind: str, title: str, expected: bool
) -> None:
    member = news("news", "Acme agrees deal to buy Beta")
    member.id = 2
    event = Event(
        id=10,
        title=member.title,
        symbols=["ACME"],
        is_rumor=initial_flag,
        last_seen_at=member.published_at,
        triaged_at=member.published_at,
        items=[member],
    )
    item = news(kind, title)
    session = session_for([event])

    assert await assign_events(session, [item], None) == [event]

    assert event.is_rumor is expected
    assert item.event_id == event.id
    assert event.triaged_at is None
    session.add.assert_not_called()


@pytest.mark.parametrize(
    ("kinds_titles", "llm_flag", "expected"),
    [
        ([("news", "Acme nears deal to buy Beta - sources")], False, True),
        ([("news", "Acme reports quarterly earnings")], False, False),
        ([("news", "Acme reports quarterly earnings")], True, True),
        (
            [
                ("news", "Acme nears deal to buy Beta - sources"),
                ("press_release", "Acme agrees to acquire Beta"),
            ],
            True,
            False,
        ),
        (
            [
                ("news", "Acme nears deal to buy Beta - sources"),
                ("filing", "Acme 8-K: agreement to acquire Beta"),
            ],
            True,
            False,
        ),
        ([("social", "Acme to buy Beta")], False, True),
        ([("social", "Acme to buy Beta"), ("news", "Acme shares rise")], False, False),
        ([("social", "Acme to buy Beta"), ("news", "Acme shares rise")], True, True),
        # Hedged item outside the last five sent to the LLM still counts.
        (
            [("news", "Acme in talks with Beta, people familiar say")]
            + [("news", f"Acme shares move {n}") for n in range(5)],
            False,
            True,
        ),
    ],
)
async def test_triage_keeps_deterministic_rumor_flag(
    kinds_titles: list[tuple[str, str]], llm_flag: bool, expected: bool
) -> None:
    event = Event(
        title=kinds_titles[0][1],
        symbols=["ACME"],
        is_rumor=False,
        first_seen_at=datetime.now(UTC),
        last_seen_at=datetime.now(UTC),
    )
    event.items = [news(kind, title) for kind, title in kinds_titles]
    for n, item in enumerate(event.items):
        item.published_at = datetime(2026, 10, 1, n, tzinfo=UTC)
    triage = TriageResult(
        event_type=EventType.MERGER,
        is_rumor=llm_flag,
        sentiment=0.1,
        materiality=0.5,
        novelty=0.5,
        time_sensitivity=TimeSensitivity.DAYS,
        summary="Acme and Beta deal news.",
    )
    llm = Mock()
    llm.complete_json = AsyncMock(return_value=Mock(value=triage, model="test"))

    await triage_event(AsyncMock(spec=AsyncSession), event, llm)

    assert event.is_rumor is expected


async def test_summary_only_hedging_survives_triage() -> None:
    event = Event(
        title="Acme update",
        symbols=["ACME"],
        is_rumor=False,
        first_seen_at=datetime.now(UTC),
        last_seen_at=datetime.now(UTC),
    )
    event.items = [news("news", "Acme update", "Acme is said to weigh a bid for Beta")]
    triage = TriageResult(
        event_type=EventType.MERGER,
        is_rumor=False,
        sentiment=0.1,
        materiality=0.5,
        novelty=0.5,
        time_sensitivity=TimeSensitivity.DAYS,
        summary="Acme may bid for Beta.",
    )
    llm = Mock()
    llm.complete_json = AsyncMock(return_value=Mock(value=triage, model="test"))

    await triage_event(AsyncMock(spec=AsyncSession), event, llm)

    assert event.is_rumor is True


@pytest.mark.parametrize(
    ("status", "expected_status"),
    [(SignalStatus.NEW.value, SignalStatus.WATCHING.value), ("accepted", "accepted")],
)
async def test_signal_below_threshold_picks_up_rumor(
    monkeypatch: pytest.MonkeyPatch, status: str, expected_status: str
) -> None:
    async def weight(*_: object) -> Decimal:
        return Decimal(1)

    monkeypatch.setattr(signals, "active_weight", weight)
    event = Event(id=10, title="Acme nears deal - sources", symbols=["ACME"], is_rumor=True)
    event.score = 0.1
    existing = Signal(event_id=10, is_rumor=False, status=status)
    session = AsyncMock(spec=AsyncSession)
    session.scalar.return_value = existing

    result = await signals.upsert_signal(session, event, 1, threshold=0.6)

    assert result is existing
    assert existing.is_rumor is True
    assert existing.status == expected_status
