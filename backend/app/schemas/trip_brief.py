"""Pydantic schemas for the Decision Tension Board response.

These models are the *contract* between the agent and the React frontend.
Pydantic is our fence: data is validated when it crosses the API boundary
and trusted everywhere downstream (the brief calls this out explicitly).

The shape mirrors the four parts of the Decision Tension Board:
  - DreamFitScore       → "How well does this match the dream?"
  - RealityPressureScore → "What do live conditions say right now?"
  - DestinationCandidate → one card on the board
  - CounterfactualCard   → "Why not the obvious pick?"
  - TripBriefResponse    → the whole briefing-room view

We keep these in one file because they describe one cohesive object.
If they grow past ~150 lines we will split per-component.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TravelStyle(str, Enum):
    """The six labels our ML classifier predicts.

    Defined here as the single source of truth so the frontend, the agent,
    and the classifier all speak the same vocabulary.
    """

    ADVENTURE = "Adventure"
    RELAXATION = "Relaxation"
    CULTURE = "Culture"
    BUDGET = "Budget"
    LUXURY = "Luxury"
    FAMILY = "Family"


class TripBriefRequest(BaseModel):
    """What the user sends to /api/v1/trip-briefs."""

    query: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="The natural-language travel question.",
    )


class DreamFitScore(BaseModel):
    """ML + RAG view: how well does this destination fit the dream?"""

    score: float = Field(..., ge=0, le=100, description="0–100, higher is better.")
    matched_traits: list[str] = Field(
        default_factory=list,
        description="Traits from the user's query that this destination satisfies.",
    )
    rationale: str = Field(
        ...,
        description="Short, human-readable explanation grounded in RAG snippets.",
    )


class RealityPressureScore(BaseModel):
    """Live-conditions view: how friendly is reality right now?

    The score is inverted from intuition on purpose: 100 = no pressure
    (smooth sailing), 0 = high pressure (bad weather, expensive flights,
    visa headaches). This keeps both axes "higher is better" for the UI.
    """

    score: float = Field(..., ge=0, le=100)
    weather_signal: str = Field(..., description="One-line weather summary for the trip window.")
    flight_signal: str = Field(..., description="One-line flight-price summary.")
    rationale: str = Field(..., description="Why these signals add up to this score.")


class DestinationCandidate(BaseModel):
    """One card on the Decision Tension Board."""

    name: str
    country: str
    travel_style: TravelStyle
    dream_fit: DreamFitScore
    reality_pressure: RealityPressureScore


class CounterfactualCard(BaseModel):
    """The 'Why Not the Obvious Pick?' card.

    Names the destination most users would have guessed and explains —
    in one or two sentences — why we did not choose it. This is what
    makes the briefing feel like a real recommendation rather than a list.
    """

    obvious_pick: str
    why_not_chosen: str


class ToolTraceEntry(BaseModel):
    """One row of the agent's visible reasoning trail.

    Day 1 returns an empty list; from Day 6 we will populate this from
    the agent's tool-call log so the UI can show what actually happened.
    """

    tool: str
    summary: str


class TripBriefMeta(BaseModel):
    """Cost / latency / model accounting.

    Day 1 is all zeros. From Day 4 onward, every LLM call updates this so
    we can show a real per-query cost breakdown in the README.
    """

    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0
    cheap_model: str = "stub"
    strong_model: str = "stub"


class TripBriefResponse(BaseModel):
    """The full Decision Tension Board payload."""

    query: str
    top_pick: DestinationCandidate
    runners_up: list[DestinationCandidate] = Field(default_factory=list)
    final_verdict: str = Field(
        ...,
        description="One paragraph that names the tradeoff between Dream Fit and Reality Pressure.",
    )
    counterfactual: CounterfactualCard
    tools_used: list[ToolTraceEntry] = Field(default_factory=list)
    meta: TripBriefMeta = Field(default_factory=TripBriefMeta)

    model_config = {
        "json_schema_extra": {
            "example": {
                "query": "Two weeks in July, $1,500, warm, hiking, not too touristy",
                "top_pick": {
                    "name": "Madeira",
                    "country": "Portugal",
                    "travel_style": "Adventure",
                    "dream_fit": {
                        "score": 86,
                        "matched_traits": ["warm", "hiking", "less touristy"],
                        "rationale": "Volcanic island with the levada hiking network; July is dry and 22–26°C.",
                    },
                    "reality_pressure": {
                        "score": 72,
                        "weather_signal": "Stable, dry, ~24°C — no heatwave warnings.",
                        "flight_signal": "Round-trip in budget if booked 4–6 weeks ahead.",
                        "rationale": "Conditions are friendly; the only pressure is booking timing.",
                    },
                },
                "runners_up": [],
                "final_verdict": "Madeira clears the dream and survives the reality check; Costa Rica wins on dream but breaks the budget.",
                "counterfactual": {
                    "obvious_pick": "Costa Rica",
                    "why_not_chosen": "Hits the warm-and-hiking dream hard, but flights from Europe in July push the trip past $1,500 before lodging.",
                },
                "tools_used": [],
                "meta": {
                    "tokens_in": 0,
                    "tokens_out": 0,
                    "cost_usd": 0,
                    "latency_ms": 0,
                    "cheap_model": "stub",
                    "strong_model": "stub",
                },
            }
        }
    }


def example_stub_response(query: str) -> dict[str, Any]:
    """Hardcoded golden-demo payload returned by the Day 1 stub endpoint.

    This is intentionally not wired to any real agent yet. Its purpose is
    to lock the response shape so the React frontend can be built against
    a stable contract while the ML/RAG/agent come online.
    """
    return {
        "query": query,
        "top_pick": {
            "name": "Madeira",
            "country": "Portugal",
            "travel_style": TravelStyle.ADVENTURE,
            "dream_fit": {
                "score": 86,
                "matched_traits": ["warm", "hiking", "less touristy"],
                "rationale": (
                    "Volcanic island with the famous levada hiking network. "
                    "July is dry and 22–26°C, and crowds skew toward the south coast — "
                    "north and interior trails stay quiet."
                ),
            },
            "reality_pressure": {
                "score": 72,
                "weather_signal": "Stable, dry, ~24°C — no heatwave warnings.",
                "flight_signal": "Round-trip lands inside the $1,500 budget if booked 4–6 weeks ahead.",
                "rationale": "Conditions are friendly; the only real pressure is booking timing.",
            },
        },
        "runners_up": [],
        "final_verdict": (
            "Madeira clears the dream (warm, hiking, off the obvious tourist trail) "
            "and survives the reality check (predictable weather, fares within budget). "
            "Costa Rica wins on dream but breaks the budget once July flights are factored in."
        ),
        "counterfactual": {
            "obvious_pick": "Costa Rica",
            "why_not_chosen": (
                "Hits the warm-and-hiking dream hard, but round-trip flights from Europe in July "
                "alone consume most of the $1,500, leaving no budget for two weeks on the ground."
            ),
        },
        "tools_used": [],
        "meta": {
            "tokens_in": 0,
            "tokens_out": 0,
            "cost_usd": 0.0,
            "latency_ms": 0,
            "cheap_model": "stub",
            "strong_model": "stub",
        },
    }
