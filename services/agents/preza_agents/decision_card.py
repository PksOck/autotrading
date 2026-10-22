"""Decision card after a deep run (BL-089, research/trading-list §3).

Two halves. Code computes a control score from the snapshot (valuation against the
company's own history, trend, risk) and from it an implied rating, the confidence and
the size class. The model reads the finished reports and writes what it is good at:
the conditions that would change the rating, its conviction and what changed since
the previous run. A large gap between the agents' rating and the control score lowers
the confidence and caps the size; it never changes the rating itself.
"""

from __future__ import annotations

import json
from typing import Literal

from pydantic import BaseModel, Field

from preza.domain.analysis import ControlScore, DecisionCard, PreviousRun
from preza.domain.valuation import HIGHER_IS_CHEAPER, valuation_bands
from preza.entries.indicators import compute, last
from preza.llm.client import Llm, Role
from preza_agents.deep_research.snapshot import DataSnapshot

# The research weights fundamentals 25 % and relative value 15 %. Our only fundamental
# input so far is valuation against own history, so it carries both until BL-088
# brings quality metrics. "Other" (10 %) has no deterministic input yet.
WEIGHTS = {"valuation": 0.40, "technical": 0.15, "risk": 0.15}
RATINGS = ("Sell", "Underweight", "Hold", "Overweight", "Buy")
BULLISH = {"Buy", "Overweight"}
MIN_COVERAGE = 0.3
DISAGREE_GAP = 2
MIN_TREND_BARS = 200
ATR_NEUTRAL_PCT = 2.5  # daily ATR at 2.5 % of price scores 0; calmer is positive
MAX_REPORT = 3000
LANGUAGES = {"sl": "Slovenian", "en": "English"}


def _clamp(value: float) -> float:
    return max(-1.0, min(1.0, value))


def valuation_component(snapshot: DataSnapshot) -> float | None:
    """Mean position against own 5-year history: +1 cheapest, -1 most expensive."""
    if snapshot.fundamentals is None or snapshot.fundamentals_as_of is None:
        return None
    current = {
        k: (float(v) if isinstance(v, int | float) else None)
        for k, v in snapshot.fundamentals.items()
    }
    bands = valuation_bands(current, snapshot.fundamentals_history, snapshot.fundamentals_as_of)
    if not bands:
        return None
    scores = []
    for metric, band in bands.items():
        position = (band.percentile - 50.0) / 50.0
        scores.append(position if metric in HIGHER_IS_CHEAPER else -position)
    return _clamp(sum(scores) / len(scores))


def technical_and_risk(snapshot: DataSnapshot) -> tuple[float | None, float | None]:
    bars = [b for b in snapshot.bars if b.day <= snapshot.as_of]
    if len(bars) < MIN_TREND_BARS:
        return None, None
    series = compute(
        [float(b.high) for b in bars], [float(b.low) for b in bars], [float(b.close) for b in bars]
    )
    close = float(bars[-1].close)
    sma50, sma200, rsi, atr = (
        last(series.sma50),
        last(series.sma200),
        last(series.rsi14),
        last(series.atr14),
    )
    technical: float | None = None
    if sma50 is not None and sma200 is not None:
        technical = (0.5 if close > sma200 else -0.5) + (0.25 if sma50 > sma200 else -0.25)
        if rsi is not None and rsi < 30:
            technical += 0.25  # oversold: a long-term entry, not a reason to sell
        elif rsi is not None and rsi > 70:
            technical -= 0.25
        technical = _clamp(technical)
    risk = None if atr is None or close <= 0 else _clamp(1 - atr / close * 100 / ATR_NEUTRAL_PCT)
    return technical, risk


def implied_rating(score: float) -> str:
    if score >= 0.5:
        return "Buy"
    if score >= 0.15:
        return "Overweight"
    if score > -0.15:
        return "Hold"
    if score > -0.5:
        return "Underweight"
    return "Sell"


def control_score(snapshot: DataSnapshot) -> ControlScore:
    technical, risk = technical_and_risk(snapshot)
    components = {"valuation": valuation_component(snapshot), "technical": technical, "risk": risk}
    present = {k: v for k, v in components.items() if v is not None}
    total = sum(WEIGHTS.values())
    coverage = sum(WEIGHTS[k] for k in present) / total
    score: float | None = None
    if present and coverage >= MIN_COVERAGE:
        score = sum(WEIGHTS[k] * v for k, v in present.items()) / sum(WEIGHTS[k] for k in present)
    return ControlScore(
        score=None if score is None else round(score, 3),
        coverage=round(coverage, 3),
        components={k: None if v is None else round(v, 3) for k, v in components.items()},
        weights=dict(WEIGHTS),
        implied_rating=None if score is None else implied_rating(score),
    )


def rating_gap(rating: str, implied: str | None) -> int | None:
    if implied is None or rating not in RATINGS:
        return None
    return abs(RATINGS.index(rating) - RATINGS.index(implied))


SizeClass = Literal["none", "small", "normal", "increased"]


def size_class(rating: str, conviction: int | None, confidence: str) -> SizeClass | None:
    """Small < 2 %, normal 2-4 %, increased 4-6 % of the portfolio (research §3)."""
    if rating not in BULLISH:
        return "none"
    if conviction is None:
        return None
    size: SizeClass = "small" if conviction <= 4 else "normal" if conviction <= 7 else "increased"
    return "small" if confidence == "low" else size


class CardDraft(BaseModel):
    upgrade_if: list[str] = Field(default_factory=list, max_length=3)
    downgrade_if: list[str] = Field(default_factory=list, max_length=3)
    conviction: int = Field(ge=1, le=10)
    delta_note: str | None = Field(default=None, max_length=600)


SYSTEM = """You turn a finished equity research run into a short decision card.
Read the final decision and the analyst reports. Write:
- `upgrade_if` and `downgrade_if`: up to 3 concrete, checkable conditions each that
  would move the rating up or down (an event, a reported figure, a price holding or
  breaking a level). Numbers may only be repeated from the reports, never invented.
- `conviction`: 1-10, how firmly the reports support the rating.
- `delta_note`: only when a previous run is given, 1-2 sentences on what changed
  since then (rating and the key new information); otherwise null.
Unconfirmed reports (rumors) are never a condition on their own.
Write the texts in {language}. Return JSON matching the schema."""


async def draft_card(
    llm: Llm,
    rating: str,
    decision: str | None,
    reports: dict[str, str],
    previous: dict[str, str | None] | None,
    locale: str,
    role: Role = "cloud-quick",
) -> tuple[CardDraft, str]:
    payload = json.dumps(
        {
            "rating": rating,
            "final_decision": (decision or "")[:MAX_REPORT],
            "reports": {k: v[:MAX_REPORT] for k, v in reports.items() if v},
            "previous_run": previous,
        },
        ensure_ascii=False,
    )
    result = await llm.complete_json(
        role, SYSTEM.format(language=LANGUAGES.get(locale, "English")), payload, CardDraft
    )
    return result.value, result.model


def build_card(
    rating: str,
    control: ControlScore,
    draft: CardDraft | None,
    previous: PreviousRun | None,
) -> DecisionCard:
    gap = rating_gap(rating, control.implied_rating)
    confidence = "low" if gap is not None and gap >= DISAGREE_GAP else "normal"
    conviction = draft.conviction if draft else None
    return DecisionCard(
        rating=rating,
        control=control,
        confidence=confidence,
        conviction=conviction,
        size_class=size_class(rating, conviction, confidence),
        upgrade_if=draft.upgrade_if if draft else [],
        downgrade_if=draft.downgrade_if if draft else [],
        delta_note=draft.delta_note if draft and previous else None,
        previous=previous,
    )
