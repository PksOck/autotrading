"""Turn scored events into catalyst signals; upgrade rumors on confirmation (BL-046, BL-047)."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from preza.domain.calibration import weighted_strength
from preza.domain.radar import (
    Direction,
    EventStatus,
    Horizon,
    SignalKind,
    SignalSource,
    SignalStatus,
)
from preza.models import Event, Signal
from preza.services.calibration import active_weight

HORIZON_BY_SENSITIVITY = {"hours": Horizon.DAYS, "days": Horizon.WEEKS, "weeks": Horizon.MONTHS}
EXPIRY = {Horizon.DAYS: 5, Horizon.WEEKS: 21, Horizon.MONTHS: 90, Horizon.YEARS: 365}


def _evidence(event: Event) -> list[dict[str, str]]:
    return [
        {
            "kind": "filing" if i.kind == "filing" else "news",
            "label": f"{i.source}: {i.title}"[:300],
            "url": i.url,
        }
        for i in sorted(event.items, key=lambda i: i.published_at)[-6:]
    ]


def _direction(event: Event) -> Direction:
    sentiment = float(event.sentiment or 0)
    return (
        Direction.UP
        if sentiment > 0.15
        else Direction.DOWN
        if sentiment < -0.15
        else Direction.NEUTRAL
    )


async def upsert_signal(
    session: AsyncSession,
    event: Event,
    instrument_id: int,
    threshold: float,
    time_sensitivity: str = "days",
) -> Signal | None:
    """One catalyst signal per event. Rumors are only watched, never acted on (AGENTS §3.4).

    The confirmed calibration weight (BL-103) scales the score before the threshold."""
    weight = await active_weight(session, SignalKind.CATALYST.value, SignalSource.RADAR.value)
    strength = weighted_strength(event.score or 0, weight)
    score = float(strength)
    existing = await session.scalar(select(Signal).where(Signal.event_id == event.id))
    if score < threshold:
        if existing is None:
            event.status = EventStatus.BELOW_THRESHOLD.value
        return existing

    horizon = HORIZON_BY_SENSITIVITY.get(time_sensitivity, Horizon.WEEKS)
    if existing is None:
        existing = Signal(
            instrument_id=instrument_id,
            kind=SignalKind.CATALYST.value,
            source=SignalSource.RADAR.value,
            horizon=horizon.value,
            event_id=event.id,
            status=(SignalStatus.WATCHING if event.is_rumor else SignalStatus.NEW).value,
            expires_at=datetime.now(UTC) + timedelta(days=EXPIRY[horizon]),
        )
        session.add(existing)
    elif (
        existing.is_rumor and not event.is_rumor and existing.status == SignalStatus.WATCHING.value
    ):
        existing.status = SignalStatus.NEW.value  # confirmed by an official source
    existing.direction = _direction(event).value
    existing.strength = strength
    existing.confidence = event.materiality
    existing.rationale = event.summary or event.title
    existing.rationale_i18n = dict(event.summary_i18n or {}) if event.summary else {}
    existing.evidence = _evidence(event)
    existing.is_rumor = event.is_rumor
    event.status = EventStatus.SIGNALLED.value
    await session.flush()
    return existing
