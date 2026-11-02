from datetime import UTC, date, datetime, timedelta
from decimal import Decimal as D

import pytest
from sqlalchemy import func, select, update
from sqlalchemy.exc import DBAPIError

from preza.data.contract import SplitHistory
from preza.db import get_sessionmaker
from preza.domain.history import IBKR_SPLIT_BASIS
from preza.domain.market import BarIn
from preza.models import Instrument, PriceHistoryCapture
from preza.services.price_history import latest_captures, store_capture

pytestmark = pytest.mark.db
NOW = datetime(2026, 11, 2, 12, tzinfo=UTC)


@pytest.fixture(autouse=True)
def fixed_capture_clock(monkeypatch):
    from preza.services import bars, price_history

    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return NOW

    monkeypatch.setattr(price_history, "datetime", Clock)
    monkeypatch.setattr(bars, "datetime", Clock)


def history(before="80", after="120"):
    year = NOW.year
    last = NOW.date() - timedelta(days=3)
    return SplitHistory(
        [
            BarIn(day=day, open=D(p), high=D(p), low=D(p), close=D(p))
            for day, p in [(date(year - 1, 12, 31), before), (last, after)]
        ],
        "USD",
        272093,
        IBKR_SPLIT_BASIS,
    )


async def test_capture_archives_two_coherent_versions_and_deduplicates_retries(api):
    async with get_sessionmaker()() as session:
        instrument = Instrument(
            symbol="CAPTURE",
            exchange="NASDAQ",
            currency="USD",
            kind="stock",
            ib_con_id=272093,
            source="fixture",
        )
        session.add(instrument)
        await session.flush()
        first = await store_capture(session, instrument, "ibkr", history())
        again = await store_capture(session, instrument, "ibkr", history())
        newer = await store_capture(session, instrument, "ibkr", history(before="40", after="60"))
        assert first.id == again.id and first.id != newer.id
        assert first.bars[0]["close"] == "80" and newer.bars[0]["close"] == "40"
        assert await session.scalar(select(func.count()).select_from(PriceHistoryCapture)) == 2
        restored = await store_capture(session, instrument, "ibkr", history())
        assert restored.id != first.id
        assert (await latest_captures(session, [instrument.id], NOW.year))[
            instrument.id
        ].id == restored.id
        assert await session.scalar(select(func.count()).select_from(PriceHistoryCapture)) == 3
        with pytest.raises(DBAPIError):
            async with session.begin_nested():
                await session.execute(
                    update(PriceHistoryCapture)
                    .where(PriceHistoryCapture.id == first.id)
                    .values(source="changed")
                )
        for bad in [
            SplitHistory(history().bars, "EUR", 272093, IBKR_SPLIT_BASIS),
            SplitHistory(history().bars, "USD", 272093, "unknown"),
        ]:
            with pytest.raises(ValueError):
                await store_capture(session, instrument, "ibkr", bad)
        with pytest.raises(ValueError):
            await store_capture(session, instrument, "yahoo", history())
        instrument.ib_con_id = None
        with pytest.raises(ValueError, match="history_identity_mismatch"):
            await store_capture(session, instrument, "ibkr", history())


async def test_portfolio_ytd_reads_one_capture_even_when_the_incremental_cache_differs(api):
    from dataclasses import replace

    from preza.models import Bar
    from tests.test_api_m1 import store_fixture_statement

    client, router = api
    await store_fixture_statement()
    async with get_sessionmaker()() as session:
        for instrument in await session.scalars(select(Instrument)):
            if not instrument.exchange:
                continue
            await store_capture(
                session, instrument, "ibkr", replace(history(), con_id=instrument.ib_con_id)
            )
            p = D(999)
            session.add(
                Bar(
                    instrument_id=instrument.id,
                    interval="1d",
                    day=NOW.date() - timedelta(days=3),
                    open=p,
                    high=p,
                    low=p,
                    close=p,
                    source="yahoo",
                )
            )
        await session.commit()
    response = await client.get("/portfolio")
    assert response.status_code == 200
    body = response.json()
    native = body["ytd_native"][0]
    assert native["amount"] == 8200 and native["percent"] == 50
    assert native["sources"] == ["ibkr"] and len(native["capture_ids"]) == 2
    assert native["adjustment_bases"] == [IBKR_SPLIT_BASIS]
    assert body["ytd_move"]["amount"] is None  # no invented EUR conversion
    assert router.calls == []


async def test_ytd_refresh_still_runs_with_fresh_bars_and_preserves_capture_on_failure(api):
    from preza.data.contract import ProviderUnavailableError
    from preza.services.bars import BarsService

    class Router:
        def __init__(self):
            self.calls = 0
            self.fail = False

        async def split_history(self, ref, start):
            self.calls += 1
            if self.fail:
                raise ProviderUnavailableError("offline")
            return "ibkr", history()

    router = Router()
    service = BarsService(router)  # type: ignore[arg-type]
    async with get_sessionmaker()() as session:
        instrument = Instrument(
            symbol="REFRESH",
            exchange="NASDAQ",
            currency="USD",
            kind="stock",
            ib_con_id=272093,
            source="fixture",
        )
        session.add(instrument)
        await session.flush()
        assert await service.refresh_year_history(session, instrument)
        assert await service.refresh_year_history(session, instrument)
        assert router.calls == 1
        router.fail = True
        # A changed identity cannot reuse the old proof; failure must not delete it.
        instrument.name = "Updated name"
        instrument.exchange = "NYSE"
        assert not await service.refresh_year_history(session, instrument)
        assert await session.scalar(select(func.count()).select_from(PriceHistoryCapture)) == 1
