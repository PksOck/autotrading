"""The whole TradingAgents graph on a fixed snapshot with a scripted model (BL-080, BL-086)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from tradingagents.graph import trading_graph

from preza_agents.deep_research import adapter, vendor_local
from preza_agents.deep_research.snapshot import DataSnapshot
from preza_agents.deep_research.timeline import Step
from tests.fake_llm import FakeChat, FakeClient


@pytest.fixture
def fake_llm(monkeypatch: pytest.MonkeyPatch) -> FakeChat:
    llm = FakeChat(rating="Overweight", seen_tool_output=[])
    monkeypatch.setattr(trading_graph, "create_tier_client", lambda *a, **k: FakeClient(llm))
    return llm


def _settings(tmp_path: Path) -> adapter.DeepSettings:
    return adapter.DeepSettings(litellm_base_url="http://litellm.invalid:4000", home=tmp_path)


def test_full_graph_reads_local_data(
    snapshot: DataSnapshot, fake_llm: FakeChat, tmp_path: Path
) -> None:
    steps: list[Step] = []
    config = adapter.build_config(_settings(tmp_path), "sl")
    result = adapter.run_deep(snapshot, config, steps.append)

    assert result.rating == "Overweight"
    assert result.decision and "Overweight" in result.decision
    assert {"market_report", "news_report", "fundamentals_report"} <= set(result.reports)
    assert result.models == {"quick": "cloud-quick", "deep": "cloud-deep"}

    kinds = {(s.agent, s.kind) for s in steps}
    assert ("market", "tool") in kinds
    assert ("bull", "debate") in kinds and ("bear", "debate") in kinds
    assert ("portfolio_manager", "decision") in kinds
    assert steps[-1].kind == "decision"

    # The tools answered from the snapshot, with its source, rumor mark and no look-ahead.
    output = "\n".join(fake_llm.seen_tool_output)
    assert "Verified market data snapshot for ASML" in output
    assert vendor_local.RUMOR_MARK in output
    assert "finnhub, as of 2026-10-19" in output
    assert "yfinance" not in output.lower()


def test_config_routes_models_through_litellm(tmp_path: Path) -> None:
    config: dict[str, Any] = adapter.build_config(_settings(tmp_path), "en")
    assert config["llm_provider"] == "openai_compatible"
    assert config["backend_url"] == "http://litellm.invalid:4000/v1"
    assert config["output_language"] == "English"
    assert config["checkpoint_enabled"] is True
    assert config["data_vendors"]["core_stock_apis"] == "local"


def test_rumor_only_caveat(snapshot: DataSnapshot) -> None:
    rumors_only = snapshot.model_copy(update={"news": [n for n in snapshot.news if n.is_rumor]})
    assert "rumor_only" in adapter.caveats(rumors_only, "Buy")
    assert "rumor_only" not in adapter.caveats(rumors_only, "Hold")
    assert "rumor_only" not in adapter.caveats(snapshot, "Buy")  # a press release confirms
