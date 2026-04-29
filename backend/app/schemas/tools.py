"""Pydantic schemas for the three allowlisted agent tools."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.schemas.trip_brief import TravelStyle


class ToolError(BaseModel):
    tool_name: str
    message: str
    recoverable: bool = True


class ToolExecutionResult(BaseModel):
    tool_name: str
    ok: bool
    input: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] | None = None
    error: ToolError | None = None


class ClassifyTravelStyleInput(BaseModel):
    query: str = Field(..., min_length=3, max_length=1000)
    destination: str | None = None
    budget_level: int = Field(default=3, ge=1, le=5)
    climate_warmth: int = Field(default=4, ge=1, le=5)
    hiking_score: int = Field(default=5, ge=1, le=5)
    culture_score: int = Field(default=3, ge=1, le=5)
    tourism_level: int = Field(default=3, ge=1, le=5)
    luxury_score: int = Field(default=2, ge=1, le=5)
    family_score: int = Field(default=3, ge=1, le=5)
    safety_score: int = Field(default=5, ge=1, le=5)
    avg_daily_cost_usd: float = Field(default=120, ge=10, le=1000)


class ClassifyTravelStyleOutput(BaseModel):
    predicted_style: TravelStyle
    confidence: float = Field(..., ge=0, le=1)
    probabilities: dict[TravelStyle, float] = Field(default_factory=dict)
    used_fallback: bool = False
    warning: str | None = None


class FetchLiveConditionsInput(BaseModel):
    destination: str = Field(..., min_length=2, max_length=120)
    country: str | None = Field(default=None, max_length=120)
    trip_month: str | None = Field(default=None, max_length=40)
    query: str = Field(..., min_length=3, max_length=1000)


class FetchLiveConditionsOutput(BaseModel):
    destination: str
    weather_signal: str
    flight_signal: str
    pressure_score: float = Field(..., ge=0, le=100)
    used_fallback: bool = False
    warning: str | None = None


class ToolTraceSummary(BaseModel):
    tool: str
    summary: str
