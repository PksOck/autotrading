from typing import Any

import pytest
from sqlalchemy import delete, select

from preza import db
from preza.config import Settings
from preza.domain.email import EmailPreferencesInput
from preza.models_email import EmailDelivery, EmailPreferences
from preza.services import email

pytestmark = pytest.mark.db


async def test_email_preferences_validation_and_revision(api: Any) -> None:
    client, _ = api
    async with db.get_sessionmaker()() as session:
        await session.execute(delete(EmailDelivery))
        await session.execute(delete(EmailPreferences))
        await session.commit()
    initial = (await client.get("/notifications/email")).json()
    assert not initial["enabled"]
    assert not initial["configured"]
    body = {"revision": 0, "recipients": ["one@example.com", "two@example.org"]}
    response = await client.patch("/notifications/email", json=body)
    assert response.status_code == 200
    assert response.json()["recipients"] == body["recipients"]
    assert (await client.patch("/notifications/email", json=body)).status_code == 409
    body.update(revision=1, enabled=True)
    assert (await client.patch("/notifications/email", json=body)).status_code == 409
    body.update(enabled=False, recipients=["invalid"])
    assert (await client.patch("/notifications/email", json=body)).status_code == 422


async def test_email_outbox_deduplicates_and_never_retries_uncertain_send(
    api: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = Settings(smtp_host="smtp.example.org", smtp_from="preza@example.org")
    calls = []

    def fake_send(settings: Settings, row: EmailDelivery) -> None:
        calls.append(row.recipient)
        raise OSError("ambiguous SMTP response")

    monkeypatch.setattr(email, "send_message", fake_send)
    async with db.get_sessionmaker()() as session:
        await session.execute(delete(EmailDelivery))
        await session.execute(delete(EmailPreferences))
        await email.save_preferences(
            session,
            settings,
            EmailPreferencesInput(enabled=True, recipients=["one@example.org", "two@example.org"]),
        )
        for _ in range(2):
            await email.queue_email(
                session, settings, "test:event", "signals", "Test", "Saved facts"
            )
        await session.commit()
        assert len(list(await session.scalars(select(EmailDelivery)))) == 2
        assert await email.deliver_one(session, settings)
        assert await email.deliver_one(session, settings)
        assert not await email.deliver_one(session, settings)
        assert sorted(calls) == ["one@example.org", "two@example.org"]
        prefs = await email.preferences(session, settings)
        assert prefs.uncertain_deliveries == 2
        assert prefs.sent_deliveries == 0
