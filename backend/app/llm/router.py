"""Two-model routing with deterministic fallback.

The real cheap/strong model providers are intentionally not called unless keys
and provider-specific clients are added later. Today this module records the
same routing shape and usage accounting while keeping local demos stable.
"""

from __future__ import annotations

import re

from app.config import get_settings
from app.schemas.llm import LLMUsage, TripPlan


def _count_tokens(text: str) -> int:
    return len(re.findall(r"\w+", text))


def extract_trip_plan(query: str) -> TripPlan:
    """Cheap-model step: extract a small plan from the free-text query."""

    settings = get_settings()
    lowered = query.lower()
    matched_traits: list[str] = []
    if "warm" in lowered:
        matched_traits.append("warm")
    if "hiking" in lowered or "hike" in lowered:
        matched_traits.append("hiking")
    if "not too touristy" in lowered or "less touristy" in lowered:
        matched_traits.append("less touristy")
    if "$1,500" in query or "1500" in lowered or "budget" in lowered:
        matched_traits.append("budget-aware")

    # Golden-demo deterministic plan. Other queries still get a sane default.
    destination = "Madeira"
    country = "Portugal"
    rag_query = "Madeira warm levada island hiking less touristy"
    counterfactual = "Costa Rica"

    feature_profile = {
        "budget_level": 3,
        "climate_warmth": 4,
        "hiking_score": 5,
        "culture_score": 3,
        "tourism_level": 3,
        "luxury_score": 2,
        "family_score": 3,
        "safety_score": 5,
        "avg_daily_cost_usd": 120,
    }

    return TripPlan(
        query=query,
        destination=destination,
        country=country,
        counterfactual_destination=counterfactual,
        rag_query=rag_query,
        matched_traits=matched_traits or ["hiking", "warm", "decision support"],
        feature_profile=feature_profile,
        cheap_usage=LLMUsage(
            model_name=settings.cheap_model_name,
            step="extract_trip_plan",
            tokens_in=_count_tokens(query),
            tokens_out=42,
            cost_usd=0.0,
            used_fallback=True,
        ),
    )


def final_synthesis_usage(text: str) -> LLMUsage:
    """Strong-model accounting for the final synthesis step."""

    settings = get_settings()
    return LLMUsage(
        model_name=settings.strong_model_name,
        step="synthesize_trip_brief",
        tokens_in=_count_tokens(text),
        tokens_out=70,
        cost_usd=0.0,
        used_fallback=True,
    )
