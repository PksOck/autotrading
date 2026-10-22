"""`local` data vendor for TradingAgents: serves our database snapshot (BL-081, ADR-0003).

TradingAgents routes most data calls through `VENDOR_METHODS`; we register `local`
there. Four places call Yahoo directly instead (price frame for indicators and the
verified snapshot, company profile, closes for the memory log), so `install()` also
points those module attributes at the snapshot. The version is pinned, and the
regression tests fail if a new version moves these call sites.

Every text block names its source and as-of date (AGENTS.md rule 5), and unconfirmed
reports are marked so the agents cannot read them as facts (rule 4).
"""

from __future__ import annotations

import threading
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date, timedelta
from typing import Any

import pandas as pd
from tradingagents.agents import context as ta_context
from tradingagents.dataflows import router
from tradingagents.dataflows.errors import NoMarketDataError
from tradingagents.dataflows.vendors.yahoo import market as ta_market
from tradingagents.dataflows.vendors.yahoo import snapshot as ta_snapshot
from tradingagents.memory import settlement as ta_settlement

from preza_agents.deep_research.snapshot import DataSnapshot, NewsRow

VENDOR = "local"
RUMOR_MARK = "[UNCONFIRMED REPORT, not a fact]"
GLOBAL_NEWS_DEFAULT_LIMIT = 15

_lock = threading.Lock()
_active: dict[str, DataSnapshot] = {}


@contextmanager
def activate(snapshot: DataSnapshot) -> Iterator[None]:
    """Serve `snapshot` for its symbol while the run is inside this block."""
    key = snapshot.symbol.upper()
    with _lock:
        _active[key] = snapshot
    try:
        yield
    finally:
        with _lock:
            _active.pop(key, None)


def _snapshot(symbol: str) -> DataSnapshot:
    with _lock:
        found = _active.get(symbol.upper())
    if found is None:
        raise NoMarketDataError(symbol, detail="not in the local snapshot")
    return found


def _any_snapshot() -> DataSnapshot | None:
    with _lock:
        return next(iter(_active.values()), None)


def _day(value: str | None, fallback: date) -> date:
    return date.fromisoformat(value[:10]) if value else fallback


# Price frames


def ohlcv_frame(symbol: str, as_of_date: str | None = None) -> pd.DataFrame:
    snap = _snapshot(symbol)
    cutoff = min(_day(as_of_date, snap.as_of), snap.as_of)
    rows = [b for b in snap.bars if b.day <= cutoff]
    if not rows:
        raise NoMarketDataError(symbol, detail=f"no local bars on or before {cutoff}")
    return pd.DataFrame(
        {
            "Date": pd.to_datetime([b.day for b in rows]),
            "Open": [float(b.open) for b in rows],
            "High": [float(b.high) for b in rows],
            "Low": [float(b.low) for b in rows],
            "Close": [float(b.close) for b in rows],
            "Volume": [b.volume or 0 for b in rows],
        }
    )


def load_ohlcv(symbol: str, as_of_date: str, fill_gaps: bool = True) -> pd.DataFrame:
    """Replacement for `yahoo.ohlcv.load_ohlcv`; our bars have no gaps to fill."""
    del fill_gaps
    return ohlcv_frame(symbol, as_of_date)


def get_closes(symbol: str, start_date: str, end_date: str) -> pd.Series:
    """Replacement for `yahoo.market.get_closes` (end exclusive)."""
    try:
        frame = ohlcv_frame(symbol)
    except NoMarketDataError:
        return pd.Series(dtype=float)
    mask = (frame["Date"] >= pd.Timestamp(start_date)) & (frame["Date"] < pd.Timestamp(end_date))
    selected = frame[mask]
    return pd.Series(selected["Close"].to_numpy(), index=selected["Date"], name="Close")


def get_stock_data(symbol: str, start_date: str, end_date: str) -> str:
    snap = _snapshot(symbol)
    frame = ohlcv_frame(symbol, end_date)
    frame = frame[frame["Date"] >= pd.Timestamp(start_date)]
    if frame.empty:
        raise NoMarketDataError(symbol, detail=f"no local bars between {start_date} and {end_date}")
    out = frame.copy()
    out["Date"] = out["Date"].dt.strftime("%Y-%m-%d")
    header = (
        f"# Stock data for {snap.symbol.upper()} from {start_date} to {end_date}\n"
        f"# Source: {snap.bars_source or 'unknown'}, daily bars as of {snap.as_of}\n"
        f"# Total records: {len(out)}\n\n"
    )
    return header + out.round(4).to_csv(index=False)


# Company and fundamentals


def get_company_profile(ticker: str) -> dict[str, Any]:
    try:
        snap = _snapshot(ticker)
    except NoMarketDataError:
        return {}
    quote_type = {"stock": "EQUITY", "etf": "ETF"}.get(snap.kind, snap.kind.upper())
    return {
        "longName": snap.name,
        "exchange": snap.exchange,
        "quoteType": quote_type,
        "currency": snap.currency,
    }


def get_fundamentals(ticker: str, as_of_date: str | None = None) -> str:
    snap = _snapshot(ticker)
    if not snap.fundamentals:
        raise NoMarketDataError(ticker, detail="no local fundamentals")
    lines = [
        f"# Company fundamentals for {snap.symbol.upper()}",
        f"# Source: {snap.fundamentals_source}, as of {snap.fundamentals_as_of}",
        "",
    ]
    if snap.name:
        lines.append(f"Name: {snap.name}")
    for key in sorted(snap.fundamentals):
        value = snap.fundamentals[key]
        if isinstance(value, int | float | str):
            lines.append(f"{key}: {value}")
    del as_of_date  # the snapshot is already cut at the run date
    return "\n".join(lines)


def _no_statements(ticker: str, *args: Any, **kwargs: Any) -> str:
    # We keep valuation metrics, not full statements: the next vendor in the
    # chain (SEC EDGAR) serves them.
    raise NoMarketDataError(ticker, detail="no local financial statements")


# News


def _news_line(row: NewsRow) -> str:
    when = row.published_at.strftime("%Y-%m-%d %H:%M UTC")
    mark = f"{RUMOR_MARK} " if row.is_rumor else ""
    text = f"- {when} · {row.source} · {mark}{row.title}"
    if row.summary:
        text += f"\n  {row.summary.strip()[:400]}"
    return f"{text}\n  {row.url}"


def _in_window(rows: list[NewsRow], start: date, end: date) -> list[NewsRow]:
    return [r for r in rows if start <= r.published_at.date() <= end]


def get_news(ticker: str, start_date: str, end_date: str) -> str:
    snap = _snapshot(ticker)
    end = min(_day(end_date, snap.as_of), snap.as_of)
    rows = _in_window(snap.news, _day(start_date, end - timedelta(days=7)), end)
    rows = [r for r in rows if r.filing_form not in ("4", "4/A")]
    header = f"## {snap.symbol.upper()} news from {start_date} to {end} (our news store)"
    if not rows:
        return f"{header}\n\nNo articles in this window."
    return header + "\n\n" + "\n".join(_news_line(r) for r in rows)


def get_global_news(
    as_of_date: str, look_back_days: int | None = None, limit: int | None = None
) -> str:
    snap = _any_snapshot()
    if snap is None:
        raise NoMarketDataError("market", detail="no active snapshot")
    end = min(_day(as_of_date, snap.as_of), snap.as_of)
    rows = _in_window(snap.global_news, end - timedelta(days=look_back_days or 7), end)
    rows = rows[: limit or GLOBAL_NEWS_DEFAULT_LIMIT]
    header = f"## Market news up to {end} (our news store)"
    if not rows:
        return f"{header}\n\nNo articles in this window."
    return header + "\n\n" + "\n".join(_news_line(r) for r in rows)


def get_insider_transactions(ticker: str, as_of_date: str | None = None) -> str:
    snap = _snapshot(ticker)
    end = min(_day(as_of_date, snap.as_of), snap.as_of)
    rows = [r for r in snap.news if r.filing_form in ("4", "4/A") and r.published_at.date() <= end]
    header = f"## Insider filings (SEC Form 4) for {snap.symbol.upper()} up to {end}"
    if not rows:
        return f"{header}\n\nNo Form 4 filings in our store for the last 30 days."
    return header + "\n\n" + "\n".join(_news_line(r) for r in rows)


LOCAL_METHODS: dict[str, Any] = {
    "get_stock_data": get_stock_data,
    # TradingAgents' own indicator code, reading our frame through the patched loader.
    "get_indicators": ta_market.get_stock_stats_indicators_window,
    "get_fundamentals": get_fundamentals,
    "get_balance_sheet": _no_statements,
    "get_cashflow": _no_statements,
    "get_income_statement": _no_statements,
    "get_news": get_news,
    "get_global_news": get_global_news,
    "get_insider_transactions": get_insider_transactions,
}

# Category vendor chains for the run config.
DATA_VENDORS = {
    "core_stock_apis": VENDOR,
    "technical_indicators": VENDOR,
    "fundamental_data": f"{VENDOR},sec_edgar",
    "news_data": VENDOR,
    "macro_data": "fred",
    "prediction_markets": "polymarket",
}

_installed = False


def install() -> None:
    """Register the vendor and redirect the direct Yahoo calls. Idempotent."""
    global _installed
    if _installed:
        return
    for method, fn in LOCAL_METHODS.items():
        # `local` goes first so the "default" chain also prefers our data.
        router.VENDOR_METHODS[method] = {VENDOR: fn, **router.VENDOR_METHODS[method]}
    ta_market.load_ohlcv = load_ohlcv
    ta_snapshot.load_ohlcv = load_ohlcv
    ta_context.get_company_profile = get_company_profile
    ta_settlement.get_closes = get_closes
    _installed = True


def is_installed() -> bool:
    return _installed


__all__ = ["DATA_VENDORS", "activate", "install", "is_installed"]
