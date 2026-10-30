"""Persist bounded automation outbox scan progress."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0020"
down_revision: str | None = "0019"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "automation_outbox_cursor",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=True),
        sa.Column("execution_id", sa.Uuid(), nullable=True),
        sa.CheckConstraint("id = 1", name="ck_automation_outbox_cursor_singleton"),
        sa.CheckConstraint(
            "(scheduled_for IS NULL) = (execution_id IS NULL)",
            name="ck_automation_outbox_cursor_pair",
        ),
    )
    op.create_index(
        "ix_process_execution_outbox", "process_execution", ["state", "scheduled_for", "id"]
    )


def downgrade() -> None:
    op.drop_index("ix_process_execution_outbox", table_name="process_execution")
    op.drop_table("automation_outbox_cursor")
