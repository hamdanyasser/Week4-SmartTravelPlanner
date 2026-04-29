"""Webhook delivery: skipped path + failure isolation."""

from __future__ import annotations

import os

import pytest

from app.config import get_settings
from app.schemas.trip_brief import (
    CounterfactualCard,
    DestinationCandidate,
    DreamFitScore,
    RealityPressureScore,
    TravelStyle,
    TripBriefResponse,
)
from app.webhooks.dispatcher import deliver_discord_webhook


def _sample_brief() -> TripBriefResponse:
    return TripBriefResponse(
        query="test",
        top_pick=DestinationCandidate(
            name="Madeira",
            country="Portugal",
            travel_style=TravelStyle.ADVENTURE,
            dream_fit=DreamFitScore(score=80, matched_traits=["warm"], rationale="ok"),
            reality_pressure=RealityPressureScore(
                score=70, weather_signal="ok", flight_signal="ok", rationale="ok"
            ),
        ),
        final_verdict="A solid pick in tension with budget pressure.",
        counterfactual=CounterfactualCard(obvious_pick="Costa Rica", why_not_chosen="budget"),
    )


@pytest.mark.asyncio
async def test_webhook_skipped_when_disabled():
    """No URL configured + WEBHOOK_ENABLED=false => skipped, never raised."""

    result = await deliver_discord_webhook(_sample_brief())
    assert result.status == "skipped"
    assert result.attempts == 0


@pytest.mark.asyncio
async def test_webhook_failure_is_isolated(monkeypatch):
    """If the URL points at nothing, retries exhaust and we record a failed result."""

    monkeypatch.setenv("WEBHOOK_ENABLED", "true")
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "http://127.0.0.1:9/atlasbrief-test")
    monkeypatch.setenv("WEBHOOK_MAX_ATTEMPTS", "1")
    monkeypatch.setenv("WEBHOOK_TIMEOUT_SECONDS", "0.2")
    get_settings.cache_clear()

    try:
        result = await deliver_discord_webhook(_sample_brief())
    finally:
        # Restore for other tests.
        os.environ["WEBHOOK_ENABLED"] = "false"
        os.environ.pop("DISCORD_WEBHOOK_URL", None)
        get_settings.cache_clear()

    assert result.status == "failed"
    assert result.attempts >= 1
    assert result.error
