"""HTTP recordings verify both bounded attempts and usage across JSON repair."""

import json
from decimal import Decimal

import httpx
import pytest
from pydantic import BaseModel

from preza.llm.client import LiteLlmClient, LlmUnavailableError


class Output(BaseModel):
    value: str


@pytest.mark.parametrize("limited", [False, True])
async def test_output_limit_each_attempt_and_accumulated_usage(limited):
    requests = []

    def handler(request):
        requests.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "model": "recorded-model",
                "choices": [
                    {"message": {"content": "not JSON" if len(requests) == 1 else '{"value":"ok"}'}}
                ],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5},
            },
            headers={"x-litellm-response-cost": "0.001"},
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        client = LiteLlmClient("http://proxy", None, http)
        kwargs = {"max_output_tokens": 4000} if limited else {}
        result = await client.complete_json(
            "cloud-deep", "system", "recorded input", Output, **kwargs
        )
    assert result.attempts == 2 and result.prompt_tokens == 20 and result.completion_tokens == 10
    assert result.cost == Decimal("0.002")
    assert result.value.value == "ok"
    assert len(requests) == 2
    for request in requests:
        assert request["model"] == "cloud-deep"
        assert request["response_format"]["json_schema"]["name"] == "Output"
        if limited:
            assert request["max_tokens"] == 4000
        else:
            assert "max_tokens" not in request


async def test_failure_records_both_attempts_and_unknown_cost():
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "{}"}}],
                "usage": {"prompt_tokens": 7, "completion_tokens": 3},
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        with pytest.raises(LlmUnavailableError) as caught:
            await LiteLlmClient("http://proxy", None, http).complete_json(
                "cloud-deep", "s", "u", Output, max_output_tokens=4000
            )
    assert len(calls) == caught.value.attempts == 2
    assert caught.value.prompt_tokens == 14 and caught.value.completion_tokens == 6
    assert caught.value.cost is None


async def test_timeout_after_repair_does_not_retry_and_keeps_usage():
    calls = []

    def handler(request):
        calls.append(request)
        if len(calls) == 2:
            raise httpx.ReadTimeout("secret provider details")
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "{}"}}],
                "usage": {"prompt_tokens": 7, "completion_tokens": 3},
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        with pytest.raises(LlmUnavailableError) as caught:
            await LiteLlmClient("http://proxy", None, http).complete_json(
                "cloud-deep", "s", "u", Output, max_output_tokens=4000
            )
    assert len(calls) == caught.value.attempts == 2
    assert caught.value.prompt_tokens == 7
    assert "secret" not in str(caught.value)


async def test_invalid_limit_never_dispatches():
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda r: pytest.fail("dispatch"))
    ) as http:
        with pytest.raises(ValueError):
            await LiteLlmClient("http://proxy", None, http).complete_json(
                "cloud-deep", "s", "u", Output, max_output_tokens=0
            )
