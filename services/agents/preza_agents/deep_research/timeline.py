"""Turn TradingAgents' stream into timeline steps (CMP-12, BL-082).

`stream_run` yields `(messages, state)`: inside an analyst's graph `state` is that
analyst's report once filed, at the top level it is the full run state. We emit a
step for each tool call, each filed report and each new turn in the two debates.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel

StepKind = Literal["tool", "report", "debate", "decision", "status"]

REPORT_AGENT = {
    "market_report": "market",
    "sentiment_report": "social",
    "news_report": "news",
    "fundamentals_report": "fundamentals",
    "investment_plan": "research_manager",
    "trader_investment_plan": "trader",
}
DECISION_KEY = "final_trade_decision"
DEBATES = {
    "investment_debate_state": {"bull_history": "bull", "bear_history": "bear"},
    "risk_debate_state": {
        "aggressive_history": "aggressive",
        "conservative_history": "conservative",
        "neutral_history": "neutral",
    },
}
TOOL_AGENT = {
    "get_stock_data": "market",
    "get_indicators": "market",
    "get_verified_market_snapshot": "market",
    "get_news": "news",
    "get_global_news": "news",
    "get_macro_indicators": "news",
    "get_prediction_markets": "news",
    "get_insider_transactions": "news",
    "get_fundamentals": "fundamentals",
    "get_balance_sheet": "fundamentals",
    "get_cashflow": "fundamentals",
    "get_income_statement": "fundamentals",
}
MAX_ARGS = 160


class Step(BaseModel):
    agent: str
    kind: StepKind
    title: str | None = None
    content: str = ""


def _tool_title(call: dict[str, Any]) -> str:
    args = ", ".join(f"{k}={v}" for k, v in (call.get("args") or {}).items())
    text = f"{call.get('name', 'tool')}({args})"
    return text if len(text) <= MAX_ARGS else text[: MAX_ARGS - 1] + "…"


class Timeline:
    """Stateful: remembers what it already emitted, so repeated states add nothing."""

    def __init__(self) -> None:
        self._calls: set[str] = set()
        self._reports: dict[str, str] = {}
        self._debate_seen: dict[str, int] = {}

    def feed(self, messages: list[Any], state: dict[str, Any] | None) -> list[Step]:
        steps = self._tool_steps(messages)
        if state:
            steps += self._report_steps(state)
            steps += self._debate_steps(state)
            decision = state.get(DECISION_KEY)
            if decision and self._reports.get(DECISION_KEY) != decision:
                self._reports[DECISION_KEY] = decision
                steps.append(Step(agent="portfolio_manager", kind="decision", content=decision))
        return steps

    def _tool_steps(self, messages: list[Any]) -> list[Step]:
        steps = []
        for message in messages:
            for call in getattr(message, "tool_calls", None) or []:
                key = call.get("id") or _tool_title(call)
                if key in self._calls:
                    continue
                self._calls.add(key)
                name = call.get("name", "")
                steps.append(
                    Step(
                        agent=TOOL_AGENT.get(name, "analyst"), kind="tool", title=_tool_title(call)
                    )
                )
        return steps

    def _report_steps(self, state: dict[str, Any]) -> list[Step]:
        steps = []
        for key, agent in REPORT_AGENT.items():
            value = state.get(key)
            if isinstance(value, str) and value and self._reports.get(key) != value:
                self._reports[key] = value
                steps.append(Step(agent=agent, kind="report", title=key, content=value))
        return steps

    def _debate_steps(self, state: dict[str, Any]) -> list[Step]:
        steps = []
        for debate, speakers in DEBATES.items():
            current = state.get(debate)
            if not isinstance(current, dict):
                continue
            for field, agent in speakers.items():
                history = current.get(field) or ""
                seen = self._debate_seen.get(f"{debate}.{field}", 0)
                if len(history) > seen:
                    self._debate_seen[f"{debate}.{field}"] = len(history)
                    turn = history[seen:].strip()
                    if turn:
                        steps.append(Step(agent=agent, kind="debate", title=debate, content=turn))
        return steps

    def reports(self) -> dict[str, str]:
        """Everything filed so far, keyed by the state field."""
        return dict(self._reports)
