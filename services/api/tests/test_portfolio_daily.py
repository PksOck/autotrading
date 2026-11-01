from datetime import date
from decimal import Decimal as D

from preza.domain.portfolio_daily import DailyHolding, daily_move, native_daily_moves


def holding(**changes):
    values = dict(
        quantity=D("2"),
        currency="USD",
        fx=D("0.9"),
        close=D("110"),
        previous=D("100"),
        day=date(2026, 10, 30),
        previous_day=date(2026, 10, 29),
        report_date=date(2026, 10, 29),
        source="synthetic",
        resolved=True,
        fx_base_currency="EUR",
    )
    return DailyHolding(**(values | changes))


def test_daily_move_uses_decimal_and_constant_fx_for_the_same_positions():
    result = daily_move([holding(), holding(quantity=D("3"), currency="EUR", fx=None)], "EUR")
    assert result.amount == D("48")
    assert result.percent == D("10")
    assert result.market_date == date(2026, 10, 30)
    assert result.basis == "held_positions_constant_reported_fx"


def test_zero_is_known_and_negative_is_preserved():
    assert daily_move([holding(close=D("100"))], "EUR").amount == 0
    assert daily_move([holding(close=D("90"))], "EUR").amount == D("-18")


def test_unverified_fx_target_cannot_be_labelled_as_the_requested_currency():
    for target in [None, "USD"]:
        assert daily_move([holding(fx=D(1), fx_base_currency=target)], "EUR").amount is None
    native = daily_move([holding(fx_base_currency=None)], "USD")
    assert native.amount == D("20") and native.percent == D("10")


def test_incomplete_or_misaligned_data_never_becomes_a_partial_total():
    for patch in [
        dict(fx=None),
        dict(close=None),
        dict(previous=D(0)),
        dict(resolved=False),
        dict(quantity=D(-1)),
        dict(day=date(2026, 10, 29)),
        dict(fx=D("NaN")),
        dict(quantity=D("Infinity")),
    ]:
        result = daily_move([holding(), holding(**patch)], "EUR")
        assert result.amount is None and result.percent is None and result.reason
    assert daily_move([], "EUR").amount is None


def test_native_groups_keep_currency_and_gaps_without_guessing_fx():
    rows = [
        holding(fx_base_currency=None),
        holding(currency="EUR", close=None),
        holding(quantity=D(0), currency="GBP"),
    ]
    eur, usd = native_daily_moves(rows)
    assert eur.currency == "EUR" and eur.amount is None and eur.reason == "missing_price"
    assert usd.currency == "USD" and usd.amount == D(20) and usd.percent == D(10)
    assert usd.position_count == 1
