"""Finnhub company and general news (BL-040). Free tier is rate limited, so 429 means quota."""

from datetime import UTC, datetime
from typing import Any

import httpx

from preza.domain.radar import NewsIn
from preza.ingest.base import SourceUnavailableError

BASE_URL = "https://finnhub.io/api/v1"


def parse_company_news(payload: list[dict[str, Any]], fallback_symbol: str | None) -> list[NewsIn]:
    items: list[NewsIn] = []
    for row in payload:
        headline = str(row.get("headline") or "").strip()
        url = str(row.get("url") or "").strip()
        ts = row.get("datetime")
        if not headline or not url or not isinstance(ts, int | float) or ts <= 0:
            continue
        symbols = [s.strip().upper() for s in str(row.get("related") or "").split(",") if s.strip()]
        if not symbols and fallback_symbol:
            symbols = [fallback_symbol.upper()]
        external_id = row.get("id")
        items.append(
            NewsIn(
                source="finnhub",
                external_id=str(external_id) if external_id is not None else None,
                url=url,
                title=headline,
                summary=str(row.get("summary") or "").strip() or None,
                published_at=datetime.fromtimestamp(ts, tz=UTC),
                symbols=list(dict.fromkeys(symbols)),
                kind="news",
            )
        )
    return items


class FinnhubSource:
    name = "finnhub"

    def __init__(self, api_key: str, symbols: list[str], client: httpx.AsyncClient | None = None):
        self._api_key = api_key
        self._symbols = symbols
        self._client = client or httpx.AsyncClient(timeout=15)

    async def _get(
        self, path: str, params: dict[str, str], *, skip_4xx: bool
    ) -> list[dict[str, Any]]:
        try:
            response = await self._client.get(
                f"{BASE_URL}/{path}", params={**params, "token": self._api_key}
            )
        except httpx.HTTPError as exc:
            # not str(exc): httpx messages can contain the request URL, which carries the token
            raise SourceUnavailableError(f"finnhub: {type(exc).__name__}") from exc
        status = response.status_code
        if status == 429:
            raise SourceUnavailableError("finnhub: quota")
        if status == 401:
            raise SourceUnavailableError("finnhub: unauthorized")
        if status >= 400:
            if skip_4xx and status < 500:
                return []
            raise SourceUnavailableError(f"finnhub: http {status}")
        try:
            payload = response.json()
        except ValueError as exc:
            raise SourceUnavailableError("finnhub: invalid json") from exc
        if not isinstance(payload, list):
            raise SourceUnavailableError("finnhub: unexpected payload")
        return [row for row in payload if isinstance(row, dict)]

    async def company_news(self, symbol: str, start: str, end: str) -> list[NewsIn]:
        rows = await self._get(
            "company-news", {"symbol": symbol, "from": start, "to": end}, skip_4xx=True
        )
        return parse_company_news(rows, symbol)

    async def fetch(self, since: datetime) -> list[NewsIn]:
        cutoff = since if since.tzinfo else since.replace(tzinfo=UTC)
        start = cutoff.astimezone(UTC).date().isoformat()
        end = datetime.now(UTC).date().isoformat()
        by_key: dict[str, NewsIn] = {}

        def add(items: list[NewsIn]) -> None:
            for item in items:
                if item.published_at < cutoff:
                    continue
                key = item.external_id or item.url
                seen = by_key.get(key)
                if seen is None:
                    by_key[key] = item
                else:  # same article returned for several tickers
                    seen.symbols = list(dict.fromkeys([*seen.symbols, *item.symbols]))

        for symbol in self._symbols:
            add(await self.company_news(symbol, start, end))
        rows = await self._get("news", {"category": "general"}, skip_4xx=False)
        add(parse_company_news(rows, None))
        return list(by_key.values())
