"""Database engine, session factory and declarative base. Created lazily so tests can point
DATABASE_URL at a test database before first use."""

from collections.abc import AsyncIterator
from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from preza.config import get_settings


class Base(DeclarativeBase):
    pass


@lru_cache
def get_engine() -> AsyncEngine:
    return create_async_engine(get_settings().database_url, pool_pre_ping=True)


@lru_cache
def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(get_engine(), expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    """One transaction per request: commit on success, roll back on any error."""
    async with get_sessionmaker()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
