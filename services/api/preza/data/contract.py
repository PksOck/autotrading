"""Market data provider contract (port of the legacy provider-contract idea, BL-020).

Every provider returns daily bars sorted by day, one per day, with consistent OHLC.
`tests/data/contract_suite.py` checks this for every implementation.
"""

from dataclasses import dataclass
from datetime import date
from typing import Protocol

from preza.domain.market import BarIn


@dataclass(frozen=True)
class InstrumentRef:
    symbol: str
    exchange: str | None = None
    currency: str | None = None
    con_id: int | None = None


class ProviderError(Exception):
    """Base error; the router tries the next provider."""


class NotFoundError(ProviderError):
    """The provider does not know this instrument."""


class QuotaExceededError(ProviderError):
    """The provider's quota is used up for now."""


class ProviderUnavailableError(ProviderError):
    """Network, auth or service failure."""


class BarsProvider(Protocol):
    name: str

    async def daily_bars(self, ref: InstrumentRef, start: date) -> list[BarIn]: ...


def normalize_bars(bars: list[BarIn], start: date) -> list[BarIn]:
    """Sort, drop duplicates (last wins), drop bars before `start` or with broken OHLC."""
    by_day: dict[date, BarIn] = {}
    for bar in bars:
        if bar.day < start:
            continue
        if not (bar.low <= min(bar.open, bar.close) and bar.high >= max(bar.open, bar.close)):
            continue
        by_day[bar.day] = bar
    return [by_day[d] for d in sorted(by_day)]
