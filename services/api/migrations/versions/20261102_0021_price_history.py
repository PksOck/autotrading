"""Archive coherent, attributable split-adjusted price captures."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0021"
down_revision: str | None = "0020"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "price_history_capture",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column(
            "instrument_id",
            sa.Integer(),
            sa.ForeignKey("instrument.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(8), nullable=False),
        sa.Column("resolved_con_id", sa.BigInteger(), nullable=False),
        sa.Column("identity", postgresql.JSONB(), nullable=False),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("price_basis", sa.String(64), nullable=False),
        sa.Column("first_day", sa.Date(), nullable=False),
        sa.Column("last_day", sa.Date(), nullable=False),
        sa.Column("bars", postgresql.JSONB(), nullable=False),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_price_history_latest", "price_history_capture", ["instrument_id", "year", "fetched_at"]
    )
    op.execute("""CREATE FUNCTION preza_reject_history_update() RETURNS trigger
        LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'immutable_history_capture'; END $$""")
    op.execute("""CREATE TRIGGER price_history_no_update BEFORE UPDATE ON price_history_capture
        FOR EACH ROW EXECUTE FUNCTION preza_reject_history_update()""")


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS price_history_no_update ON price_history_capture")
    op.execute("DROP FUNCTION IF EXISTS preza_reject_history_update()")
    op.drop_index("ix_price_history_latest", table_name="price_history_capture")
    op.drop_table("price_history_capture")
