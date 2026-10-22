"""Group news about the same happening into events (BL-043).

With embeddings (role `embed`): cosine similarity to the event centroid. Without them
(local model offline): word overlap of titles. Both only within a 48 h window and only
across items that share a symbol or have none.
"""

import math
import re
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from preza.llm.client import Llm, LlmUnavailableError
from preza.models import Event, NewsItem

WINDOW = timedelta(hours=48)
EMBED_THRESHOLD = 0.85
JACCARD_THRESHOLD = 0.5
WORD = re.compile(r"[a-z0-9]{3,}")
STOP = {
    "the",
    "and",
    "for",
    "with",
    "inc",
    "corp",
    "announces",
    "reports",
    "its",
    "from",
    "this",
    "that",
}


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def words(text: str) -> set[str]:
    return {w for w in WORD.findall(text.lower()) if w not in STOP}


def jaccard(a: set[str], b: set[str]) -> float:
    return len(a & b) / len(a | b) if a and b else 0.0


def centroid(vectors: list[list[float]]) -> list[float]:
    return [sum(col) / len(vectors) for col in zip(*vectors, strict=True)] if vectors else []


def _compatible(item: NewsItem, event: Event) -> bool:
    return not item.symbols or not event.symbols or bool(set(item.symbols) & set(event.symbols))


async def assign_events(
    session: AsyncSession, items: list[NewsItem], llm: Llm | None
) -> list[Event]:
    """Attaches each item to a similar recent event or opens one. Returns touched events."""
    if not items:
        return []
    if llm is not None:
        try:
            vectors = await llm.embed([f"{i.title}\n{i.summary or ''}"[:2000] for i in items])
            for item, vector in zip(items, vectors, strict=True):
                item.embedding = vector
        except LlmUnavailableError:
            pass

    since = datetime.now(UTC) - WINDOW
    candidates = list(await session.scalars(select(Event).where(Event.last_seen_at >= since)))
    touched: dict[int, Event] = {}
    for item in items:
        best: Event | None = None
        best_score = 0.0
        for event in candidates:
            if not _compatible(item, event):
                continue
            members = [m for m in event.items if m.id != item.id] or []
            vectors = [m.embedding for m in members if m.embedding]
            if item.embedding and vectors:
                score, threshold = cosine(item.embedding, centroid(vectors)), EMBED_THRESHOLD
            else:
                score = max(
                    (jaccard(words(item.title), words(m.title)) for m in members), default=0.0
                )
                threshold = JACCARD_THRESHOLD
            if score >= threshold and score > best_score:
                best, best_score = event, score
        if best is None:
            best = Event(
                title=item.title,
                summary=item.summary,
                symbols=list(item.symbols),
                is_rumor=item.kind == "social",
                first_seen_at=item.published_at,
                last_seen_at=item.published_at,
            )
            session.add(best)
            await session.flush()
            candidates.append(best)
        else:
            best.symbols = sorted(set(best.symbols) | set(item.symbols))
            best.last_seen_at = max(best.last_seen_at, item.published_at)
            best.triaged_at = None  # new information: triage again
        item.event_id = best.id
        await session.flush()
        await session.refresh(best, ["items"])
        touched[best.id] = best
    return list(touched.values())
