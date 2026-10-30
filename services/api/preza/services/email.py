"""SMTP transport with durable per-recipient deduplication and no uncertain replay."""

import asyncio
import hashlib
import smtplib
import ssl
from datetime import UTC, datetime
from email.message import EmailMessage

from fastapi import HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from preza.config import Settings
from preza.domain.email import EmailPreferencesInput, EmailPreferencesOut
from preza.models_automation import AutomationControl
from preza.models_email import EmailDelivery, EmailPreferences


def configured(settings: Settings) -> bool:
    return bool(
        settings.smtp_host and settings.smtp_from and settings.smtp_security in {"starttls", "tls"}
    )


async def preferences(session: AsyncSession, settings: Settings) -> EmailPreferencesOut:
    await session.execute(
        insert(EmailPreferences)
        .values(id=1, enabled=False, revision=0, recipients=[], kinds=["signals"])
        .on_conflict_do_nothing()
    )
    row = await session.get(EmailPreferences, 1, populate_existing=True)
    assert row is not None
    counts = dict(
        (
            await session.execute(
                select(EmailDelivery.state, func.count()).group_by(EmailDelivery.state)
            )
        ).all()
    )
    return EmailPreferencesOut(
        revision=row.revision,
        enabled=row.enabled,
        recipients=row.recipients,
        kinds=row.kinds,
        configured=configured(settings),
        queued_deliveries=counts.get("pending", 0),
        sent_deliveries=counts.get("sent", 0),
        uncertain_deliveries=counts.get("unknown", 0) + counts.get("sending", 0),
    )


async def save_preferences(
    session: AsyncSession, settings: Settings, body: EmailPreferencesInput
) -> EmailPreferencesOut:
    await preferences(session, settings)
    if body.enabled and not configured(settings):
        raise HTTPException(409, "smtp_unconfigured")
    row = await session.scalar(
        update(EmailPreferences)
        .where(EmailPreferences.id == 1, EmailPreferences.revision == body.revision)
        .values(**body.model_dump(exclude={"revision"}), revision=body.revision + 1)
        .returning(EmailPreferences)
    )
    if row is None:
        raise HTTPException(409, "revision_conflict")
    return await preferences(session, settings)


async def queue_email(
    session: AsyncSession, settings: Settings, event_key: str, kind: str, subject: str, body: str
) -> None:
    prefs = await preferences(session, settings)
    if not prefs.enabled or not prefs.configured or kind not in prefs.kinds:
        return
    for recipient in prefs.recipients:
        await session.execute(
            insert(EmailDelivery)
            .values(
                event_key=event_key,
                recipient=recipient,
                kind=kind,
                subject=subject[:200],
                body=body,
                state="pending",
            )
            .on_conflict_do_nothing()
        )


def send_message(settings: Settings, row: EmailDelivery) -> None:
    assert settings.smtp_host is not None
    message = EmailMessage()
    message["From"] = settings.smtp_from
    message["To"] = row.recipient
    message["Subject"] = row.subject
    digest = hashlib.sha256(f"{row.event_key}:{row.recipient}".encode()).hexdigest()
    message["Message-ID"] = f"<{digest}@preza.local>"
    message.set_content(row.body)
    context = ssl.create_default_context()
    client: smtplib.SMTP
    if settings.smtp_security == "tls":
        client = smtplib.SMTP_SSL(
            settings.smtp_host, settings.smtp_port, timeout=20, context=context
        )
    else:
        client = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20)
        client.starttls(context=context)
    with client:
        if settings.smtp_username and settings.smtp_password:
            client.login(settings.smtp_username, settings.smtp_password.get_secret_value())
        client.send_message(message)


async def deliver_one(session: AsyncSession, settings: Settings) -> bool:
    control = await session.get(AutomationControl, 1, populate_existing=True)
    if control is not None and control.paused:
        return False
    prefs = await preferences(session, settings)
    if not prefs.enabled or not prefs.configured:
        return False
    row = await session.scalar(
        select(EmailDelivery)
        .where(EmailDelivery.state == "pending")
        .order_by(EmailDelivery.event_key)
        .with_for_update(skip_locked=True)
        .limit(1)
    )
    if row is None:
        return False
    if row.recipient not in prefs.recipients or row.kind not in prefs.kinds:
        row.state = "cancelled"
        await session.commit()
        return True
    control = await session.get(AutomationControl, 1, populate_existing=True)
    if control is not None and control.paused:
        return False
    # Commit before SMTP. A crash or ambiguous SMTP response must not resend automatically.
    row.state, row.attempted_at = "sending", datetime.now(UTC)
    await session.commit()
    try:
        await asyncio.to_thread(send_message, settings, row)
    except (smtplib.SMTPException, OSError):
        row.state = "unknown"
    else:
        row.state, row.sent_at = "sent", datetime.now(UTC)
    await session.commit()
    return True
