"""Async SQLAlchemy session setup.

This module is the database entry point for the backend. It owns:

- the declarative `Base` all models inherit from
- the async engine
- the async session factory
- the FastAPI dependency that yields one session per request/tool call

No route or tool should build its own engine.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""


@lru_cache(maxsize=1)
def get_engine() -> AsyncEngine:
    """Create the process-wide async engine lazily."""

    settings = get_settings()
    return create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)


@lru_cache(maxsize=1)
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the process-wide async session factory."""

    return async_sessionmaker(
        bind=get_engine(),
        expire_on_commit=False,
        autoflush=False,
    )


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: one database session for one request."""

    session_factory = get_session_factory()
    async with session_factory() as session:
        yield session


async def dispose_engine() -> None:
    """Close pooled database connections on shutdown or in scripts."""

    await get_engine().dispose()
