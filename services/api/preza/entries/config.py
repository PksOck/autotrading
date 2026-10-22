"""Entry rules configuration loaded from `rules.yaml` (BL-060)."""

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, field_validator

RULES_FILE = Path(__file__).with_name("rules.yaml")


class Pullback(BaseModel):
    rsi_max: float = 40
    sma200_rising_lookback: int = 20


class Support(BaseModel):
    atr_mult: float = 1.0


class Drawdown(BaseModel):
    stock_pct: float = 15
    etf_pct: float = 8


class Overreaction(BaseModel):
    z_max: float = -2.0
    materiality_max: float = 0.5
    days: int = 5


class Insider(BaseModel):
    min_filings: int = 2
    days: int = 30


class Valuation(BaseModel):
    min_cheap_share: float = 0.5


class Ladder(BaseModel):
    weights: list[float] = Field(default_factory=lambda: [0.4, 0.3, 0.3])
    step_atr: float = 1.0

    @field_validator("weights")
    @classmethod
    def _sum_to_one(cls, v: list[float]) -> list[float]:
        if not v or abs(sum(v) - 1) > 1e-6 or any(w <= 0 for w in v):
            raise ValueError("ladder weights must be positive and sum to 1")
        return v


class EntryRules(BaseModel):
    version: int = 1
    zone_half_width_atr: float = 0.5
    near_atr: float = 2.0
    stop_below_zone_atr: float = 1.5
    pullback: Pullback = Pullback()
    support: Support = Support()
    drawdown: Drawdown = Drawdown()
    overreaction: Overreaction = Overreaction()
    insider: Insider = Insider()
    valuation: Valuation = Valuation()
    ladder: Ladder = Ladder()


@lru_cache
def load_rules(path: Path = RULES_FILE) -> EntryRules:
    return EntryRules.model_validate(yaml.safe_load(path.read_text()) or {})
