"""Notifications use existing policy and send path. No Telegram or database."""

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from preza.config import Settings
from preza.notify import service
from preza.notify.telegram import (
    REVIEW_LABEL,
    Decision,
    NotificationPolicy,
    format_signal,
    signal_buttons,
)


def signal():
    return SimpleNamespace(
        id=uuid.uuid4(),
        instrument=SimpleNamespace(symbol="ASML"),
        kind="thesis_break",
        strength=Decimal("0.8"),
        rationale="Recorded interpretation",
        rationale_i18n={},
        is_rumor=False,
        entry_low=None,
        entry_high=None,
        stop=None,
    )


@pytest.mark.parametrize("locale", ["sl", "en"])
def test_review_label_and_link_callbacks_remain_signal_only(locale):
    url = "https://preza.test/theses/123"
    text = format_signal(
        "ASML", "thesis_break", "Interpretation", 0.8, True, url, locale, review_proposal=True
    )
    assert REVIEW_LABEL[locale] in text and url in text
    buttons = signal_buttons("signal-id", locale, "https://preza.test", url=url)[0]
    assert buttons[0]["url"] == url
    assert buttons[1]["callback_data"] == "w:signal-id"
    assert buttons[2]["callback_data"] == "x:signal-id"


@pytest.mark.parametrize("held", [False, True])
def test_existing_quiet_hours_and_held_limit_policy(held):
    policy = NotificationPolicy()
    assert (
        policy.decide("thesis_break", 0.8, held, datetime(2026, 10, 25, 23, tzinfo=UTC), 10)
        == Decision.DEFER_TO_DIGEST
    )
    assert policy.decide("thesis_break", 0.8, held, datetime(2026, 10, 25, 12, tzinfo=UTC), 10) == (
        Decision.SEND_NOW if held else Decision.DEFER_TO_DIGEST
    )


@pytest.mark.parametrize("locale", ["sl", "en"])
async def test_direct_send_and_digest_use_proposal_link(monkeypatch, locale):
    item = signal()
    url = f"https://preza.test/theses/{uuid.uuid4()}"
    links = AsyncMock(return_value={item.id: url})
    monkeypatch.setattr(service, "review_signal_links", links)
    monkeypatch.setattr(service, "user_symbols", AsyncMock(return_value=({"ASML"}, set())))
    settings = Settings(app_base_url="https://preza.test", default_locale=locale)
    session = MagicMock()
    session.scalars = AsyncMock(return_value=[item])
    session.scalar = AsyncMock(return_value=0)
    session.flush = AsyncMock()
    client = SimpleNamespace(send_message=AsyncMock())
    now = datetime(2026, 10, 25, 12, tzinfo=UTC)
    assert await service.notify_new_signals(session, client, "chat", settings, now) == 1
    args = client.send_message.call_args.args
    assert REVIEW_LABEL[locale] in args[1] and url in args[1]
    assert args[2][0][0]["url"] == url
    client.send_message.reset_mock()
    session.execute = AsyncMock(return_value=[(item, None)])
    session.scalars = AsyncMock(return_value=[])
    assert await service.morning_digest(session, client, "chat", settings, now) == 1
    digest = client.send_message.call_args.args[1]
    assert REVIEW_LABEL[locale] in digest and url in digest


async def test_existing_notification_filtered_before_send():
    session = MagicMock(scalars=AsyncMock(return_value=[]))
    client = SimpleNamespace(send_message=AsyncMock())
    assert await service.notify_new_signals(session, client, "chat", Settings()) == 0
    query = str(session.scalars.call_args.args[0])
    assert "notification.id IS NULL" in query
    client.send_message.assert_not_called()


async def test_review_link_resolution_only_uses_proposal_relationship():
    signal_id, thesis_id = uuid.uuid4(), uuid.uuid4()
    session = MagicMock(execute=AsyncMock(return_value=[(signal_id, thesis_id)]))
    links = await service.review_signal_links(session, [signal_id], "https://preza.test/")
    assert links == {signal_id: f"https://preza.test/theses/{thesis_id}"}
    assert "thesis_claim_review_proposal.signal_id IN" in str(session.execute.call_args.args[0])
    session.execute.reset_mock()
    assert await service.review_signal_links(session, [], "https://preza.test") == {}
    session.execute.assert_not_called()
