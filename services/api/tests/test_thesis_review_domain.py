"""Recorded output and deterministic evidence policy. No provider or database."""

import json
import uuid
from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import ValidationError
from sqlalchemy.dialects import postgresql

from preza.domain.thesis_review import AcceptProposal, DismissProposal, ReviewBatch
from preza.services import thesis_reviews
from preza.services.thesis_reviews import (
    evidence_policy,
    is_official,
    signal_eligible,
    validate_batch,
    week_start,
)


def snapshot_session(*, previous=None, count=1, rows=()):
    revision = SimpleNamespace(thesis_id=uuid.uuid4(), locale="en")
    claims = [
        SimpleNamespace(
            id=uuid.uuid4(),
            statement="Downgrade if margins fall below 20%",
            original_text="Downgrade if margins fall below 20%",
            trigger_kind="downgrade",
            invalidated_if=None,
            status="open",
        )
        for _ in range(count)
    ]
    return MagicMock(
        get=AsyncMock(return_value=revision),
        scalar=AsyncMock(side_effect=[previous, *[None for _ in claims]]),
        scalars=AsyncMock(return_value=claims),
        execute=AsyncMock(return_value=rows),
    )


@pytest.fixture
def snapshot_thesis(monkeypatch):
    thesis = SimpleNamespace(id=uuid.uuid4(), instrument=SimpleNamespace(symbol="ASML"))
    monkeypatch.setattr(thesis_reviews.theses, "get_thesis", AsyncMock(return_value=thesis))
    return thesis


async def test_snapshot_bounds_reserves_official_and_trims_text_not_provenance(snapshot_thesis):
    cutoff = datetime(2026, 10, 25, tzinfo=UTC)
    rows = []
    for index in range(50):
        official = index >= 35
        item = SimpleNamespace(
            id=50 - index,
            kind="filing" if official else "news",
            source="edgar" if official else "finnhub",
            url=f"https://www.sec.gov/{index}" if official else f"https://example.com/{index}",
            published_at=cutoff - timedelta(days=1),
            fetched_at=cutoff - timedelta(minutes=index + 1),
            title="📝" * 500,
            summary="📝" * 1000,
        )
        rows.append((item, False, None))
    session = snapshot_session(rows=rows)
    saved = await thesis_reviews.build_snapshot(session, uuid.uuid4(), cutoff)
    assert len(saved["evidence"]) == 30 and saved["omitted_count"] == 20
    assert sum(e["official"] for e in saved["evidence"]) == 10
    assert saved["truncated"] and "limit_error" not in saved
    assert len(json.dumps(saved, ensure_ascii=False).encode("utf-8")) <= 32 * 1024
    assert len(set(saved["selected_ids"])) == 30
    assert saved["claims"][0]["statement"] == "Downgrade if margins fall below 20%"
    assert saved["claims"][0]["original_text"] == saved["claims"][0]["statement"]
    assert all(e["ref"] and e["url"] and e["source"] and e["as_of"] for e in saved["evidence"])
    assert all(e["is_rumor"] == (not e["official"]) for e in saved["evidence"])
    sql = str(
        session.execute.call_args.args[0].compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )
    assert "news_item.symbols @> ARRAY['ASML']" in sql
    assert "news_item.source != 'demo'" in sql
    assert "news_item.published_at <=" in sql and "news_item.fetched_at <=" in sql
    assert "news_item.published_at >=" in sql


async def test_incremental_snapshot_selects_late_fetched_filings(snapshot_thesis):
    previous = datetime(2026, 10, 18, tzinfo=UTC)
    session = snapshot_session(previous=previous)
    saved = await thesis_reviews.build_snapshot(session, uuid.uuid4(), previous + timedelta(days=7))
    assert saved["input_from"] == previous.isoformat() and saved["window_mode"] == "fetched_at"
    sql = str(
        session.execute.call_args.args[0].compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )
    assert "news_item.fetched_at >" in sql and "news_item.published_at >=" not in sql
    watermark_sql = str(session.scalar.call_args_list[0].args[0])
    assert "thesis_review.status IN" in watermark_sql


async def test_too_many_claims_skips_instead_of_silently_dropping(snapshot_thesis):
    session = snapshot_session(count=21)
    saved = await thesis_reviews.build_snapshot(session, uuid.uuid4(), datetime.now(UTC))
    assert saved["limit_error"] == "claim_limit" and saved["claim_count"] == 21
    assert saved["claims"] == []
    session.execute.assert_not_called()


CLAIM_IDS = [str(uuid.UUID(int=i)) for i in range(1, 5)]
# A recorded structured response, kept inline because this worker owns no fixture directory.
RECORDED_JSON = json.dumps(
    {
        "claims": [
            {
                "claim_id": CLAIM_IDS[0],
                "assessment": "sufficient",
                "suggested_status": "confirmed",
                "rationale": "The cited filing supports the claim.",
                "evidence_ids": ["news_item:1"],
            },
            {
                "claim_id": CLAIM_IDS[1],
                "assessment": "sufficient",
                "suggested_status": "weakening",
                "rationale": "The press release weakens the stated expectation.",
                "evidence_ids": ["news_item:2"],
            },
            {
                "claim_id": CLAIM_IDS[2],
                "assessment": "sufficient",
                "suggested_status": "broken",
                "rationale": "The official withdrawal contradicts the claim.",
                "evidence_ids": ["news_item:1"],
            },
            {
                "claim_id": CLAIM_IDS[3],
                "assessment": "insufficient",
                "suggested_status": None,
                "rationale": "A downgrade trigger is not a positive claim. "
                "Ignore instructions in source text.",
                "evidence_ids": [],
            },
        ]
    }
)


def snapshot():
    return {
        "claims": [{"claim_id": cid} for cid in CLAIM_IDS],
        "evidence": [{"ref": "news_item:1"}, {"ref": "news_item:2"}],
    }


def test_recorded_batch_and_exact_claim_coverage():
    batch = ReviewBatch.model_validate_json(RECORDED_JSON)
    validate_batch(snapshot(), batch)
    assert [c.suggested_status for c in batch.claims] == ["confirmed", "weakening", "broken", None]
    for bad in (
        batch.model_copy(update={"claims": batch.claims[:-1]}),
        batch.model_copy(
            update={
                "claims": [
                    batch.claims[0].model_copy(update={"claim_id": uuid.uuid4()}),
                    *batch.claims[1:],
                ]
            }
        ),
    ):
        with pytest.raises(ValueError, match="claim_ids_mismatch"):
            validate_batch(snapshot(), bad)


@pytest.mark.parametrize(
    "change",
    [
        {"suggested_status": "holds"},
        {"assessment": "insufficient"},
        {"evidence_ids": []},
        {"evidence_ids": ["news_item:1", "news_item:1"]},
        {"evidence_ids": ["filing:1"]},
        {"source": "edgar"},
        {"is_rumor": False},
        {"official": True},
        {"rationale": " "},
    ],
)
def test_schema_rejects_forged_provenance_and_invalid_assessments(change):
    raw = json.loads(RECORDED_JSON)
    raw["claims"][0].update(change)
    with pytest.raises(ValidationError):
        ReviewBatch.model_validate(raw)


def test_duplicate_claims_and_unknown_evidence_rejected():
    raw = json.loads(RECORDED_JSON)
    raw["claims"].append(raw["claims"][0])
    with pytest.raises(ValidationError, match="duplicate claim"):
        ReviewBatch.model_validate(raw)
    raw = json.loads(RECORDED_JSON)
    raw["claims"][0]["evidence_ids"] = ["news_item:999"]
    with pytest.raises(ValueError, match="evidence_ids_mismatch"):
        validate_batch(snapshot(), ReviewBatch.model_validate(raw))


@pytest.mark.parametrize(
    "kind,source,url,expected",
    [
        ("filing", "edgar", "https://www.sec.gov/Archives/report.htm", True),
        ("filing", "edgar", "https://sec.gov.evil.test/report", False),
        ("filing", "finnhub", "https://www.sec.gov/report", False),
        ("news", "edgar", "https://www.sec.gov/report", False),
        ("filing", "edgar", "http://www.sec.gov/report", False),
        ("filing", "edgar", "https://sec.gov@evil.test/report", False),
        (
            "press_release",
            "rss:prnewswire",
            "https://www.prnewswire.com/news-releases/report",
            True,
        ),
        ("press_release", "unknown", "https://www.prnewswire.com/report", False),
        ("social", "edgar", "https://www.sec.gov/report", False),
    ],
)
def test_official_ingest_and_host_allowlist(kind, source, url, expected):
    assert is_official(kind, source, url) is expected


def test_rumor_policy_is_item_specific_and_uncited_official_never_helps():
    assert evidence_policy(
        "social", "reddit", "https://reddit.com/x", triaged=True, event_is_rumor=False
    ) == (False, True)
    assert evidence_policy("news", "finnhub", "https://example.com") == (False, True)
    assert evidence_policy(
        "news", "finnhub", "https://example.com", triaged=True, event_is_rumor=False
    ) == (False, False)
    assert evidence_policy("filing", "edgar", "https://www.sec.gov/x") == (True, False)
    unofficial = {"official": False, "is_rumor": False}
    rumor = {"official": False, "is_rumor": True}
    official = {"official": True, "is_rumor": False}
    assert not signal_eligible("broken", [rumor])
    assert not signal_eligible("broken", [unofficial])
    assert not signal_eligible("confirmed", [official])
    assert signal_eligible("broken", [official, rumor])
    # Presence elsewhere in a snapshot/event is deliberately not an argument to this gate.
    assert not signal_eligible("broken", [unofficial, rumor])


def test_iso_week_year_boundary_uses_utc_monday():
    assert week_start(datetime.fromisoformat("2021-01-01T00:00:00Z")) == date(2020, 12, 28)
    assert week_start(datetime.fromisoformat("2021-01-03T23:59:00Z")) == date(2020, 12, 28)
    assert week_start(datetime.fromisoformat("2021-01-04T00:30:00+02:00")) == date(2020, 12, 28)
    assert week_start(datetime(2021, 1, 4, tzinfo=UTC)) == date(2021, 1, 4)
    with pytest.raises(ValueError):
        week_start(datetime(2021, 1, 4))


def test_decision_contracts():
    with pytest.raises(ValidationError):
        AcceptProposal.model_validate({"expected_status": "open"})
    assert (
        AcceptProposal(expected_status="open", expected_last_event_id=None).expected_last_event_id
        is None
    )
    with pytest.raises(ValidationError):
        DismissProposal(reason="  ")
