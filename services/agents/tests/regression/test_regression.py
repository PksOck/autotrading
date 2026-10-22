"""Agent regression on five fixed snapshots (BL-086, ADR-0003).

For every scenario the deterministic parts of a run are compared with a stored
"golden" file: what each data tool returns, the step sequence of the graph, the
caveats and the control score. A TradingAgents upgrade that moves a call, changes a
tool's text or lets a request reach Yahoo shows up here as a diff.

Regenerate after a deliberate change with `UPDATE_GOLDEN=1 uv run pytest tests/regression`
and review the diff like code.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

import pytest
from tradingagents.agents import tools as ta_tools
from tradingagents.dataflows.config import run_config
from tradingagents.graph import trading_graph

from preza_agents.decision_card import build_card, control_score
from preza_agents.deep_research import adapter, vendor_local
from preza_agents.deep_research.snapshot import DataSnapshot
from preza_agents.deep_research.timeline import Step
from preza_agents.etf_analyst import analyst
from preza_agents.etf_analyst.exposure import Holding, look_through, overlap
from tests.fake_llm import FakeChat, FakeClient
from tests.fake_role_llm import FakeRoleLlm
from tests.regression.scenarios import AS_OF, SCENARIOS

GOLDEN = Path(__file__).parent / "golden"
UPDATE = os.environ.get("UPDATE_GOLDEN") == "1"
RATING = {
    "uptrend_cheap": "Buy",
    "downtrend_expensive": "Overweight",  # against the control score: low confidence
    "rumor_only": "Buy",
    "short_history": "Hold",
    "etf_fund": "Overweight",
}
DAY = AS_OF.isoformat()


def _digest(text: str) -> dict[str, Any]:
    """Enough to see what changed without storing every line of every tool."""
    lines = text.splitlines()
    return {
        "sha256": hashlib.sha256(text.encode()).hexdigest()[:16],
        "lines": len(lines),
        "head": lines[:6],
    }


def _steps(steps: list[Step]) -> dict[str, Any]:
    """Analysts run in parallel, so their steps are kept per agent; the rest in order."""
    analysts = set(adapter.ANALYSTS) | {"profile", "exposure"}
    per_agent: dict[str, list[str]] = {}
    sequence = []
    last_analyst = first_other = None
    for i, s in enumerate(steps):
        label = f"{s.kind}:{s.title or ''}"
        if s.agent in analysts:
            per_agent.setdefault(s.agent, []).append(label)
            last_analyst = i
        else:
            sequence.append(f"{s.agent}:{label}")
            first_other = i if first_other is None else first_other
    if last_analyst is not None and first_other is not None:
        assert last_analyst < first_other, "the debate started before the analysts finished"
    return {"analysts": per_agent, "sequence": sequence}


def _tool_outputs(snap: DataSnapshot, config: dict[str, Any]) -> dict[str, Any]:
    s = snap.symbol
    calls: dict[str, Any] = {
        "get_stock_data": lambda: ta_tools.get_stock_data.func(s, "2026-09-01", DAY),
        "get_indicators": lambda: ta_tools.get_indicators.func(s, "rsi,macd,boll", DAY, 30),
        "get_verified_market_snapshot": lambda: ta_tools.get_verified_market_snapshot.func(
            s, DAY, 30
        ),
        "get_news": lambda: ta_tools.get_news.func(s, "2026-09-20", DAY),
        "get_global_news": lambda: ta_tools.get_global_news.func(DAY, 7, 10),
        "get_insider_transactions": lambda: ta_tools.get_insider_transactions.func(s, DAY),
    }
    if snap.fundamentals is not None:  # without them the chain goes on to SEC EDGAR
        calls["get_fundamentals"] = lambda: ta_tools.get_fundamentals.func(s, DAY)
    out: dict[str, Any] = {}
    with vendor_local.activate(snap), run_config(config):
        for name, call in calls.items():
            out[name] = _digest(str(call()))
    return out


def _compare(name: str, actual: dict[str, Any]) -> None:
    path = GOLDEN / f"{name}.json"
    text = json.dumps(actual, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if UPDATE or not path.exists():
        path.write_text(text, encoding="utf-8")
        if not UPDATE:
            pytest.fail(f"golden file {path.name} was missing and has been written; rerun")
        return
    assert json.loads(path.read_text(encoding="utf-8")) == json.loads(text)


@pytest.mark.parametrize("name", [n for n in SCENARIOS if n != "etf_fund"])
def test_stock_scenario(name: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    vendor_local.install()
    snap = SCENARIOS[name]()
    rating = RATING[name]
    llm = FakeChat(rating=rating, seen_tool_output=[])
    monkeypatch.setattr(trading_graph, "create_tier_client", lambda *a, **k: FakeClient(llm))
    config = adapter.build_config(
        adapter.DeepSettings(litellm_base_url="http://litellm.invalid:4000", home=tmp_path), "en"
    )
    analysts = adapter.ANALYSTS if snap.fundamentals is not None else ("market", "news")
    steps: list[Step] = []
    result = adapter.run_deep(snap, config, steps.append, analysts=analysts)

    output = "\n".join(llm.seen_tool_output).lower()
    assert "yfinance" not in output and "yahoo" not in output
    control = control_score(snap)
    card = build_card(result.rating, control, None, None)
    _compare(
        name,
        {
            "rating": result.rating,
            "caveats": adapter.caveats(snap, result.rating),
            "control": control.model_dump(mode="json"),
            "confidence": card.confidence,
            "steps": _steps(steps),
            "reports": sorted(result.reports),
            "tools": _tool_outputs(snap, config),
        },
    )


async def test_etf_scenario() -> None:
    snap = SCENARIOS["etf_fund"]()
    holdings = [
        {"symbol": "NVDA", "name": "NVIDIA", "weight": 0.22},
        {"symbol": "AVGO", "name": "Broadcom", "weight": 0.09},
        {"symbol": "ASML.AS", "name": "ASML", "weight": 0.08},
    ]
    profile = {
        "as_of": "2026-10-19",
        "ter": 0.0035,
        "index_name": "Technology",
        "distribution": "acc",
        "holdings": holdings,
        "holdings_coverage": 0.39,
        "sectors": {"technology": 0.97},
        "source": "yahoo",
    }
    exposure = look_through([Holding("NVDA", "stock", 0.06), Holding("ASML", "stock", 0.04)], {})
    facts = analyst.compute_facts(snap, profile, 0.0, overlap(holdings, exposure), None)
    steps: list[Step] = []
    result = await analyst.run_etf(FakeRoleLlm(RATING["etf_fund"]), facts, "sl", steps.append)
    control = control_score(snap)
    _compare(
        "etf_fund",
        {
            "rating": result.rating,
            "caveats": [c for c in adapter.caveats(snap, result.rating) if c != "no_fundamentals"],
            "control": control.model_dump(mode="json"),
            "steps": _steps(steps),
            "reports": {k: _digest(v) for k, v in result.reports.items()},
        },
    )
