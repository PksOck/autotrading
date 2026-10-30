from typing import Any

import pytest
from sqlalchemy import func, select

from preza.cli.seed_demo_theses import seed_theses
from preza.db import get_sessionmaker
from preza.models import Instrument, ThesisClaimEvent, ThesisRevision


@pytest.mark.db
async def test_demo_theses_are_guarded_idempotent_and_cover_states(
    api: Any, monkeypatch: Any
) -> None:
    monkeypatch.delenv("PREZA_DEMO_DB", raising=False)
    with pytest.raises(RuntimeError, match="demo_only"):
        await seed_theses()
    monkeypatch.setenv("PREZA_DEMO_DB", "1")
    async with get_sessionmaker()() as session:
        for symbol in ("MSFT", "ORCL", "COST"):
            session.add(
                Instrument(symbol=symbol, name=symbol, kind="stock", currency="USD", source="demo")
            )
        await session.commit()
    await seed_theses()
    await seed_theses()
    async with get_sessionmaker()() as session:
        statuses = list(await session.scalars(select(ThesisRevision.status)))
        assert sorted(statuses) == ["active", "active", "draft"]
        assert await session.scalar(select(func.count()).select_from(ThesisClaimEvent)) == 1
    response = await api[0].get("/theses")
    assert response.status_code == 200
    assert len(response.json()) == 3
