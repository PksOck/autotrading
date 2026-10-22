from datetime import UTC, datetime, timedelta

import httpx
import pytest
from pydantic import BaseModel
from sqlalchemy import select

from preza.llm.client import LlmResult
from preza.models import Proposal, Signal, WatchlistItem
from tests.conftest import FakeRouter
from tests.test_radar_pipeline import FakeLlm, FakeSource, news, run, seed_portfolio

pytestmark = pytest.mark.db


async def test_radar_views_split_portfolio_watchlist_discover(
    api: tuple[httpx.AsyncClient, FakeRouter],
) -> None:
    client, _ = api
    await seed_portfolio()  # holds MSFT and VWRA
    await client.post("/watchlist", json={"symbol": "ORCL"})
    items = [
        news("Microsoft raises cloud guidance", "https://a.test/1", 30),
        news("Oracle insiders buy shares", "https://a.test/2", 20, symbols=["ORCL"]),
        news("Unknown Bio wins approval", "https://a.test/3", 10, symbols=["UNKB"]),
    ]
    await run([FakeSource("test", items)], FakeLlm(), threshold=0.2)

    def symbols(events: list[dict]) -> set[str]:  # type: ignore[type-arg]
        return {s for e in events for s in e["symbols"]}

    portfolio = (await client.get("/radar/events", params={"view": "portfolio"})).json()
    watch = (await client.get("/radar/events", params={"view": "watchlist"})).json()
    discover = (await client.get("/radar/events", params={"view": "discover"})).json()
    assert "MSFT" in symbols(portfolio)
    assert symbols(watch) == {"ORCL"}
    assert "UNKB" in symbols(discover) and "MSFT" not in symbols(discover)
    assert portfolio[0]["sources"][0]["url"] == "https://a.test/1"


async def test_signal_status_and_rumor_guard(api: tuple[httpx.AsyncClient, FakeRouter]) -> None:
    client, _ = api
    await seed_portfolio()
    await run(
        [
            FakeSource(
                "r", [news("Reddit rumor about Microsoft", "https://r.test/1", 5, kind="social")]
            )
        ],
        FakeLlm(),
        0.2,
    )
    signals = (await client.get("/signals")).json()
    assert len(signals) == 1 and signals[0]["is_rumor"] and signals[0]["status"] == "watching"
    sid = signals[0]["id"]
    refused = await client.patch(f"/signals/{sid}", json={"status": "accepted"})
    assert refused.status_code == 409 and refused.json()["detail"] == "rumor_cannot_be_accepted"
    dismissed = await client.patch(
        f"/signals/{sid}", json={"status": "dismissed", "reason": "noise"}
    )
    assert dismissed.json()["status"] == "dismissed"
    assert (await client.get("/signals", params={"status": "watching"})).json() == []


class VerdictLlm(FakeLlm):
    def __init__(self) -> None:
        super().__init__()
        self.last_user = ""
        self.roles: list[str] = []

    async def complete_json(self, role, system, user, schema: type[BaseModel]):  # type: ignore[no-untyped-def]
        self.last_user, self.roles = user, [*self.roles, role]
        value = schema.model_validate(
            {
                "verdict": "partly",
                "summary": "Padec je sektorski, vrednotenje je pod mediano.",
                "key_points": ["sector drawdown"],
                "risks": ["cloud growth slowdown"],
                "direction": "up",
                "horizon": "months",
                "strength": 0.55,
            }
        )
        return LlmResult(value=value, model="fake-reason", prompt_tokens=1, completion_tokens=1)


async def test_proposal_analysis_creates_manual_signal_and_watchlist_entry(
    api: tuple[httpx.AsyncClient, FakeRouter],
) -> None:
    from preza.db import get_sessionmaker
    from preza.proposals.analyze import analyze_proposal

    client, _router = api
    await seed_portfolio()
    llm = VerdictLlm()
    async with get_sessionmaker()() as session:
        proposal = Proposal(
            symbols=["ORCL"],
            hypothesis="Padec po poročilu je pretiran.",
            depth="quick",
            save_to="reserve",
        )
        session.add(proposal)
        await session.flush()
        signal = await analyze_proposal(session, proposal, llm, None)  # type: ignore[arg-type]
        await session.commit()
        assert signal is not None and signal.source == "manual" and signal.status == "new"
        assert proposal.status == "done" and llm.roles == ["local-reason"]
        assert "Padec po poro" in llm.last_user  # hypothesis passed as data
        item = await session.scalar(select(WatchlistItem))
        assert item is not None and item.tier == "reserve" and item.source == "proposal"

    listed = (await client.get("/proposals")).json()
    assert listed[0]["status"] == "done" and listed[0]["verdict"].startswith("Padec")
    assert listed[0]["signal_id"] == str(signal.id)
    assert datetime.now(UTC) - timedelta(minutes=5) < datetime.fromisoformat(
        listed[0]["created_at"]
    )
    assert Signal  # imported for type context


async def test_proposal_is_accepted_even_when_the_queue_is_down(
    api: tuple[httpx.AsyncClient, FakeRouter], monkeypatch: pytest.MonkeyPatch
) -> None:
    import time

    from preza.config import get_settings

    client, _ = api
    monkeypatch.setenv("REDIS_URL", "redis://127.0.0.1:9/0")  # nothing listens here
    get_settings.cache_clear()
    started = time.monotonic()
    response = await client.post("/proposals", json={"symbols": ["nvda"], "hypothesis": "test"})
    assert response.status_code == 202
    assert response.json()["status"] == "queued" and response.json()["symbols"] == ["NVDA"]
    assert time.monotonic() - started < 5, "a missing queue must not stall the request"
    sync = await client.post("/portfolio/sync")
    assert sync.status_code in (409, 503)
    get_settings.cache_clear()
