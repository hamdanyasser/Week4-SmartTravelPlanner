"""compare_destinations agent: schema validation + side-by-side run."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.agent.compare import compare_destinations
from app.schemas.compare import CompareDestinationsRequest


def test_request_requires_two_distinct_destinations():
    with pytest.raises(ValidationError):
        CompareDestinationsRequest(
            query="warm hiking under $1500", destinations=["Madeira", "Madeira"]
        )

    with pytest.raises(ValidationError):
        CompareDestinationsRequest(query="warm hiking under $1500", destinations=["Madeira"])

    with pytest.raises(ValidationError):
        CompareDestinationsRequest(
            query="warm hiking under $1500",
            destinations=["Madeira", "Slovenia", "Costa Rica"],
        )


def test_request_strips_and_compares_case_insensitively():
    with pytest.raises(ValidationError):
        CompareDestinationsRequest(
            query="warm hiking under $1500",
            destinations=["Madeira", " madeira "],
        )


@pytest.mark.asyncio
async def test_compare_runs_for_both_destinations():
    response = await compare_destinations(
        query="Two weeks in July, $1,500, warm, hiking, not too touristy",
        destinations=["Madeira", "Costa Rica"],
    )
    assert {c.name for c in response.candidates} == {"Madeira", "Costa Rica"}
    assert response.dream_fit_winner in {"Madeira", "Costa Rica"}
    assert response.reality_pressure_winner in {"Madeira", "Costa Rica"}
    assert response.comparison_verdict
    # 6 tool calls = 3 per destination * 2 destinations.
    assert len(response.tools_used) == 6
