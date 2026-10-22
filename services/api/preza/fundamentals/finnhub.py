"""Finnhub fundamentals for valuation bands (BL-061).

Endpoint: GET /stock/metric?symbol=..&metric=all (free tier, 60 calls/min).

NOTE: parsed against Finnhub's documented response shape and a hand-written fixture only.
Live verification against finnhub.io is pending (same status as BL-059); series key names
are therefore matched against several candidates.

Field choices:
- pe: current `peTTM`, else `peBasicExclExtraTTM`; history from series `pe` / `peTTM`.
- fcf_yield (percent): current 100 / `pfcfShareTTM` when positive, else
  `freeCashFlowTTM` / `marketCapitalization` * 100 (both in millions); history is
  100 / `pfcf` for each point where pfcf > 0.
- ev_ebit: current `enterpriseValue` / `ebitTTM` when both are present and ebit > 0, else None.
  History uses a direct `evEbit` series if present, otherwise annual `ev` / annual `ebit`
  joined on period (quarterly ebit is not TTM, so it is not used).
Quarterly and annual points are merged per metric, quarterly winning on equal dates.
"""

from datetime import UTC, date, datetime
from typing import Any

import httpx
from pydantic import BaseModel, Field

BASE_URL = "https://finnhub.io/api/v1"
SOURCE = "finnhub"

Point = tuple[date, float]


class FundamentalsUnavailableError(Exception):
    """Network, quota, auth or payload failure."""


class FundamentalsSnapshot(BaseModel):
    symbol: str
    source: str = SOURCE
    as_of: date
    metrics: dict[str, float | None] = Field(default_factory=dict)
    history: dict[str, list[Point]] = Field(default_factory=dict)


def _num(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return float(value)


def _first(metric: dict[str, Any], *keys: str) -> float | None:
    for key in keys:
        value = _num(metric.get(key))
        if value is not None:
            return value
    return None


def _points(rows: Any) -> dict[date, float]:
    out: dict[date, float] = {}
    if not isinstance(rows, list):
        return out
    for row in rows:
        if not isinstance(row, dict):
            continue
        value = _num(row.get("v"))
        try:
            day = date.fromisoformat(str(row.get("period")))
        except ValueError:
            continue
        if value is not None:
            out[day] = value
    return out


def _series(series: dict[str, Any], freq: str, *keys: str) -> dict[date, float]:
    block = (series.get(freq) or {}) if isinstance(series, dict) else {}
    if not isinstance(block, dict):
        return {}
    for key in keys:
        pts = _points(block.get(key))
        if pts:
            return pts
    return {}


def _merged(series: dict[str, Any], *keys: str) -> dict[date, float]:
    merged = _series(series, "annual", *keys)
    merged.update(_series(series, "quarterly", *keys))
    return merged


def parse_metric(symbol: str, payload: dict[str, Any], as_of: date) -> FundamentalsSnapshot:
    metric = payload.get("metric")
    series = payload.get("series")
    if not isinstance(metric, dict) or not metric:
        raise FundamentalsUnavailableError("finnhub: no metrics")
    if not isinstance(series, dict):
        series = {}

    pe = _first(metric, "peTTM", "peBasicExclExtraTTM")

    pfcf = _first(metric, "pfcfShareTTM")
    fcf_yield: float | None = None
    if pfcf is not None and pfcf > 0:
        fcf_yield = 100.0 / pfcf
    else:
        fcf, cap = _first(metric, "freeCashFlowTTM"), _first(metric, "marketCapitalization")
        if fcf is not None and cap is not None and cap > 0:
            fcf_yield = fcf / cap * 100.0

    ev, ebit = _first(metric, "enterpriseValue"), _first(metric, "ebitTTM")
    ev_ebit = ev / ebit if ev is not None and ebit is not None and ebit > 0 else None

    pe_hist = _merged(series, "pe", "peTTM")
    fcf_hist = {d: 100.0 / v for d, v in _merged(series, "pfcf", "pfcfTTM").items() if v > 0}
    ev_ebit_hist = _merged(series, "evEbit")
    if not ev_ebit_hist:
        ev_hist = _series(series, "annual", "ev")
        ebit_hist = _series(series, "annual", "ebit")
        ev_ebit_hist = {
            d: ev_hist[d] / ebit_hist[d] for d in ev_hist if d in ebit_hist and ebit_hist[d] > 0
        }

    def as_list(points: dict[date, float]) -> list[Point]:
        return sorted(points.items())

    return FundamentalsSnapshot(
        symbol=symbol.upper(),
        as_of=as_of,
        metrics={
            "pe": pe,
            "ev_ebit": ev_ebit,
            "fcf_yield": fcf_yield,
            # Quality and payout (BL-088); Finnhub reports these in percent.
            "roe_pct": _first(metric, "roeTTM", "roeRfy"),
            "gross_margin_pct": _first(metric, "grossMarginTTM", "grossMarginAnnual"),
            "net_margin_pct": _first(metric, "netProfitMarginTTM", "netProfitMarginAnnual"),
            "revenue_growth_pct": _first(
                metric, "revenueGrowthTTMYoy", "revenueGrowthQuarterlyYoy"
            ),
            "debt_to_equity": _first(
                metric, "totalDebt/totalEquityQuarterly", "totalDebt/totalEquityAnnual"
            ),
            "dividend_yield_pct": _first(
                metric, "dividendYieldIndicatedAnnual", "currentDividendYieldTTM"
            ),
            "payout_ratio_pct": _first(metric, "payoutRatioTTM", "payoutRatioAnnual"),
        },
        history={
            "pe": as_list(pe_hist),
            "ev_ebit": as_list(ev_ebit_hist),
            "fcf_yield": as_list(fcf_hist),
        },
    )


class FinnhubFundamentals:
    def __init__(self, api_key: str, client: httpx.AsyncClient | None = None):
        self._api_key = api_key
        self._client = client or httpx.AsyncClient(timeout=15)

    async def fetch(self, symbol: str) -> FundamentalsSnapshot:
        try:
            response = await self._client.get(
                f"{BASE_URL}/stock/metric",
                params={"symbol": symbol, "metric": "all", "token": self._api_key},
            )
        except httpx.HTTPError as exc:
            # not str(exc): httpx messages can contain the request URL, which carries the token
            raise FundamentalsUnavailableError(f"finnhub: {type(exc).__name__}") from exc
        status = response.status_code
        if status == 429:
            raise FundamentalsUnavailableError("finnhub: quota")
        if status in (401, 403):
            raise FundamentalsUnavailableError("finnhub: unauthorized")
        if status >= 400:
            raise FundamentalsUnavailableError(f"finnhub: http {status}")
        try:
            payload = response.json()
        except ValueError as exc:
            raise FundamentalsUnavailableError("finnhub: invalid json") from exc
        if not isinstance(payload, dict):
            raise FundamentalsUnavailableError("finnhub: unexpected payload")
        return parse_metric(symbol, payload, datetime.now(UTC).date())
