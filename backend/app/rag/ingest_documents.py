"""Ingest markdown knowledge documents into Postgres/pgvector or local fallback."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.init_db import init_db
from app.db.session import dispose_engine, get_session_factory
from app.models.destination_document import DestinationDocument
from app.models.document_chunk import DocumentChunk
from app.rag.chunking import DEFAULT_KNOWLEDGE_ROOT, build_chunks, iter_markdown_documents
from app.rag.embeddings import EmbeddingProvider, get_embedding_provider
from app.schemas.rag import RagIngestStats


async def ingest_documents_to_db(
    session: AsyncSession,
    knowledge_root: Path = DEFAULT_KNOWLEDGE_ROOT,
    provider: EmbeddingProvider | None = None,
    reset: bool = False,
) -> RagIngestStats:
    """Load markdown docs, embed chunks, and store them in Postgres."""

    provider = provider or get_embedding_provider()
    documents = iter_markdown_documents(knowledge_root)
    chunks = build_chunks(knowledge_root)
    embeddings = provider.embed_many([chunk.text_for_embedding for chunk in chunks])

    if reset:
        await session.execute(delete(DocumentChunk))
        await session.execute(delete(DestinationDocument))

    document_rows: dict[str, DestinationDocument] = {}
    for document in documents:
        relative_path = document.path.relative_to(knowledge_root.parents[1]).as_posix()
        row = DestinationDocument(
            destination=document.destination,
            source_title=document.source_title,
            source_type=document.source_type,
            source_path=relative_path,
            content_hash=document.content_hash,
            content=document.content,
        )
        session.add(row)
        document_rows[relative_path] = row

    await session.flush()

    for chunk, embedding in zip(chunks, embeddings):
        document = document_rows[chunk.source_path]
        session.add(
            DocumentChunk(
                document_id=document.id,
                destination=chunk.destination,
                source_title=chunk.source_title,
                source_type=chunk.source_type,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                embedding=embedding,
            )
        )

    await session.commit()
    return RagIngestStats(
        documents=len(documents),
        destinations=len({document.destination for document in documents}),
        chunks=len(chunks),
        embedding_provider=provider.name,
        used_database=True,
        message="Stored chunks and embeddings in Postgres/pgvector.",
    )


def build_local_ingest_stats(
    knowledge_root: Path = DEFAULT_KNOWLEDGE_ROOT,
    provider: EmbeddingProvider | None = None,
) -> RagIngestStats:
    """Verify ingestion locally without touching the database."""

    provider = provider or get_embedding_provider()
    documents = iter_markdown_documents(knowledge_root)
    chunks = build_chunks(knowledge_root)
    provider.embed_many([chunk.text_for_embedding for chunk in chunks])
    return RagIngestStats(
        documents=len(documents),
        destinations=len({document.destination for document in documents}),
        chunks=len(chunks),
        embedding_provider=provider.name,
        used_database=False,
        message="Local fallback index built in memory.",
    )


async def run_database_ingest(reset: bool) -> RagIngestStats:
    """Initialise DB tables, then ingest into Postgres."""

    await init_db()
    session_factory = get_session_factory()
    async with session_factory() as session:
        return await ingest_documents_to_db(session=session, reset=reset)


async def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest RAG knowledge documents.")
    parser.add_argument(
        "--db",
        action="store_true",
        help="Use Postgres/pgvector. Default is local fallback verification.",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing RAG documents/chunks before DB ingest.",
    )
    args = parser.parse_args()

    try:
        if args.db:
            stats = await run_database_ingest(reset=args.reset)
        else:
            stats = build_local_ingest_stats()
        print(stats.model_dump_json(indent=2))
    finally:
        if args.db:
            await dispose_engine()


if __name__ == "__main__":
    asyncio.run(main())
