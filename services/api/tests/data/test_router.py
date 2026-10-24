from datetime import date
from decimal import Decimal

import pytest

from preza.data.contract import InstrumentRef, NotFoundError, ProviderUnavailableError
from preza.data.quota import Quota
from preza.data.router import AllProvidersFailedError, BarsRouter, Route
from preza.domain.market import BarIn

REF = InstrumentRef("MSFT")
BAR = BarIn(day=date(2026, 10, 22), open=Decimal(1), high=Decimal(2), low=Decimal("0.5"), close=Decimal("1.5"))


class Fake:
    def __init__(self, name: str, result: list[BarIn] | Exception):
        self.name = name
        self.result = result
        self.calls = 0

    async def daily_bars(self, ref: InstrumentRef, start: date) -> list[BarIn]:
        self.calls += 1
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def test_quota_sliding_window() -> None:
    now = [0.0]
    quota = Quota(2, 10, clock=lambda: now[0])
    assert quota.try_acquire() and quota.try_acquire()
    assert not quota.try_acquire()
    now[0] = 10.5
    assert quota.remaining == 2


async def test_router_falls_back_in_order() -> None:
    first = Fake("ibkr", ProviderUnavailableError("gateway down"))
    second = Fake("yahoo", NotFoundError("x"))
    third = Fake("stooq", [BAR])
    router = BarsRouter([Route(p, Quota(10, 60)) for p in (first, second, third)])
    routed = await router.daily_bars(REF, date(2026, 1, 1))
    assert routed.provider == "stooq" and routed.bars == [BAR]


async def test_router_skips_exhausted_quota_without_calling() -> None:
    limited = Fake("ibkr", [BAR])
    spent = Quota(1, 60)
    spent.try_acquire()
    router = BarsRouter([Route(limited, spent), Route(Fake("yahoo", [BAR]), Quota(5, 60))])
    assert (await router.daily_bars(REF, date(2026, 1, 1))).provider == "yahoo"
    assert limited.calls == 0


async def test_router_reports_every_failure() -> None:
    router = BarsRouter([Route(Fake("ibkr", ProviderUnavailableError("down")), Quota(1, 60)), Route(Fake("yahoo", []), Quota(1, 60))])
    with pytest.raises(AllProvidersFailedError) as info:
        await router.daily_bars(REF, date(2026, 1, 1))
    assert info.value.errors == {"ibkr": "down", "yahoo": "empty"}
