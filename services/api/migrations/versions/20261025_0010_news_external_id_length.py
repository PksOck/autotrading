"""Widen news_item.external_id: PR Newswire guids are full URLs (200+ chars).

Revision ID: 0010
Revises: 0009
Create Date: 2026-10-25 10:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "news_item",
        "external_id",
        existing_type=sa.String(length=128),
        type_=sa.String(length=1000),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "news_item",
        "external_id",
        existing_type=sa.String(length=1000),
        type_=sa.String(length=128),
        existing_nullable=True,
        postgresql_using="left(external_id, 128)",
    )
