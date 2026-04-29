"""Streaming-events generator on the agent."""

from __future__ import annotations

import pytest

from app.agent.graph import AtlasBriefAgent


@pytest.mark.asyncio
async def test_stream_events_emits_expected_lifecycle():
    agent = AtlasBriefAgent()

    seen_types: list[str] = []
    seen_stages: list[str] = []
    final_brief = None
    async for event in agent.stream_events(
        query="Two weeks in July, $1500, warm hiking, not too touristy",
    ):
        seen_types.append(event["type"])
        if event["type"] == "stage":
            seen_stages.append(f"{event['stage']}:{event['status']}")
        if event["type"] == "brief":
            final_brief = event["response"]

    assert seen_types[-1] == "done"
    assert "plan:completed" in seen_stages
    # All three tools must report both start and completed/error
    for tool in [
        "tool:retrieve_destination_knowledge",
        "tool:classify_travel_style",
        "tool:fetch_live_conditions",
    ]:
        assert f"{tool}:started" in seen_stages
        assert any(s.startswith(f"{tool}:") and s.endswith(":completed") for s in seen_stages) or (
            f"{tool}:error" in seen_stages
        )
    assert "synthesize:started" in seen_stages
    assert "synthesize:completed" in seen_stages
    assert final_brief is not None
    assert final_brief["top_pick"]["name"] == "Madeira"
