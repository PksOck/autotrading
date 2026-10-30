"""Recheck the master switch before each automatic external model request."""

from typing import cast

from pydantic import BaseModel

from preza.db import get_sessionmaker
from preza.llm.client import Llm, LlmResult, LlmUnavailableError, OutputLimitedLlm, Role
from preza.services.automation import automatic_analyses_allowed


class AutomaticLlm:
    def __init__(self, inner: Llm):
        self.inner = inner

    async def allowed(self) -> None:
        async with get_sessionmaker()() as session:
            if not await automatic_analyses_allowed(session):
                raise LlmUnavailableError("automatic_analyses_disabled")

    async def complete_json[T: BaseModel](
        self,
        role: Role,
        system: str,
        user: str,
        schema: type[T],
        *,
        max_output_tokens: int | None = None,
    ) -> LlmResult[T]:
        await self.allowed()
        if max_output_tokens is not None:
            return await cast(OutputLimitedLlm, self.inner).complete_json(
                role, system, user, schema, max_output_tokens=max_output_tokens
            )
        return await self.inner.complete_json(role, system, user, schema)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        await self.allowed()
        return await self.inner.embed(texts)
