"""Theses: revisions drafted from decision cards, claims and their audit (M5: BL-100).

Revision ID: 0012
Revises: 0011
Create Date: 2026-10-25 16:30:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TZ = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "thesis",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("instrument_id", sa.Integer(), sa.ForeignKey("instrument.id"), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("as_of", TZ, nullable=False),
        sa.Column("created_at", TZ, nullable=False),
        sa.UniqueConstraint("instrument_id"),
    )
    op.create_table(
        "thesis_revision",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "thesis_id", sa.Uuid(), sa.ForeignKey("thesis.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("analysis_run_id", sa.Uuid(), sa.ForeignKey("analysis_run.id"), nullable=False),
        sa.Column("status", sa.String(12), nullable=False),
        sa.Column("locale", sa.String(5), nullable=False),
        sa.Column("delta_note", sa.Text(), nullable=True),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("as_of", TZ, nullable=False),
        sa.Column("created_at", TZ, nullable=False),
        sa.Column("confirmed_at", TZ, nullable=True),
        sa.UniqueConstraint("thesis_id", "version"),
        sa.UniqueConstraint("thesis_id", "analysis_run_id"),
    )
    op.create_index("ix_thesis_revision_thesis_id", "thesis_revision", ["thesis_id"])
    op.create_index(
        "uq_thesis_revision_active",
        "thesis_revision",
        ["thesis_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
    )
    op.create_table(
        "thesis_claim",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "revision_id",
            sa.Uuid(),
            sa.ForeignKey("thesis_revision.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("trigger_kind", sa.String(10), nullable=False),
        sa.Column("trigger_index", sa.Integer(), nullable=False),
        sa.Column("original_text", sa.Text(), nullable=False),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("invalidated_if", sa.Text(), nullable=True),
        sa.Column("status", sa.String(12), nullable=False),
        sa.Column("expires_at", TZ, nullable=True),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("as_of", TZ, nullable=False),
        sa.UniqueConstraint("revision_id", "ordinal"),
        sa.UniqueConstraint("revision_id", "trigger_kind", "trigger_index"),
    )
    op.create_index("ix_thesis_claim_revision_id", "thesis_claim", ["revision_id"])
    op.create_table(
        "thesis_claim_event",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "claim_id",
            sa.Uuid(),
            sa.ForeignKey("thesis_claim.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("from_status", sa.String(12), nullable=False),
        sa.Column("to_status", sa.String(12), nullable=False),
        sa.Column("actor", sa.String(16), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("as_of", TZ, nullable=False),
        sa.Column("created_at", TZ, nullable=False),
    )
    op.create_index("ix_thesis_claim_event_claim_id", "thesis_claim_event", ["claim_id"])


def downgrade() -> None:
    op.drop_table("thesis_claim_event")
    op.drop_table("thesis_claim")
    op.drop_table("thesis_revision")
    op.drop_table("thesis")
