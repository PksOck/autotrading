"""Thesis drafts, user-confirmed revisions and append-only claim audit (BL-100)."""

import uuid
from typing import Annotated, Literal, Self
from urllib.parse import urlsplit

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)

ClaimStatus = Literal["open", "confirmed", "weakening", "broken", "expired"]
UserClaimStatus = Literal["open", "confirmed", "weakening", "broken"]
RevisionStatus = Literal["draft", "active", "superseded"]
Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=10000)]


class ThesisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ThesisDraftCreate(ThesisRequest):
    analysis_run_id: uuid.UUID


class ThesisClaimPatch(ThesisRequest):
    id: uuid.UUID
    statement: Text | None = None
    invalidated_if: Text | None = None
    expires_at: AwareDatetime | None = None

    @model_validator(mode="after")
    def statement_not_null(self) -> Self:
        if "statement" in self.model_fields_set and self.statement is None:
            raise ValueError("statement cannot be null")
        return self


class ThesisRevisionPatch(ThesisRequest):
    expected_version: int | None = Field(
        default=None,
        ge=1,
        description="Checks the revision sequence number, not a mutable edit counter.",
    )
    claims: list[ThesisClaimPatch] = Field(min_length=1, max_length=200)

    @model_validator(mode="after")
    def unique_claims(self) -> Self:
        if len({claim.id for claim in self.claims}) != len(self.claims):
            raise ValueError("duplicate claim ids")
        return self


class ThesisEvidence(ThesisRequest):
    ref: Text | None = None
    url: Annotated[str, StringConstraints(min_length=1, max_length=2000)] | None = None
    source: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=64)]
    as_of: AwareDatetime
    is_rumor: bool

    @model_validator(mode="after")
    def reference_required(self) -> Self:
        if not self.ref and not (self.url and self.url.strip()):
            raise ValueError("evidence requires ref or url")
        if self.url:
            parsed = urlsplit(self.url)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise ValueError("evidence url must be an absolute HTTP(S) URL")
        return self


class ThesisClaimStatusChange(ThesisRequest):
    to_status: UserClaimStatus
    rationale: Text
    evidence: list[ThesisEvidence] = Field(default_factory=list, max_length=100)
    expected_status: ClaimStatus

    @model_validator(mode="after")
    def evidence_required(self) -> Self:
        if self.to_status != "open" and not self.evidence:
            raise ValueError("confirmed, weakening and broken require evidence")
        return self


class ThesisInstrument(BaseModel):
    id: int
    symbol: str
    name: str | None


class ThesisClaimEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    claim_id: uuid.UUID
    from_status: ClaimStatus
    to_status: ClaimStatus
    actor: Literal["user", "deterministic"]
    rationale: str
    evidence: list[ThesisEvidence]
    source: str
    as_of: AwareDatetime
    created_at: AwareDatetime


class ThesisClaimOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    revision_id: uuid.UUID
    ordinal: int
    trigger_kind: Literal["upgrade", "downgrade"]
    trigger_index: int
    original_text: str
    statement: str
    invalidated_if: str | None
    status: ClaimStatus
    expires_at: AwareDatetime | None
    source: str
    as_of: AwareDatetime
    events: list[ThesisClaimEventOut] = Field(default_factory=list)


class ThesisRevisionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    thesis_id: uuid.UUID
    version: int
    analysis_run_id: uuid.UUID
    status: RevisionStatus
    locale: str
    delta_note: str | None
    source: str
    as_of: AwareDatetime
    created_at: AwareDatetime
    confirmed_at: AwareDatetime | None
    claims: list[ThesisClaimOut] = Field(default_factory=list)


class ThesisSummary(BaseModel):
    id: uuid.UUID
    instrument: ThesisInstrument
    active_revision_version: int | None
    claim_status_counts: dict[ClaimStatus, int]
    latest_draft_id: uuid.UUID | None
    updated_at: AwareDatetime = Field(
        description=(
            "Latest creation, confirmation or claim event time; "
            "draft edits have no stored timestamp."
        )
    )


class ThesisOut(BaseModel):
    id: uuid.UUID
    instrument: ThesisInstrument
    source: str
    as_of: AwareDatetime
    created_at: AwareDatetime
    updated_at: AwareDatetime = Field(
        description=(
            "Latest creation, confirmation or claim event time; "
            "draft edits have no stored timestamp."
        )
    )
    revisions: list[ThesisRevisionOut]
