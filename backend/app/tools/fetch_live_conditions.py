"""Allowlisted live-conditions tool."""

from __future__ import annotations

from typing import Any

import httpx

from app.config import get_settings
from app.schemas.tools import FetchLiveConditionsInput, FetchLiveConditionsOutput

TOOL_NAME = "fetch_live_conditions"

DESTINATION_COORDS = {
    "madeira": (32.7607, -16.9595),
    "costa rica": (9.7489, -83.7534),
    "slovenia": (46.1512, 14.9955),
    "azores": (37.7412, -25.6756),
    "canary islands": (28.2916, -16.6291),
}


def fallback_live_conditions(payload: FetchLiveConditionsInput) -> FetchLiveConditionsOutput:
    """Deterministic fallback used when no live weather path is configured."""

    destination = payload.destination.lower()
    if "costa rica" in destination:
        return FetchLiveConditionsOutput(
            destination=payload.destination,
            weather_signal="Green season: warm, humid, with frequent afternoon rain.",
            flight_signal="Budget pressure is high for a two-week July trip.",
            pressure_score=48,
            used_fallback=True,
            warning="Live weather disabled or unavailable; used deterministic Costa Rica fallback.",
        )
    if "madeira" in destination:
        return FetchLiveConditionsOutput(
            destination=payload.destination,
            weather_signal="Typically stable July weather: warm, dry, and hiking-friendly.",
            flight_signal="Flights can fit the budget when booked several weeks ahead.",
            pressure_score=74,
            used_fallback=True,
            warning="Live weather disabled or unavailable; used deterministic Madeira fallback.",
        )
    return FetchLiveConditionsOutput(
        destination=payload.destination,
        weather_signal="Seasonal conditions look workable, but confirm close to booking.",
        flight_signal="Flight pressure depends on origin and booking timing.",
        pressure_score=62,
        used_fallback=True,
        warning="Live weather disabled or unavailable; used generic fallback.",
    )


async def fetch_live_conditions(
    payload: FetchLiveConditionsInput | dict[str, Any],
) -> FetchLiveConditionsOutput:
    """Return current weather pressure with deterministic fallback."""

    request = (
        payload
        if isinstance(payload, FetchLiveConditionsInput)
        else FetchLiveConditionsInput.model_validate(payload)
    )
    settings = get_settings()
    if not settings.weather_live_enabled:
        return fallback_live_conditions(request)

    coords = DESTINATION_COORDS.get(request.destination.lower())
    if coords is None:
        return fallback_live_conditions(request)

    latitude, longitude = coords
    try:
        async with httpx.AsyncClient(timeout=settings.weather_timeout_seconds) as client:
            response = await client.get(
                settings.weather_api_base_url,
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "current": "temperature_2m,wind_speed_10m,precipitation",
                },
            )
            response.raise_for_status()
            data = response.json()
    except Exception:
        return fallback_live_conditions(request)

    current = data.get("current", {})
    temp = current.get("temperature_2m")
    wind = current.get("wind_speed_10m")
    rain = current.get("precipitation", 0)
    pressure = 78
    if rain and float(rain) > 0:
        pressure -= 18
    if wind and float(wind) > 25:
        pressure -= 10

    return FetchLiveConditionsOutput(
        destination=request.destination,
        weather_signal=f"Current weather: {temp}C, wind {wind} km/h, precipitation {rain} mm.",
        flight_signal="Live flight pricing is not connected yet; using booking-timing heuristic.",
        pressure_score=max(0, min(100, pressure)),
        used_fallback=False,
        warning="Weather is live; flights remain heuristic until the flight API phase.",
    )
