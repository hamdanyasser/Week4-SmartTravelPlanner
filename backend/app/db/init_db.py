"""Database initialisation helpers.

Day 2 needs the pgvector-backed table design, but local Docker may not always
be available during review. This module keeps the real Postgres path clean and
explicit while the RAG retriever also supports a deterministic local fallback.
"""

from __future__ import annotations

import asyncio

from sqlalchemy import text

from app.db.session import Base, dispose_engine, get_engine

# Import models so SQLAlchemy registers their tables on Base.metadata.
from app import models  # noqa: F401


async def init_db() -> None:
    """Enable pgvector and create the current tables if they are missing."""

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)


async def main() -> None:
    """CLI entry point used by `python -m app.db.init_db`."""

    try:
        await init_db()
        print("Database initialized with pgvector extension and RAG tables.")
    finally:
        await dispose_engine()


if __name__ == "__main__":
    asyncio.run(main())
