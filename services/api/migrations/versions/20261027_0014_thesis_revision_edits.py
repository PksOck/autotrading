"""Count draft edits on thesis revisions so stale editors get a conflict.

Revision ID: 0014
Revises: 0013
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0014"
down_revision: str | None = "0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "thesis_revision",
        sa.Column("edit_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("thesis_revision", sa.Column("edited_at", sa.DateTime(timezone=True)))


def downgrade() -> None:
    op.drop_column("thesis_revision", "edited_at")
    op.drop_column("thesis_revision", "edit_count")
