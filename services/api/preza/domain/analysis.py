"""Deep analysis (M4): run summaries, details and timeline steps (SCR-06, CMP-12)."""

import uuid
from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class AnalysisStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class AnalysisCreate(BaseModel):
    symbol: str = Field(min_length=1, max_length=20)
    trade_date: date | None = None
    hypothesis: str | None = Field(default=None, max_length=2000)


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


class AnalysisOut(AnalysisSummary):
    locale: str
    hypothesis: str | None
    decision: str | None
    reports: dict[str, str]
    models: dict[str, str]
    error: str | None
    started_at: datetime | None
    data_sources: dict[str, str | None]
    steps: list[AnalysisStepOut]
