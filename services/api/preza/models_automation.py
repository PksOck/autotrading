"""Durable scheduling policies and execution/outbox records (ADR-0019)."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from preza.db import Base
from preza.models import utcnow


class AutomationControl(Base):
    __tablename__ = "automation_control"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    paused: Mapped[bool] = mapped_column(Boolean, default=False)
    revision: Mapped[int] = mapped_column(Integer, default=0)


class ProcessPolicy(Base):
    __tablename__ = "process_policy"
    process_key: Mapped[str] = mapped_column(String(40), primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    revision: Mapped[int] = mapped_column(Integer, default=0)
    config: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ProcessExecution(Base):
    __tablename__ = "process_execution"
    __table_args__ = (UniqueConstraint("process_key", "scheduled_for", name="uq_process_slot"),)
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    process_key: Mapped[str] = mapped_column(ForeignKey("process_policy.process_key"))
    policy_revision: Mapped[int] = mapped_column(Integer)
    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    origin: Mapped[str] = mapped_column(String(16), default="automatic")
    outside_window: Mapped[bool] = mapped_column(Boolean, default=False)
    state: Mapped[str] = mapped_column(String(16), default="pending", index=True)
    job_id: Mapped[str] = mapped_column(String(80))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reason: Mapped[str | None] = mapped_column(String(160))
    counts: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class ProcessAnalysis(Base):
    """Links automatically accepted analyses to the policy rechecked by the agents worker."""

    __tablename__ = "process_analysis"
    run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("analysis_run.id", ondelete="CASCADE"), primary_key=True
    )
    execution_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("process_execution.id"), index=True)
