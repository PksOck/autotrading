"""Complete account snapshots, metric bases and reversible watchlist removal."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0018"
down_revision: str | None = "0017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "account_snapshot",
        sa.Column("account_id", sa.String(32), primary_key=True),
        sa.Column("report_date", sa.Date(), primary_key=True),
        sa.Column("positions_complete", sa.Boolean(), nullable=False),
        sa.Column("cash_complete", sa.Boolean(), nullable=False),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column(
            "fetched_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.add_column(
        "fundamentals", sa.Column("metrics_meta", JSONB(), nullable=False, server_default="{}")
    )
    op.add_column("watchlist_item", sa.Column("removed_at", sa.DateTime(timezone=True)))
    op.add_column(
        "watchlist_item", sa.Column("revision", sa.Integer(), nullable=False, server_default="1")
    )


def downgrade() -> None:
    op.drop_column("watchlist_item", "revision")
    op.drop_column("watchlist_item", "removed_at")
    op.drop_column("fundamentals", "metrics_meta")
    op.drop_table("account_snapshot")
