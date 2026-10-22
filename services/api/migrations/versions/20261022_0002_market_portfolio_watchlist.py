"""Instruments, daily bars, IBKR portfolio snapshot, watchlist and sync audit (M1).

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-22 10:30:25.735947
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "cash_balance",
        sa.Column("account_id", sa.String(length=32), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("report_date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.PrimaryKeyConstraint("account_id", "currency", "report_date"),
    )
    op.create_table(
        "instrument",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("exchange", sa.String(length=20), nullable=True),
        sa.Column("name", sa.String(length=200), nullable=True),
        sa.Column("kind", sa.String(length=10), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=True),
        sa.Column("isin", sa.String(length=12), nullable=True),
        sa.Column("ib_con_id", sa.BigInteger(), nullable=True),
        sa.Column("ucits", sa.Boolean(), nullable=False),
        sa.Column("domicile", sa.String(length=2), nullable=True),
        sa.Column("tradable_for_user", sa.Boolean(), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ib_con_id"),
        sa.UniqueConstraint(
            "symbol",
            "exchange",
            name="uq_instrument_symbol_exchange",
            postgresql_nulls_not_distinct=True,
        ),
    )
    op.create_index(op.f("ix_instrument_symbol"), "instrument", ["symbol"], unique=False)
    op.create_table(
        "sync_run",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sync_run_kind"), "sync_run", ["kind"], unique=False)
    op.create_table(
        "bar",
        sa.Column("instrument_id", sa.Integer(), nullable=False),
        sa.Column("interval", sa.String(length=4), nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("open", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("high", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("low", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("close", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("volume", sa.BigInteger(), nullable=True),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["instrument_id"], ["instrument.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("instrument_id", "interval", "day"),
    )
    op.create_table(
        "position",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.String(length=32), nullable=False),
        sa.Column("instrument_id", sa.Integer(), nullable=False),
        sa.Column("report_date", sa.Date(), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("avg_cost", sa.Numeric(precision=20, scale=6), nullable=True),
        sa.Column("market_price", sa.Numeric(precision=20, scale=6), nullable=True),
        sa.Column("market_value", sa.Numeric(precision=20, scale=6), nullable=True),
        sa.Column("unrealized_pnl", sa.Numeric(precision=20, scale=6), nullable=True),
        sa.Column("fx_rate_to_base", sa.Numeric(precision=20, scale=10), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["instrument_id"],
            ["instrument.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "account_id", "instrument_id", "report_date", name="uq_position_snapshot"
        ),
    )
    op.create_index(op.f("ix_position_account_id"), "position", ["account_id"], unique=False)
    op.create_index(op.f("ix_position_report_date"), "position", ["report_date"], unique=False)
    op.create_table(
        "trade",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.String(length=32), nullable=False),
        sa.Column("ib_trade_id", sa.String(length=64), nullable=False),
        sa.Column("instrument_id", sa.Integer(), nullable=False),
        sa.Column("trade_date", sa.Date(), nullable=False),
        sa.Column("side", sa.String(length=8), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("price", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("commission", sa.Numeric(precision=20, scale=6), nullable=True),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(
            ["instrument_id"],
            ["instrument.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ib_trade_id"),
    )
    op.create_index(op.f("ix_trade_account_id"), "trade", ["account_id"], unique=False)
    op.create_table(
        "watchlist_item",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("instrument_id", sa.Integer(), nullable=False),
        sa.Column("tier", sa.String(length=10), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("tags", postgresql.ARRAY(sa.String(length=40)), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("target_price", sa.Numeric(precision=20, scale=6), nullable=True),
        sa.Column("alert_below", sa.Numeric(precision=20, scale=6), nullable=True),
        sa.Column("alert_above", sa.Numeric(precision=20, scale=6), nullable=True),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("added_price", sa.Numeric(precision=20, scale=6), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["instrument_id"],
            ["instrument.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("instrument_id"),
    )
    # Daily bars become a hypertable when TimescaleDB is installed (production image).
    op.execute(
        """
        DO $$ BEGIN
          IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'timescaledb') THEN
            PERFORM create_hypertable('bar', 'day', chunk_time_interval => INTERVAL '1 year',
                                      migrate_data => true);
          END IF;
        END $$;
        """
    )


def downgrade() -> None:
    op.drop_table("watchlist_item")
    op.drop_index(op.f("ix_trade_account_id"), table_name="trade")
    op.drop_table("trade")
    op.drop_index(op.f("ix_position_report_date"), table_name="position")
    op.drop_index(op.f("ix_position_account_id"), table_name="position")
    op.drop_table("position")
    op.drop_table("bar")
    op.drop_index(op.f("ix_sync_run_kind"), table_name="sync_run")
    op.drop_table("sync_run")
    op.drop_index(op.f("ix_instrument_symbol"), table_name="instrument")
    op.drop_table("instrument")
    op.drop_table("cash_balance")
