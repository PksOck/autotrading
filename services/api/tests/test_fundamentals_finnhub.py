import json
from datetime import date
from pathlib import Path

import httpx
import pytest

from preza.domain.valuation import valuation_bands
from preza.fundamentals.finnhub import (
    FinnhubFundamentals,
    FundamentalsUnavailableError,
    parse_metric,
)

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


@pytest.mark.parametrize("margin", [46.73, 0, -10, None])
def test_ev_ebit_falls_back_to_revenue_and_operating_margin(margin: float | None) -> None:
    payload = {
        "metric": {"evRevenueTTM": 11.9973, "operatingMarginTTM": margin},
        "series": {
            "annual": {
                "evRevenue": [{"period": f"{year}-06-30", "v": 10.0} for year in range(2019, 2026)],
                "operatingMargin": [
                    {"period": "2025-06-30", "v": 0.4673},
                    {"period": "2024-06-30", "v": 40.0},
                    {"period": "2023-06-30", "v": 0},
                    {"period": "2022-06-30", "v": -0.1},
                    {"period": "2021-06-30", "v": None},
                    {"period": "2018-06-30", "v": 0.5},
                    {"period": "2019-06-30", "v": 1.5},
                ],
            },
            "quarterly": {
                "evRevenue": [{"period": "2025-06-30", "v": 99}],
                "operatingMargin": [{"period": "2025-06-30", "v": 0.1}],
            },
        },
    }
    snap = parse_metric("MSFT", payload, date(2026, 10, 25))
    expected = 11.9973 / (46.73 / 100) if margin == 46.73 else None
    assert snap.metrics["ev_ebit"] == (pytest.approx(expected) if expected else None)
    assert snap.history["ev_ebit"] == [
        (date(2019, 6, 30), pytest.approx(10 / 1.5)),
        (date(2024, 6, 30), pytest.approx(25)),
        (date(2025, 6, 30), pytest.approx(10 / 0.4673)),
    ]


@pytest.mark.parametrize("direct_series", [False, True])
def test_ev_ebit_prefers_existing_paths(direct_series: bool) -> None:
    payload = json.loads(FIXTURE.read_text())
    payload["metric"].update(evRevenueTTM=100, operatingMarginTTM=10)
    payload["series"]["annual"].update(
        evRevenue=[{"period": "2024-12-31", "v": 100}],
        operatingMargin=[{"period": "2024-12-31", "v": 0.1}],
    )
    if direct_series:
        payload["series"]["annual"]["evEbit"] = [{"period": "2024-12-31", "v": 20}]
        payload["series"]["quarterly"]["evEbit"] = [{"period": "2024-12-31", "v": 21}]
    snap = parse_metric("AAPL", payload, date(2026, 10, 25))
    assert snap.metrics["ev_ebit"] == pytest.approx(2960000 / 123000)
    assert snap.history["ev_ebit"][-1] == (
        date(2024, 12, 31),
        pytest.approx(21 if direct_series else 3300000 / 123000),
    )


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
