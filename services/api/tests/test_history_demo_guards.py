import pytest
from sqlalchemy import func, select

from preza.cli.seed_ytd_demo import seed
from preza.db import get_sessionmaker
from preza.models import PriceHistoryCapture


async def test_history_demo_requires_explicit_opt_in(monkeypatch):
    monkeypatch.delenv("PREZA_DEMO_DB", raising=False)
    with pytest.raises(RuntimeError, match="opt_in"):
        await seed()


@pytest.mark.db
async def test_history_demo_refuses_private_portfolio_without_any_insert(api, monkeypatch):
    from tests.test_api_m1 import store_fixture_statement

    await store_fixture_statement()
    monkeypatch.setenv("PREZA_DEMO_DB", "1")
    with pytest.raises(RuntimeError, match="non_demo_positions"):
        await seed()
    async with get_sessionmaker()() as session:
        assert await session.scalar(select(func.count()).select_from(PriceHistoryCapture)) == 0


@pytest.mark.db
async def test_history_demo_is_a_valid_noop_before_the_first_completed_session(api, monkeypatch):
    from datetime import UTC, date, datetime
    from decimal import Decimal

    from preza.cli import seed_ytd_demo
    from preza.models import Bar, Instrument, Position

    class January(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2027, 1, 1, 12, tzinfo=UTC)

    monkeypatch.setenv("PREZA_DEMO_DB", "1")
    monkeypatch.setattr(seed_ytd_demo, "datetime", January)
    async with get_sessionmaker()() as session:
        instrument = Instrument(
            symbol="DEMOYEAR", exchange="NYSE", currency="USD", kind="stock", source="demo"
        )
        session.add(instrument)
        await session.flush()
        session.add(
            Position(
                instrument_id=instrument.id,
                account_id="DEMO",
                report_date=date(2026, 12, 31),
                quantity=Decimal(1),
                currency="USD",
                source="demo",
            )
        )
        session.add(
            Bar(
                instrument_id=instrument.id,
                interval="1d",
                day=date(2026, 12, 31),
                open=Decimal(80),
                high=Decimal(80),
                low=Decimal(80),
                close=Decimal(80),
                source="demo",
            )
        )
        await session.commit()
    assert await seed() == 0
    async with get_sessionmaker()() as session:
        assert await session.scalar(select(func.count()).select_from(PriceHistoryCapture)) == 0
