"""Validate one coherent daily capture, never stitch incremental price versions."""

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from preza.domain.market import BarIn

IBKR_SPLIT_BASIS = "ibkr-trades-split-only-v1"
DEMO_SPLIT_BASIS = "demo-split-only-v1"


@dataclass(frozen=True)
class CapturePayload:
    bars: list[dict[str, str]]
    first_day: date
    last_day: date
    content_hash: str


def capture_payload(bars: list[BarIn], year: int, now: datetime) -> CapturePayload:
    if now.tzinfo is None:
        raise ValueError("capture_requires_utc_time")
    now = now.astimezone(UTC)
    if year != now.year or len(bars) > 800:
        raise ValueError("invalid_capture_scope")
    start = date(year, 1, 1)
    closed = [b for b in bars if start - timedelta(days=7) <= b.day < now.date()]
    if len({b.day for b in closed}) != len(closed):
        raise ValueError("duplicate_capture_day")
    for bar in closed:
        values = (bar.open, bar.high, bar.low, bar.close)
        if any(not value.is_finite() or value <= 0 for value in values):
            raise ValueError("invalid_capture_price")
        if not bar.low <= min(bar.open, bar.close) <= max(bar.open, bar.close) <= bar.high:
            raise ValueError("invalid_capture_ohlc")
    closed.sort(key=lambda b: b.day)
    before = [b for b in closed if b.day < start]
    current = [b for b in closed if b.day >= start]
    if not before or not current:
        raise ValueError("missing_capture_endpoint")
    payload = [{"day": b.day.isoformat(), "close": str(b.close)} for b in closed]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return CapturePayload(
        payload, before[-1].day, current[-1].day, hashlib.sha256(encoded).hexdigest()
    )
