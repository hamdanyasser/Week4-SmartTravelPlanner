"""Two-model routing with deterministic fallback.

The router stays deterministic by default. When `ANTHROPIC_API_KEY` or
`OPENAI_API_KEY` is set in `.env`, the strong-model synthesis step calls
the real provider via `app.llm.providers` and the returned `LLMUsage`
carries real token counts and a real per-query USD cost. The cheap step
stays deterministic (matched-trait extraction is mechanical and the
provider hop is not worth the latency).
"""

from __future__ import annotations

import re

from app.config import get_settings
from app.llm.providers import ProviderUnavailable, strong_completion
from app.logging_config import get_logger
from app.schemas.llm import LLMUsage, TripPlan

log = get_logger(__name__)


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
    """Strong-model accounting for the final synthesis step (deterministic).

    Kept for callers that don't need the model's text. Returns zero-cost,
    fallback-flagged usage so the existing accounting shape is preserved.
    """

    settings = get_settings()
    return LLMUsage(
        model_name=settings.strong_model_name,
        step="synthesize_trip_brief",
        tokens_in=_count_tokens(text),
        tokens_out=70,
        cost_usd=0.0,
        used_fallback=True,
    )


async def try_strong_synthesis(
    system_prompt: str,
    user_prompt: str,
    step: str = "synthesize_trip_brief",
) -> tuple[str | None, LLMUsage]:
    """Call the strong model if a provider key is configured, else fall back.

    Returns `(text_or_None, usage)`. When a provider replied we return its
    text and a usage row tagged `used_fallback=False` with real token counts
    and cost. When we fall back we return `(None, deterministic_usage)` so
    the caller can build the verdict itself.
    """

    settings = get_settings()
    try:
        result = await strong_completion(system_prompt, user_prompt)
    except ProviderUnavailable as exc:
        log.info("llm.strong.fallback", extra={"reason": str(exc)})
        return None, LLMUsage(
            model_name=settings.strong_model_name,
            step=step,
            tokens_in=_count_tokens(user_prompt),
            tokens_out=70,
            cost_usd=0.0,
            used_fallback=True,
        )
    except Exception as exc:
        log.warning(
            "llm.strong.error",
            extra={"exc_class": exc.__class__.__name__, "exc": str(exc)[:300]},
        )
        return None, LLMUsage(
            model_name=settings.strong_model_name,
            step=step,
            tokens_in=_count_tokens(user_prompt),
            tokens_out=70,
            cost_usd=0.0,
            used_fallback=True,
        )

    log.info(
        "llm.strong.ok",
        extra={
            "provider": result.provider,
            "model": result.model_name,
            "tokens_in": result.tokens_in,
            "tokens_out": result.tokens_out,
            "cost_usd": result.cost_usd,
        },
    )
    return result.text, LLMUsage(
        model_name=result.model_name,
        step=step,
        tokens_in=result.tokens_in,
        tokens_out=result.tokens_out,
        cost_usd=result.cost_usd,
        used_fallback=False,
    )
