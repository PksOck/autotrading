"""TradingAgents adapter (BL-080, ADR-0003, ADR-0011).

Models: both tiers talk to LiteLLM as an OpenAI-compatible endpoint, with our role
names as model names (`cloud-quick`, `cloud-deep`), so the routing stays in one place
(ADR-0004). Data: the `local` vendor serves a snapshot of our database. Crash safety:
TradingAgents' SQLite checkpoints resume a run with the same symbol and date.
"""

from __future__ import annotations

import copy
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from tradingagents.agents.rating import run_rating
from tradingagents.dataflows.config import run_config
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph.trading_graph import TradingAgentsGraph

from preza_agents.deep_research import vendor_local
from preza_agents.deep_research.snapshot import DataSnapshot
from preza_agents.deep_research.timeline import Step, Timeline

# The social analyst reads Reddit and StockTwits directly; our news store already
# carries social posts with the rumor flag, which the news analyst sees.
ANALYSTS: tuple[str, ...] = ("market", "news", "fundamentals")
LANGUAGES = {"sl": "Slovenian", "en": "English"}
BULLISH = {"Buy", "Overweight"}
OFFICIAL_KINDS = {"press_release", "filing"}
MIN_BARS = 200


@dataclass(frozen=True)
class DeepSettings:
    litellm_base_url: str
    quick_role: str = "cloud-quick"
    deep_role: str = "cloud-deep"
    debate_rounds: int = 1
    home: Path = Path("/data/agents")
    benchmark: str | None = None


@dataclass
class DeepResult:
    rating: str
    decision: str | None
    reports: dict[str, str] = field(default_factory=dict)
    models: dict[str, str] = field(default_factory=dict)


def build_config(settings: DeepSettings, locale: str) -> dict[str, Any]:
    config: dict[str, Any] = copy.deepcopy(DEFAULT_CONFIG)
    home = settings.home
    config.update(
        {
            "llm_provider": "openai_compatible",
            "backend_url": settings.litellm_base_url.rstrip("/") + "/v1",
            "quick_think_llm": settings.quick_role,
            "deep_think_llm": settings.deep_role,
            "output_language": LANGUAGES.get(locale, "English"),
            "max_debate_rounds": settings.debate_rounds,
            "max_risk_discuss_rounds": settings.debate_rounds,
            "checkpoint_enabled": True,
            "results_dir": str(home / "logs"),
            "data_cache_dir": str(home / "cache"),
            "memory_log_path": str(home / "memory" / "trading_memory.md"),
            "data_vendors": dict(vendor_local.DATA_VENDORS),
            "tool_vendors": {},
        }
    )
    if settings.benchmark:
        config["benchmark_ticker"] = settings.benchmark
    return config


def caveats(snapshot: DataSnapshot, rating: str) -> list[str]:
    """Deterministic warnings shown next to the agents' rating (AGENTS.md rules 4 and 5)."""
    found = []
    rumors = [n for n in snapshot.news if n.is_rumor]
    official = [n for n in snapshot.news if not n.is_rumor and n.kind in OFFICIAL_KINDS]
    if rating in BULLISH and rumors and not official:
        found.append("rumor_only")
    if snapshot.fundamentals is None:
        found.append("no_fundamentals")
    if len(snapshot.bars) < MIN_BARS:
        found.append("short_history")
    return found


def run_deep(
    snapshot: DataSnapshot,
    config: dict[str, Any],
    on_step: Callable[[Step], None],
    analysts: Sequence[str] = ANALYSTS,
    graph_factory: Callable[..., Any] = TradingAgentsGraph,
) -> DeepResult:
    """Run the graph to the end; blocking, call it from a worker thread."""
    vendor_local.install()
    graph = graph_factory(selected_analysts=tuple(analysts), config=config)
    timeline = Timeline()
    symbol, day = snapshot.symbol, snapshot.as_of.isoformat()
    final: dict[str, Any] = {}
    with (
        vendor_local.activate(snapshot),
        run_config(graph.config),
        graph.checkpoint_scope(symbol, day) as thread_id,
    ):
        initial = graph.create_run_state(symbol, day)
        args = graph.propagator.get_graph_args()
        if thread_id is not None:
            args.setdefault("config", {}).setdefault("configurable", {})["thread_id"] = thread_id
        for messages, state in graph.stream_run(graph.checkpoint_input(initial), **args):
            for step in timeline.feed(messages, state):
                on_step(step)
            if state is not None:
                final.update(state)
        graph.record_decision(symbol, day, final)
        graph.clear_checkpoint_on_success(symbol, day)
    return DeepResult(
        rating=run_rating(final),
        decision=final.get("final_trade_decision"),
        reports=timeline.reports(),
        models={"quick": config["quick_think_llm"], "deep": config["deep_think_llm"]},
    )
