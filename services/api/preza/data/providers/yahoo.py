"""Yahoo Finance chart API (no key). Fallback for daily bars; unofficial, so never primary."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any

import httpx

from preza.data.contract import InstrumentRef, NotFoundError, ProviderUnavailableError
from preza.data.symbols import yahoo_symbol
from preza.domain.market import BarIn

BASE_URL = "https://query1.finance.yahoo.com/v8/finance/chart/"


def parse_chart(payload: dict[str, Any]) -> list[BarIn]:
    chart = payload.get("chart") or {}
    if chart.get("error"):
        raise NotFoundError(str(chart["error"].get("code", "error")))
    results = chart.get("result") or []
    if not results:
        raise NotFoundError("no result")
    result = results[0]
    offset = int((result.get("meta") or {}).get("gmtoffset", 0))
    quote = ((result.get("indicators") or {}).get("quote") or [{}])[0]
    series = {key: quote.get(key) or [] for key in ("open", "high", "low", "close", "volume")}

    def at(key: str, i: int) -> Any:
        values = series[key]
        return values[i] if i < len(values) else None

    bars: list[BarIn] = []
    for i, ts in enumerate(result.get("timestamp") or []):
        prices = [at(key, i) for key in ("open", "high", "low", "close")]
        if any(v is None for v in prices):
            continue  # Yahoo leaves holes for halted or partial days
        o, h, low, c = (Decimal(str(v)) for v in prices)
        volume = at("volume", i)
        day = datetime.fromtimestamp(ts + offset, tz=UTC).date()
        bars.append(BarIn(day=day, open=o, high=h, low=low, close=c, volume=int(volume) if volume else None))
    return bars


class YahooProvider:
    name = "yahoo"

    def __init__(self, client: httpx.AsyncClient | None = None):
        self._client = client or httpx.AsyncClient(timeout=15, headers={"User-Agent": "Mozilla/5.0 Preza"})

    async def daily_bars(self, ref: InstrumentRef, start: date) -> list[BarIn]:
        start_ts = int(datetime.combine(start, datetime.min.time(), UTC).timestamp())
        end_ts = int((datetime.now(UTC) + timedelta(days=1)).timestamp())
        url = BASE_URL + yahoo_symbol(ref.symbol, ref.exchange)
        params: dict[str, str | int] = {
            "period1": start_ts,
            "period2": end_ts,
            "interval": "1d",
            "events": "div,split",
        }
        try:
            response = await self._client.get(url, params=params)
        except httpx.HTTPError as exc:
            raise ProviderUnavailableError(type(exc).__name__) from exc
        if response.status_code == 404:
            raise NotFoundError(ref.symbol)
        if response.status_code >= 400:
            raise ProviderUnavailableError(f"http {response.status_code}")
        return parse_chart(response.json())
