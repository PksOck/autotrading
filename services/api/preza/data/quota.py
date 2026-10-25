"""Sliding-window call quota per provider (port of legacy quota-tracker, BL-021)."""

import time
from collections import deque
from collections.abc import Callable


class Quota:
    def __init__(
        self, max_calls: int, per_seconds: float, clock: Callable[[], float] = time.monotonic
    ):
        self.max_calls = max_calls
        self.per_seconds = per_seconds
        self._clock = clock
        self._calls: deque[float] = deque()

    def _trim(self) -> None:
        cutoff = self._clock() - self.per_seconds
        while self._calls and self._calls[0] <= cutoff:
            self._calls.popleft()

    @property
    def remaining(self) -> int:
        self._trim()
        return max(0, self.max_calls - len(self._calls))

    def try_acquire(self) -> bool:
        self._trim()
        if len(self._calls) >= self.max_calls:
            return False
        self._calls.append(self._clock())
        return True
