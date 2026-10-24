"""Daily bars from IB Gateway via ib_async (primary source, delayed data is enough, ADR-0006).

Prirejeno po zamisli iz Vibe-Trading agent/src/trading/connectors/ibkr/local.py (MIT):
read-only connection, delayed market data by default, no order methods.
"""

import asyncio
from datetime import date
from decimal import Decimal
from typing import Any, Protocol

from preza.data.contract import InstrumentRef, NotFoundError, ProviderUnavailableError
from preza.domain.market import BarIn

DELAYED = 3  # reqMarketDataType: 15-minute delayed data, free (no subscription needed)


class IBLike(Protocol):
    """The subset of ib_async.IB this provider uses (lets tests inject a fake)."""

    def isConnected(self) -> bool: ...
    async def connectAsync(self, host: str, port: int, clientId: int, readonly: bool) -> Any: ...
    def reqMarketDataType(self, marketDataType: int) -> None: ...
    async def qualifyContractsAsync(self, *contracts: Any) -> list[Any]: ...
    async def reqHistoricalDataAsync(self, contract: Any, **kwargs: Any) -> list[Any]: ...


def make_contract(ref: InstrumentRef) -> Any:
    from ib_async import Contract, Stock

    if ref.con_id:
        return Contract(conId=ref.con_id)
    exchange = "SMART" if ref.exchange in (None, "", "NASDAQ", "NYSE", "ARCA") else ref.exchange
    return Stock(ref.symbol, exchange, ref.currency or "USD")


def duration_for(start: date, today: date) -> str:
    days = (today - start).days + 1
    return f"{days} D" if days <= 365 else f"{min(20, days // 365 + 1)} Y"


class IbkrProvider:
    name = "ibkr"

    def __init__(self, ib: IBLike, host: str, port: int, client_id: int = 17):
        self._ib = ib
        self._host = host
        self._port = port
        self._client_id = client_id
        self._lock = asyncio.Lock()  # IB pacing: one historical request at a time

    async def _ensure_connected(self) -> None:
        if self._ib.isConnected():
            return
        try:
            await self._ib.connectAsync(self._host, self._port, clientId=self._client_id, readonly=True)
        except (OSError, TimeoutError) as exc:
            raise ProviderUnavailableError(f"gateway: {type(exc).__name__}") from exc
        self._ib.reqMarketDataType(DELAYED)

    async def daily_bars(self, ref: InstrumentRef, start: date) -> list[BarIn]:
        async with self._lock:
            await self._ensure_connected()
            qualified = await self._ib.qualifyContractsAsync(make_contract(ref))
            if not qualified or qualified[0] is None:
                raise NotFoundError(ref.symbol)
            rows = await self._ib.reqHistoricalDataAsync(
                qualified[0],
                endDateTime="",
                durationStr=duration_for(start, date.today()),
                barSizeSetting="1 day",
                whatToShow="TRADES",
                useRTH=True,
                formatDate=1,
            )
        return [
            BarIn(
                day=row.date if isinstance(row.date, date) else row.date.date(),
                open=Decimal(str(row.open)),
                high=Decimal(str(row.high)),
                low=Decimal(str(row.low)),
                close=Decimal(str(row.close)),
                volume=int(row.volume) if row.volume and row.volume > 0 else None,
            )
            for row in rows
        ]
