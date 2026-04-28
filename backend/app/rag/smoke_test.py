"""Smoke-test the Day 2 RAG foundation without external services.

Run from `backend/`:

    .\\.venv\\Scripts\\python -m app.rag.smoke_test

This intentionally uses the deterministic local fallback. It proves the
pipeline shape is healthy even when Docker/Postgres is unavailable:

1. DB/session/model modules import cleanly.
2. Markdown knowledge docs load and chunk.
3. Local deterministic embeddings are produced.
4. The Pydantic tool wrapper returns valid retrieval results.
"""

from __future__ import annotations

import asyncio

from app.db.init_db import init_db
from app.db.session import get_session_factory
from app.models.destination_document import DestinationDocument
from app.models.document_chunk import DocumentChunk
from app.rag.chunking import DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE
from app.rag.ingest_documents import build_local_ingest_stats
from app.rag.retriever import MANUAL_RETRIEVAL_TEST_QUERIES
from app.schemas.rag import DestinationKnowledgeResponse
from app.tools.retrieve_destination_knowledge import retrieve_destination_knowledge


async def main() -> None:
    """Run fast assertions and print the important demo facts."""

    # Import references are intentionally touched so accidental import breaks
    # fail loudly in this smoke test.
    assert init_db is not None
    assert get_session_factory is not None
    assert DestinationDocument.__tablename__ == "destination_documents"
    assert DocumentChunk.__tablename__ == "document_chunks"

    ingest_stats = build_local_ingest_stats()
    assert 20 <= ingest_stats.documents <= 30
    assert 10 <= ingest_stats.destinations <= 15
    assert ingest_stats.chunks > 0
    assert ingest_stats.used_database is False

    query = MANUAL_RETRIEVAL_TEST_QUERIES[0]
    response = await retrieve_destination_knowledge({"query": query, "top_k": 3})
    assert isinstance(response, DestinationKnowledgeResponse)
    assert response.used_fallback is True
    assert response.results

    print("RAG smoke test passed.")
    print(f"documents={ingest_stats.documents}")
    print(f"destinations={ingest_stats.destinations}")
    print(f"chunks={ingest_stats.chunks}")
    print(f"chunk_size={DEFAULT_CHUNK_SIZE}")
    print(f"chunk_overlap={DEFAULT_CHUNK_OVERLAP}")
    print(f"embedding_provider={ingest_stats.embedding_provider}")
    print(f"query={query}")
    for result in response.results:
        print(
            "result="
            f"{result.score:.3f}|{result.destination}|"
            f"{result.source_title}|chunk={result.chunk_index}"
        )


if __name__ == "__main__":
    asyncio.run(main())
