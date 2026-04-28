"""Tool wrapper for destination RAG retrieval."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.rag.retriever import retrieve_destination_knowledge as retrieve_rag
from app.schemas.rag import DestinationKnowledgeQuery, DestinationKnowledgeResponse


TOOL_NAME = "retrieve_destination_knowledge"


async def retrieve_destination_knowledge(
    payload: DestinationKnowledgeQuery | dict[str, Any],
    session: AsyncSession | None = None,
) -> DestinationKnowledgeResponse:
    """Validate input, then retrieve matching destination knowledge chunks."""

    request = (
        payload
        if isinstance(payload, DestinationKnowledgeQuery)
        else DestinationKnowledgeQuery.model_validate(payload)
    )
    return await retrieve_rag(request=request, session=session)
