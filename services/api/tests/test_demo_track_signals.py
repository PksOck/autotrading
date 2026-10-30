"""Historical synthetic signals must remain valid signal-detail examples."""

import uuid
from typing import Any

import pytest

from preza.cli.seed_demo import DEMO_TRACK, DEMO_TRACK_NS, seed_track_record
from preza.db import get_sessionmaker
from preza.domain.radar import SignalOut
from preza.models import Instrument


@pytest.mark.db
async def test_every_historical_demo_signal_can_be_opened(api: Any) -> None:
    async with get_sessionmaker()() as session:
        for symbol in sorted({row[0] for row in DEMO_TRACK}):
            session.add(Instrument(symbol=symbol, kind="stock", currency="USD", source="demo"))
        await session.commit()
    await seed_track_record()
    for index in range(len(DEMO_TRACK)):
        signal_id = uuid.uuid5(DEMO_TRACK_NS, str(index))
        response = await api[0].get(f"/signals/{signal_id}")
        assert response.status_code == 200
        result = SignalOut.model_validate(response.json())
        assert result.id == signal_id
        assert result.evidence[0].kind == "indicator"
        assert result.evidence[0].label == "demo"
