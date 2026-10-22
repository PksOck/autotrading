"""Machine translations of event summaries and signal rationales (BL-055).

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-22 16:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    for table, column in (("event", "summary_i18n"), ("signal", "rationale_i18n")):
        op.add_column(
            table,
            sa.Column(
                column,
                postgresql.JSONB(astext_type=sa.Text()),
                server_default=sa.text("'{}'::jsonb"),
                nullable=False,
            ),
        )


def downgrade() -> None:
    op.drop_column("signal", "rationale_i18n")
    op.drop_column("event", "summary_i18n")
