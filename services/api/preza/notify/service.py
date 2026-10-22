"""Selects signals worth a notification, sends them per policy, handles button callbacks."""

import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from preza.config import Settings, get_settings
from preza.models import EntryCandidate, Signal
from preza.notify.models import Notification
from preza.notify.telegram import (
    Decision,
    NotificationPolicy,
    TelegramClient,
    TelegramError,
    _lang,
    fmt_num,
    format_signal,
    kind_label,
    signal_buttons,
)
from preza.services.radar_views import user_symbols

log = logging.getLogger(__name__)
DIGEST_LIMIT = 10


ALWAYS_NOTIFY_KINDS = ("entry", "thesis_break")  # already filtered by rules and dip analysis
ENTRY_LIMIT = 5
STATE_WORDS = {
    "sl": {"in_zone": "v coni", "below": "pod cono"},
    "en": {"in_zone": "in zone", "below": "below zone"},
}
CAUSE_WORDS = {
    "sl": {
        "market": "trg",
        "sector": "sektor",
        "transient": "začasno",
        "fundamental": "temeljno",
        None: "čaka na analizo",
    },
    "en": {
        "market": "market",
        "sector": "sector",
        "transient": "transient",
        "fundamental": "fundamental",
        None: "awaiting analysis",
    },
}


def _candidates(settings: Settings, now: datetime) -> Any:
    return (
        Signal.status.in_(("new", "watching")),
        or_(
            Signal.kind.in_(ALWAYS_NOTIFY_KINDS),
            Signal.strength >= settings.radar_notify_threshold,
        ),
        Signal.created_at >= now - timedelta(hours=24),
    )


async def notify_new_signals(
    session: AsyncSession,
    client: TelegramClient,
    chat_id: str,
    settings: Settings,
    now: datetime | None = None,
) -> int:
    """Returns the number of messages sent now. Each signal is notified at most once."""
    now = now or datetime.now(UTC)
    policy = NotificationPolicy()
    signals = list(
        await session.scalars(
            select(Signal)
            .outerjoin(Notification, Notification.signal_id == Signal.id)
            .where(Notification.id.is_(None), *_candidates(settings, now))
            .order_by(Signal.created_at)
        )
    )
    if not signals:
        return 0
    held, _ = await user_symbols(session)
    sent_today = int(
        await session.scalar(
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.status == "sent",
                Notification.sent_at >= policy.local_day_start(now),
            )
        )
        or 0
    )
    sent = 0
    for signal in signals:
        symbol = signal.instrument.symbol
        decision = policy.decide(
            signal.kind, float(signal.strength), symbol in held, now, sent_today
        )
        if decision is Decision.SKIP:
            continue
        status = "deferred"
        if decision is Decision.SEND_NOW:
            link = f"{settings.app_base_url.rstrip('/')}/signals?peek=signal:{signal.id}"
            text = format_signal(
                symbol,
                signal.kind,
                (signal.rationale_i18n or {}).get(settings.default_locale, signal.rationale),
                float(signal.strength),
                signal.is_rumor,
                link,
                settings.default_locale,
                zone=(
                    (float(signal.entry_low), float(signal.entry_high))
                    if signal.entry_low is not None and signal.entry_high is not None
                    else None
                ),
                stop=float(signal.stop) if signal.stop is not None else None,
            )
            try:
                buttons = signal_buttons(signal.id, settings.default_locale, settings.app_base_url)
                await client.send_message(chat_id, text, buttons)
            except TelegramError as exc:
                log.warning("telegram send failed, will retry: %s", exc)
                break
            status = "sent"
            sent += 1
            sent_today += 1
        session.add(Notification(signal_id=signal.id, sent_at=now, status=status))
        await session.flush()
    return sent


async def morning_digest(
    session: AsyncSession,
    client: TelegramClient,
    chat_id: str,
    settings: Settings,
    now: datetime | None = None,
) -> int:
    """One message with deferred and not yet notified signals of the last 24 h (top 10)."""
    now = now or datetime.now(UTC)
    locale = _lang(settings.default_locale)
    rows = list(
        await session.execute(
            select(Signal, Notification)
            .outerjoin(Notification, Notification.signal_id == Signal.id)
            .where(
                or_(Notification.id.is_(None), Notification.status == "deferred"),
                *_candidates(settings, now),
            )
            .order_by(Signal.strength.desc())
        )
    )
    entries = list(
        await session.scalars(
            select(EntryCandidate).where(
                EntryCandidate.state.in_(("in_zone", "below")),
                func.jsonb_array_length(EntryCandidate.rules) > 0,
            )
        )
    )
    entries.sort(key=lambda e: (-len(e.rules), e.instrument.symbol))
    entries = entries[:ENTRY_LIMIT]
    if not rows and not entries:
        return 0
    top = rows[:DIGEST_LIMIT]
    count = len(rows)
    if locale == "sl":
        head = f"Jutranji povzetek · {count} {'signal' if count == 1 else 'signalov'}"
        strength_label, open_label, entries_title = "Moč", "Odpri", "Vstopi"
    else:
        head = f"Morning digest · {count} {'signal' if count == 1 else 'signals'}"
        strength_label, open_label, entries_title = "Strength", "Open", "Entries"
    lines = [head]
    for signal, _ in top:
        prefix = {"sl": "Nepotrjeno. ", "en": "Unconfirmed. "}[locale] if signal.is_rumor else ""
        lines.append(
            f"{prefix}{signal.instrument.symbol} · {kind_label(signal.kind, locale)} · "
            f"{strength_label} {fmt_num(float(signal.strength), locale)}"
        )
    if entries:
        lines.append(entries_title)
        for entry in entries:
            state = STATE_WORDS[locale].get(entry.state or "", entry.state or "")
            cause = CAUSE_WORDS[locale].get(entry.cause, entry.cause or "")
            lines.append(f"{entry.instrument.symbol} · {state} · {cause}")
    lines.append(f"{open_label}: {settings.app_base_url.rstrip('/')}/signals")
    await client.send_message(chat_id, "\n".join(lines))
    for signal, notification in top:
        if notification is None:
            session.add(Notification(signal_id=signal.id, sent_at=now, status="digested"))
        else:
            notification.status = "digested"
            notification.sent_at = now
    await session.flush()
    return len(top)


async def handle_callback(
    session: AsyncSession, update_: dict[str, Any], chat_id: str | None = None
) -> str:
    """Applies a button press. Returns the text for the callback answer, or "" if ignored."""
    settings = get_settings()
    allowed = chat_id if chat_id is not None else settings.telegram_chat_id
    query = update_.get("callback_query")
    if not allowed or not isinstance(query, dict):
        return ""
    message = query.get("message") or {}
    if str((message.get("chat") or {}).get("id", "")) != str(allowed):
        return ""
    lang = _lang(settings.default_locale)
    action, _, raw_id = str(query.get("data", "")).partition(":")
    if action not in ("w", "x"):
        return ""
    try:
        signal_id = uuid.UUID(raw_id)
    except ValueError:
        return ""
    signal = await session.get(Signal, signal_id)
    if signal is None:
        return "Signala ni več." if lang == "sl" else "Signal no longer exists."
    if signal.status not in ("new", "watching"):
        return "Signal je že obravnavan." if lang == "sl" else "Signal already handled."
    if action == "w":
        signal.status = "watching"
        await session.flush()
        return (
            f"Spremljam {signal.instrument.symbol}."
            if lang == "sl"
            else (f"Watching {signal.instrument.symbol}.")
        )
    signal.status = "dismissed"
    signal.status_reason = "telegram"
    await session.flush()
    return "Zavrženo." if lang == "sl" else "Dismissed."
