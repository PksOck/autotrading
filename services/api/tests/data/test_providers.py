import json
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import httpx
import pytest

from preza.data.contract import InstrumentRef, NotFoundError, ProviderUnavailableError
from preza.data.providers.ibkr import IbkrProvider, duration_for
from preza.data.providers.stooq import StooqProvider, parse_csv
from preza.data.providers.yahoo import YahooProvider, parse_chart
from preza.data.symbols import stooq_symbol, yahoo_symbol
from tests.data.contract_suite import assert_provider_contract

FIXTURES = Path(__file__).parent.parent / "fixtures"
MSFT = InstrumentRef("MSFT", "NASDAQ", "USD")


def client_returning(status: int, body: str | bytes, seen: list[httpx.Request] | None = None):
    def handler(request: httpx.Request) -> httpx.Response:
        if seen is not None:
            seen.append(request)
        return httpx.Response(status, content=body)

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def test_symbol_mapping_for_ucits_listings() -> None:
    assert yahoo_symbol("VWRA", "LSEETF") == "VWRA.L"
    assert yahoo_symbol("BRK.B", "NYSE") == "BRK-B"
    assert stooq_symbol("MSFT", "NASDAQ") == "msft.us"
    assert stooq_symbol("SXR8", "IBIS") == "sxr8.de"


def test_yahoo_parser_skips_holes_and_uses_exchange_dates() -> None:
    bars = parse_chart(json.loads((FIXTURES / "yahoo_chart.json").read_text()))
    assert [b.day for b in bars] == [date(2025, 10, 20), date(2025, 10, 21), date(2025, 10, 23)]
    assert str(bars[-1].close) == "406.8"


def test_yahoo_error_is_not_found() -> None:
    with pytest.raises(NotFoundError):
        parse_chart({"chart": {"result": None, "error": {"code": "Not Found"}}})


async def test_yahoo_provider_contract() -> None:
    seen: list[httpx.Request] = []
    provider = YahooProvider(
        client_returning(200, (FIXTURES / "yahoo_chart.json").read_bytes(), seen)
    )
    await assert_provider_contract(provider, MSFT, date(2025, 1, 1))
    assert seen[0].url.path.endswith("/MSFT")


async def test_yahoo_http_failure_is_unavailable() -> None:
    with pytest.raises(ProviderUnavailableError):
        await YahooProvider(client_returning(503, b"")).daily_bars(MSFT, date(2025, 1, 1))


def test_stooq_parser_and_no_data() -> None:
    bars = parse_csv((FIXTURES / "stooq.csv").read_text())
    assert len(bars) == 3 and bars[0].volume == 21000000
    with pytest.raises(NotFoundError):
        parse_csv("No data")


async def test_stooq_provider_contract() -> None:
    provider = StooqProvider(client_returning(200, (FIXTURES / "stooq.csv").read_bytes()))
    await assert_provider_contract(provider, MSFT, date(2026, 1, 1))


class FakeIB:
    def __init__(self, rows: list[Any], qualify: bool = True):
        self.connected = False
        self.rows = rows
        self.qualify = qualify
        self.data_type: int | None = None
        self.kwargs: dict[str, Any] = {}

    def isConnected(self) -> bool:
        return self.connected

    async def connectAsync(self, host: str, port: int, clientId: int, readonly: bool) -> None:
        assert readonly, "the gateway connection must be read-only (ADR-0006)"
        self.connected = True

    def reqMarketDataType(self, marketDataType: int) -> None:
        self.data_type = marketDataType

    async def qualifyContractsAsync(self, *contracts: Any) -> list[Any]:
        return list(contracts) if self.qualify else [None]

    async def reqHistoricalDataAsync(self, contract: Any, **kwargs: Any) -> list[Any]:
        self.kwargs = kwargs
        return self.rows


def bar(day: date, o: float, h: float, low: float, c: float, v: float) -> SimpleNamespace:
    return SimpleNamespace(date=day, open=o, high=h, low=low, close=c, volume=v)


async def test_ibkr_provider_contract_read_only_and_delayed() -> None:
    ib = FakeIB(
        [
            bar(date(2026, 10, 21), 408, 409.9, 404.1, 405, 100),
            bar(date(2026, 10, 22), 405.2, 407.8, 403.6, 406.8, -1),
        ]
    )
    provider = IbkrProvider(ib, "gw", 4003)
    await assert_provider_contract(provider, MSFT, date(2026, 10, 1))
    assert ib.data_type == 3
    assert ib.kwargs["barSizeSetting"] == "1 day"


async def test_ibkr_unknown_contract_is_not_found() -> None:
    with pytest.raises(NotFoundError):
        await IbkrProvider(FakeIB([], qualify=False), "gw", 4003).daily_bars(MSFT, date(2026, 1, 1))


def test_duration_strings() -> None:
    assert duration_for(date(2026, 10, 1), date(2026, 10, 22)) == "22 D"
    assert duration_for(date(2021, 10, 22), date(2026, 10, 22)) == "6 Y"
