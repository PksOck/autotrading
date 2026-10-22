"""News items, events, signals and manual proposals (M2).

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-22 10:51:30.286711
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "event",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("symbols", postgresql.ARRAY(sa.String(length=20)), nullable=False),
        sa.Column("event_type", sa.String(length=16), nullable=True),
        sa.Column("is_rumor", sa.Boolean(), nullable=False),
        sa.Column("sentiment", sa.Numeric(precision=6, scale=4), nullable=True),
        sa.Column("materiality", sa.Numeric(precision=6, scale=4), nullable=True),
        sa.Column("novelty", sa.Numeric(precision=6, scale=4), nullable=True),
        sa.Column("attention", sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column("reaction_z", sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column("score", sa.Numeric(precision=6, scale=4), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("triage_model", sa.String(length=64), nullable=True),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("triaged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("confirmed_by_news_id", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_event_last_seen_at"), "event", ["last_seen_at"], unique=False)
    op.create_index(op.f("ix_event_score"), "event", ["score"], unique=False)
    op.create_table(
        "proposal",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("symbols", postgresql.ARRAY(sa.String(length=20)), nullable=False),
        sa.Column("hypothesis", sa.Text(), nullable=False),
        sa.Column("source_text", sa.Text(), nullable=False),
        sa.Column("direction", sa.String(length=8), nullable=False),
        sa.Column("horizon", sa.String(length=8), nullable=False),
        sa.Column("depth", sa.String(length=10), nullable=False),
        sa.Column("save_to", sa.String(length=8), nullable=False),
        sa.Column("status", sa.String(length=10), nullable=False),
        sa.Column("verdict", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "news_item",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("external_id", sa.String(length=128), nullable=True),
        sa.Column("url", sa.String(length=1000), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("symbols", postgresql.ARRAY(sa.String(length=20)), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("filing_form", sa.String(length=16), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("embedding", postgresql.ARRAY(sa.Float()), nullable=True),
        sa.Column("event_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["event_id"], ["event.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url"),
    )
    op.create_index(op.f("ix_news_item_event_id"), "news_item", ["event_id"], unique=False)
    op.create_index(op.f("ix_news_item_published_at"), "news_item", ["published_at"], unique=False)
    op.create_index(op.f("ix_news_item_source"), "news_item", ["source"], unique=False)
    op.create_table(
        "signal",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("instrument_id", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("source", sa.String(length=10), nullable=False),
        sa.Column("direction", sa.String(length=8), nullable=False),
        sa.Column("horizon", sa.String(length=8), nullable=False),
        sa.Column("strength", sa.Numeric(precision=6, scale=4), nullable=False),
        sa.Column("confidence", sa.Numeric(precision=6, scale=4), nullable=True),
        sa.Column("entry_low", sa.Numeric(precision=20, scale=6), nullable=True),
        sa.Column("entry_high", sa.Numeric(precision=20, scale=6), nullable=True),
        sa.Column("stop", sa.Numeric(precision=20, scale=6), nullable=True),
        sa.Column("target", sa.Numeric(precision=20, scale=6), nullable=True),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("is_rumor", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(length=10), nullable=False),
        sa.Column("status_reason", sa.Text(), nullable=True),
        sa.Column("event_id", sa.Integer(), nullable=True),
        sa.Column("proposal_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["event_id"], ["event.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["instrument_id"],
            ["instrument.id"],
        ),
        sa.ForeignKeyConstraint(["proposal_id"], ["proposal.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_signal_created_at"), "signal", ["created_at"], unique=False)
    op.create_index(op.f("ix_signal_instrument_id"), "signal", ["instrument_id"], unique=False)
    op.create_index(op.f("ix_signal_status"), "signal", ["status"], unique=False)
    op.create_foreign_key(
        "fk_event_confirmed_by_news", "event", "news_item", ["confirmed_by_news_id"], ["id"]
    )


def downgrade() -> None:
    op.drop_constraint("fk_event_confirmed_by_news", "event", type_="foreignkey")
    op.drop_index(op.f("ix_signal_status"), table_name="signal")
    op.drop_index(op.f("ix_signal_instrument_id"), table_name="signal")
    op.drop_index(op.f("ix_signal_created_at"), table_name="signal")
    op.drop_table("signal")
    op.drop_index(op.f("ix_news_item_source"), table_name="news_item")
    op.drop_index(op.f("ix_news_item_published_at"), table_name="news_item")
    op.drop_index(op.f("ix_news_item_event_id"), table_name="news_item")
    op.drop_table("news_item")
    op.drop_table("proposal")
    op.drop_index(op.f("ix_event_score"), table_name="event")
    op.drop_index(op.f("ix_event_last_seen_at"), table_name="event")
    op.drop_table("event")
