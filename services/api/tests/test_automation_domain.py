from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from preza.domain.automation import PolicyInput, in_window, next_slots


def test_overnight_window_belongs_to_start_weekday():
    policy = PolicyInput(enabled=True, weekdays=[0], window_start="22:00", window_end="02:00")
    assert in_window(policy, datetime(2026, 10, 27, 1, tzinfo=UTC))
    assert not in_window(policy, datetime(2026, 10, 27, 2, tzinfo=UTC))
    assert not in_window(policy, datetime(2026, 10, 28, 1, tzinfo=UTC))


def test_dst_missing_hour_skipped_and_repeated_hour_once():
    policy = PolicyInput(timezone="Europe/Ljubljana", schedule_kind="daily", local_time="02:30")
    spring = next_slots(policy, datetime(2026, 3, 28, 23, tzinfo=UTC), count=1)
    assert spring == [datetime(2026, 3, 30, 0, 30, tzinfo=UTC)]
    autumn = next_slots(policy, datetime(2026, 10, 24, 23, tzinfo=UTC), count=2)
    assert autumn == [
        datetime(2026, 10, 25, 0, 30, tzinfo=UTC),
        datetime(2026, 10, 26, 1, 30, tzinfo=UTC),
    ]


def test_invalid_timezone_and_half_window_rejected():
    with pytest.raises(ValidationError):
        PolicyInput(timezone="invented/zone")
    with pytest.raises(ValidationError):
        PolicyInput(window_start="12:00")


def test_new_schedules_default_disabled():
    assert PolicyInput().enabled is False
