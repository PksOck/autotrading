"""SEC EDGAR "latest filings" Atom feeds (BL-041). EDGAR gives CIK, not ticker."""

import re
from datetime import UTC, datetime
from typing import Any

import httpx

from preza.domain.radar import NewsIn
from preza.ingest.base import SourceUnavailableError
from preza.ingest.rss import (
    child_link,
    child_text,
    children,
    local_name,
    parse_datetime,
    parse_xml,
    strip_html,
)

FEED_URL = "https://www.sec.gov/cgi-bin/browse-edgar"
DEFAULT_FORMS = ("8-K", "4", "SC 13D")

_TITLE = re.compile(
    r"^(?P<form>.+?)\s+-\s+(?P<name>.+?)\s+\((?P<cik>\d{1,10})\)(?:\s+\((?P<role>[^)]*)\))?\s*$"
)
_ACCESSION = re.compile(r"AccNo:\s*(\d{10}-\d{2}-\d{6})")
_ITEMS = re.compile(r"Size:\s*\S+\s*\S*\s*(.*)$")


def parse_edgar_atom(xml: str) -> list[NewsIn]:
    root = parse_xml(xml)
    items: list[NewsIn] = []
    for entry in root.iter():
        if local_name(entry) != "entry":
            continue
        raw_title = strip_html(child_text(entry, "title") or "")
        url = child_link(entry)
        published = parse_datetime(child_text(entry, "updated", "published"))
        if not raw_title or not url or published is None:
            continue
        match = _TITLE.match(raw_title)
        form = ""
        for category in children(entry, "category"):
            form = (category.get("term") or "").strip()
            if form:
                break
        title = raw_title
        cik: str | None = None
        if match:
            form = form or match.group("form").strip()
            cik = match.group("cik").zfill(10)
            title = f"{match.group('form').strip()} · {match.group('name').strip()}"
        body = strip_html(child_text(entry, "summary", "content") or "")
        accession = _ACCESSION.search(body)
        parts = [f"CIK {cik}"] if cik else []
        items_match = _ITEMS.search(body)
        if items_match and items_match.group(1):
            parts.append(items_match.group(1))
        items.append(
            NewsIn(
                source="edgar",
                external_id=accession.group(1) if accession else child_text(entry, "id"),
                url=url,
                title=title,
                summary=" · ".join(parts) or None,
                published_at=published,
                symbols=[],
                kind="filing",
                filing_form=form or None,
            )
        )
    return items


def parse_company_tickers(payload: dict[str, Any]) -> dict[str, str]:
    """SEC company_tickers.json into {10-digit zero-padded CIK: ticker}; first ticker wins."""
    mapping: dict[str, str] = {}
    for row in payload.values():
        if not isinstance(row, dict):
            continue
        cik, ticker = row.get("cik_str"), row.get("ticker")
        if cik is None or not ticker:
            continue
        try:
            key = str(int(cik)).zfill(10)
        except (TypeError, ValueError):
            continue
        mapping.setdefault(key, str(ticker).upper())
    return mapping


def _cik_of(item: NewsIn) -> str | None:
    match = re.match(r"CIK (\d{10})", item.summary or "")
    return match.group(1) if match else None


class EdgarSource:
    name = "edgar"

    def __init__(
        self,
        user_agent: str,
        forms: tuple[str, ...] = DEFAULT_FORMS,
        cik_to_ticker: dict[str, str] | None = None,
        client: httpx.AsyncClient | None = None,
    ):
        self._user_agent = user_agent
        self._forms = forms
        self._cik_to_ticker = cik_to_ticker
        self._client = client or httpx.AsyncClient(timeout=20)

    async def _fetch_form(self, form: str) -> list[NewsIn]:
        params = {
            "action": "getcurrent",
            "type": form,
            "company": "",
            "dateb": "",
            "owner": "include",
            "count": "100",
            "output": "atom",
        }
        try:
            response = await self._client.get(
                FEED_URL, params=params, headers={"User-Agent": self._user_agent}
            )
        except httpx.HTTPError as exc:
            raise SourceUnavailableError(f"edgar: {type(exc).__name__}") from exc
        status = response.status_code
        if status == 429:
            raise SourceUnavailableError("edgar: quota")
        if status == 403:
            raise SourceUnavailableError("edgar: forbidden (check User-Agent)")
        if status >= 400:
            raise SourceUnavailableError(f"edgar: http {status}")
        try:
            return parse_edgar_atom(response.text)
        except ValueError as exc:
            raise SourceUnavailableError(f"edgar: {exc}") from exc

    async def fetch(self, since: datetime) -> list[NewsIn]:
        cutoff = since if since.tzinfo else since.replace(tzinfo=UTC)
        seen: set[str] = set()
        result: list[NewsIn] = []
        for form in self._forms:
            for item in await self._fetch_form(form):
                key = item.url
                if item.published_at < cutoff or key in seen:
                    continue
                seen.add(key)
                if self._cik_to_ticker is not None:
                    cik = _cik_of(item)
                    ticker = self._cik_to_ticker.get(cik) if cik else None
                    if ticker:
                        item.symbols = [ticker]
                result.append(item)
        return result
