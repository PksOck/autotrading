"""Decision card: deterministic control score and size, the model's draft (BL-089)."""

from datetime import date, timedelta

from preza.domain.analysis import ControlScore, PreviousRun
from preza_agents.decision_card import (
    CardDraft,
    build_card,
    control_score,
    implied_rating,
    rating_gap,
    size_class,
    valuation_component,
)
from tests.conftest import make_snapshot


def _history(values: list[float], end: date) -> list[tuple[date, float]]:
    return [(end - timedelta(days=90 * i), v) for i, v in enumerate(values)]


def test_valuation_against_own_history() -> None:
    snap = make_snapshot()
    end = date(2026, 10, 1)
    snap.fundamentals = {"pe": 15.0, "fcf_yield": 6.0, "ev_ebit": None}
    snap.fundamentals_history = {
        "pe": _history([20, 22, 25, 18, 21, 24, 26, 23, 19, 20], end),  # 15 is the cheapest
        "fcf_yield": _history([3, 4, 3.5, 4.5, 3, 4, 3.2, 3.8, 4.1, 3.9], end),  # 6 is the best
    }
    assert valuation_component(snap) == 1.0
    snap.fundamentals = {"pe": 30.0}
    assert valuation_component(snap) == -1.0
    snap.fundamentals_history = {}
    assert valuation_component(snap) is None  # too little history


def test_control_score_without_fundamental_history() -> None:
    control = control_score(make_snapshot())  # the fixture has metrics, no history
    assert control.components["valuation"] is None and control.components["quality"] is None
    assert control.components["technical"] is not None and control.components["risk"] is not None
    assert control.coverage == round(0.30 / 0.70, 3)  # technical and risk of four weights
    assert control.score is not None and control.implied_rating == implied_rating(control.score)
    # The bar after the run date is ignored: the fixture's look-ahead close of 1.00
    # would make the risk component -1.
    assert control.components["risk"] > -1


def test_implied_rating_and_gap() -> None:
    assert [implied_rating(s) for s in (0.6, 0.2, 0.0, -0.3, -0.8)] == [
        "Buy",
        "Overweight",
        "Hold",
        "Underweight",
        "Sell",
    ]
    assert rating_gap("Buy", "Underweight") == 3
    assert rating_gap("Buy", None) is None and rating_gap("Accumulate", "Hold") is None


def test_size_class() -> None:
    assert size_class("Hold", 9, "normal") == "none"
    assert size_class("Buy", None, "normal") is None
    assert [size_class("Buy", c, "normal") for c in (3, 6, 9)] == ["small", "normal", "increased"]
    assert size_class("Overweight", 9, "low") == "small"


def _control(implied: str | None) -> ControlScore:
    return ControlScore(
        score=None if implied is None else -0.6,
        coverage=1.0,
        components={},
        weights={},
        implied_rating=implied,
    )


def test_disagreement_lowers_confidence_but_not_the_rating() -> None:
    draft = CardDraft(conviction=9, upgrade_if=["x"], delta_note="changed")
    card = build_card("Buy", _control("Sell"), draft, None)
    assert card.rating == "Buy" and card.confidence == "low" and card.size_class == "small"
    assert card.delta_note is None  # no previous run, nothing to compare
    previous = PreviousRun(
        id="00000000-0000-0000-0000-000000000001", trade_date=date(2026, 9, 1), rating="Hold"
    )  # type: ignore[arg-type]
    card = build_card("Buy", _control("Overweight"), draft, previous)
    assert card.confidence == "normal" and card.size_class == "increased"
    assert card.delta_note == "changed"
    bare = build_card("Hold", _control(None), None, None)
    assert bare.conviction is None and bare.upgrade_if == [] and bare.confidence == "normal"
