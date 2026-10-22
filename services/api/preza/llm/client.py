"""LLM access by role through LiteLLM (ADR-0004). Code never names a provider or model.

Structured output: the JSON schema of a Pydantic model is sent as `response_format`; the
reply is validated, and one repair attempt is made with the validation error.
"""

import json
import re
from dataclasses import dataclass
from typing import Literal, Protocol, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

Role = Literal["local-fast", "local-reason", "cloud-quick", "cloud-deep"]
T = TypeVar("T", bound=BaseModel)

FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


class LlmUnavailableError(Exception):
    """LiteLLM or the routed provider failed; callers degrade (skip triage, retry later)."""


@dataclass
class LlmResult[T: BaseModel]:
    value: T
    model: str
    prompt_tokens: int
    completion_tokens: int


class Llm(Protocol):
    async def complete_json(
        self, role: Role, system: str, user: str, schema: type[T]
    ) -> LlmResult[T]: ...

    async def embed(self, texts: list[str]) -> list[list[float]]: ...


class LiteLlmClient:
    def __init__(self, base_url: str, api_key: str | None, client: httpx.AsyncClient | None = None):
        self._base = base_url.rstrip("/")
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self._client = client or httpx.AsyncClient(timeout=300, headers=headers)
        if client is not None and api_key:
            self._client.headers.update(headers)

    async def _post(self, path: str, body: dict[str, object]) -> dict[str, object]:
        try:
            response = await self._client.post(f"{self._base}{path}", json=body)
        except httpx.HTTPError as exc:
            raise LlmUnavailableError(type(exc).__name__) from exc
        if response.status_code >= 400:
            raise LlmUnavailableError(f"http {response.status_code}: {response.text[:200]}")
        data: dict[str, object] = response.json()
        return data

    async def complete_json(
        self, role: Role, system: str, user: str, schema: type[T]
    ) -> LlmResult[T]:
        messages: list[dict[str, str]] = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        response_format = {
            "type": "json_schema",
            "json_schema": {"name": schema.__name__, "schema": schema.model_json_schema()},
        }
        last_error = ""
        for _attempt in range(2):
            data = await self._post(
                "/v1/chat/completions",
                {
                    "model": role,
                    "messages": messages,
                    "temperature": 0.1,
                    "response_format": response_format,
                },
            )
            choices = data.get("choices") or []
            content = (
                str(choices[0]["message"]["content"])
                if isinstance(choices, list) and choices
                else ""
            )
            usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
            try:
                value = schema.model_validate_json(FENCE.sub("", content).strip())
            except ValidationError as exc:
                last_error = str(exc)[:800]
                messages += [
                    {"role": "assistant", "content": content},
                    {
                        "role": "user",
                        "content": f"Invalid JSON for the schema: {last_error}. "
                        "Reply with corrected JSON only.",
                    },
                ]
                continue
            return LlmResult(
                value=value,
                model=str(data.get("model", role)),
                prompt_tokens=int(usage.get("prompt_tokens", 0)) if isinstance(usage, dict) else 0,
                completion_tokens=int(usage.get("completion_tokens", 0))
                if isinstance(usage, dict)
                else 0,
            )
        raise LlmUnavailableError(f"invalid structured output: {last_error}")

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        data = await self._post("/v1/embeddings", {"model": "embed", "input": texts})
        rows = data.get("data")
        if not isinstance(rows, list):
            raise LlmUnavailableError("embeddings: unexpected response")
        return [
            list(map(float, row["embedding"]))
            for row in sorted(rows, key=lambda r: r.get("index", 0))
        ]


def dumps(obj: object) -> str:
    return json.dumps(obj, ensure_ascii=False, default=str)
