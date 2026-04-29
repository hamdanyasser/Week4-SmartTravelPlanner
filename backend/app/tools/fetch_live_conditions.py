"""Allowlisted live-conditions tool."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

import httpx

from app.cache import TTLCache
from app.config import get_settings
from app.logging_config import get_logger
from app.schemas.tools import FetchLiveConditionsInput, FetchLiveConditionsOutput

TOOL_NAME = "fetch_live_conditions"
log = get_logger(__name__)

DESTINATION_COORDS = {
    "madeira": (32.7607, -16.9595),
    "costa rica": (9.7489, -83.7534),
    "slovenia": (46.1512, 14.9955),
    "azores": (37.7412, -25.6756),
    "canary islands": (28.2916, -16.6291),
}


@lru_cache(maxsize=1)
def _live_conditions_cache() -> TTLCache[FetchLiveConditionsOutput]:
    """One TTL cache per process, sized by the configured weather TTL."""

    settings = get_settings()
    return TTLCache[FetchLiveConditionsOutput](
        ttl_seconds=settings.weather_cache_ttl_seconds,
        max_entries=128,
    )


def reset_live_conditions_cache() -> None:
    """Drop the cached live-conditions TTL store (used by tests)."""

    _live_conditions_cache.cache_clear()


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


async def _fetch_uncached(
    request: FetchLiveConditionsInput,
) -> FetchLiveConditionsOutput:
    """Single network round-trip; isolated so it can sit behind a TTL cache."""

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
    except Exception as exc:
        log.warning(
            "live_conditions.api_failed",
            extra={"destination": request.destination, "exc_class": exc.__class__.__name__},
        )
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


async def fetch_live_conditions(
    payload: FetchLiveConditionsInput | dict[str, Any],
) -> FetchLiveConditionsOutput:
    """Return current weather pressure with TTL caching + deterministic fallback.

    Why cache: weather for the same city within ten minutes is the same answer.
    The brief explicitly says "don't pay the API twice." We key on the
    destination/country/trip_month tuple so unrelated queries don't collide.
    """

    request = (
        payload
        if isinstance(payload, FetchLiveConditionsInput)
        else FetchLiveConditionsInput.model_validate(payload)
    )

    cache = _live_conditions_cache()
    cache_key = (
        "live_conditions",
        request.destination.lower(),
        (request.country or "").lower(),
        (request.trip_month or "").lower(),
    )

    async def _produce() -> FetchLiveConditionsOutput:
        return await _fetch_uncached(request)

    result = await cache.get_or_set(cache_key, _produce)
    log.info(
        "live_conditions.served",
        extra={
            "destination": request.destination,
            "used_fallback": result.used_fallback,
            "cache_hits": cache.hits,
            "cache_misses": cache.misses,
        },
    )
    return result
