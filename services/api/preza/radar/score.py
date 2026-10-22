"""Opportunity score (research §5.2.1). Deterministic; weights are versioned config."""

from dataclasses import dataclass

SCORE_VERSION = "2026-10-v1"


@dataclass(frozen=True)
class ScoreInput:
    materiality: float
    novelty: float
    reaction_z: float | None
    relevance: float  # portfolio 1.0 · watchlist 0.8 · known universe 0.5 · unknown 0.3
    is_rumor: bool
    attention: float | None  # mentions vs 30-day baseline, 1.0 = normal


def opportunity_score(x: ScoreInput) -> float:
    reaction = 0.5 + 0.5 * min(abs(x.reaction_z or 0.0) / 3.0, 1.0)
    attention_boost = 1.0 + 0.5 * min(max((x.attention or 1.0) - 1.0, 0.0) / 7.0, 1.0)
    rumor_penalty = 0.6 if x.is_rumor else 1.0
    raw = x.materiality * x.novelty * reaction * x.relevance * rumor_penalty * attention_boost
    return round(max(0.0, min(raw, 1.0)), 4)
