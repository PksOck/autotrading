import json
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from preza import db
from preza.models import Proposal

pytestmark = pytest.mark.db


async def test_proposal_filters_apply_before_limit_and_include_invalid_done_in_attention(api: Any):
    client, _ = api
    now = datetime.now(UTC)
    verdict = json.dumps(
        dict(
            verdict="supports",
            summary="Validated synthetic result",
            direction="up",
            horizon="months",
            strength=0.5,
        )
    )
    async with db.get_sessionmaker()() as session:
        saved = Proposal(
            symbols=["TARGET"],
            hypothesis="Older matching idea",
            status="done",
            verdict=verdict,
            created_at=now - timedelta(days=1),
        )
        invalid = Proposal(symbols=["BAD"], status="done", verdict="invalid", created_at=now)
        session.add_all(
            [
                saved,
                invalid,
                *[Proposal(symbols=["NEW"], status="queued", created_at=now) for _ in range(205)],
            ]
        )
        await session.commit()
        saved_id = str(saved.id)
        invalid_id = str(invalid.id)
    response = await client.get("/proposals?status=done&limit=1&q=matching")
    assert response.status_code == 200
    assert [row["id"] for row in response.json()] == [saved_id]
    attention = (await client.get("/proposals?status=attention&limit=1")).json()
    assert [row["id"] for row in attention] == [invalid_id]
    assert attention[0]["error_code"] == "invalid_result"
    pending = (await client.get("/proposals?status=pending&limit=2")).json()
    assert len(pending) == 2 and all(row["status"] == "queued" for row in pending)
    assert (await client.get("/proposals?status=unexpected")).status_code == 422
