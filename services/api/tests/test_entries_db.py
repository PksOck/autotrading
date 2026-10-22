import math
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import httpx
import pytest
from pydantic import BaseModel
from sqlalchemy import select

from preza.entries.dip import DipCause, DipVerdict
from preza.llm.client import LlmResult, LlmUnavailableError
from preza.models import Bar, EntryCandidate, Instrument, Position, Signal, WatchlistItem
from tests.conftest import FakeRouter

pytestmark = pytest.mark.db


class FakeDip:
    def __init__(self, cause: DipCause, fail_local: bool = False) -> None:
        self.cause = cause
        self.fail_local = fail_local
        self.roles: list[str] = []

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return []

    async def complete_json(self, role, system, user, schema: type[BaseModel]):  # type: ignore[no-untyped-def]
        self.roles.append(role)
        if self.fail_local and role == "local-reason":
            raise LlmUnavailableError("local down")
        verdict = DipVerdict(
            cause=self.cause,
            thesis_intact=self.cause != DipCause.FUNDAMENTAL,
            confidence=0.7,
            rationale="Padec sledi trgu.",
            evidence=[999],  # unknown id: must be dropped
        )
        return LlmResult(value=verdict, model=f"fake-{role}", prompt_tokens=1, completion_tokens=1)


def dip_closes(days: int = 300) -> list[float]:
    base = [100 + 0.2 * i + 2 * math.sin(i / 5) for i in range(days - 10)]
    return base + [base[-1] - 8 * (i + 1) / 10 for i in range(10)]


async def seed(symbol: str, held: bool) -> int:
    from preza.db import get_sessionmaker

    async with get_sessionmaker()() as session:
        inst = Instrument(symbol=symbol, exchange="X", kind="stock", currency="USD", source="test")
        session.add(inst)
        await session.flush()
        start = date.today() - timedelta(days=300)
        for i, c in enumerate(dip_closes()):
            d = Decimal(str(round(c, 4)))
            session.add(
                Bar(
                    instrument_id=inst.id,
                    day=start + timedelta(days=i),
                    open=d,
                    high=d + 1,
                    low=d - 1,
                    close=d,
                    source="test",
                )
            )
        if held:
            session.add(
                Position(
                    account_id="U1",
                    instrument_id=inst.id,
                    report_date=date.today(),
                    quantity=Decimal(10),
                    currency="USD",
                    source="test",
                )
            )
        else:
            session.add(WatchlistItem(instrument_id=inst.id))
        await session.commit()
        return inst.id


async def rebuild(llm: FakeDip | None):  # type: ignore[no-untyped-def]
    from preza.db import get_sessionmaker
    from preza.entries.service import rebuild_entries

    async with get_sessionmaker()() as session:
        run = await rebuild_entries(session, llm, "sl")  # type: ignore[arg-type]
        await session.commit()
    return run


async def test_transient_dip_becomes_entry_signal(
    api: tuple[httpx.AsyncClient, FakeRouter],
) -> None:
    from preza.db import get_sessionmaker

    client, _ = api
    await seed("ACME", held=False)
    llm = FakeDip(DipCause.MARKET, fail_local=True)
    run = await rebuild(llm)
    assert run.evaluated == 1 and run.active == 1 and run.analyzed == 1 and run.signals == 1
    assert llm.roles == ["local-reason", "cloud-quick"]  # fallback when the local model is down

    async with get_sessionmaker()() as session:
        cand = (await session.scalars(select(EntryCandidate))).one()
        signal = (await session.scalars(select(Signal))).one()
    assert cand.cause == "market" and cand.thesis_intact is True
    assert cand.dip_evidence == []
    assert cand.state == "in_zone" and cand.ladder
    assert signal.kind == "entry" and signal.source == "rule"
    assert signal.entry_low == cand.zone_low and signal.stop == cand.stop
    assert cand.signal_id == signal.id

    # Second run on the same data: no new analysis (recent), no duplicate signal.
    run = await rebuild(llm)
    assert run.analyzed == 0 and run.signals == 0

    body = (await client.get("/entries", params={"view": "watchlist"})).json()
    assert [e["symbol"] for e in body] == ["ACME"]
    assert body[0]["rules"] and body[0]["ladder"][0]["weight"] == 0.4
    assert (await client.get("/entries", params={"view": "portfolio"})).json() == []
    assert (await client.get("/entries/acme")).json()["cause"] == "market"


async def test_dismissed_signal_is_not_recreated(
    api: tuple[httpx.AsyncClient, FakeRouter],
) -> None:
    from preza.db import get_sessionmaker

    await seed("ACME", held=False)
    await rebuild(FakeDip(DipCause.TRANSIENT))
    async with get_sessionmaker()() as session:
        signal = (await session.scalars(select(Signal))).one()
        signal.status = "dismissed"
        cand = (await session.scalars(select(EntryCandidate))).one()
        cand.analyzed_at = datetime.now(UTC) - timedelta(days=5)
        await session.commit()
    run = await rebuild(FakeDip(DipCause.TRANSIENT))
    assert run.analyzed == 1 and run.signals == 0


async def test_fundamental_cause_on_holding_is_thesis_break(
    api: tuple[httpx.AsyncClient, FakeRouter],
) -> None:
    from preza.db import get_sessionmaker

    await seed("BRKN", held=True)
    await rebuild(FakeDip(DipCause.FUNDAMENTAL))
    async with get_sessionmaker()() as session:
        signal = (await session.scalars(select(Signal))).one()
    assert signal.kind == "thesis_break" and signal.direction == "down" and signal.stop is None


async def test_without_llm_candidates_but_no_signals(
    api: tuple[httpx.AsyncClient, FakeRouter],
) -> None:
    await seed("ACME", held=False)
    run = await rebuild(None)
    assert run.active == 1 and run.signals == 0
