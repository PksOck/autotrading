"""One Radar run: fetch → store → cluster → triage → context → score → signal (PLAN §5.2)."""

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from preza.domain.radar import NewsIn
from preza.ingest.base import NewsSource, SourceUnavailableError
from preza.llm.client import Llm, LlmUnavailableError
from preza.models import Event, SyncRun
from preza.radar.cluster import assign_events
from preza.radar.context import attention, reaction_z, relevance
from preza.radar.score import ScoreInput, opportunity_score
from preza.radar.signals import upsert_signal
from preza.radar.store import store_news
from preza.radar.translate import translate_events
from preza.radar.triage import triage_event

log = logging.getLogger(__name__)


@dataclass
class RadarRun:
    fetched: int = 0
    new_items: int = 0
    events: int = 0
    triaged: int = 0
    signals: int = 0
    translated: int = 0
    errors: dict[str, str] = field(default_factory=dict)


async def fetch_all(
    session: AsyncSession, sources: list[NewsSource], since: datetime, run: RadarRun
) -> list[NewsIn]:
    items: list[NewsIn] = []
    for source in sources:
        status, detail = "ok", ""
        try:
            batch = await source.fetch(since)
            items.extend(batch)
            detail = f"{len(batch)} items"
        except SourceUnavailableError as exc:
            status, detail = "failed", str(exc) or type(exc).__name__
            run.errors[source.name] = detail
        now = datetime.now(UTC)
        session.add(
            SyncRun(
                kind=f"news:{source.name}",
                status=status,
                started_at=now,
                finished_at=now,
                detail=detail,
            )
        )
    run.fetched = len(items)
    return items


async def process_events(
    session: AsyncSession,
    events: list[Event],
    llm: Llm | None,
    threshold: float,
    run: RadarRun,
    locale: str = "en",
) -> None:
    sensitivity: dict[int, str] = {}
    for event in events:
        if llm is not None and event.triaged_at is None:
            try:
                triage = await triage_event(session, event, llm)
                sensitivity[event.id] = triage.time_sensitivity.value
                run.triaged += 1
            except LlmUnavailableError as exc:
                run.errors["triage"] = str(exc)
    if llm is not None:
        run.translated = await translate_events(events, llm, locale)

    for event in events:
        if event.materiality is None or event.novelty is None:
            continue  # untriaged events wait for the local model; they are not scored blind

        weight, instrument_id = await relevance(session, event.symbols)
        z = await reaction_z(session, instrument_id) if instrument_id else None
        mentions = max([await attention(session, s) for s in event.symbols[:3]], default=1.0)
        event.reaction_z = Decimal(str(z)) if z is not None else None
        event.attention = Decimal(str(mentions))
        event.score = Decimal(
            str(
                opportunity_score(
                    ScoreInput(
                        materiality=float(event.materiality),
                        novelty=float(event.novelty),
                        reaction_z=z,
                        relevance=weight,
                        is_rumor=event.is_rumor,
                        attention=mentions,
                    )
                )
            )
        )
        if instrument_id is not None and await upsert_signal(
            session, event, instrument_id, threshold, sensitivity.get(event.id, "days")
        ):
            run.signals += 1


async def run_radar(
    session: AsyncSession,
    sources: list[NewsSource],
    llm: Llm | None,
    threshold: float = 0.6,
    lookback: timedelta = timedelta(hours=6),
    locale: str = "en",
) -> RadarRun:
    run = RadarRun()
    items = await fetch_all(session, sources, datetime.now(UTC) - lookback, run)
    stored = await store_news(session, items)
    run.new_items = len(stored)
    touched = await assign_events(session, stored, llm)
    # Also retry events that could not be triaged earlier (local model was down).
    pending = list(
        await session.scalars(
            select(Event).where(
                Event.triaged_at.is_(None),
                Event.last_seen_at >= datetime.now(UTC) - timedelta(days=2),
            )
        )
    )
    events = list({e.id: e for e in [*touched, *pending]}.values())
    run.events = len(events)
    await process_events(session, events, llm, threshold, run, locale)
    await session.flush()
    return run
