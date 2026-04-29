"""Schemas for deterministic LLM-routing fallback."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class LLMUsage(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    model_name: str
    step: str
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    used_fallback: bool = True


class TripPlan(BaseModel):
    query: str
    destination: str = "Madeira"
    country: str = "Portugal"
    counterfactual_destination: str = "Costa Rica"
    counterfactual_reason: str = (
        "It matches the rainforest adventure dream, but budget and July weather "
        "pressure are higher."
    )
    rag_query: str = "Madeira warm levada island hiking less touristy"
    matched_traits: list[str] = Field(default_factory=list)
    feature_profile: dict[str, float | int] = Field(default_factory=dict)
    cheap_usage: LLMUsage
