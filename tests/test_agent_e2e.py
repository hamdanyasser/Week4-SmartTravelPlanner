"""End-to-end agent run with deterministic fallbacks (no external services).

Mocked APIs in this case = the live weather API is disabled and we trust
the deterministic local RAG/ML paths. The point of this test is to prove
the LangGraph wiring composes without crashing and the response respects
the locked frontend contract.
"""

from __future__ import annotations

import pytest

from app.agent.graph import AtlasBriefAgent
from app.agent.registry import ALLOWED_TOOL_NAMES
from app.schemas.trip_brief import TravelStyle, TripBriefResponse


@pytest.mark.asyncio
async def test_agent_returns_decision_tension_board():
    agent = AtlasBriefAgent()
    state = await agent.run_state(
        query="Two weeks in July, $1,500, warm, hiking, not too touristy",
        session=None,
        ml_model=None,
    )

    response = state["response"]
    tool_results = state["tool_results"]

    assert isinstance(response, TripBriefResponse)
    assert response.top_pick.name == "Madeira"
    assert isinstance(response.top_pick.travel_style, TravelStyle)
    assert response.final_verdict
    assert response.counterfactual.obvious_pick

    # All three tools fired, every name is allowlisted, every tool returned
    # something or a recoverable error.
    assert len(tool_results) == 3
    assert {r.tool_name for r in tool_results} == ALLOWED_TOOL_NAMES


@pytest.mark.asyncio
async def test_agent_token_accounting_is_present():
    agent = AtlasBriefAgent()
    response = await agent.run(
        query="Quick trip suggestion for 10 days under $2000 with hiking",
    )
    assert response.meta.tokens_in >= 0
    assert response.meta.tokens_out >= 0
    assert response.meta.cost_usd >= 0
    assert response.meta.cheap_model
    assert response.meta.strong_model


@pytest.mark.asyncio
async def test_agent_returns_three_tool_trace_entries():
    agent = AtlasBriefAgent()
    response = await agent.run(query="Family-friendly culture trip in early autumn")
    assert len(response.tools_used) == 3
    for entry in response.tools_used:
        assert entry.tool in ALLOWED_TOOL_NAMES
        assert entry.summary
