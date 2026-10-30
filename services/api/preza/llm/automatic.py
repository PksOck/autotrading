"""Recheck the master switch before each automatic external model request."""

from typing import cast

from pydantic import BaseModel

from preza.db import get_sessionmaker
from preza.llm.client import AttemptGuardedLlm, Llm, LlmAutomaticDisabledError, LlmResult, Role
from preza.services.automation import automatic_analyses_allowed


class AutomaticLlm:
    def __init__(self, inner: Llm):
        self.inner = inner

    async def allowed(self) -> None:
        async with get_sessionmaker()() as session:
            if not await automatic_analyses_allowed(session):
                raise LlmAutomaticDisabledError("automatic_analyses_disabled")

    async def complete_json[T: BaseModel](
        self,
        role: Role,
        system: str,
        user: str,
        schema: type[T],
        *,
        max_output_tokens: int | None = None,
    ) -> LlmResult[T]:
        # No unguarded fallback: an incompatible transport must fail closed.
        return await cast(AttemptGuardedLlm, self.inner).complete_json(
            role,
            system,
            user,
            schema,
            max_output_tokens=max_output_tokens,
            before_attempt=self.allowed,
        )

    async def embed(self, texts: list[str]) -> list[list[float]]:
        await self.allowed()
        return await self.inner.embed(texts)
