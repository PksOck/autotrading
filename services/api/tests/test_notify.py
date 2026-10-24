import json
import logging
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import httpx
import pytest
from sqlalchemy import func, select

from preza.cli.telegram_bot import configure_logging, handle_update, parse_predlog
from preza.config import Settings
from preza.models import EntryCandidate, Instrument, Proposal, Signal
from preza.notify.models import Notification
from preza.notify.service import handle_callback, morning_digest, notify_new_signals
from preza.notify.telegram import (
    Decision,
    NotificationPolicy,
    TelegramClient,
    TelegramError,
    format_signal,
    signal_buttons,
)
from tests.conftest import FakeRouter

TOKEN = "123456:SECRET-TOKEN"
NOON = datetime(2026, 10, 22, 10, 0, tzinfo=UTC)  # 12:00 Ljubljana (CEST)
NIGHT = datetime(2026, 10, 22, 21, 30, tzinfo=UTC)  # 23:30 Ljubljana


# ---------- formatting ----------


def test_format_signal_sl_uses_decimal_comma_and_stays_short() -> None:
    text = format_signal(
        "MSFT", "catalyst", "Padec sledi sektorju.", 0.72, False, "http://x/s", "sl"
    )
    lines = text.split("\n")
    assert lines[0] == "MSFT · Katalizator"
    assert "Moč 0,72" in lines[1] and "0.72" not in text
    assert lines[2] == "Odpri: http://x/s"
    assert len(lines) <= 4 and "!" not in text


def test_format_signal_en_and_rumor_prefix() -> None:
    en = format_signal("XYZ", "catalyst", "Buzz.", 0.8, True, "http://x", "en")
    assert en.startswith("Unconfirmed. XYZ") and "Strength 0.80" in en
    sl = format_signal("XYZ", "catalyst", "Šum.", 0.8, True, "http://x", "sl")
    assert sl.startswith("Nepotrjeno.")


def test_format_signal_escapes_html_and_strips_exclamations() -> None:
    text = format_signal(
        "A&B", "entry", "<b>Buy</b> now! Big & fast\n\nreally", 0.5, False, "", "sl"
    )
    assert "<b>" not in text and "&lt;b&gt;Buy&lt;/b&gt;" in text and "&amp;" in text
    assert "!" not in text and text.count("\n") == 1  # no url line, rationale collapsed


def test_buttons_labels_and_callbacks() -> None:
    sid = uuid.uuid4()
    sl = signal_buttons(sid, "sl", "http://app/")[0]
    assert [b["text"] for b in sl] == ["Odpri", "Spremljaj", "Zavrzi"]
    assert sl[0]["url"] == f"http://app/signals?peek=signal:{sid}"
    assert sl[1]["callback_data"] == f"w:{sid}" and sl[2]["callback_data"] == f"x:{sid}"
    assert signal_buttons(sid, "en", "http://app")[0][2]["text"] == "Dismiss"


# ---------- policy ----------


def test_policy_quiet_hours_and_daily_cap() -> None:
    policy = NotificationPolicy()
    assert policy.decide("entry", 0.8, False, NOON, 0) is Decision.SEND_NOW
    assert policy.decide("entry", 0.8, False, NIGHT, 0) is Decision.DEFER_TO_DIGEST
    early = datetime(2026, 10, 22, 4, 59, tzinfo=UTC)  # 06:59 local
    assert policy.decide("entry", 0.8, False, early, 0) is Decision.DEFER_TO_DIGEST
    seven = datetime(2026, 10, 22, 5, 0, tzinfo=UTC)  # 07:00 local
    assert policy.decide("entry", 0.8, False, seven, 0) is Decision.SEND_NOW
    assert policy.decide("entry", 0.8, False, NOON, 5) is Decision.DEFER_TO_DIGEST
    assert policy.decide("entry", 0.8, False, NOON, 4) is Decision.SEND_NOW


def test_policy_thesis_break_bypass() -> None:
    policy = NotificationPolicy()
    assert policy.decide("thesis_break", 0.7, True, NOON, 9) is Decision.SEND_NOW
    assert policy.decide("thesis_break", 0.7, True, NIGHT, 0) is Decision.DEFER_TO_DIGEST
    assert policy.decide("thesis_break", 0.9, True, NIGHT, 9) is Decision.SEND_NOW
    # not held: ordinary rules apply
    assert policy.decide("thesis_break", 0.7, False, NOON, 5) is Decision.DEFER_TO_DIGEST


def test_policy_skip_below_minimum() -> None:
    assert (
        NotificationPolicy(min_strength=0.5).decide("entry", 0.4, False, NOON, 0) is Decision.SKIP
    )


def test_local_day_start_is_local_midnight_in_utc() -> None:
    assert NotificationPolicy.local_day_start(NOON) == datetime(2026, 10, 21, 22, 0, tzinfo=UTC)


# ---------- client ----------


async def test_client_sends_expected_request() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"ok": True, "result": {"message_id": 1}})

    client = TelegramClient(TOKEN, httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    buttons = [[{"text": "Odpri", "url": "http://x"}]]
    assert await client.send_message("42", "hi", buttons) == {"message_id": 1}
    body = json.loads(seen[0].content)
    assert seen[0].url.path == f"/bot{TOKEN}/sendMessage"
    assert body["parse_mode"] == "HTML" and body["disable_web_page_preview"] is True
    assert body["reply_markup"] == {"inline_keyboard": buttons}
    await client.send_message("42", "plain")
    assert "reply_markup" not in json.loads(seen[1].content)


async def test_client_updates_and_callback_answer() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        result: Any = [{"update_id": 7}] if request.url.path.endswith("getUpdates") else True
        return httpx.Response(200, json={"ok": True, "result": result})

    client = TelegramClient(TOKEN, httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    assert await client.get_updates(5, timeout=1) == [{"update_id": 7}]
    assert json.loads(seen[0].content)["offset"] == 5
    await client.answer_callback("cb1", "ok")
    assert json.loads(seen[1].content) == {"callback_query_id": "cb1", "text": "ok"}


async def test_client_errors_never_contain_token() -> None:
    def api_error(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"ok": False, "description": "Unauthorized"})

    def network_error(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError(f"cannot reach {request.url}")

    for handler in (api_error, network_error):
        client = TelegramClient(TOKEN, httpx.AsyncClient(transport=httpx.MockTransport(handler)))
        with pytest.raises(TelegramError) as info:
            await client.send_message("42", "hi")
        assert TOKEN not in str(info.value) and "SECRET" not in repr(info.value)


def test_parse_predlog() -> None:
    assert parse_predlog("/predlog NVDA AMD cloud demand grows") == (
        ["AMD", "NVDA"],
        "cloud demand grows",
    )
    assert parse_predlog("/predlog $msft, maybe") == ([], "$msft, maybe")
    assert parse_predlog("/predlog") == ([], "")


# ---------- DB ----------

CHAT = "4242"


class Outbox:
    """Telegram client over a mock transport that records sent texts."""

    def __init__(self) -> None:
        self.requests: list[dict[str, Any]] = []

        def handler(request: httpx.Request) -> httpx.Response:
            self.requests.append(
                {"method": request.url.path.rsplit("/", 1)[1], **json.loads(request.content)}
            )
            return httpx.Response(200, json={"ok": True, "result": {}})

        self.client = TelegramClient(
            TOKEN, httpx.AsyncClient(transport=httpx.MockTransport(handler))
        )

    @property
    def texts(self) -> list[str]:
        return [r["text"] for r in self.requests if r["method"] == "sendMessage"]


def settings(**kw: Any) -> Settings:
    return Settings(telegram_chat_id=CHAT, app_base_url="http://app", **kw)  # type: ignore[arg-type]


async def seed_signal(
    symbol: str,
    strength: float = 0.8,
    kind: str = "catalyst",
    status: str = "new",
    hours_ago: float = 1,
    rumor: bool = False,
    zone: tuple[str, str, str] | None = None,
) -> uuid.UUID:
    from preza.db import get_sessionmaker

    async with get_sessionmaker()() as session:
        instrument = await session.scalar(select(Instrument).where(Instrument.symbol == symbol))
        if instrument is None:
            instrument = Instrument(symbol=symbol, exchange="X", source="test")
            session.add(instrument)
            await session.flush()
        signal = Signal(
            instrument_id=instrument.id,
            kind=kind,
            source="radar",
            direction="up",
            horizon="weeks",
            strength=Decimal(str(strength)),
            rationale=f"{symbol} moves.",
            evidence=[],
            is_rumor=rumor,
            status=status,
            created_at=NOON - timedelta(hours=hours_ago),
        )
        if zone:
            signal.source = "rule"
            signal.entry_low, signal.entry_high, signal.stop = (Decimal(z) for z in zone)
        session.add(signal)
        await session.commit()
        return signal.id


@pytest.mark.db
async def test_notify_sends_once(api: tuple[httpx.AsyncClient, FakeRouter]) -> None:
    from preza.db import get_sessionmaker

    await seed_signal("AAA", 0.8)
    await seed_signal("BBB", 0.5)  # below threshold
    await seed_signal("CCC", 0.9, hours_ago=30)  # too old
    await seed_signal("DDD", 0.9, status="dismissed")
    outbox = Outbox()
    async with get_sessionmaker()() as session:
        assert await notify_new_signals(session, outbox.client, CHAT, settings(), NOON) == 1
        await session.commit()
    async with get_sessionmaker()() as session:
        assert await notify_new_signals(session, outbox.client, CHAT, settings(), NOON) == 0
        await session.commit()
        assert await session.scalar(select(func.count()).select_from(Notification)) == 1
    assert len(outbox.texts) == 1 and outbox.texts[0].startswith("AAA · Katalizator")
    markup = outbox.requests[0]["reply_markup"]["inline_keyboard"][0]
    assert markup[1]["callback_data"].startswith("w:")


def test_format_signal_entry_zone_line() -> None:
    kw: dict[str, Any] = {"zone": (906.77, 929.63), "stop": 872.48}
    sl = format_signal("AAA", "entry", "Padec je začasen.", 0.5, False, "http://x", "sl", **kw)
    lines = sl.split("\n")
    assert lines[1] == "Cona 906,77\u2013929,63 · stop 872,48" and len(lines) <= 5
    en = format_signal("AAA", "entry", "Temporary dip.", 0.5, False, "http://x", "en", **kw)
    assert en.split("\n")[1] == "Zone 906.77\u2013929.63 · stop 872.48"
    other = format_signal("AAA", "catalyst", "x", 0.8, False, "", "en", **kw)
    assert "Zone" not in other


@pytest.mark.db
async def test_entry_below_threshold_sent_with_zone_catalyst_not(
    api: tuple[httpx.AsyncClient, FakeRouter],
) -> None:
    from preza.db import get_sessionmaker

    await seed_signal("ENT", 0.5, kind="entry", zone=("906.77", "929.63", "872.48"))
    await seed_signal("CAT", 0.5)  # catalyst below threshold
    outbox = Outbox()
    async with get_sessionmaker()() as session:
        assert await notify_new_signals(session, outbox.client, CHAT, settings(), NOON) == 1
        await session.commit()
    assert len(outbox.texts) == 1 and outbox.texts[0].startswith("ENT · Vstop")
    assert "Cona 906,77\u2013929,63 · stop 872,48" in outbox.texts[0]


@pytest.mark.db
async def test_digest_lists_entries_in_zone(api: tuple[httpx.AsyncClient, FakeRouter]) -> None:
    from preza.db import get_sessionmaker

    await seed_signal("AAA", 0.8)
    async with get_sessionmaker()() as session:
        for symbol, state, cause, rules in [
            ("ZZ1", "in_zone", "market", [{"r": 1}]),
            ("ZZ2", "below", None, [{"r": 1}, {"r": 2}]),
            ("ZZ3", "near", "sector", [{"r": 1}]),
            ("ZZ4", "in_zone", "sector", []),
        ]:
            instrument = Instrument(symbol=symbol, exchange="X", source="test")
            session.add(instrument)
            await session.flush()
            session.add(
                EntryCandidate(
                    instrument_id=instrument.id,
                    as_of=NOON.date(),
                    price=Decimal("10"),
                    rules=rules,
                    state=state,
                    cause=cause,
                    source="test",
                )
            )
        await session.commit()
    outbox = Outbox()
    async with get_sessionmaker()() as session:
        await morning_digest(session, outbox.client, CHAT, settings(), NOON)
        await session.commit()
    lines = outbox.texts[0].split("\n")
    i = lines.index("Vstopi")
    assert lines[i + 1 : i + 3] == [
        "ZZ2 · pod cono · čaka na analizo",
        "ZZ1 · v coni · trg",
    ]
    assert lines[i + 3].startswith("Odpri:") and "ZZ3" not in outbox.texts[0]
    en = Outbox()
    async with get_sessionmaker()() as session:
        await morning_digest(session, en.client, CHAT, settings(default_locale="en"), NOON)
    assert "Entries" in en.texts[0] and "ZZ2 · below zone · awaiting analysis" in en.texts[0]


@pytest.mark.db
async def test_notify_defers_at_night_and_digest_collects(
    api: tuple[httpx.AsyncClient, FakeRouter],
) -> None:
    from preza.db import get_sessionmaker

    for i, symbol in enumerate(["AAA", "BBB"]):
        await seed_signal(symbol, 0.75 + i / 10)
    outbox = Outbox()
    async with get_sessionmaker()() as session:
        assert await notify_new_signals(session, outbox.client, CHAT, settings(), NIGHT) == 0
        await session.commit()
        statuses = set(await session.scalars(select(Notification.status)))
    assert statuses == {"deferred"} and outbox.texts == []
    async with get_sessionmaker()() as session:
        assert await morning_digest(session, outbox.client, CHAT, settings(), NOON) == 2
        await session.commit()
        assert set(await session.scalars(select(Notification.status))) == {"digested"}
        assert await morning_digest(session, outbox.client, CHAT, settings(), NOON) == 0
    assert len(outbox.texts) == 1
    lines = outbox.texts[0].split("\n")
    assert lines[0].startswith("Jutranji povzetek · 2")
    assert lines[1].startswith("BBB") and "Moč 0,85" in lines[1]  # strongest first


@pytest.mark.db
async def test_notify_daily_cap_and_thesis_break_bypass(
    api: tuple[httpx.AsyncClient, FakeRouter],
) -> None:
    from preza.db import get_sessionmaker
    from tests.test_radar_pipeline import seed_portfolio

    await seed_portfolio()  # holds MSFT
    for i in range(6):
        await seed_signal(f"S{i}", 0.8, hours_ago=3 - i / 10)
    await seed_signal("MSFT", 0.8, kind="thesis_break", hours_ago=0.5)
    outbox = Outbox()
    async with get_sessionmaker()() as session:
        sent = await notify_new_signals(session, outbox.client, CHAT, settings(), NOON)
        await session.commit()
        deferred = await session.scalar(
            select(func.count()).select_from(Notification).where(Notification.status == "deferred")
        )
    assert sent == 6 and deferred == 1  # 5 regular, 1 deferred by the cap, thesis_break bypasses
    assert any(t.startswith("MSFT · Zlom teze") for t in outbox.texts)


@pytest.mark.db
async def test_notify_failure_leaves_signal_unnotified(
    api: tuple[httpx.AsyncClient, FakeRouter],
) -> None:
    from preza.db import get_sessionmaker

    await seed_signal("AAA", 0.8)
    client = TelegramClient(
        TOKEN,
        httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(500, json={}))),
    )
    async with get_sessionmaker()() as session:
        assert await notify_new_signals(session, client, CHAT, settings(), NOON) == 0
        await session.commit()
        assert await session.scalar(select(func.count()).select_from(Notification)) == 0


def callback(data: str, chat: str = CHAT) -> dict[str, Any]:
    return {
        "update_id": 1,
        "callback_query": {"id": "cb", "data": data, "message": {"chat": {"id": int(chat)}}},
    }


@pytest.mark.db
async def test_handle_callback_changes_status(api: tuple[httpx.AsyncClient, FakeRouter]) -> None:
    from preza.db import get_sessionmaker

    watch, drop = await seed_signal("AAA"), await seed_signal("BBB")
    async with get_sessionmaker()() as session:
        assert "AAA" in await handle_callback(session, callback(f"w:{watch}"), CHAT)
        assert await handle_callback(session, callback(f"x:{drop}"), CHAT) == "Zavrženo."
        await session.commit()
    async with get_sessionmaker()() as session:
        first, second = await session.get(Signal, watch), await session.get(Signal, drop)
        assert first and first.status == "watching"
        assert second and second.status == "dismissed" and second.status_reason == "telegram"


@pytest.mark.db
async def test_handle_callback_ignores_foreign_chat_and_junk(
    api: tuple[httpx.AsyncClient, FakeRouter],
) -> None:
    from preza.db import get_sessionmaker

    sid = await seed_signal("AAA")
    async with get_sessionmaker()() as session:
        assert await handle_callback(session, callback(f"x:{sid}", "999"), CHAT) == ""
        assert (
            await handle_callback(session, callback(f"x:{sid}"), None) == ""
        )  # no chat configured
        assert await handle_callback(session, callback("x:not-a-uuid"), CHAT) == ""
        assert await handle_callback(session, callback("zzz"), CHAT) == ""
        assert await handle_callback(session, {"message": {}}, CHAT) == ""
        signal = await session.get(Signal, sid)
        assert signal and signal.status == "new"


@pytest.mark.db
async def test_bot_start_predlog_and_foreign_chat(
    api: tuple[httpx.AsyncClient, FakeRouter],
) -> None:
    from preza.db import get_sessionmaker

    queued: list[str] = []

    async def enqueue(proposal_id: str) -> None:
        queued.append(proposal_id)

    def message(text: str, chat: int) -> dict[str, Any]:
        return {"update_id": 1, "message": {"text": text, "chat": {"id": chat}}}

    outbox = Outbox()
    async with get_sessionmaker()() as session:
        await handle_update(session, outbox.client, message("/start", 777), settings(), enqueue)
        await handle_update(
            session, outbox.client, message("/predlog NVDA cloud", 777), settings(), enqueue
        )
        assert queued == [] and outbox.texts == [
            "Tvoj chat ID je 777. Vpiši ga v TELEGRAM_CHAT_ID."
        ]
        await handle_update(
            session, outbox.client, message("/predlog nothing", int(CHAT)), settings(), enqueue
        )
        await handle_update(
            session,
            outbox.client,
            message("/predlog nvda AMD growth", int(CHAT)),
            settings(),
            enqueue,
        )
        await handle_update(
            session,
            outbox.client,
            message("/predlog NVDA AMD growth", int(CHAT)),
            settings(),
            enqueue,
        )
        proposal = await session.scalar(select(Proposal))
    assert proposal and proposal.symbols == ["AMD", "NVDA"] and proposal.hypothesis == "growth"
    assert proposal.depth == "quick" and proposal.save_to == "reserve"
    assert queued == [str(proposal.id)] and "AMD, NVDA" in outbox.texts[-1]
    assert outbox.texts[1].startswith("Uporaba")


def test_bot_logging_hides_request_urls() -> None:
    # Bot API URLs embed the token; httpx must not log them at INFO.
    configure_logging()
    assert not logging.getLogger("httpx").isEnabledFor(logging.INFO)
