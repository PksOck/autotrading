"""Validated process policies and civil-time scheduling (ADR-0019)."""

from datetime import UTC, datetime, time, timedelta
from typing import Literal, Self
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class PolicyInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    revision: int = Field(default=0, ge=0)
    enabled: bool = False
    timezone: str = "UTC"
    schedule_kind: Literal["legacy", "daily", "interval", "manual"] = "manual"
    local_time: str = "06:00"
    interval_minutes: int = Field(default=60, ge=5, le=10080)
    weekdays: list[int] = Field(default_factory=lambda: list(range(7)))
    window_start: str | None = None
    window_end: str | None = None
    cap: int = Field(default=5, ge=1, le=100)
    scope: Literal["portfolio", "watchlist", "both"] = "portfolio"

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError("unknown_timezone") from exc
        return value

    @field_validator("local_time", "window_start", "window_end")
    @classmethod
    def valid_time(cls, value: str | None) -> str | None:
        if value is not None:
            parsed = time.fromisoformat(value)
            if parsed.second or parsed.microsecond or parsed.tzinfo or len(value) != 5:
                raise ValueError("use_HH_MM")
        return value

    @field_validator("weekdays")
    @classmethod
    def valid_days(cls, value: list[int]) -> list[int]:
        if not value or any(day not in range(7) for day in value):
            raise ValueError("invalid_weekdays")
        return sorted(set(value))

    @model_validator(mode="after")
    def paired_window(self) -> Self:
        if (self.window_start is None) != (self.window_end is None):
            raise ValueError("both_window_bounds_required")
        if self.window_start is not None and self.window_start == self.window_end:
            raise ValueError("empty_window")
        return self


class PolicyOut(PolicyInput):
    process_key: str
    next_runs: list[datetime] = Field(default_factory=list)


class ControlInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    revision: int = Field(ge=0)
    paused: bool


class BatchInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scope: Literal["portfolio", "watchlist", "both"] = "portfolio"
    cap: int = Field(default=5, ge=1, le=100)
    account_id: str | None = Field(default=None, max_length=32)
    revision: int | None = Field(default=None, ge=0)
    outside_window: bool = False


class BatchItem(BaseModel):
    instrument_id: int
    symbol: str
    reason: Literal["ready", "active", "cap", "quota", "disabled", "outside_window"]


class BatchPreview(BaseModel):
    items: list[BatchItem]
    quota_used: int
    quota_limit: int
    resets_at: datetime
    run_ids: list[str] = Field(default_factory=list)
    policy_revision: int = 0
    blocked_reason: str | None = None


class RunInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    revision: int = Field(ge=0)
    outside_window: bool = False


def in_window(policy: PolicyInput, now: datetime) -> bool:
    local = now.astimezone(ZoneInfo(policy.timezone))
    clock = local.time().replace(tzinfo=None)
    day = local.weekday()
    if policy.window_start is None or policy.window_end is None:
        return day in policy.weekdays
    start, end = time.fromisoformat(policy.window_start), time.fromisoformat(policy.window_end)
    if start < end:
        return day in policy.weekdays and start <= clock < end
    if clock < end:
        return (day - 1) % 7 in policy.weekdays
    return day in policy.weekdays and clock >= start


def next_slots(policy: PolicyInput, after: datetime, count: int = 5) -> list[datetime]:
    """Daily fold=0; skip missing civil times. Intervals are anchored in UTC."""
    if policy.schedule_kind in {"legacy", "manual"}:
        return []
    after = after.astimezone(UTC)
    if policy.schedule_kind == "interval":
        seconds = policy.interval_minutes * 60
        cursor = datetime.fromtimestamp((int(after.timestamp()) // seconds + 1) * seconds, UTC)
        result = []
        for _ in range(9 * 24 * 60 // policy.interval_minutes + 1):
            if in_window(policy, cursor):
                result.append(cursor)
                if len(result) == count:
                    break
            cursor += timedelta(seconds=seconds)
        return result
    zone = ZoneInfo(policy.timezone)
    day = after.astimezone(zone).date()
    result = []
    for offset in range(370):
        naive = datetime.combine(
            day + timedelta(days=offset), time.fromisoformat(policy.local_time)
        )
        local = naive.replace(tzinfo=zone, fold=0)
        utc = local.astimezone(UTC)
        if utc.astimezone(zone).replace(tzinfo=None) != naive:
            continue
        if utc > after and in_window(policy, utc):
            result.append(utc)
            if len(result) == count:
                break
    return result


class ExecutionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    process_key: str
    policy_revision: int
    scheduled_for: datetime
    origin: str
    outside_window: bool
    state: str
    reason: str | None
    started_at: datetime | None
    finished_at: datetime | None
    heartbeat_at: datetime | None
    counts: dict[str, int | str]
