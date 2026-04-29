"""Similarity retrieval over destination knowledge chunks."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document_chunk import DocumentChunk
from app.rag.chunking import DEFAULT_KNOWLEDGE_ROOT, build_chunks
from app.rag.embeddings import (
    EmbeddingProvider,
    cosine_similarity,
    get_embedding_provider,
)
from app.schemas.rag import (
    DestinationKnowledgeChunk,
    DestinationKnowledgeQuery,
    DestinationKnowledgeResponse,
)

MANUAL_RETRIEVAL_TEST_QUERIES = [
    "Madeira warm levada island hiking less touristy",
    "Slovenia Julian Alps Bohinj Soca hiking culture",
    "Costa Rica rainforest green season budget pressure",
]


def _normalize_destinations(destinations: list[str] | None) -> set[str] | None:
    if not destinations:
        return None
    return {destination.casefold() for destination in destinations}


@lru_cache(maxsize=1)
def _cached_local_chunks(root: str) -> tuple:
    """Load and chunk markdown once for fallback retrieval."""

    return tuple(build_chunks(Path(root)))


def retrieve_from_local(
    request: DestinationKnowledgeQuery,
    knowledge_root: Path = DEFAULT_KNOWLEDGE_ROOT,
    provider: EmbeddingProvider | None = None,
) -> DestinationKnowledgeResponse:
    """Retrieve from an in-memory fallback index."""

    provider = provider or get_embedding_provider()
    query_embedding = provider.embed_text(request.query)
    destination_filter = _normalize_destinations(request.destinations)

    scored: list[DestinationKnowledgeChunk] = []
    for chunk in _cached_local_chunks(str(knowledge_root)):
        if destination_filter and chunk.destination.casefold() not in destination_filter:
            continue
        chunk_embedding = provider.embed_text(chunk.text_for_embedding)
        scored.append(
            DestinationKnowledgeChunk(
                destination=chunk.destination,
                source_title=chunk.source_title,
                source_type=chunk.source_type,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                score=cosine_similarity(query_embedding, chunk_embedding),
                source_path=chunk.source_path,
            )
        )

    scored.sort(key=lambda item: item.score, reverse=True)
    results = scored[: request.top_k]
    return DestinationKnowledgeResponse(
        query=request.query,
        results=results,
        used_fallback=True,
        message="Retrieved from deterministic local fallback index.",
    )


async def retrieve_from_db(
    request: DestinationKnowledgeQuery,
    session: AsyncSession,
    provider: EmbeddingProvider | None = None,
) -> DestinationKnowledgeResponse:
    """Retrieve nearest chunks from Postgres/pgvector."""

    provider = provider or get_embedding_provider()
    query_embedding = provider.embed_text(request.query)
    distance = DocumentChunk.embedding.cosine_distance(query_embedding)

    statement: Select[tuple[DocumentChunk, float]] = select(
        DocumentChunk,
        distance.label("distance"),
    )
    if request.destinations:
        statement = statement.where(DocumentChunk.destination.in_(request.destinations))
    statement = statement.order_by(distance).limit(request.top_k)

    rows = (await session.execute(statement)).all()
    if not rows:
        return DestinationKnowledgeResponse(
            query=request.query,
            results=[],
            used_fallback=False,
            message="No RAG chunks found in the database yet.",
        )

    results: list[DestinationKnowledgeChunk] = []
    for chunk, distance_value in rows:
        results.append(
            DestinationKnowledgeChunk(
                destination=chunk.destination,
                source_title=chunk.source_title,
                source_type=chunk.source_type,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                score=1.0 - float(distance_value),
                source_path=None,
            )
        )

    return DestinationKnowledgeResponse(
        query=request.query,
        results=results,
        used_fallback=False,
        message="Retrieved from Postgres/pgvector.",
    )


async def retrieve_destination_knowledge(
    request: DestinationKnowledgeQuery,
    session: AsyncSession | None = None,
    provider: EmbeddingProvider | None = None,
) -> DestinationKnowledgeResponse:
    """Retrieve destination knowledge with DB first, local fallback otherwise."""

    if session is None:
        return retrieve_from_local(request=request, provider=provider)
    try:
        return await retrieve_from_db(request=request, session=session, provider=provider)
    except Exception as exc:
        fallback = retrieve_from_local(request=request, provider=provider)
        fallback.message = (
            "Database retrieval failed; used deterministic local fallback. "
            f"Reason: {exc.__class__.__name__}"
        )
        return fallback
