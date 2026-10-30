"""Non-secret email preferences and durable delivery intent."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from preza.db import Base
from preza.domain.email import NotificationKind


class EmailPreferences(Base):
    __tablename__ = "email_preferences"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    revision: Mapped[int] = mapped_column(Integer, default=0)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    recipients: Mapped[list[str]] = mapped_column(JSONB, default=list)
    kinds: Mapped[list[NotificationKind]] = mapped_column(JSONB, default=lambda: ["signals"])


class EmailDelivery(Base):
    __tablename__ = "email_delivery"
    event_key: Mapped[str] = mapped_column(String(180), primary_key=True)
    recipient: Mapped[str] = mapped_column(String(254), primary_key=True)
    kind: Mapped[str] = mapped_column(String(40))
    subject: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    state: Mapped[str] = mapped_column(String(20), default="pending")
    attempted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
