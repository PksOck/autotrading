"""Owner sessions and distributed login throttling."""

import sqlalchemy as sa
from alembic import op

revision = "0022"
down_revision = "0021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "owner_session",
        sa.Column("token_hash", sa.String(64), primary_key=True),
        sa.Column("credential_version", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_owner_session_expires_at", "owner_session", ["expires_at"])
    op.create_table(
        "login_throttle",
        sa.Column("key", sa.String(20), primary_key=True),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("login_throttle")
    op.drop_index("ix_owner_session_expires_at", table_name="owner_session")
    op.drop_table("owner_session")
