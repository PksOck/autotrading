"""Separate dividend ledgers and explicit source coverage (BL-198)."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dividend_cash_event",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("broker", sa.String(16), nullable=False),
        sa.Column("account_id", sa.String(64), nullable=False),
        sa.Column("transaction_id", sa.String(128), nullable=False),
        sa.Column("booking_date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(28, 10), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.UniqueConstraint(
            "broker", "account_id", "transaction_id", name="uq_dividend_cash_identity"
        ),
    )
    op.create_index("ix_dividend_cash_event_account_id", "dividend_cash_event", ["account_id"])
    op.create_index("ix_dividend_cash_event_booking_date", "dividend_cash_event", ["booking_date"])
    op.create_table(
        "dividend_accrual_snapshot",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("account_id", sa.String(64), nullable=False),
        sa.Column("natural_key", sa.String(256), nullable=False),
        sa.Column("as_of", sa.DateTime(timezone=True), nullable=False),
        sa.Column("gross_amount", sa.Numeric(28, 10)),
        sa.Column("net_amount", sa.Numeric(28, 10)),
        sa.Column("tax", sa.Numeric(28, 10)),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.UniqueConstraint(
            "account_id", "natural_key", "as_of", name="uq_dividend_accrual_snapshot"
        ),
    )
    op.create_index(
        "ix_dividend_accrual_snapshot_account_id", "dividend_accrual_snapshot", ["account_id"]
    )
    op.create_index("ix_dividend_accrual_snapshot_as_of", "dividend_accrual_snapshot", ["as_of"])
    op.create_table(
        "dividend_import_coverage",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("account_id", sa.String(64), nullable=False),
        sa.Column("section", sa.String(64), nullable=False),
        sa.Column("from_date", sa.Date(), nullable=False),
        sa.Column("to_date", sa.Date(), nullable=False),
        sa.Column("as_of", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.UniqueConstraint(
            "account_id", "section", "from_date", "to_date", "as_of", name="uq_dividend_coverage"
        ),
    )
    op.create_index(
        "ix_dividend_import_coverage_account_id", "dividend_import_coverage", ["account_id"]
    )
    op.create_table(
        "dividend_projection_basis",
        sa.Column("symbol", sa.String(32), primary_key=True),
        sa.Column("currency", sa.String(3), primary_key=True),
        sa.Column("annual_per_share", sa.Numeric(28, 10)),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
    )


def downgrade() -> None:
    for table in (
        "dividend_projection_basis",
        "dividend_import_coverage",
        "dividend_accrual_snapshot",
        "dividend_cash_event",
    ):
        op.drop_table(table)
