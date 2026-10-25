"""Thesis request validation without a database."""

import uuid
from typing import Any

import pytest
from pydantic import ValidationError

from preza.domain.thesis import (
    ThesisClaimPatch,
    ThesisClaimStatusChange,
    ThesisDraftCreate,
    ThesisEvidence,
    ThesisRevisionPatch,
)


def evidence() -> dict[str, Any]:
    return {
        "ref": "filing:2026-10-25",
        "source": "EDGAR",
        "as_of": "2026-10-25T10:00:00Z",
        "is_rumor": False,
    }


@pytest.mark.parametrize("status", ["confirmed", "weakening", "broken"])
def test_status_requires_evidence(status: str) -> None:
    with pytest.raises(ValidationError):
        ThesisClaimStatusChange.model_validate(
            {"to_status": status, "expected_status": "open", "rationale": "Checked filing"}
        )
    change = ThesisClaimStatusChange.model_validate(
        {
            "to_status": status,
            "expected_status": "open",
            "rationale": "Checked filing",
            "evidence": [evidence()],
        }
    )
    assert change.evidence[0].as_of.utcoffset() is not None


@pytest.mark.parametrize("rationale", ["", "   ", "x" * 10001])
def test_rationale_required(rationale: str) -> None:
    with pytest.raises(ValidationError):
        ThesisClaimStatusChange(to_status="open", expected_status="broken", rationale=rationale)


@pytest.mark.parametrize(
    "field,value",
    [
        ("to_status", "expired"),
        ("to_status", "unknown"),
        ("expected_status", "unknown"),
        ("actor", "deterministic"),
        ("rationale", None),
    ],
)
def test_user_status_constraints(field: str, value: Any) -> None:
    body = {"to_status": "open", "expected_status": "confirmed", "rationale": "Revisit"}
    body[field] = value
    with pytest.raises(ValidationError):
        ThesisClaimStatusChange.model_validate(body)


@pytest.mark.parametrize(
    "override",
    [
        {"ref": None},
        {"source": " "},
        {"as_of": "2026-10-25T10:00:00"},
        {"url": "javascript:alert(1)"},
        {"is_rumor": None},
        {"unexpected": "value"},
    ],
)
def test_evidence_constraints(override: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        ThesisEvidence.model_validate({**evidence(), **override})


def test_url_evidence_and_rumor_preserved() -> None:
    item = ThesisEvidence.model_validate(
        {**evidence(), "ref": None, "url": "https://example.com/news", "is_rumor": True}
    )
    assert item.is_rumor is True


@pytest.mark.parametrize(
    "override",
    [
        {"statement": " "},
        {"statement": None},
        {"statement": "x" * 10001},
        {"expires_at": "2026-10-25T10:00:00"},
        {"status": "confirmed"},
        {"original_text": "replace"},
    ],
)
def test_patch_constraints(override: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        ThesisClaimPatch.model_validate({"id": str(uuid.uuid4()), **override})


def test_patch_optional_fields_and_unique_ids() -> None:
    claim_id = uuid.uuid4()
    patch = ThesisClaimPatch(id=claim_id, expires_at=None, invalidated_if=None)
    assert "statement" not in patch.model_fields_set
    with pytest.raises(ValidationError):
        ThesisRevisionPatch(claims=[patch, patch])
    with pytest.raises(ValidationError):
        ThesisRevisionPatch(claims=[])
    with pytest.raises(ValidationError):
        ThesisRevisionPatch(claims=[patch], expected_version=0)


def test_client_cannot_supply_triggers() -> None:
    with pytest.raises(ValidationError):
        ThesisDraftCreate.model_validate(
            {"analysis_run_id": str(uuid.uuid4()), "upgrade_if": ["Invented"]}
        )
