"""Stooq daily CSV (no key). Second fallback for daily bars."""

import csv
import io
from datetime import date
from decimal import Decimal, InvalidOperation

import httpx

from preza.data.contract import InstrumentRef, NotFoundError, ProviderUnavailableError
from preza.data.symbols import stooq_symbol
from preza.domain.market import BarIn

BASE_URL = "https://stooq.com/q/d/l/"


def parse_csv(text: str) -> list[BarIn]:
    if not text.strip() or text.strip().lower().startswith("no data"):
        raise NotFoundError("no data")
    reader = csv.DictReader(io.StringIO(text))
    bars: list[BarIn] = []
    for row in reader:
        try:
            bars.append(
                BarIn(
                    day=date.fromisoformat(row["Date"]),
                    open=Decimal(row["Open"]),
                    high=Decimal(row["High"]),
                    low=Decimal(row["Low"]),
                    close=Decimal(row["Close"]),
                    volume=int(float(row["Volume"])) if row.get("Volume") else None,
                )
            )
        except (KeyError, ValueError, InvalidOperation):
            continue
    if not bars:
        raise NotFoundError("unparseable")
    return bars


class StooqProvider:
    name = "stooq"

    def __init__(self, client: httpx.AsyncClient | None = None):
        self._client = client or httpx.AsyncClient(timeout=15)

    async def daily_bars(self, ref: InstrumentRef, start: date) -> list[BarIn]:
        params = {
            "s": stooq_symbol(ref.symbol, ref.exchange),
            "i": "d",
            "d1": start.strftime("%Y%m%d"),
        }
        try:
            response = await self._client.get(BASE_URL, params=params)
        except httpx.HTTPError as exc:
            raise ProviderUnavailableError(type(exc).__name__) from exc
        if response.status_code >= 400:
            raise ProviderUnavailableError(f"http {response.status_code}")
        return parse_csv(response.text)
