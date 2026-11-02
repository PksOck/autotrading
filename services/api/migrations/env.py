"""Alembic environment. The database URL comes from Settings, never from alembic.ini."""

import asyncio

from alembic import context
from sqlalchemy import Index
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.schema import SchemaItem

import preza.models  # (registers tables on Base.metadata)
import preza.models_auth
import preza.models_automation
import preza.models_dividends
import preza.models_email
import preza.notify.models  # noqa: F401
from preza.config import get_settings
from preza.db import Base

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=get_settings().database_url, target_metadata=target_metadata, literal_binds=True
    )
    with context.begin_transaction():
        context.run_migrations()


def include_object(
    obj: SchemaItem, name: str | None, type_: str, reflected: bool, compare_to: SchemaItem | None
) -> bool:
    # Timescale creates this descending time index itself when making the hypertable.
    return not (
        type_ == "index"
        and reflected
        and compare_to is None
        and isinstance(obj, Index)
        and obj.table is not None
        and obj.table.name == "bar"
        and name == "bar_day_idx"
    )


def _run(connection) -> None:  # type: ignore[no-untyped-def]
    context.configure(
        connection=connection, target_metadata=target_metadata, include_object=include_object
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    engine = create_async_engine(get_settings().database_url)
    async with engine.connect() as connection:
        await connection.run_sync(_run)
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
