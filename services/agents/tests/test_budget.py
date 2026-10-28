"""Input budgets must preserve JSON and fail before contacting a model."""

import json

import pytest
from pydantic import BaseModel, Field

from preza_agents.budget import (
    MAX_INPUT_TOKENS,
    REPAIR_CONTENT_TOKENS,
    REPAIR_OVERHEAD_TOKENS,
    WORK_INPUT_TOKENS,
    UsageLlm,
    estimate_tokens,
    fit_reports,
    guard_input,
    guard_payload,
    input_estimate,
)


def test_estimate_and_trim_priority() -> None:
    assert [estimate_tokens("x" * n) for n in range(5)] == [0, 1, 1, 2, 2]
    system = "Keep instructions intact."
    user = guard_payload(
        system, {"facts": "required", "low": "l" * 100_000, "high": "h" * 1000}, ("low", "high")
    )
    data = json.loads(user)
    assert data["facts"] == "required" and data["high"] == "h" * 1000
    assert len(data["low"]) < 100_000
    assert estimate_tokens(system + user) <= MAX_INPUT_TOKENS


def test_reports_and_serialization_overhead() -> None:
    fitted = fit_reports({"decision": "d" * 100, "news": "n" * 1000}, 100)
    assert fitted["decision"] == "d" * 100
    assert estimate_tokens(json.dumps(fitted, ensure_ascii=False)) <= 100
    user = guard_payload(
        "system",
        {"reports": {"first": "a sentence.\n" * 10_000, "second": "b\n" * 100_000}},
        ("reports",),
    )
    assert estimate_tokens("system" + user) <= 16_000
    assert json.loads(user)["reports"]


def test_required_content_raises() -> None:
    with pytest.raises(ValueError, match="LLM input budget exceeded"):
        guard_payload("x" * 48_001, {"reports": {"a": "trim me"}}, ("reports",))
    with pytest.raises(ValueError, match="LLM input budget exceeded"):
        guard_payload("system", {"hypothesis": "x" * 50_000})


async def test_etf_postprocessing_inputs_share_the_cap() -> None:
    from preza_agents.decision_card import draft_card
    from preza_agents.hypothesis import check_hypothesis
    from tests.fake_role_llm import FakeRoleLlm

    llm = FakeRoleLlm()
    reports = {f"report_{i}": "long report " * 5000 for i in range(40)}
    await draft_card(llm, "Hold", "A decision", reports, None, "en")
    await check_hypothesis(llm, "A hypothesis", reports, "Hold", "en")
    assert all(size <= MAX_INPUT_TOKENS for size in llm.input_sizes)
    assert all(json.loads(call[2])["reports"] for call in llm.calls)


class SmallOutput(BaseModel):
    text: str = Field(max_length=100)


def test_schema_and_message_overhead_are_counted() -> None:
    system, user = "system", "user"
    assert input_estimate(system, user, SmallOutput) > input_estimate(system, user)
    expected_schema = estimate_tokens(json.dumps(SmallOutput.model_json_schema()))
    assert (
        input_estimate(system, user, SmallOutput) - input_estimate(system, user) == expected_schema
    )
    with pytest.raises(ValueError, match="input budget exceeded"):
        guard_input("", "x" * (WORK_INPUT_TOKENS * 2 - 64), schema=SmallOutput)
    with pytest.raises(ValueError, match="input budget exceeded"):
        guard_input("", "x" * 24_500, max_output_tokens=5000)


async def test_usage_forwards_limit_and_rejects_clients_without_caps() -> None:
    from preza_agents.stock_analyst.analyst import StockSummary
    from tests.fake_role_llm import FakeRoleLlm

    limited = FakeRoleLlm()
    usage = UsageLlm(limited)
    await usage.complete_json("local-fast", "system", "{}", StockSummary, max_output_tokens=800)
    assert limited.output_caps == [800]
    assert usage.calls[0]["input_token_estimate"] == input_estimate("system", "{}", StockSummary)
    assert (
        usage.calls[0]["repair_input_estimate"]
        == usage.calls[0]["input_token_estimate"] + 800 + REPAIR_OVERHEAD_TOKENS
    )

    class PlainLlm(FakeRoleLlm):
        async def complete_json(self, role, system, user, schema):  # type: ignore[no-untyped-def]
            return await super().complete_json(role, system, user, schema)

    plain = PlainLlm()
    with pytest.raises(TypeError, match="must support max_output_tokens"):
        await UsageLlm(plain).complete_json(
            "local-fast", "system", "{}", StockSummary, max_output_tokens=800
        )
    assert not plain.calls


@pytest.mark.parametrize(
    ("role", "cap"),
    [
        ("local-fast", 6000),
        ("local-reason", 6000),
        ("cloud-quick", 6000),
        ("cloud-deep", 10_000),
    ],
)
async def test_usage_default_cap_matches_repair_reserve(role: str, cap: int) -> None:
    from preza_agents.stock_analyst.analyst import StockSummary
    from tests.fake_role_llm import FakeRoleLlm

    raw = FakeRoleLlm()
    usage = UsageLlm(raw)
    await usage.complete_json(role, "system", "{}", StockSummary)  # type: ignore[arg-type]
    assert raw.output_caps == [cap]
    assert usage.calls[0]["max_output_tokens"] == cap
    assert usage.calls[0]["repair_input_estimate"] == (
        usage.calls[0]["input_token_estimate"]
        + min(cap, REPAIR_CONTENT_TOKENS)
        + REPAIR_OVERHEAD_TOKENS
    )


async def test_real_client_repair_is_reserved_and_capped() -> None:
    import httpx

    from preza.llm.client import LiteLlmClient

    bodies = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        bodies.append(body)
        return httpx.Response(
            200,
            json={
                "choices": [
                    {"message": {"content": "bad JSON" if len(bodies) == 1 else '{"text":"fixed"}'}}
                ]
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        usage = UsageLlm(LiteLlmClient("http://test.invalid", None, client))
        result = await usage.complete_json(
            "cloud-quick", "system", "u" * 20_000, SmallOutput, max_output_tokens=1500
        )
    assert result.attempts == 2 and result.value.text == "fixed"
    assert [b["max_completion_tokens"] for b in bodies] == [1500, 1500]
    assert usage.calls[0]["repair_input_estimate"] <= MAX_INPUT_TOKENS
    second = sum(estimate_tokens(m["content"]) + 16 for m in bodies[1]["messages"])
    second += estimate_tokens(json.dumps(SmallOutput.model_json_schema()))
    assert second <= usage.calls[0]["repair_input_estimate"]


@pytest.mark.parametrize("finish_reason", ["length", "stop"])
async def test_usage_distinguishes_truncation_from_schema_failure(finish_reason: str) -> None:
    import httpx

    from preza.llm.client import LiteLlmClient, LlmUnavailableError

    bodies = []

    def handler(request: httpx.Request) -> httpx.Response:
        bodies.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "choices": [{"finish_reason": finish_reason, "message": {"content": "{}"}}],
                "usage": {"prompt_tokens": 7, "completion_tokens": 3},
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        usage = UsageLlm(LiteLlmClient("http://test.invalid", None, client))
        with pytest.raises(LlmUnavailableError):
            await usage.complete_json(
                "cloud-quick", "system", "user", SmallOutput, max_output_tokens=100
            )
    truncated = finish_reason == "length"
    attempts = 1 if truncated else 2
    assert len(bodies) == attempts
    assert usage.calls[0]["status"] == "failed"
    assert usage.calls[0]["error_code"] == (
        "output_truncated" if truncated else "schema_validation_failed"
    )
    assert usage.calls[0]["prompt_tokens"] == 7 * attempts
    assert usage.calls[0]["completion_tokens"] == 3 * attempts
