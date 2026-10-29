"""Radar: news → events → triage → score → signals (M2, PLAN §5.2, DESIGN §11)."""

from datetime import datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from preza.domain.types import Num

NewsKind = Literal["news", "press_release", "filing", "social"]


class NewsIn(BaseModel):
    """One item as delivered by a news source, before dedupe and clustering."""

    source: str = Field(description="e.g. finnhub, rss:prnewswire, edgar, reddit")
    external_id: str | None = None
    url: str
    title: str
    summary: str | None = None
    published_at: datetime
    symbols: list[str] = Field(default_factory=list, description="tickers tagged by the source")
    kind: NewsKind = "news"
    filing_form: str | None = Field(default=None, description="8-K, 4, SC 13D ... for EDGAR items")


class EventType(StrEnum):
    EARNINGS = "earnings"
    GUIDANCE = "guidance"
    MERGER = "merger"
    FILING = "filing"
    INSIDER = "insider"
    ANALYST = "analyst"
    PRODUCT = "product"
    REGULATORY = "regulatory"
    LEGAL = "legal"
    MACRO = "macro"
    RUMOR = "rumor"
    OTHER = "other"


class TimeSensitivity(StrEnum):
    HOURS = "hours"
    DAYS = "days"
    WEEKS = "weeks"


class TriageResult(BaseModel):
    """Structured output of the `local-fast` triage call (BL-044). Numbers are model estimates."""

    tickers: list[str] = Field(default_factory=list, max_length=8)
    event_type: EventType
    is_rumor: bool
    sentiment: float = Field(ge=-1, le=1)
    materiality: float = Field(ge=0, le=1)
    novelty: float = Field(ge=0, le=1)
    time_sensitivity: TimeSensitivity
    summary: str = Field(max_length=400, description="one factual sentence in English")


class TranslatedText(BaseModel):
    id: int
    text: str = Field(max_length=600)


class TranslationBatch(BaseModel):
    """Structured output of the summary translation call (BL-055)."""

    items: list[TranslatedText]


class EventStatus(StrEnum):
    NEW = "new"
    BELOW_THRESHOLD = "below_threshold"
    SIGNALLED = "signalled"
    DISMISSED = "dismissed"


class RadarView(StrEnum):
    DISCOVER = "discover"
    WATCHLIST = "watchlist"
    PORTFOLIO = "portfolio"


class EventSource(BaseModel):
    title: str
    url: str
    source: str
    published_at: datetime
    kind: NewsKind | None = None


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    summary: str | None
    summary_translations: dict[str, str] = Field(default_factory=dict)
    symbols: list[str]
    event_type: EventType | None
    is_rumor: bool
    sentiment: Num | None
    materiality: Num | None
    novelty: Num | None
    attention: Num | None
    reaction_z: Num | None
    score: Num | None
    status: EventStatus
    first_seen_at: datetime
    last_seen_at: datetime
    sources: list[EventSource] = Field(default_factory=list)


class SignalKind(StrEnum):
    CATALYST = "catalyst"
    ENTRY = "entry"
    EXIT_WARNING = "exit_warning"
    THESIS_BREAK = "thesis_break"
    OPTIONS_IDEA = "options_idea"


class SignalSource(StrEnum):
    RULE = "rule"
    RADAR = "radar"
    AGENT = "agent"
    MANUAL = "manual"


class SignalStatus(StrEnum):
    NEW = "new"
    WATCHING = "watching"
    ACCEPTED = "accepted"
    DISMISSED = "dismissed"
    EXPIRED = "expired"


class Direction(StrEnum):
    UP = "up"
    DOWN = "down"
    NEUTRAL = "neutral"


class Horizon(StrEnum):
    DAYS = "days"
    WEEKS = "weeks"
    MONTHS = "months"
    YEARS = "years"


class EvidenceRef(BaseModel):
    kind: Literal["news", "filing", "event", "indicator", "analysis"]
    label: str
    url: str | None = None
    ref_id: str | None = None


class SignalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    symbol: str
    kind: SignalKind
    source: SignalSource
    direction: Direction
    horizon: Horizon
    strength: Num
    confidence: Num | None
    entry_low: Num | None
    entry_high: Num | None
    stop: Num | None
    target: Num | None
    rationale: str
    rationale_translations: dict[str, str] = Field(default_factory=dict)
    evidence: list[EvidenceRef]
    is_rumor: bool
    status: SignalStatus
    event_id: int | None
    proposal_id: UUID | None
    created_at: datetime
    expires_at: datetime | None


class SignalUpdate(BaseModel):
    status: SignalStatus
    reason: str | None = Field(default=None, max_length=500)


class ProposalDepth(StrEnum):
    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"


class ProposalCreate(BaseModel):
    request_id: UUID | None = None
    symbols: list[str] = Field(min_length=1, max_length=8)
    hypothesis: str = Field(default="", max_length=4000)
    source_text: str = Field(default="", max_length=20000)
    direction: Literal["up", "down", "unsure"] = "unsure"
    horizon: Horizon = Horizon.MONTHS
    depth: ProposalDepth = ProposalDepth.QUICK
    save_to: Literal["active", "reserve", "once"] = "reserve"


class ProposalResult(BaseModel):
    verdict: Literal["supports", "partly", "contradicts", "insufficient"]
    summary: str = Field(min_length=1, max_length=900)
    key_points: list[str] = Field(default_factory=list, max_length=5)
    risks: list[str] = Field(default_factory=list, max_length=4)
    direction: Literal["up", "down", "neutral"]
    horizon: Literal["days", "weeks", "months", "years"]
    strength: float = Field(ge=0, le=1)


class ProposalAnalysisLink(BaseModel):
    id: UUID
    symbol: str
    status: str


class ProposalOut(ProposalCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: Literal["queued", "running", "done", "failed"]
    verdict: str | None
    verdict_result: ProposalResult | None = None
    error_code: Literal["analysis_failed", "invalid_result"] | None = None
    analysis_links: list[ProposalAnalysisLink] = Field(default_factory=list)
    signal_id: UUID | None
    analysis_id: UUID | None = None
    created_at: datetime
    finished_at: datetime | None
