"""Pydantic schemas for RAG retrieval and ingestion."""

from __future__ import annotations

from pydantic import BaseModel, Field


class DestinationKnowledgeQuery(BaseModel):
    """Input for the `retrieve_destination_knowledge` tool."""

    query: str = Field(..., min_length=3, max_length=1000)
    destinations: list[str] | None = Field(
        default=None,
        description="Optional destination filter, e.g. ['Madeira', 'Azores'].",
    )
    top_k: int = Field(default=5, ge=1, le=10)


class DestinationKnowledgeChunk(BaseModel):
    """One retrieved chunk with metadata the agent can cite."""

    destination: str
    source_title: str
    source_type: str
    chunk_index: int
    content: str
    score: float = Field(..., ge=-1, le=1)
    source_path: str | None = None


class DestinationKnowledgeResponse(BaseModel):
    """Output from RAG retrieval."""

    query: str
    results: list[DestinationKnowledgeChunk] = Field(default_factory=list)
    used_fallback: bool = False
    message: str | None = None


class RagIngestStats(BaseModel):
    """Plain-language ingestion stats for scripts and review notes."""

    documents: int
    destinations: int
    chunks: int
    embedding_provider: str
    used_database: bool
    message: str | None = None
