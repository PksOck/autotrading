"""RSS 2.0 / Atom press-release feeds (BL-041). Pure parsing plus a thin HTTP source."""

import html
import re
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from xml.etree.ElementTree import Element, ParseError

import httpx
from defusedxml import ElementTree as DefusedET

from preza.domain.radar import NewsIn, NewsKind
from preza.ingest.base import SourceUnavailableError

# (name, url). TODO: URLs are from memory of the public feed listings; verify once network
# access exists (they are not exercised by tests).
DEFAULT_FEEDS: list[tuple[str, str]] = [
    (
        "globenewswire",
        "https://www.globenewswire.com/RssFeed/orgclass/1/feedTitle/"
        "GlobeNewswire%20-%20News%20about%20Public%20Companies",
    ),
    ("prnewswire", "https://www.prnewswire.com/rss/news-releases-list.rss"),
    ("businesswire", "https://feed.businesswire.com/rss/home/?rss=G1QFDERJXkJeEFpRWA=="),
]

SUMMARY_MAX = 1000

_BLOCK_TAG = re.compile(r"</?(?:br|p|div|li|ul|ol|tr|td|table|h[1-6])\b[^>]*>", re.IGNORECASE)
_ANY_TAG = re.compile(r"<[^>]*>")
_SPACES = re.compile(r"\s+")
_TICKER = re.compile(
    r"(?i:\b(?:NASDAQ|NYSE(?:\s+(?:American|MKT|Arca))?|AMEX|NYSEAMERICAN))"
    r"(?:\s+(?:GS|GM|CM))?\s*:\s*([A-Z]{1,5}(?:[.\-][A-Z])?)\b"
)


def strip_html(text: str) -> str:
    """Remove tags, decode entities and collapse whitespace."""
    text = _BLOCK_TAG.sub(" ", text)
    text = _ANY_TAG.sub("", text)
    return _SPACES.sub(" ", html.unescape(text)).strip()


def extract_tickers(text: str) -> list[str]:
    """Tickers written like "(NASDAQ: MSFT)" or "NYSE American: XYZ", uppercase and deduped."""
    found: list[str] = []
    for match in _TICKER.finditer(text):
        ticker = match.group(1).upper()
        if ticker not in found:
            found.append(ticker)
    return found


def parse_datetime(value: str | None) -> datetime | None:
    """RFC 822 or ISO 8601 into an aware UTC datetime; None when unparseable."""
    if not value or not value.strip():
        return None
    value = value.strip()
    parsed: datetime | None = None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        try:
            parsed = parsedate_to_datetime(value)
        except (TypeError, ValueError):
            return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def local_name(element: Element) -> str:
    return str(element.tag).rsplit("}", 1)[-1]


def children(element: Element, *names: str) -> list[Element]:
    return [child for child in element if local_name(child) in names]


def child_text(element: Element, *names: str) -> str | None:
    """Text of the first non-empty child with one of `names`, tried in the given order."""
    for name in names:
        for child in children(element, name):
            text = "".join(child.itertext()).strip()
            if text:
                return text
    return None


def child_link(element: Element) -> str | None:
    """RSS <link>text</link> or Atom <link href=... rel=alternate/>."""
    for link in children(element, "link"):
        href = link.get("href")
        if href and link.get("rel") in (None, "alternate"):
            return href.strip()
        text = (link.text or "").strip()
        if text:
            return text
    return None


def parse_xml(xml: str) -> Element:
    try:
        return DefusedET.fromstring(xml)
    except (ParseError, ValueError) as exc:
        raise ValueError(f"invalid feed xml: {exc}") from exc


def parse_rss(xml: str, source: str, kind: NewsKind) -> list[NewsIn]:
    """Parse RSS 2.0 and Atom feeds; items lacking title, link or date are skipped."""
    root = parse_xml(xml)
    items: list[NewsIn] = []
    for element in root.iter():
        if local_name(element) not in ("item", "entry"):
            continue
        title = strip_html(child_text(element, "title") or "")
        url = child_link(element)
        published = parse_datetime(child_text(element, "pubDate", "published", "updated", "date"))
        if not title or not url or published is None:
            continue
        summary_full = strip_html(
            child_text(element, "description", "summary", "encoded", "content") or ""
        )
        symbols = extract_tickers(f"{title} {summary_full}")
        items.append(
            NewsIn(
                source=source,
                external_id=child_text(element, "guid", "id"),
                url=url,
                title=title,
                summary=summary_full[:SUMMARY_MAX] or None,
                published_at=published,
                symbols=symbols,
                kind=kind,
            )
        )
    return items


class RssSource:
    def __init__(
        self,
        name: str,
        url: str,
        kind: NewsKind = "press_release",
        client: httpx.AsyncClient | None = None,
    ):
        self.name = f"rss:{name}"
        self._url = url
        self._kind: NewsKind = kind
        self._client = client or httpx.AsyncClient(timeout=15, headers={"User-Agent": "Preza/0.1"})

    async def fetch(self, since: datetime) -> list[NewsIn]:
        try:
            response = await self._client.get(self._url)
        except httpx.HTTPError as exc:
            raise SourceUnavailableError(f"{self.name}: {type(exc).__name__}") from exc
        if response.status_code == 429:
            raise SourceUnavailableError(f"{self.name}: quota")
        if response.status_code >= 400:
            raise SourceUnavailableError(f"{self.name}: http {response.status_code}")
        try:
            items = parse_rss(response.text, self.name, self._kind)
        except ValueError as exc:
            raise SourceUnavailableError(f"{self.name}: {exc}") from exc
        cutoff = since if since.tzinfo else since.replace(tzinfo=UTC)
        return [item for item in items if item.published_at >= cutoff]
