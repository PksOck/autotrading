"""Event triage with the local model (`local-fast`, BL-044)."""

import re
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from preza.domain.radar import EventType, TriageResult
from preza.domain.rumor import OFFICIAL_KINDS, item_is_rumor
from preza.llm.client import Llm
from preza.models import Event
from preza.radar.prompts import TRIAGE_SYSTEM, triage_user

TICKER = re.compile(r"^[A-Z][A-Z0-9.]{0,9}$")


async def triage_event(session: AsyncSession, event: Event, llm: Llm) -> TriageResult:
    items = sorted(event.items, key=lambda i: i.published_at)[-5:]
    result = await llm.complete_json(
        "local-fast",
        TRIAGE_SYSTEM,
        triage_user(
            [(i.source, i.published_at.isoformat(), i.title, i.summary or "") for i in items]
        ),
        TriageResult,
    )
    triage = result.value
    official = any(i.kind in OFFICIAL_KINDS for i in event.items)
    # Deterministic hedging survives an LLM verdict that misses it.
    hedged = any(item_is_rumor(i.kind, i.title, i.summary) for i in event.items)
    only_social = all(i.kind == "social" for i in event.items)

    event.summary = triage.summary
    event.event_type = triage.event_type.value
    # A rumor stays a rumor until an official source (filing, press release) joins the event.
    event.is_rumor = (triage.is_rumor or only_social or hedged) and not official
    if event.is_rumor and triage.event_type != EventType.RUMOR and only_social:
        event.event_type = EventType.RUMOR.value
    event.sentiment = Decimal(str(round(triage.sentiment, 4)))
    event.materiality = Decimal(str(round(triage.materiality, 4)))
    event.novelty = Decimal(str(round(triage.novelty, 4)))
    tickers = {t.upper() for t in triage.tickers if TICKER.match(t.upper())}
    event.symbols = sorted(set(event.symbols) | tickers)
    event.triage_model = result.model
    event.triaged_at = datetime.now(UTC)
    return triage
