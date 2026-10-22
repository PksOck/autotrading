"""A scripted chat model: no network, deterministic replies, real tool calls.

With tools bound and no tool result yet, it calls the first tool it knows how to
fill; otherwise it answers with a fixed report carrying the rating lines the
TradingAgents parsers look for.
"""

from __future__ import annotations

import itertools
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult

TOOL_ARGS: dict[str, dict[str, Any]] = {
    "get_verified_market_snapshot": {"curr_date": "2026-10-20", "look_back_days": 10},
    "get_news": {"start_date": "2026-10-10", "end_date": "2026-10-20"},
    "get_fundamentals": {"curr_date": "2026-10-20"},
}

_ids = itertools.count(1)


class FakeChat(BaseChatModel):
    rating: str = "Hold"
    tool_names: tuple[str, ...] = ()
    seen_tool_output: list[str] = []  # noqa: RUF012 (pydantic field, copied per instance)

    @property
    def _llm_type(self) -> str:
        return "fake-chat"

    def bind_tools(self, tools: Any, **kwargs: Any) -> Any:  # type: ignore[override]
        names = tuple(getattr(t, "name", "") for t in tools)
        return self.model_copy(update={"tool_names": names})

    def with_structured_output(self, schema: Any, **kwargs: Any) -> Any:  # type: ignore[override]
        raise NotImplementedError  # TradingAgents falls back to free text

    def _generate(
        self, messages: list[BaseMessage], stop: Any = None, run_manager: Any = None, **kw: Any
    ) -> ChatResult:
        results = [m for m in messages if isinstance(m, ToolMessage)]
        self.seen_tool_output.extend(str(m.content) for m in results)
        callable_tools = [n for n in self.tool_names if n in TOOL_ARGS]
        if callable_tools and not results:
            name = callable_tools[0]
            message = AIMessage(
                content="",
                tool_calls=[{"name": name, "args": TOOL_ARGS[name], "id": f"call_{next(_ids)}"}],
            )
        else:
            message = AIMessage(
                content=(
                    "Report based on the provided data.\n\n"
                    f"**Rating**: {self.rating}\n\n"
                    f"FINAL TRANSACTION PROPOSAL: **{self.rating.upper()}**"
                )
            )
        return ChatResult(generations=[ChatGeneration(message=message)])


class FakeClient:
    def __init__(self, llm: FakeChat) -> None:
        self.llm = llm

    def get_llm(self) -> FakeChat:
        return self.llm
