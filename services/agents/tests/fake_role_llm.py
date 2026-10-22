"""Scripted stand-in for preza's LiteLLM client (role-based JSON calls)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from preza.llm.client import LlmResult
from preza_agents.decision_card import CardDraft
from preza_agents.etf_analyst.analyst import EtfDecision, EtfTheme
from preza_agents.hypothesis import HypothesisCheck


class FakeRoleLlm:
    def __init__(
        self, rating: str = "Hold", check_fails: bool = False, conviction: int = 6
    ) -> None:
        self.rating = rating
        self.conviction = conviction
        self.check_fails = check_fails
        self.calls: list[tuple[str, str, str]] = []

    async def complete_json(
        self, role: str, system: str, user: str, schema: type[BaseModel]
    ) -> LlmResult[Any]:
        self.calls.append((role, system, user))
        value: BaseModel
        if schema is EtfTheme:
            value = EtfTheme(summary="Polprevodniki rastejo z naložbami v AI.", drivers=["AI"])
        elif schema is EtfDecision:
            value = EtfDecision(rating=self.rating, rationale="Prekrivanje je majhno.")  # type: ignore[arg-type]
        elif schema is CardDraft:
            value = CardDraft(
                upgrade_if=["Cena zapre nad 200-dnevnim povprečjem."],
                downgrade_if=["Naročila padejo dve četrtletji zapored."],
                conviction=self.conviction,
                delta_note="Ocena ostaja, nov je podatek o naročilih.",
            )
        elif schema is HypothesisCheck:
            if self.check_fails:
                raise RuntimeError("model unavailable")
            value = HypothesisCheck(
                verdict="partly",
                reasoning="Tema drži, vstop je zgoden.",
                evidence_for=["Rast naložb v AI."],
            )
        else:
            raise AssertionError(schema)
        return LlmResult(value=value, model=f"fake-{role}", prompt_tokens=0, completion_tokens=0)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.0] for _ in texts]
