from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import select

from preza import db
from preza.models import Event, Instrument, Signal, SignalOutcome
from preza.radar.signals import upsert_signal

pytestmark = pytest.mark.db


async def _seed_outcomes(hits: int, misses: int, kind: str = "entry", source: str = "rule") -> None:
    async with db.get_sessionmaker()() as s:
        inst = await s.scalar(select(Instrument).where(Instrument.symbol == "AAPL"))
        if inst is None:
            inst = Instrument(symbol="AAPL", exchange="X", kind="stock", source="test")
            s.add(inst)
            await s.flush()
        for i in range(hits + misses):
            signal = Signal(
                instrument_id=inst.id,
                kind=kind,
                source=source,
                direction="up",
                horizon="weeks",
                strength=Decimal("0.5"),
                rationale="test",
                evidence=[],
                status="dismissed",
            )
            s.add(signal)
            await s.flush()
            ret = Decimal(2 if i < hits else -2)
            s.add(
                SignalOutcome(
                    signal_id=signal.id,
                    horizon_days=20,
                    start_day=date(2026, 3, 2),
                    end_day=date(2026, 3, 30),
                    start_price=Decimal(100),
                    end_price=Decimal(100) + ret,
                    return_pct=ret,
                    mfe_pct=Decimal(0),
                    mae_pct=Decimal(0),
                )
            )
        await s.commit()


async def test_weights_change_only_on_explicit_confirmation(api) -> None:  # type: ignore[no-untyped-def]
    client, _ = api
    await _seed_outcomes(4, 26, kind="catalyst", source="radar")
    await _seed_outcomes(28, 2)

    empty = (await client.get("/calibration")).json()
    assert empty == {"tunable": ["catalyst:radar", "entry:rule"], "active": None, "proposal": None}
    assert (await client.post("/calibration/proposals?horizon_days=3")).status_code == 422

    first = (await client.post("/calibration/proposals")).json()
    proposal = (await client.post("/calibration/proposals")).json()
    assert proposal["status"] == "proposed" and proposal["proposal"]["changed"]
    assert proposal["weights"] == {"catalyst:radar": "0.50", "entry:rule": "1.50"}
    state = (await client.get("/calibration")).json()
    assert state["active"] is None and state["proposal"]["id"] == proposal["id"]

    # A newer proposal supersedes the older one, which can no longer be confirmed.
    confirm = {"confirm": True}
    stale = await client.post(f"/calibration/{first['id']}/confirm", json=confirm)
    assert stale.status_code == 409
    # Confirmation must be explicit.
    url = f"/calibration/{proposal['id']}/confirm"
    assert (await client.post(url, json={})).status_code == 422
    assert (await client.post(url, json={"confirm": False})).status_code == 422

    active = (await client.post(url, json=confirm)).json()
    assert active["status"] == "active" and active["decided_at"]
    assert (await client.post(url, json=confirm)).status_code == 409

    # Proposals now start from the active weights: nothing new to change.
    again = (await client.post("/calibration/proposals")).json()
    assert not again["proposal"]["changed"]
    unchanged = await client.post(f"/calibration/{again['id']}/confirm", json=confirm)
    assert unchanged.status_code == 422
    rejected = (await client.post(f"/calibration/{again['id']}/reject")).json()
    assert rejected["status"] == "rejected"
    state = (await client.get("/calibration")).json()
    assert state["active"]["id"] == active["id"] and state["proposal"] is None


async def test_confirmed_weight_scales_radar_signals_before_threshold(api) -> None:  # type: ignore[no-untyped-def]
    client, _ = api
    await _seed_outcomes(4, 26, kind="catalyst", source="radar")
    await _seed_outcomes(28, 2)
    proposal = (await client.post("/calibration/proposals")).json()
    await client.post(f"/calibration/{proposal['id']}/confirm", json={"confirm": True})

    async with db.get_sessionmaker()() as s:
        inst = await s.scalar(select(Instrument).where(Instrument.symbol == "AAPL"))
        assert inst is not None
        now = datetime.now(UTC)
        strong, weak = (
            Event(
                title=title,
                symbols=["AAPL"],
                score=Decimal(score),
                sentiment=Decimal("0.5"),
                materiality=Decimal("0.8"),
                is_rumor=False,
                first_seen_at=now,
                last_seen_at=now,
            )
            for title, score in (("strong", "0.9"), ("weak", "0.5"))
        )
        s.add_all([strong, weak])
        await s.flush()
        for event in (strong, weak):
            await s.refresh(event, ["items"])
        signal = await upsert_signal(s, strong, inst.id, threshold=0.4)
        assert signal is not None and signal.strength == Decimal("0.4500")
        # 0.5 * 0.5 = 0.25 falls below the threshold once weighted.
        assert await upsert_signal(s, weak, inst.id, threshold=0.4) is None
        assert weak.status == "below_threshold"
