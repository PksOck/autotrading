"""Conservative input budgets and usage accounting for role-based analysis calls."""

from __future__ import annotations

import inspect
import json
from collections.abc import Sequence
from typing import Any, cast

from pydantic import BaseModel

from preza.llm.client import Llm, LlmResult, OutputLimitedLlm, Role

MAX_INPUT_TOKENS = 16_000
WORK_INPUT_TOKENS = 12_000
MESSAGE_OVERHEAD = 16
# client.py appends two messages and at most 800 characters of validation error.
REPAIR_OVERHEAD_TOKENS = 2 * MESSAGE_OVERHEAD + (800 + 80) // 2
# Output caps include hidden reasoning: MiniMax spent 2x1500 tokens thinking and
# returned no content on the first live run.
ANALYST_OUTPUT_TOKENS = 6000
REVIEWER_OUTPUT_TOKENS = 6000
DECISION_OUTPUT_TOKENS = 10_000
COMPOSE_OUTPUT_TOKENS = 2000
# A repair resends only the visible JSON content, which the schemas keep small.
REPAIR_CONTENT_TOKENS = 2000
ROLE_OUTPUT_TOKENS = {
    "local-fast": ANALYST_OUTPUT_TOKENS,
    "local-reason": ANALYST_OUTPUT_TOKENS,
    "cloud-quick": ANALYST_OUTPUT_TOKENS,
    "cloud-deep": DECISION_OUTPUT_TOKENS,
}


def estimate_tokens(text: str) -> int:
    return (len(text) + 1) // 2


def input_estimate(system: str, user: str, schema: type[BaseModel] | None = None) -> int:
    schema_text = json.dumps(schema.model_json_schema()) if schema else ""
    return (
        estimate_tokens(system)
        + estimate_tokens(user)
        + estimate_tokens(schema_text)
        + 2 * MESSAGE_OVERHEAD
    )


def input_limit(budget: int, max_output_tokens: int | None) -> int:
    reserved = DECISION_OUTPUT_TOKENS if max_output_tokens is None else max_output_tokens
    if reserved < 1:
        raise ValueError("max_output_tokens must be positive")
    resent = min(reserved, REPAIR_CONTENT_TOKENS)
    return min(budget, WORK_INPUT_TOKENS, MAX_INPUT_TOKENS - resent - REPAIR_OVERHEAD_TOKENS)


def fit_reports(reports: dict[str, str], budget: int) -> dict[str, str]:
    """Keep earlier, higher-priority reports first, including JSON overhead."""
    if budget < 0:
        raise ValueError("Report budget must be non-negative")
    fitted: dict[str, str] = {}
    for key, value in reports.items():
        lines: list[str] = []
        for line in value.splitlines():
            candidate = {**fitted, key: "\n".join([*lines, line])}
            if estimate_tokens(json.dumps(candidate, ensure_ascii=False)) <= budget:
                lines.append(line)
            else:
                break
        if lines:
            fitted[key] = "\n".join(lines)
    return fitted


def guard_input(
    system: str,
    user: str,
    budget: int = WORK_INPUT_TOKENS,
    *,
    schema: type[BaseModel] | None = None,
    max_output_tokens: int | None = None,
) -> None:
    needed = input_estimate(system, user, schema)
    limit = input_limit(budget, max_output_tokens)
    if needed > limit:
        raise ValueError(f"LLM input budget exceeded: {needed} estimated tokens > {limit}")


def guard_payload(
    system: str,
    payload: dict[str, Any],
    trimmable: Sequence[str] = (),
    budget: int = WORK_INPUT_TOKENS,
    *,
    schema: type[BaseModel] | None = None,
    max_output_tokens: int | None = None,
) -> str:
    """Trim named top-level fields in lowest-priority-first order, preserving JSON.

    Required facts, source/time headers and system instructions must not be named
    as trimmable. Oversized required input fails before contacting the model.
    """
    data = dict(payload)
    budget = input_limit(budget, max_output_tokens)

    def dump() -> str:
        return json.dumps(data, ensure_ascii=False, default=str)

    for key in trimmable:
        if input_estimate(system, dump(), schema) <= budget:
            break
        original = data.get(key)
        if original is None:
            continue
        size = (
            len(original.splitlines())
            if isinstance(original, str)
            else estimate_tokens(json.dumps(original, ensure_ascii=False, default=str))
        )

        def trim(amount: int, original: Any = original, key: str = key) -> None:
            if isinstance(original, str):
                data[key] = "\n".join(original.splitlines()[:amount])
            elif isinstance(original, dict):
                data[key] = fit_reports(original, amount)
            else:
                raise TypeError(f"Trimmable field {key} must be text or reports")

        low, high = 0, size
        trim(0)
        if input_estimate(system, dump(), schema) > budget:
            continue
        while low < high:
            mid = (low + high + 1) // 2
            trim(mid)
            if input_estimate(system, dump(), schema) <= budget:
                low = mid
            else:
                high = mid - 1
        trim(low)
    user = dump()
    guard_input(system, user, budget, schema=schema, max_output_tokens=max_output_tokens)
    return user


class UsageLlm:
    """Wrap a client without changing its public structured-output API."""

    def __init__(self, llm: Llm) -> None:
        self.llm = llm
        self.calls: list[dict[str, Any]] = []

    async def complete_json[T: BaseModel](
        self,
        role: Role,
        system: str,
        user: str,
        schema: type[T],
        *,
        max_output_tokens: int | None = None,
    ) -> LlmResult[T]:
        if max_output_tokens is None:
            max_output_tokens = ROLE_OUTPUT_TOKENS.get(role, DECISION_OUTPUT_TOKENS)
        guard_input(system, user, schema=schema, max_output_tokens=max_output_tokens)
        parameters = inspect.signature(self.llm.complete_json).parameters
        supports_limit = "max_output_tokens" in parameters or any(
            p.kind == inspect.Parameter.VAR_KEYWORD for p in parameters.values()
        )
        try:
            if not supports_limit:
                raise TypeError("Analysis client must support max_output_tokens")
            result = await cast(OutputLimitedLlm, self.llm).complete_json(
                role, system, user, schema, max_output_tokens=max_output_tokens
            )
        except Exception as exc:
            self.calls.append(
                {
                    "role": role,
                    "model": None,
                    "prompt_tokens": getattr(exc, "prompt_tokens", 0),
                    "completion_tokens": getattr(exc, "completion_tokens", 0),
                    "input_token_estimate": input_estimate(system, user, schema),
                    "max_output_tokens": max_output_tokens,
                    "repair_input_estimate": input_estimate(system, user, schema)
                    + min(max_output_tokens, REPAIR_CONTENT_TOKENS)
                    + REPAIR_OVERHEAD_TOKENS,
                    "status": "failed",
                }
            )
            raise
        self.calls.append(
            {
                "role": role,
                "model": result.model,
                "prompt_tokens": result.prompt_tokens,
                "completion_tokens": result.completion_tokens,
                "input_token_estimate": input_estimate(system, user, schema),
                "max_output_tokens": max_output_tokens,
                "repair_input_estimate": input_estimate(system, user, schema)
                + min(max_output_tokens, REPAIR_CONTENT_TOKENS)
                + REPAIR_OVERHEAD_TOKENS,
            }
        )
        return result

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return await self.llm.embed(texts)

    def usage(self) -> dict[str, Any]:
        return {
            "calls": list(self.calls),
            "prompt_tokens": sum(c["prompt_tokens"] for c in self.calls),
            "completion_tokens": sum(c["completion_tokens"] for c in self.calls),
            "input_token_estimate": sum(c["input_token_estimate"] for c in self.calls),
        }
