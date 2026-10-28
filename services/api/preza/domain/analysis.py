"""Deep analysis (M4): run summaries, details and timeline steps (SCR-06, CMP-12)."""

import uuid
from datetime import date, datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field

from preza.domain.outlook import Outlook, OutlookBrief


class AnalysisStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class AnalysisCreate(BaseModel):
    symbol: str = Field(min_length=1, max_length=20)
    trade_date: date | None = None
    hypothesis: str | None = Field(default=None, max_length=2000)


class AnalysisQuota(BaseModel):
    limit: int = Field(description="0 means no limit")
    used: int


class AnalysisStepOut(BaseModel):
    seq: int
    agent: str
    kind: str
    title: str | None
    content: str
    created_at: datetime


class AnalysisSummary(BaseModel):
    id: uuid.UUID
    symbol: str
    name: str | None
    engine: str
    trade_date: date
    status: AnalysisStatus
    rating: str | None
    caveats: list[str]
    created_at: datetime
    finished_at: datetime | None
    conviction: int | None = None
    outlook_brief: OutlookBrief | None = Field(
        default=None, description="horizon verdicts from the snapshot (ADR-0014)"
    )


class ControlScore(BaseModel):
    """Deterministic composite next to the agents' rating (BL-089). Components in -1..1."""

    score: float | None
    coverage: float = Field(ge=0, le=1, description="share of the weights with data")
    components: dict[str, float | None]
    weights: dict[str, float]
    implied_rating: str | None


class PreviousRun(BaseModel):
    id: uuid.UUID
    trade_date: date
    rating: str | None


class DecisionCard(BaseModel):
    """Structured decision (BL-089). The model writes triggers, conviction and the delta
    note; the control score, size class and confidence are computed by code."""

    rating: str
    control: ControlScore
    confidence: Literal["normal", "low"]
    conviction: int | None = Field(default=None, ge=1, le=10)
    size_class: Literal["none", "small", "normal", "increased"] | None
    upgrade_if: list[str] = Field(default_factory=list)
    downgrade_if: list[str] = Field(default_factory=list)
    delta_note: str | None = None
    previous: PreviousRun | None = None


class AnalysisOut(AnalysisSummary):
    locale: str
    hypothesis: str | None
    decision: str | None
    reports: dict[str, str]
    models: dict[str, Any]
    error: str | None
    started_at: datetime | None
    data_sources: dict[str, str | None]
    card: DecisionCard | None = None
    outlook: Outlook | None = None
    steps: list[AnalysisStepOut]
