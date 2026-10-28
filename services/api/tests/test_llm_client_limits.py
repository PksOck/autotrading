"""HTTP recordings verify both bounded attempts and usage across JSON repair."""

import json
from decimal import Decimal
from pathlib import Path

import httpx
import pytest
import yaml
from pydantic import BaseModel

from preza.llm.client import (
    CLIENT_TIMEOUT_SECONDS,
    LiteLlmClient,
    LlmSchemaError,
    LlmTruncatedError,
    LlmUnavailableError,
)


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
            assert request["max_completion_tokens"] == 4000
        else:
            assert "max_completion_tokens" not in request
        assert "max_tokens" not in request
        assert "thinking" not in request and "extra_body" not in request


async def test_failure_records_both_attempts_and_unknown_cost(caplog):
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
        with pytest.raises(LlmSchemaError) as caught:
            await LiteLlmClient("http://proxy", None, http).complete_json(
                "cloud-deep", "s", "u", Output, max_output_tokens=4000
            )
    assert len(calls) == caught.value.attempts == 2
    assert caught.value.prompt_tokens == 14 and caught.value.completion_tokens == 6
    assert caught.value.cost is None
    assert caught.value.error_code == "schema_validation_failed"
    assert "schema_validation_failed" in caplog.text
    assert "output_truncated" not in caplog.text


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


@pytest.mark.parametrize("content", [None, "", '{"value":', '{"value":"valid but truncated"}'])
@pytest.mark.parametrize("repair_first", [False, True])
async def test_length_never_repairs_even_valid_json(content, repair_first, caplog):
    calls = []

    def handler(request):
        calls.append(request)
        repair = repair_first and len(calls) == 1
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "finish_reason": "stop" if repair else "length",
                        "message": {"content": "{}" if repair else content},
                    }
                ],
                "usage": {"prompt_tokens": 7, "completion_tokens": 3},
            },
            headers={"x-litellm-response-cost": "0.01"},
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        with pytest.raises(LlmTruncatedError) as caught:
            await LiteLlmClient("http://proxy", None, http).complete_json(
                "cloud-deep", "private system", "private user", Output, max_output_tokens=3
            )
    attempts = 2 if repair_first else 1
    assert len(calls) == caught.value.attempts == attempts
    assert caught.value.prompt_tokens == 7 * attempts
    assert caught.value.completion_tokens == 3 * attempts
    assert caught.value.cost == Decimal("0.01") * attempts
    assert caught.value.error_code == "output_truncated"
    assert "output_truncated" in caplog.text and "finish_reason=length" in caplog.text
    assert "schema_validation_failed" not in caplog.text
    assert "private" not in caplog.text


@pytest.mark.parametrize("role", ["local-fast", "local-reason", "cloud-quick", "cloud-deep"])
async def test_role_options_and_timeout_with_injected_transport(role):
    def handler(request):
        body = json.loads(request.content)
        local = role.startswith("local-")
        token_param = "max_tokens" if local else "max_completion_tokens"
        other_param = "max_completion_tokens" if local else "max_tokens"
        assert body[token_param] == 42 and other_param not in body
        assert body["response_format"]["type"] == "json_schema"
        assert "extra_body" not in body and "thinking" not in body
        assert set(request.extensions["timeout"].values()) == {CLIENT_TIMEOUT_SECONDS}
        return httpx.Response(200, json={"choices": [{"message": {"content": '{"value":"ok"}'}}]})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler), timeout=None) as http:
        await LiteLlmClient("http://proxy", None, http).complete_json(
            role, "s", "u", Output, max_output_tokens=42
        )


def test_client_deadline_has_proxy_margin():
    config_path = Path(__file__).resolve().parents[3] / "infra/litellm/config.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert CLIENT_TIMEOUT_SECONDS > 0
    assert CLIENT_TIMEOUT_SECONDS <= config["litellm_settings"]["request_timeout"] - 60


async def test_truncated_unknown_cost():
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(
                200, json={"choices": [{"finish_reason": "length", "message": {"content": None}}]}
            )
        )
    ) as http:
        with pytest.raises(LlmTruncatedError) as caught:
            await LiteLlmClient("http://proxy", None, http).complete_json(
                "cloud-quick", "s", "u", Output
            )
    assert caught.value.cost is None
