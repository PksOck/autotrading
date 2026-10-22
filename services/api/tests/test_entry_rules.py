import math
from decimal import Decimal

import pytest

from preza.entries.config import EntryRules, load_rules
from preza.entries.indicators import compute
from preza.entries.ladder import build_ladder
from preza.entries.rules import EventFact, RuleId, ZoneState, evaluate

RULES = load_rules()


def series_from(closes: list[float], spread: float = 1.0):  # type: ignore[no-untyped-def]
    return compute([c + spread for c in closes], [c - spread for c in closes], closes)


def uptrend_then_dip(dip: float, days: int = 300) -> list[float]:
    base = [100 + 0.2 * i + 2 * math.sin(i / 5) for i in range(days - 10)]
    top = base[-1]
    return base + [top - dip * (i + 1) / 10 for i in range(10)]


def test_rules_file_is_valid() -> None:
    assert RULES.version >= 1
    assert sum(RULES.ladder.weights) == pytest.approx(1)


def test_pullback_in_uptrend() -> None:
    ev = evaluate(series_from(uptrend_then_dip(8)), "stock", RULES)
    assert ev is not None
    rules = {h.rule for h in ev.hits}
    assert RuleId.PULLBACK in rules
    assert ev.price > (ev.sma200 or 0)
    assert ev.state == ZoneState.IN_ZONE  # anchored at the price when a rule fires
    assert ev.stop is not None and ev.zone_low is not None and ev.stop < ev.zone_low


def test_quiet_uptrend_waits_at_sma200() -> None:
    closes = [100 + 0.3 * i for i in range(300)]
    ev = evaluate(series_from(closes), "stock", RULES)
    assert ev is not None and not ev.active
    assert ev.anchor == "sma200"
    assert ev.state == ZoneState.FAR and (ev.distance_atr or 0) > RULES.near_atr


def test_drawdown_threshold_depends_on_kind() -> None:
    closes = [100.0] * 200 + [100 - i * 0.1 for i in range(100)]  # -9.9 %
    stock = evaluate(series_from(closes, 0.3), "stock", RULES)
    etf = evaluate(series_from(closes, 0.3), "etf", RULES)
    assert stock is not None and etf is not None
    assert RuleId.DRAWDOWN not in {h.rule for h in stock.hits}
    assert RuleId.DRAWDOWN in {h.rule for h in etf.hits}


def test_overreaction_needs_low_materiality_and_no_rumor() -> None:
    s = series_from([100 + 0.1 * i for i in range(300)])
    fact = EventFact("guidance", False, 0.3, -0.4, -2.5, 1)
    assert RuleId.OVERREACTION in {h.rule for h in evaluate(s, "stock", RULES, [fact]).hits}  # type: ignore[union-attr]
    material = EventFact("guidance", False, 0.8, -0.4, -2.5, 1)
    rumor = EventFact("rumor", True, 0.3, -0.4, -2.5, 1)
    for f in (material, rumor):
        ev = evaluate(s, "stock", RULES, [f])
        assert ev is not None and RuleId.OVERREACTION not in {h.rule for h in ev.hits}


def test_insider_and_valuation() -> None:
    s = series_from([100 + 0.1 * i for i in range(300)])
    buys = [EventFact("insider", False, 0.5, 0.5, None, d) for d in (3, 10)]
    ev = evaluate(s, "stock", RULES, buys, valuation_cheap_share=0.67)
    assert ev is not None
    assert {RuleId.INSIDER, RuleId.VALUATION} <= {h.rule for h in ev.hits}


def test_too_short_history() -> None:
    assert evaluate(series_from([100.0] * 30), "stock", RULES) is None


def test_ladder_respects_stop_and_budget() -> None:
    levels = build_ladder(
        Decimal("100"), Decimal("4"), Decimal("93"), [0.4, 0.3, 0.3], 1.0, Decimal("1000")
    )
    assert [lv.price for lv in levels] == [Decimal("100.00"), Decimal("96.00")]
    assert [lv.weight for lv in levels] == [Decimal("0.4"), Decimal("0.6")]  # last takes the rest
    assert levels[0].amount == Decimal("400.00") and levels[0].quantity == Decimal("4")
    full = build_ladder(Decimal("100"), Decimal("2"), Decimal("90"), [0.4, 0.3, 0.3])
    assert [lv.price for lv in full] == [Decimal("100.00"), Decimal("98.00"), Decimal("96.00")]


def test_invalid_weights_rejected() -> None:
    with pytest.raises(ValueError):
        EntryRules.model_validate({"ladder": {"weights": [0.5, 0.2]}})
