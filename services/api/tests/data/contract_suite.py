"""Shared checks every BarsProvider must pass (DESIGN: provider contract, BL-020)."""

from datetime import date

from preza.data.contract import BarsProvider, InstrumentRef, normalize_bars


async def assert_provider_contract(provider: BarsProvider, ref: InstrumentRef, start: date) -> None:
    assert provider.name and provider.name.islower()
    bars = normalize_bars(await provider.daily_bars(ref, start), start)
    assert bars, "provider returned no usable bars"
    days = [b.day for b in bars]
    assert days == sorted(days) and len(set(days)) == len(days)
    for bar in bars:
        assert bar.low <= min(bar.open, bar.close) <= max(bar.open, bar.close) <= bar.high
        assert bar.volume is None or bar.volume >= 0
