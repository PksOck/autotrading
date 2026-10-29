"""Durable process policies and outbox (ADR-0019).

Revision ID: 0016
Revises: 0015
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "automation_control",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("paused", sa.Boolean(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
    )
    op.create_table(
        "process_policy",
        sa.Column("process_key", sa.String(40), primary_key=True),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("config", JSONB(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "process_execution",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "process_key",
            sa.String(40),
            sa.ForeignKey("process_policy.process_key"),
            nullable=False,
        ),
        sa.Column("policy_revision", sa.Integer(), nullable=False),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=False),
        sa.Column("origin", sa.String(16), nullable=False),
        sa.Column("outside_window", sa.Boolean(), nullable=False),
        sa.Column("state", sa.String(16), nullable=False),
        sa.Column("job_id", sa.String(80), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("heartbeat_at", sa.DateTime(timezone=True)),
        sa.Column("reason", sa.String(160)),
        sa.Column("counts", JSONB(), nullable=False),
        sa.UniqueConstraint("process_key", "scheduled_for", name="uq_process_slot"),
    )
    op.create_index("ix_process_execution_state", "process_execution", ["state"])

    op.create_table(
        "process_analysis",
        sa.Column(
            "run_id",
            sa.Uuid(),
            sa.ForeignKey("analysis_run.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("execution_id", sa.Uuid(), sa.ForeignKey("process_execution.id"), nullable=False),
    )
    op.create_index("ix_process_analysis_execution_id", "process_analysis", ["execution_id"])


def downgrade() -> None:
    op.drop_table("process_analysis")
    op.drop_table("process_execution")
    op.drop_table("process_policy")
    op.drop_table("automation_control")
