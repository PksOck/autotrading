"""Thesis lifecycle API against Postgres. Run only with the existing DB fixtures."""

import uuid
from datetime import UTC, date, datetime
from typing import Any

import pytest
from sqlalchemy import func, select

from preza import db
from preza.cli.seed_demo_analysis import CARD
from preza.models import AnalysisRun, Instrument, ThesisClaimEvent, ThesisRevision

pytestmark = pytest.mark.db


async def seed_run(
    symbol: str = "ASML", *, status: str = "done", triggers: bool = True, card: bool = True
) -> uuid.UUID:
    async with db.get_sessionmaker()() as session:
        instrument = await session.scalar(select(Instrument).where(Instrument.symbol == symbol))
        if instrument is None:
            instrument = Instrument(
                symbol=symbol, name=f"{symbol} Inc", kind="stock", source="test"
            )
            session.add(instrument)
            await session.flush()
        run = AnalysisRun(
            instrument_id=instrument.id,
            engine="tradingagents",
            trade_date=date(2026, 10, 25),
            locale="en",
            status=status,
            finished_at=datetime.now(UTC) if status == "done" else None,
            card={
                **CARD,
                "upgrade_if": ["", "Revenue grows 10%", "  "] if triggers else [" "],
                "downgrade_if": ["Margins fall below 20%"] if triggers else [],
                "delta_note": "Compare the previous report",
            }
            if card
            else None,
        )
        session.add(run)
        await session.commit()
        return run.id


async def draft(client: Any, **kwargs: Any) -> dict[str, Any]:
    run_id = await seed_run(**kwargs)
    response = await client.post("/theses/drafts", json={"analysis_run_id": str(run_id)})
    assert response.status_code == 201, response.text
    return response.json()  # type: ignore[no-any-return]


def revision_path(revision: dict[str, Any]) -> str:
    return f"/theses/{revision['thesis_id']}/revisions/{revision['id']}"


def status_path(revision: dict[str, Any], index: int = 0) -> str:
    return f"/theses/{revision['thesis_id']}/claims/{revision['claims'][index]['id']}/status"


def status_body(**overrides: Any) -> dict[str, Any]:
    return {
        "to_status": "confirmed",
        "expected_status": "open",
        "rationale": "Read official report",
        "evidence": [
            {
                "ref": "filing:123",
                "source": "EDGAR",
                "as_of": "2026-10-25T12:00:00Z",
                "is_rumor": False,
            }
        ],
        **overrides,
    }


async def test_draft_idempotency_and_read_models(api: Any) -> None:
    client, _ = api
    first = await draft(client)
    repeated = await client.post(
        "/theses/drafts", json={"analysis_run_id": first["analysis_run_id"]}
    )
    assert repeated.status_code == 200 and repeated.json() == first
    assert first["version"] == 1 and first["status"] == "draft" and first["locale"] == "en"
    assert first["delta_note"] == "Compare the previous report"
    assert [c["ordinal"] for c in first["claims"]] == [0, 1]
    assert [c["trigger_index"] for c in first["claims"]] == [1, 0]
    downgrade = first["claims"][1]
    assert downgrade["trigger_kind"] == "downgrade"
    assert downgrade["original_text"] == downgrade["statement"] == "Margins fall below 20%"
    assert all(c["status"] == "open" and not c["events"] for c in first["claims"])
    assert downgrade["source"] == f"analysis_card:{first['analysis_run_id']}"
    assert downgrade["as_of"] == first["as_of"]
    listed = (await client.get("/theses", params={"symbol": "asml"})).json()
    assert listed[0]["latest_draft_id"] == first["id"]
    assert listed[0]["active_revision_version"] is None
    assert (await client.get("/theses", params={"offset": 1})).json() == []
    assert (await client.get("/theses", params={"symbol": "NOPE"})).json() == []
    detail = (await client.get(f"/theses/{first['thesis_id']}")).json()
    assert detail["instrument"]["symbol"] == "ASML" and detail["revisions"] == [first]
    assert (await client.get("/theses", params={"limit": -1})).status_code == 422
    async with db.get_sessionmaker()() as session:
        assert await session.scalar(select(func.count()).select_from(ThesisRevision)) == 1


@pytest.mark.parametrize(
    "kwargs",
    [
        {"status": "running"},
        {"triggers": False},
        {"card": False},
    ],
)
async def test_invalid_analysis_conflicts(api: Any, kwargs: dict[str, Any]) -> None:
    client, _ = api
    run_id = await seed_run(**kwargs)
    response = await client.post("/theses/drafts", json={"analysis_run_id": str(run_id)})
    assert response.status_code == 409


async def test_missing_and_wrong_owner_entities(api: Any) -> None:
    client, _ = api
    missing = str(uuid.uuid4())
    assert (
        await client.post("/theses/drafts", json={"analysis_run_id": missing})
    ).status_code == 404
    assert (await client.get(f"/theses/{missing}")).status_code == 404
    first = await draft(client)
    other = await draft(client, symbol="ORCL")
    wrong = f"/theses/{first['thesis_id']}/revisions/{other['id']}"
    assert (await client.post(wrong + "/confirm")).status_code == 404
    assert (await client.patch(wrong, json={"claims": [{"id": missing}]})).status_code == 404
    wrong_claim = f"/theses/{first['thesis_id']}/claims/{other['claims'][0]['id']}/status"
    assert (await client.post(wrong_claim, json=status_body())).status_code == 404
    assert (
        await client.patch(
            revision_path(first),
            json={"claims": [{"id": other["claims"][0]["id"], "statement": "Wrong owner"}]},
        )
    ).status_code == 404


async def test_patch_and_confirm_supersedes_without_confirming_claims(api: Any) -> None:
    client, _ = api
    first = await draft(client)
    path = revision_path(first)
    patch = {
        "expected_version": 1,
        "claims": [
            {
                "id": first["claims"][0]["id"],
                "statement": "Adjusted by user",
                "invalidated_if": "Report withdrawn",
                "expires_at": "2027-01-01T12:00:00+02:00",
            }
        ],
    }
    assert (await client.patch(path, json={**patch, "expected_version": 2})).status_code == 409
    assert first["edit_count"] == 0 and first["edited_at"] is None
    response = await client.patch(path, json={**patch, "expected_edit_count": 0})
    assert response.status_code == 200
    assert response.json()["edit_count"] == 1 and response.json()["edited_at"]
    stale = await client.patch(path, json={**patch, "expected_edit_count": 0})
    assert stale.status_code == 409 and stale.json()["detail"] == "revision_edit_conflict"
    claim = response.json()["claims"][0]
    assert (
        claim["statement"] == "Adjusted by user" and claim["original_text"] == "Revenue grows 10%"
    )
    assert claim["invalidated_if"] == "Report withdrawn" and claim["expires_at"] is not None
    cleared = await client.patch(path, json={"claims": [{"id": claim["id"], "expires_at": None}]})
    assert cleared.json()["claims"][0]["expires_at"] is None
    assert cleared.json()["edit_count"] == 2
    assert cleared.json()["claims"][0]["statement"] == "Adjusted by user"
    active = await client.post(path + "/confirm")
    assert active.status_code == 200 and active.json()["confirmed_at"]
    assert all(c["status"] == "open" and not c["events"] for c in active.json()["claims"])
    assert (await client.patch(path, json=patch)).status_code == 409
    assert (await client.post(path + "/confirm")).status_code == 409
    second = await draft(client)
    assert second["version"] == 2 and second["thesis_id"] == first["thesis_id"]
    assert (await client.post(revision_path(second) + "/confirm")).status_code == 200
    detail = (await client.get(f"/theses/{first['thesis_id']}")).json()
    assert [r["status"] for r in detail["revisions"]] == ["active", "superseded"]
    assert (await client.patch(path, json=patch)).status_code == 409
    assert (await client.post(status_path(first), json=status_body())).status_code == 409
    listed = (await client.get("/theses")).json()[0]
    assert listed["active_revision_version"] == 2 and listed["claim_status_counts"]["open"] == 2
    assert listed["latest_draft_id"] is None


async def test_status_validation_conflict_and_append_only_audit(api: Any) -> None:
    client, _ = api
    revision = await draft(client)
    path = status_path(revision)
    assert (await client.post(path, json=status_body())).status_code == 409
    await client.post(revision_path(revision) + "/confirm")
    for invalid in [
        status_body(rationale=" "),
        status_body(evidence=[]),
        status_body(to_status="expired"),
    ]:
        assert (await client.post(path, json=invalid)).status_code == 422
    changed = await client.post(path, json=status_body())
    assert changed.status_code == 200 and changed.json()["status"] == "confirmed"
    event = changed.json()["events"][0]
    assert event["from_status"] == "open" and event["to_status"] == "confirmed"
    assert event["actor"] == event["source"] == "user" and event["as_of"]
    assert event["evidence"][0]["is_rumor"] is False
    assert (await client.post(path, json=status_body())).status_code == 409
    reopened = await client.post(
        path,
        json=status_body(
            to_status="open", expected_status="confirmed", evidence=[], rationale="Revisit"
        ),
    )
    assert reopened.status_code == 200 and len(reopened.json()["events"]) == 2
    detail = (await client.get(f"/theses/{revision['thesis_id']}")).json()
    assert len(detail["revisions"][0]["claims"][0]["events"]) == 2
    async with db.get_sessionmaker()() as session:
        assert await session.scalar(select(func.count()).select_from(ThesisClaimEvent)) == 2
