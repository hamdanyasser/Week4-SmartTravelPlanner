"""Tool allowlist and structured-error behavior."""

from __future__ import annotations

import pytest

from app.agent.registry import ALLOWED_TOOL_NAMES, execute_tool


def test_allowlist_is_exactly_three_tools():
    assert ALLOWED_TOOL_NAMES == {
        "retrieve_destination_knowledge",
        "classify_travel_style",
        "fetch_live_conditions",
    }


@pytest.mark.asyncio
async def test_execute_tool_refuses_unknown_name():
    result = await execute_tool("send_email", {"to": "x@y.com"})
    assert result.ok is False
    assert result.error is not None
    assert "allowlist" in result.error.message.lower()


@pytest.mark.asyncio
async def test_execute_tool_returns_structured_error_on_invalid_payload():
    """If the LLM sends garbage, we must not crash — we must record a recoverable error."""

    result = await execute_tool("fetch_live_conditions", {"query": "bad"})
    assert result.ok is False
    assert result.error is not None
    assert result.error.recoverable is True


@pytest.mark.asyncio
async def test_execute_tool_runs_classifier_with_valid_payload():
    result = await execute_tool(
        "classify_travel_style",
        {"query": "Two weeks of warm island hiking with $1500 budget"},
        ml_model=None,
    )
    assert result.ok is True
    assert result.output is not None
    assert "predicted_style" in result.output
