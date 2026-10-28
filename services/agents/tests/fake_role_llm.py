"""Scripted stand-in for preza's LiteLLM client (role-based JSON calls)."""

from __future__ import annotations

import json
import re
from typing import Any

from pydantic import BaseModel

from preza.llm.client import LlmResult
from preza_agents.budget import input_estimate
from preza_agents.decision_card import CardDraft
from preza_agents.etf_analyst.analyst import EtfDecision, EtfTheme
from preza_agents.hypothesis import HypothesisCheck
from preza_agents.stock_analyst.analyst import (
    AnalystNote,
    EvidencePoint,
    StockDecision,
    StockHypothesis,
    StockSummary,
)


class FakeRoleLlm:
    def __init__(
        self,
        rating: str = "Hold",
        check_fails: bool = False,
        conviction: int = 6,
        compose_fails: bool = False,
        invented_number: bool = False,
        evidence_ids: list[str] | None = None,
        hypothesis_verdict: str = "partly",
        decision_fails: bool = False,
    ) -> None:
        self.rating = rating
        self.conviction = conviction
        self.check_fails = check_fails
        self.calls: list[tuple[str, str, str]] = []
        self.input_sizes: list[int] = []
        self.output_caps: list[int | None] = []
        self.compose_fails = compose_fails
        self.invented_number = invented_number
        self.evidence_ids = evidence_ids
        self.hypothesis_verdict = hypothesis_verdict
        self.decision_fails = decision_fails

    async def complete_json(
        self,
        role: str,
        system: str,
        user: str,
        schema: type[BaseModel],
        *,
        max_output_tokens: int | None = None,
    ) -> LlmResult[Any]:
        self.calls.append((role, system, user))
        self.input_sizes.append(input_estimate(system, user, schema))
        self.output_caps.append(max_output_tokens)
        register = json.loads(user).get("evidence_register", "")
        ids = self.evidence_ids
        if ids is None:
            ids = re.findall(r"\[([A-Z]\d+)\].*?; confirmed", register)[:1]

        def point(text: str) -> EvidencePoint:
            return EvidencePoint(text=text, evidence_ids=ids)

        value: BaseModel
        if schema is AnalystNote:
            value = AnalystNote(
                stance=0,
                key_points=[point("Dokazi so mešani.")],
                risks=[point("Manjkajo podatki.")],
                what_to_watch=[point("Uradna objava.")],
            )
        elif schema is StockDecision:
            if self.decision_fails:
                raise RuntimeError("invalid structured output after repair")
            value = StockDecision(
                rating=self.rating,  # type: ignore[arg-type]
                rationale="Cena bo 987654.32." if self.invented_number else "Dokazi so mešani.",
                evidence_ids=ids,
                reasons=[point("Tehnična slika je na voljo.")],
                risks=[point("Manjkajo temeljni podatki.")],
                upgrade_if=[point("Podjetje potrdi rast naročil.")],
                downgrade_if=[point("Podjetje zniža obete.")],
                conviction=self.conviction,
                delta_note="Ocena ostaja.",
                hypothesis=StockHypothesis(
                    verdict=self.hypothesis_verdict,  # type: ignore[arg-type]
                    reasoning="Dokazi so nepopolni.",
                    evidence_ids=ids,
                    evidence_for=[point("Uradna objava naročila.")],
                )
                if '"hypothesis": null' not in user and not self.check_fails
                else None,
            )
        elif schema is StockSummary:
            if self.compose_fails:
                raise RuntimeError("compose unavailable")
            value = StockSummary(summary="Počakaj na dodatne uradne podatke.")
        elif schema is EtfTheme:
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
        return LlmResult(
            value=value,
            model=f"fake-{role}",
            prompt_tokens=self.input_sizes[-1],
            completion_tokens=42,
        )

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.0] for _ in texts]
