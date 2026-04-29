"""retrieve_destination_knowledge tool — exercises the local fallback index."""

from __future__ import annotations

import pytest

from app.schemas.rag import DestinationKnowledgeQuery
from app.tools.retrieve_destination_knowledge import retrieve_destination_knowledge


@pytest.mark.asyncio
async def test_local_fallback_returns_chunks_for_madeira():
    request = DestinationKnowledgeQuery(
        query="Madeira warm levada island hiking less touristy",
        destinations=["Madeira"],
        top_k=3,
    )
    response = await retrieve_destination_knowledge(request, session=None)
    assert response.used_fallback is True
    assert response.results
    assert all(chunk.destination == "Madeira" for chunk in response.results)
    assert all(-1.0 <= chunk.score <= 1.0 for chunk in response.results)


@pytest.mark.asyncio
async def test_top_k_is_respected():
    request = DestinationKnowledgeQuery(
        query="hiking budget warm island", destinations=None, top_k=2
    )
    response = await retrieve_destination_knowledge(request, session=None)
    assert len(response.results) <= 2


@pytest.mark.asyncio
async def test_destination_filter_excludes_others():
    request = DestinationKnowledgeQuery(
        query="alpine culture hiking Slovenia",
        destinations=["Slovenia"],
        top_k=4,
    )
    response = await retrieve_destination_knowledge(request, session=None)
    assert response.results
    for chunk in response.results:
        assert chunk.destination == "Slovenia"
