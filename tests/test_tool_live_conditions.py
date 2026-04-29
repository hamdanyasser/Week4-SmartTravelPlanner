"""fetch_live_conditions tool — fallback path, cache hit/miss."""

from __future__ import annotations

import pytest

from app.tools.fetch_live_conditions import (
    _live_conditions_cache,
    fetch_live_conditions,
    reset_live_conditions_cache,
)


@pytest.mark.asyncio
async def test_live_conditions_uses_fallback_when_disabled():
    payload = {
        "query": "Two warm hiking weeks in July",
        "destination": "Madeira",
        "country": "Portugal",
        "trip_month": "July",
    }
    result = await fetch_live_conditions(payload)
    assert result.used_fallback is True
    assert 0 <= result.pressure_score <= 100
    assert "Madeira" in result.weather_signal or "Madeira" in result.warning


@pytest.mark.asyncio
async def test_live_conditions_caches_repeated_calls():
    reset_live_conditions_cache()
    payload = {
        "query": "Costa Rica green-season trip",
        "destination": "Costa Rica",
        "country": "CR",
        "trip_month": "July",
    }
    await fetch_live_conditions(payload)
    await fetch_live_conditions(payload)
    cache = _live_conditions_cache()
    assert cache.misses == 1
    assert cache.hits == 1


@pytest.mark.asyncio
async def test_live_conditions_invalid_payload_raises():
    """The schema is the boundary — bad input must not be silently accepted."""

    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        await fetch_live_conditions({"query": "no destination here"})


@pytest.mark.asyncio
async def test_live_conditions_unknown_destination_falls_back():
    result = await fetch_live_conditions(
        {
            "query": "hiking somewhere remote",
            "destination": "Atlantis",
            "country": "??",
            "trip_month": "July",
        }
    )
    assert result.used_fallback is True
    assert "fallback" in (result.warning or "").lower()
