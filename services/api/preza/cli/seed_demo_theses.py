"""Repeatable, explicitly synthetic thesis examples in the isolated demo only."""

import os
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from preza.cli.seed_demo_analysis import CARD
from preza.db import get_sessionmaker
from preza.domain.thesis import ThesisClaimStatusChange, ThesisEvidence
from preza.models import AnalysisRun, Instrument, ThesisClaim
from preza.services.theses import change_claim_status, confirm_revision, create_draft


async def seed_theses() -> None:
    if os.environ.get("PREZA_DEMO_DB") != "1":
        raise RuntimeError("demo_only: thesis fixtures require PREZA_DEMO_DB=1")
    async with get_sessionmaker()() as session:
        now = datetime.now(UTC)
        for symbol, state in (("MSFT", "active"), ("ORCL", "draft"), ("COST", "weakening")):
            instrument = await session.scalar(select(Instrument).where(Instrument.symbol == symbol))
            if instrument is None or instrument.source != "demo":
                continue
            run_id = uuid.uuid5(uuid.NAMESPACE_URL, f"preza-demo-thesis-{symbol}")
            run = await session.get(AnalysisRun, run_id)
            if run is None:
                available = now - timedelta(days=45)
                run = AnalysisRun(
                    id=run_id,
                    instrument_id=instrument.id,
                    engine="tradingagents",
                    locale="sl",
                    trade_date=available.date(),
                    status="done",
                    rating="Overweight",
                    created_at=available - timedelta(minutes=5),
                    finished_at=available,
                    decision="Sintetični demo primer teze; ni dejanska analiza družbe.",
                    models={"quick": "demo_thesis"},
                    reports={},
                    caveats=["synthetic_demo"],
                    card={
                        **CARD,
                        "upgrade_if": ["DEMO: naslednje uradno poročilo potrdi rast poslovanja."],
                        "downgrade_if": ["DEMO: uradni vir potrdi slabšanje poslovanja."],
                        "delta_note": "Sintetični primer za preverjanje uporabniške poti.",
                    },
                )
                session.add(run)
                await session.flush()
            revision, created = await create_draft(session, run_id)
            # Do not reset edits or user decisions on a repeated demo seed.
            if not created:
                continue
            if state != "draft":
                await confirm_revision(session, revision.thesis_id, revision.id)
            if state == "weakening":
                claim = await session.scalar(
                    select(ThesisClaim).where(
                        ThesisClaim.revision_id == revision.id, ThesisClaim.ordinal == 0
                    )
                )
                assert claim is not None
                await change_claim_status(
                    session,
                    revision.thesis_id,
                    claim.id,
                    ThesisClaimStatusChange(
                        to_status="weakening",
                        expected_status="open",
                        rationale="DEMO: opozorilo in revizijska sled; ne dejstvo o družbi.",
                        evidence=[
                            ThesisEvidence(
                                ref="synthetic-demo-report",
                                source="demo",
                                as_of=now,
                                is_rumor=False,
                            )
                        ],
                    ),
                )
        await session.commit()
