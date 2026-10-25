"""Add weekly thesis reviews and user-decidable proposals only.

Revision ID: 0013
Revises: 0012
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0013"
down_revision: str | None = "0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None
TZ = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "thesis_review",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "revision_id",
            sa.Uuid(),
            sa.ForeignKey("thesis_revision.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("week_start", sa.Date(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("as_of", TZ, nullable=False),
        sa.Column("input_from", TZ, nullable=False),
        sa.Column("input_cutoff", TZ, nullable=False),
        sa.Column("snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("truncated", sa.Boolean(), nullable=False),
        sa.Column("role", sa.String(32), nullable=False),
        sa.Column("model", sa.String(200)),
        sa.Column("prompt_version", sa.String(64), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False),
        sa.Column("completion_tokens", sa.Integer(), nullable=False),
        sa.Column("cost", sa.Numeric(18, 10)),
        sa.Column("error_code", sa.String(64)),
        sa.Column("created_at", TZ, nullable=False),
        sa.Column("started_at", TZ),
        sa.Column("finished_at", TZ),
        sa.Column("dispatch_at", TZ),
        sa.UniqueConstraint("revision_id", "week_start"),
    )
    op.create_index("ix_thesis_review_revision_id", "thesis_review", ["revision_id"])
    op.create_table(
        "thesis_claim_review_proposal",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "review_id",
            sa.Uuid(),
            sa.ForeignKey("thesis_review.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "claim_id",
            sa.Uuid(),
            sa.ForeignKey("thesis_claim.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status_at_review", sa.String(12), nullable=False),
        sa.Column(
            "last_claim_event_id_at_review", sa.Uuid(), sa.ForeignKey("thesis_claim_event.id")
        ),
        sa.Column("suggested_status", sa.String(12)),
        sa.Column("assessment", sa.String(16), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("evidence", postgresql.JSONB(), nullable=False),
        sa.Column("actor", sa.String(16), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("as_of", TZ, nullable=False),
        sa.Column("state", sa.String(12), nullable=False),
        sa.Column("decided_at", TZ),
        sa.Column("dismissal_reason", sa.Text()),
        sa.Column("accepted_event_id", sa.Uuid(), sa.ForeignKey("thesis_claim_event.id")),
        sa.Column("signal_id", sa.Uuid(), sa.ForeignKey("signal.id"), unique=True),
        sa.UniqueConstraint("review_id", "claim_id"),
    )
    for column in ("review_id", "claim_id", "state"):
        op.create_index(
            f"ix_thesis_claim_review_proposal_{column}", "thesis_claim_review_proposal", [column]
        )


def downgrade() -> None:
    op.drop_table("thesis_claim_review_proposal")
    op.drop_table("thesis_review")
