"""Chunk + embedding model for pgvector retrieval."""

from __future__ import annotations

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.rag.embeddings import DEFAULT_EMBEDDING_DIMENSION


class DocumentChunk(Base):
    """One searchable chunk from a destination knowledge document."""

    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("destination_documents.id", ondelete="CASCADE"),
        index=True,
    )
    destination: Mapped[str] = mapped_column(String(120), index=True)
    source_title: Mapped[str] = mapped_column(String(240))
    source_type: Mapped[str] = mapped_column(String(80), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(Vector(DEFAULT_EMBEDDING_DIMENSION))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    document = relationship("DestinationDocument", back_populates="chunks")


Index(
    "ix_document_chunks_embedding_cosine",
    DocumentChunk.embedding,
    postgresql_using="ivfflat",
    postgresql_with={"lists": 100},
    postgresql_ops={"embedding": "vector_cosine_ops"},
)
