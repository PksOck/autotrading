"""Versioned signal strength weights from outcome calibration (BL-103).

Revision ID: 0015
Revises: 0014
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0015"
down_revision: str | None = "0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "signal_weight_set",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("status", sa.String(12), nullable=False),
        sa.Column("horizon_days", sa.Integer(), nullable=False),
        sa.Column("weights", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("basis", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_signal_weight_set_status", "signal_weight_set", ["status"])
    # At most one active set at a time.
    op.create_index(
        "uq_signal_weight_set_active",
        "signal_weight_set",
        ["status"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
    )


def downgrade() -> None:
    op.drop_table("signal_weight_set")
