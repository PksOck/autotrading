from __future__ import annotations

import pytest
from tradingagents.agents import context as ta_context
from tradingagents.dataflows.config import run_config
from tradingagents.dataflows.errors import NoMarketDataError
from tradingagents.dataflows.router import route_to_vendor
from tradingagents.dataflows.vendors.yahoo.snapshot import build_verified_market_snapshot
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.memory import settlement

from preza_agents.deep_research import vendor_local
from preza_agents.deep_research.snapshot import DataSnapshot

CONFIG = {**DEFAULT_CONFIG, "data_vendors": vendor_local.DATA_VENDORS}


def test_stock_data_is_cut_at_run_date(snapshot: DataSnapshot) -> None:
    with vendor_local.activate(snapshot), run_config(CONFIG):
        text = route_to_vendor("get_stock_data", "ASML", "2026-10-01", "2026-10-25")
    assert "# Source: ibkr" in text
    assert "2026-10-20" in text
    assert "2026-10-21" not in text


def test_indicators_use_local_frame(snapshot: DataSnapshot) -> None:
    with vendor_local.activate(snapshot), run_config(CONFIG):
        text = route_to_vendor("get_indicators", "ASML", "rsi", "2026-10-20", 5)
    values = [line for line in text.splitlines() if line.startswith("2026-10-20:")]
    assert values and "N/A" not in values[0]


def test_verified_snapshot_reads_local_bars(snapshot: DataSnapshot) -> None:
    with vendor_local.activate(snapshot), run_config(CONFIG):
        text = build_verified_market_snapshot("ASML", "2026-10-20", 10)
    assert "2026-10-20" in text
    assert "close_200_sma" in text


def test_profile_and_closes_patched(snapshot: DataSnapshot) -> None:
    with vendor_local.activate(snapshot):
        assert ta_context.get_company_profile("ASML")["longName"] == "ASML Holding N.V."
        closes = settlement.get_closes("ASML", "2026-10-13", "2026-10-20")
    assert len(closes) == 5  # end is exclusive


def test_news_marks_rumors_and_separates_insiders(snapshot: DataSnapshot) -> None:
    with vendor_local.activate(snapshot), run_config(CONFIG):
        news = route_to_vendor("get_news", "ASML", "2026-10-10", "2026-10-20")
        insiders = route_to_vendor("get_insider_transactions", "ASML", "2026-10-20")
        world = route_to_vendor("get_global_news", "2026-10-20", 7, 5)
    assert f"{vendor_local.RUMOR_MARK} ASML may be acquired" in news
    assert "Form 4" not in news
    assert "CFO buys shares" in insiders
    assert "Fed holds rates" in world


def test_fundamentals_name_source(snapshot: DataSnapshot) -> None:
    with vendor_local.activate(snapshot), run_config(CONFIG):
        text = route_to_vendor("get_fundamentals", "ASML", "2026-10-20")
    assert "finnhub, as of 2026-10-19" in text
    assert "peTTM: 31.2" in text


def test_unknown_symbol_has_no_data() -> None:
    vendor_local.install()
    with pytest.raises(NoMarketDataError):
        vendor_local.ohlcv_frame("NOPE")
