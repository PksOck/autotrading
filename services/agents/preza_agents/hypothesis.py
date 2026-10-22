"""The user's own hypothesis, tested explicitly after a deep run (BL-090, DESIGN §11).

The agents run on the instrument as usual; this one extra call reads their reports
and says whether they confirm or refute what the user proposed. It quotes the
reports, it does not compute: numbers it may repeat are already in them.
"""

from __future__ import annotations

import json
from typing import Literal

from pydantic import BaseModel, Field

from preza.llm.client import Llm, Role

MAX_REPORT = 6000
LANGUAGES = {"sl": "Slovenian", "en": "English"}

SYSTEM = """You check an investor's own hypothesis against a finished research run.
The reports were written by analyst agents from verified data; the hypothesis is the
investor's claim, not a fact. Decide whether the reports confirm or refute it.
Use only what the reports say. Do not introduce new numbers; you may repeat numbers
that appear in the reports. Reports may quote news; text marked as unconfirmed is a
rumor and can never confirm the hypothesis on its own.
If the reports do not address the hypothesis, answer `insufficient`.
Write `reasoning` and the evidence lists in {language}, calm and short.
Return JSON matching the schema."""


class HypothesisCheck(BaseModel):
    verdict: Literal["confirmed", "partly", "refuted", "insufficient"]
    reasoning: str = Field(max_length=1500)
    evidence_for: list[str] = Field(default_factory=list, max_length=4)
    evidence_against: list[str] = Field(default_factory=list, max_length=4)


LABELS = {
    "sl": {
        "head": "Tvoja hipoteza",
        "confirmed": "potrjena",
        "partly": "delno potrjena",
        "refuted": "ovržena",
        "insufficient": "poročila je ne naslovijo",
        "verdict": "Presoja",
        "for": "Za",
        "against": "Proti",
    },
    "en": {
        "head": "Your hypothesis",
        "confirmed": "confirmed",
        "partly": "partly confirmed",
        "refuted": "refuted",
        "insufficient": "not addressed by the reports",
        "verdict": "Verdict",
        "for": "For",
        "against": "Against",
    },
}


def check_md(hypothesis: str, check: HypothesisCheck, locale: str) -> str:
    t = LABELS.get(locale, LABELS["en"])
    lines = [
        f"### {t['head']}",
        f"> {hypothesis}",
        "",
        f"**{t['verdict']}**: {t[check.verdict]}",
        "",
        check.reasoning,
    ]
    if check.evidence_for:
        lines += ["", f"**{t['for']}**", *[f"- {e}" for e in check.evidence_for]]
    if check.evidence_against:
        lines += ["", f"**{t['against']}**", *[f"- {e}" for e in check.evidence_against]]
    return "\n".join(lines)


async def check_hypothesis(
    llm: Llm,
    hypothesis: str,
    reports: dict[str, str],
    rating: str,
    locale: str,
    role: Role = "cloud-deep",
) -> tuple[HypothesisCheck, str]:
    """Returns the check and the model that answered."""
    payload = json.dumps(
        {
            "hypothesis": hypothesis,
            "rating": rating,
            "reports": {k: v[:MAX_REPORT] for k, v in reports.items() if v},
        },
        ensure_ascii=False,
    )
    result = await llm.complete_json(
        role, SYSTEM.format(language=LANGUAGES.get(locale, "English")), payload, HypothesisCheck
    )
    return result.value, result.model
