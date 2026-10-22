"""Dedupe and store incoming news (BL-040)."""

from collections.abc import Sequence
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from preza.domain.radar import NewsIn
from preza.models import NewsItem

TRACKING = ("utm_", "mc_", "fbclid", "gclid", "cmpid", "ref")


def canonical_url(url: str) -> str:
    parts = urlsplit(url.strip())
    query = [(k, v) for k, v in parse_qsl(parts.query) if not k.lower().startswith(TRACKING)]
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, urlencode(query), ""))


async def store_news(session: AsyncSession, items: Sequence[NewsIn]) -> list[NewsItem]:
    """Inserts unseen items and returns only the new rows (same URL = same item)."""
    by_url: dict[str, NewsIn] = {}
    for item in items:
        url = canonical_url(item.url)
        if url in by_url:
            # e.g. a Form 4 arrives once for the issuer and once for the reporting owner
            first = by_url[url]
            by_url[url] = first.model_copy(
                update={"symbols": sorted({*first.symbols, *item.symbols})}
            )
        else:
            by_url[url] = item
    if not by_url:
        return []
    rows = [
        {
            "source": item.source,
            "external_id": item.external_id,
            "url": url,
            "title": item.title[:500],
            "summary": item.summary,
            "published_at": item.published_at,
            "symbols": sorted({s.upper() for s in item.symbols}),
            "kind": item.kind,
            "filing_form": item.filing_form,
        }
        for url, item in by_url.items()
    ]
    stmt = (
        insert(NewsItem)
        .values(rows)
        .on_conflict_do_nothing(index_elements=["url"])
        .returning(NewsItem.id)
    )
    new_ids = list((await session.execute(stmt)).scalars())
    if not new_ids:
        return []
    return list(
        await session.scalars(
            select(NewsItem).where(NewsItem.id.in_(new_ids)).order_by(NewsItem.published_at)
        )
    )
