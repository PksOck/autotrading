from datetime import date, timedelta
from decimal import Decimal

import pytest

from preza.db import get_sessionmaker
from preza.models import Bar, Instrument
from preza.services.market_context import market_context


@pytest.mark.db
async def test_price_trend_has_bounded_chronological_dates_and_daily_change(api) -> None:
    async with get_sessionmaker()() as session:
        instrument = Instrument(symbol="TREND", kind="stock", currency="USD", source="test")
        session.add(instrument)
        await session.flush()
        for offset in range(35):
            session.add(
                Bar(
                    instrument_id=instrument.id,
                    interval="1d",
                    day=date(2026, 1, 1) + timedelta(days=offset),
                    open=Decimal(100 + offset),
                    high=Decimal(101 + offset),
                    low=Decimal(99 + offset),
                    close=Decimal(100 + offset),
                    volume=100,
                    source="test",
                )
            )
        await session.flush()
        context = (await market_context(session, [instrument.id]))[instrument.id]
        trend = context["price_trend"]
        assert len(trend.points) == 30
        assert trend.points[0].market_date == date(2026, 1, 6)
        assert trend.points[-1].market_date == date(2026, 2, 4)
        assert context["change_pct"] == (Decimal(134) / Decimal(133) - 1) * 100
