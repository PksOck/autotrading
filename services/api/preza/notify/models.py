"""Notification log: one row per signal that was sent, deferred or digested."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from preza.db import Base
from preza.models import utcnow


class Notification(Base):
    """status: sent | deferred | digested. A signal is notified at most once (unique)."""

    __tablename__ = "notification"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    signal_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("signal.id", ondelete="CASCADE"), unique=True
    )
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    channel: Mapped[str] = mapped_column(String(16), default="telegram")
    status: Mapped[str] = mapped_column(String(10))
