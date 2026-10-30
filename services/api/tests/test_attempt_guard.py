"""Automatic permission is checked at each actual HTTP attempt."""

import json
from contextlib import asynccontextmanager
from decimal import Decimal
from types import SimpleNamespace

import httpx
import pytest
from pydantic import BaseModel

from preza.llm import automatic
from preza.llm.client import LiteLlmClient, LlmUnavailableError


class Output(BaseModel):
    value: str


@pytest.mark.parametrize(
    "enabled,manual,expected_calls", [(False, False, 1), (True, False, 2), (False, True, 2)]
)
async def test_automatic_schema_repair_rechecks_switch(
    monkeypatch, enabled, manual, expected_calls
):
    control = SimpleNamespace(automatic_analyses_enabled=True)
    requests = []

    @asynccontextmanager
    async def sessions():
        yield object()

    async def allowed(_session):
        return control.automatic_analyses_enabled

    monkeypatch.setattr(automatic, "get_sessionmaker", lambda: sessions)
    monkeypatch.setattr(automatic, "automatic_analyses_allowed", allowed)

    def handler(request):
        requests.append(json.loads(request.content))
        control.automatic_analyses_enabled = enabled
        return httpx.Response(
            200,
            json={
                "choices": [
                    {"message": {"content": "{}" if len(requests) == 1 else '{"value":"ok"}'}}
                ],
                "usage": {"prompt_tokens": 7, "completion_tokens": 3},
            },
            headers={"x-litellm-response-cost": "0.01"},
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        raw = LiteLlmClient("http://proxy", None, http)
        llm = raw if manual else automatic.AutomaticLlm(raw)
        if not enabled and not manual:
            with pytest.raises(LlmUnavailableError) as caught:
                await llm.complete_json("cloud-deep", "s", "u", Output, max_output_tokens=42)
            assert caught.value.error_code == "automatic_analyses_disabled"
            assert caught.value.attempts == 1
            assert caught.value.prompt_tokens == 7
            assert caught.value.completion_tokens == 3
            assert caught.value.cost == Decimal("0.01")
        else:
            result = await llm.complete_json("cloud-deep", "s", "u", Output, max_output_tokens=42)
            assert result.attempts == 2
            assert result.cost == Decimal("0.02")
    assert len(requests) == expected_calls
    assert all(body["max_completion_tokens"] == 42 for body in requests)


async def test_disabled_before_first_attempt_has_known_zero_usage(monkeypatch):
    @asynccontextmanager
    async def sessions():
        yield object()

    async def disabled(_session):
        return False

    monkeypatch.setattr(automatic, "get_sessionmaker", lambda: sessions)
    monkeypatch.setattr(automatic, "automatic_analyses_allowed", disabled)
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: pytest.fail("unexpected HTTP"))
    ) as http:
        with pytest.raises(LlmUnavailableError) as caught:
            await automatic.AutomaticLlm(LiteLlmClient("http://proxy", None, http)).complete_json(
                "cloud-deep", "s", "u", Output
            )
    assert caught.value.attempts == 0
    assert caught.value.error_code == "automatic_analyses_disabled"
    assert caught.value.prompt_tokens == caught.value.completion_tokens == 0
    assert caught.value.cost == Decimal("0")


async def test_incompatible_automatic_transport_never_falls_back_unguarded():
    calls = []

    class LegacyTransport:
        async def complete_json(self, role, system, user, schema):
            calls.append(role)

    with pytest.raises(TypeError, match="unexpected keyword argument"):
        await automatic.AutomaticLlm(LegacyTransport()).complete_json(
            "cloud-deep", "s", "u", Output
        )
    assert calls == []
