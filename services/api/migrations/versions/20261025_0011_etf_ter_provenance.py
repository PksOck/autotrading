"""Record where an ETF's TER came from: Yahoo omits it for some funds (Vanguard).

Revision ID: 0011
Revises: 0010
Create Date: 2026-10-25 16:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("etf_profile", sa.Column("ter_source", sa.String(length=64), nullable=True))
    op.add_column("etf_profile", sa.Column("ter_as_of", sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column("etf_profile", "ter_as_of")
    op.drop_column("etf_profile", "ter_source")
