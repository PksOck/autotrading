"""Integration tests run against a real Postgres when TEST_DATABASE_URL is set (CI and local).

The database is reset with Alembic (downgrade base → upgrade head) once per session.
"""

import os
import subprocess
from collections.abc import AsyncIterator
from datetime import date
from pathlib import Path

import httpx
import pytest

from preza.data.contract import InstrumentRef
from preza.domain.market import BarIn

API_ROOT = Path(__file__).parent.parent
TEST_DB = os.environ.get("TEST_DATABASE_URL")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if TEST_DB:
        return
    skip = pytest.mark.skip(reason="TEST_DATABASE_URL not set")
    for item in items:
        if "db" in item.keywords:
            item.add_marker(skip)


@pytest.fixture(scope="session")
def migrated_db() -> str:
    assert TEST_DB
    env = {**os.environ, "DATABASE_URL": TEST_DB}
    for args in (["downgrade", "base"], ["upgrade", "head"]):
        subprocess.run(["alembic", *args], cwd=API_ROOT, env=env, check=True, capture_output=True)
    return TEST_DB


class FakeRouter:
    """Stands in for BarsRouter in API tests; records what was asked."""

    def __init__(self, bars: list[BarIn] | None = None):
        self.bars = bars or []
        self.calls: list[tuple[InstrumentRef, date]] = []

    async def daily_bars(self, ref: InstrumentRef, start: date):  # type: ignore[no-untyped-def]
        from preza.data.contract import NotFoundError
        from preza.data.router import RoutedBars

        self.calls.append((ref, start))
        if not self.bars:
            raise NotFoundError(ref.symbol)
        return RoutedBars(provider="fake", bars=[b for b in self.bars if b.day >= start])


@pytest.fixture
async def api(
    migrated_db: str, monkeypatch: pytest.MonkeyPatch
) -> AsyncIterator[tuple[httpx.AsyncClient, FakeRouter]]:
    from sqlalchemy import text

    from preza import db, deps
    from preza.config import get_settings
    from preza.main import create_app
    from preza.services.bars import BarsService

    monkeypatch.setenv("DATABASE_URL", migrated_db)
    get_settings.cache_clear()
    db.get_engine.cache_clear()
    db.get_sessionmaker.cache_clear()

    async with db.get_engine().begin() as conn:
        await conn.execute(
            text(
                "TRUNCATE watchlist_item, position, trade, cash_balance, bar, sync_run, instrument "
                "RESTART IDENTITY CASCADE"
            )
        )

    router = FakeRouter()
    app = create_app()
    app.dependency_overrides[deps.get_bars_service] = lambda: BarsService(router, 400)  # type: ignore[arg-type]
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client, router
    await db.get_engine().dispose()
