import json
from datetime import date
from pathlib import Path

import httpx
import pytest

from preza.domain.valuation import valuation_bands
from preza.fundamentals.finnhub import FinnhubFundamentals, FundamentalsUnavailableError

FIXTURE = Path(__file__).parent / "fixtures" / "finnhub_metric.json"


def client_returning(status: int, body: str | bytes = b"", seen: list[httpx.Request] | None = None):  # type: ignore[no-untyped-def]
    def handler(request: httpx.Request) -> httpx.Response:
        if seen is not None:
            seen.append(request)
        return httpx.Response(status, content=body)

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


async def test_fetch_parses_fixture() -> None:
    seen: list[httpx.Request] = []
    api = FinnhubFundamentals("k", client_returning(200, FIXTURE.read_text(), seen))
    snap = await api.fetch("aapl")
    assert seen[0].url.path == "/api/v1/stock/metric"
    assert seen[0].url.params["symbol"] == "aapl" and seen[0].url.params["metric"] == "all"
    assert snap.source == "finnhub" and snap.symbol == "AAPL"
    assert snap.metrics["pe"] == 31.2
    assert snap.metrics["fcf_yield"] == pytest.approx(100 / 29.4)
    assert snap.metrics["ev_ebit"] == pytest.approx(2960000 / 123000)
    assert snap.metrics["roe_pct"] == 52.1 and snap.metrics["debt_to_equity"] == 0.28
    assert snap.metrics["dividend_yield_pct"] == 0.95 and snap.metrics["payout_ratio_pct"] == 33.0
    pe = snap.history["pe"]
    assert len(pe) == 10 and pe == sorted(pe) and pe[0] == (date(2023, 6, 30), 30.3)
    fcf = snap.history["fcf_yield"]
    assert len(fcf) == 9  # negative pfcf dropped
    assert fcf[-1] == (date(2025, 9, 30), pytest.approx(100 / 30.0))
    assert snap.history["ev_ebit"][-1] == (date(2024, 12, 31), pytest.approx(3300000 / 123000))
    bands = valuation_bands(snap.metrics, {k: v for k, v in snap.history.items()}, snap.as_of)
    assert "ev_ebit" not in bands  # only 3 annual points


async def test_fcf_yield_falls_back_to_cash_flow_over_market_cap() -> None:
    payload = json.loads(FIXTURE.read_text())
    del payload["metric"]["pfcfShareTTM"]
    api = FinnhubFundamentals("k", client_returning(200, json.dumps(payload)))
    snap = await api.fetch("AAPL")
    assert snap.metrics["fcf_yield"] == pytest.approx(99500 / 2925000 * 100)


@pytest.mark.parametrize("status", [429, 401, 500])
async def test_http_errors(status: int) -> None:
    with pytest.raises(FundamentalsUnavailableError):
        await FinnhubFundamentals("k", client_returning(status)).fetch("AAPL")


async def test_network_error_does_not_leak_token() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom", request=request)

    api = FinnhubFundamentals("secret", httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    with pytest.raises(FundamentalsUnavailableError) as exc:
        await api.fetch("AAPL")
    assert "secret" not in str(exc.value)


@pytest.mark.parametrize("body", ["not json", "[]", "{}", '{"metric": {}}'])
async def test_bad_payloads(body: str) -> None:
    with pytest.raises(FundamentalsUnavailableError):
        await FinnhubFundamentals("k", client_returning(200, body)).fetch("AAPL")
