"""Enable TimescaleDB (price bars) and pgvector (news embeddings).

Revision ID: 0001
Revises:
Create Date: 2026-10-22
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Production runs timescaledb-ha (both extensions). Plain Postgres (local tests)
    # skips them; later migrations check pg_extension before using either.
    for extension in ("timescaledb", "vector"):
        op.execute(
            f"""
            DO $$ BEGIN
              IF EXISTS (SELECT 1 FROM pg_available_extensions WHERE name = '{extension}') THEN
                CREATE EXTENSION IF NOT EXISTS {extension};
              END IF;
            END $$;
            """
        )


def downgrade() -> None:
    op.execute("DROP EXTENSION IF EXISTS vector")
    op.execute("DROP EXTENSION IF EXISTS timescaledb")
