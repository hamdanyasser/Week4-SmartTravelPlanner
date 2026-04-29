"""Schemas for the compare-two-destinations agent mode."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.schemas.trip_brief import (
    DestinationCandidate,
    ToolTraceEntry,
    TripBriefMeta,
)


class CompareDestinationsRequest(BaseModel):
    """User input: same free-text query plus exactly two destinations."""

    query: str = Field(..., min_length=10, max_length=2000)
    destinations: list[str] = Field(..., min_length=2, max_length=2)

    @field_validator("destinations")
    @classmethod
    def _two_distinct_destinations(cls, value: list[str]) -> list[str]:
        cleaned = [d.strip() for d in value if d and d.strip()]
        if len(cleaned) != 2:
            raise ValueError("Exactly two destinations are required.")
        if cleaned[0].casefold() == cleaned[1].casefold():
            raise ValueError("The two destinations must be distinct.")
        return cleaned


class CompareDestinationsResponse(BaseModel):
    """Two candidates + a comparison verdict."""

    query: str
    candidates: list[DestinationCandidate] = Field(..., min_length=2, max_length=2)
    comparison_verdict: str
    dream_fit_winner: str
    reality_pressure_winner: str
    tools_used: list[ToolTraceEntry] = Field(default_factory=list)
    meta: TripBriefMeta = Field(default_factory=TripBriefMeta)
