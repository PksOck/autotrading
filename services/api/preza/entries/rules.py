"""Deterministic entry candidates (research §5.3 step A, BL-060).

Every hit carries the numbers that triggered it. The zone, stop and distance are computed here;
`dip_analyst` only interprets why the price fell.
"""

from dataclasses import dataclass, field
from enum import StrEnum

import numpy as np

from preza.entries.config import EntryRules
from preza.entries.indicators import Series, last


class RuleId(StrEnum):
    PULLBACK = "pullback"
    SUPPORT = "support"
    DRAWDOWN = "drawdown"
    OVERREACTION = "overreaction"
    INSIDER = "insider"
    VALUATION = "valuation"


class ZoneState(StrEnum):
    IN_ZONE = "in_zone"
    NEAR = "near"
    FAR = "far"
    BELOW = "below"


@dataclass(frozen=True)
class RuleHit:
    rule: RuleId
    values: dict[str, float]


@dataclass(frozen=True)
class EventFact:
    """An event the Radar scored for this instrument, reduced to what the rules need."""

    event_type: str | None
    is_rumor: bool
    materiality: float | None
    sentiment: float | None
    reaction_z: float | None
    age_days: float


@dataclass
class Evaluation:
    price: float
    atr: float | None
    sma50: float | None
    sma200: float | None
    rsi14: float | None
    drawdown_pct: float
    hits: list[RuleHit] = field(default_factory=list)
    zone_low: float | None = None
    zone_high: float | None = None
    stop: float | None = None
    distance_atr: float | None = None
    state: ZoneState | None = None
    anchor: str | None = None

    @property
    def active(self) -> bool:
        return bool(self.hits)


def _swing_low(series: Series, window: int = 252, exclude_recent: int = 10) -> float | None:
    if len(series.low) <= exclude_recent:
        return None
    return float(np.min(series.low[-window:-exclude_recent]))


def evaluate(
    series: Series,
    kind: str,
    rules: EntryRules,
    events: list[EventFact] | None = None,
    valuation_cheap_share: float | None = None,
) -> Evaluation | None:
    if len(series.close) < 60:
        return None
    price = float(series.close[-1])
    atr = last(series.atr14)
    sma50 = last(series.sma50)
    sma200 = last(series.sma200)
    rsi14 = last(series.rsi14)
    high_52w = float(np.max(series.high[-252:]))
    ev = Evaluation(
        price=price,
        atr=atr,
        sma50=sma50,
        sma200=sma200,
        rsi14=rsi14,
        drawdown_pct=(price / high_52w - 1) * 100,
    )
    hits = ev.hits

    # Pullback in a long-term uptrend.
    sma200_before = last(series.sma200, rules.pullback.sma200_rising_lookback)
    uptrend = sma200 is not None and (
        price > sma200 or (sma200_before is not None and sma200 > sma200_before)
    )
    if uptrend and sma50 is not None and rsi14 is not None:
        if price <= sma50 and rsi14 < rules.pullback.rsi_max:
            hits.append(RuleHit(RuleId.PULLBACK, {"sma50": sma50, "rsi14": rsi14}))

    # Support test: SMA200 or the 52-week swing low, within k x ATR.
    support_level: tuple[str, float] | None = None
    if atr:
        swing = _swing_low(series)
        for name, level in (("sma200", sma200), ("swing_low", swing)):
            if level is not None and abs(price - level) <= rules.support.atr_mult * atr:
                support_level = (name, level)
                hits.append(RuleHit(RuleId.SUPPORT, {name: level, "atr14": atr}))
                break

    # Drawdown from the 52-week high (ETFs move less, so their threshold is lower).
    limit = rules.drawdown.etf_pct if kind == "etf" else rules.drawdown.stock_pct
    if ev.drawdown_pct <= -limit:
        hits.append(RuleHit(RuleId.DRAWDOWN, {"drawdown_pct": ev.drawdown_pct, "limit": -limit}))

    for fact in events or []:
        o = rules.overreaction
        if (
            fact.age_days <= o.days
            and fact.reaction_z is not None
            and fact.reaction_z <= o.z_max
            and fact.materiality is not None
            and fact.materiality < o.materiality_max
            and not fact.is_rumor
        ):
            hits.append(
                RuleHit(
                    RuleId.OVERREACTION,
                    {"reaction_z": fact.reaction_z, "materiality": fact.materiality},
                )
            )
            break

    insider_buys = [
        f
        for f in events or []
        if f.event_type == "insider"
        and not f.is_rumor
        and (f.sentiment or 0) > 0
        and f.age_days <= rules.insider.days
    ]
    if len(insider_buys) >= rules.insider.min_filings:
        hits.append(RuleHit(RuleId.INSIDER, {"filings": float(len(insider_buys))}))

    if (
        valuation_cheap_share is not None
        and valuation_cheap_share >= rules.valuation.min_cheap_share
    ):
        hits.append(RuleHit(RuleId.VALUATION, {"cheap_share": valuation_cheap_share}))

    _zone(ev, rules, support_level)
    return ev


def _zone(ev: Evaluation, rules: EntryRules, support: tuple[str, float] | None) -> None:
    """Anchor: the support level if tested, else the price itself when a rule fired, else SMA200
    (the long-term level a watcher waits for). Without ATR there is no zone."""
    if ev.atr is None:
        return
    if support is not None:
        ev.anchor, anchor = support
    elif ev.hits:
        ev.anchor, anchor = "price", ev.price
    elif ev.sma200 is not None and ev.sma200 < ev.price:
        ev.anchor, anchor = "sma200", ev.sma200
    else:
        return
    half = rules.zone_half_width_atr * ev.atr
    ev.zone_low, ev.zone_high = anchor - half, anchor + half
    ev.stop = ev.zone_low - rules.stop_below_zone_atr * ev.atr
    if ev.price > ev.zone_high:
        ev.distance_atr = (ev.price - ev.zone_high) / ev.atr
        ev.state = ZoneState.NEAR if ev.distance_atr <= rules.near_atr else ZoneState.FAR
    elif ev.price < ev.zone_low:
        ev.distance_atr = (ev.price - ev.zone_low) / ev.atr
        ev.state = ZoneState.BELOW
    else:
        ev.distance_atr = 0.0
        ev.state = ZoneState.IN_ZONE
