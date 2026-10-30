"""Automatic analysis switch and email delivery preferences/outbox."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0019"
down_revision: str | None = "0018"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "automation_control",
        sa.Column(
            "automatic_analyses_enabled", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
    )
    op.create_table(
        "email_preferences",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("recipients", JSONB(), nullable=False),
        sa.Column("kinds", JSONB(), nullable=False),
    )
    op.create_table(
        "email_delivery",
        sa.Column("event_key", sa.String(180), primary_key=True),
        sa.Column("recipient", sa.String(254), primary_key=True),
        sa.Column("kind", sa.String(40), nullable=False),
        sa.Column("subject", sa.String(200), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("state", sa.String(20), nullable=False),
        sa.Column("attempted_at", sa.DateTime(timezone=True)),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
    )


def downgrade() -> None:
    op.drop_table("email_delivery")
    op.drop_table("email_preferences")
    op.drop_column("automation_control", "automatic_analyses_enabled")
