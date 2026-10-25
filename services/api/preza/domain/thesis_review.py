"""Bounded weekly review contracts. Assessments are proposals, never claim events."""

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Annotated, Any, Literal, Self

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

from preza.domain.thesis import ClaimStatus, ThesisEvidence

ReviewStatus = Literal[
    "queued",
    "running",
    "done",
    "done_no_evidence",
    "failed",
    "failed_unknown",
    "stale",
    "skipped_limits",
]
ProposalState = Literal["pending", "accepted", "dismissed"]
SuggestedStatus = Literal["confirmed", "weakening", "broken"]
Rationale = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=10000)]
EvidenceId = Annotated[str, StringConstraints(pattern=r"^news_item:[1-9][0-9]*$", max_length=64)]


class ReviewModel(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    @field_validator("*", mode="after")
    @classmethod
    def utc_times(cls, value: Any) -> Any:
        if isinstance(value, datetime):
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError("timezone required")
            return value.astimezone(UTC)
        return value


class ReviewClaimAssessment(ReviewModel):
    claim_id: uuid.UUID
    assessment: Literal["sufficient", "insufficient"]
    suggested_status: SuggestedStatus | None
    rationale: Rationale
    evidence_ids: list[EvidenceId] = Field(max_length=30)

    @model_validator(mode="after")
    def coherent(self) -> Self:
        if (self.assessment == "insufficient") != (self.suggested_status is None):
            raise ValueError(
                "insufficient requires null suggested_status; sufficient requires status"
            )
        if self.assessment == "sufficient" and not self.evidence_ids:
            raise ValueError("sufficient assessment requires citations")
        if len(set(self.evidence_ids)) != len(self.evidence_ids):
            raise ValueError("duplicate evidence ids")
        return self


class ReviewBatch(ReviewModel):
    claims: list[ReviewClaimAssessment] = Field(min_length=1, max_length=20)

    @model_validator(mode="after")
    def unique_claims(self) -> Self:
        if len({c.claim_id for c in self.claims}) != len(self.claims):
            raise ValueError("duplicate claim ids")
        return self


class AcceptProposal(ReviewModel):
    expected_status: ClaimStatus
    expected_last_event_id: uuid.UUID | None


class DismissProposal(ReviewModel):
    reason: Rationale


class ReviewOut(ReviewModel):
    id: uuid.UUID  # also the worker's run_id
    revision_id: uuid.UUID
    week_start: date
    status: ReviewStatus
    source: str
    as_of: AwareDatetime
    input_from: AwareDatetime
    input_cutoff: AwareDatetime
    snapshot: dict[str, Any]
    truncated: bool
    role: str
    model: str | None
    prompt_version: str
    attempts: int
    prompt_tokens: int
    completion_tokens: int
    cost: Decimal | None
    error_code: str | None
    created_at: AwareDatetime
    started_at: AwareDatetime | None
    finished_at: AwareDatetime | None
    dispatch_at: AwareDatetime | None


class ClaimReviewProposalOut(ReviewModel):
    id: uuid.UUID
    review_id: uuid.UUID
    claim_id: uuid.UUID
    status_at_review: ClaimStatus
    last_claim_event_id_at_review: uuid.UUID | None
    suggested_status: SuggestedStatus | None
    assessment: Literal["sufficient", "insufficient"]
    rationale: str
    evidence: list[ThesisEvidence]
    actor: Literal["agent"]
    source: str
    as_of: AwareDatetime
    state: ProposalState
    decided_at: AwareDatetime | None
    dismissal_reason: str | None
    accepted_event_id: uuid.UUID | None
    signal_id: uuid.UUID | None
