from datetime import UTC, date, datetime
from decimal import Decimal as D

import pytest

from preza.domain.history import capture_payload
from preza.domain.market import BarIn


def prices(before="80", after="120"):
    return [
        BarIn(day=day, open=D(value), high=D(value), low=D(value), close=D(value))
        for day, value in [(date(2025, 12, 31), before), (date(2026, 10, 30), after)]
    ]


def test_capture_requires_one_split_only_basis_and_excludes_unfinished_today():
    now = datetime(2026, 11, 2, 12, tzinfo=UTC)
    payload = capture_payload(
        [*prices(), BarIn(day=date(2026, 11, 2), open=1, high=1, low=1, close=1)], 2026, now
    )
    assert payload.first_day == date(2025, 12, 31) and payload.last_day == date(2026, 10, 30)
    assert payload.bars[-1]["close"] == "120"
    assert payload.content_hash == capture_payload(prices(), 2026, now).content_hash
    assert payload.content_hash != capture_payload(prices(after="121"), 2026, now).content_hash


def test_capture_rejects_missing_baseline_and_duplicate_or_invalid_prices():
    now = datetime(2026, 11, 2, 12, tzinfo=UTC)
    for make in [
        lambda: prices()[1:],
        lambda: prices() + prices(),
        lambda: prices(before="NaN"),
        lambda: prices(after="0"),
    ]:
        with pytest.raises(ValueError):
            capture_payload(make(), 2026, now)
