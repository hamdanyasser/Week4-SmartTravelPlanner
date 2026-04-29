"""Optional real LLM providers for the cheap/strong routing layer.

The router stays deterministic by default. The moment an `ANTHROPIC_API_KEY`
or `OPENAI_API_KEY` lands in `.env`, this module's `cheap_completion`
and `strong_completion` start returning real model output with real
token-cost accounting; until then they raise `ProviderUnavailable` so
the caller can fall back cleanly.

Why it lives in its own file: the router was already shaped around a
thin "cheap step / strong step" surface, so we keep that intact and
inject *what model speaks* through this provider layer.
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.config import Settings, get_settings


class ProviderUnavailable(RuntimeError):
    """Raised when no real provider is configured for the requested step."""


@dataclass(frozen=True)
class CompletionResult:
    text: str
    model_name: str
    provider: str
    tokens_in: int
    tokens_out: int
    cost_usd: float


# Per-1M-token USD prices for the models above. We hardcode them so
# the per-query cost breakdown in the README is reproducible without
# scraping a pricing page at runtime. Update when the provider does.
PRICE_TABLE_PER_MTOKENS: dict[str, tuple[float, float]] = {
    "claude-haiku-4-5-20251001": (1.0, 5.0),
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-opus-4-7": (15.0, 75.0),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.5, 10.0),
}


def _cost_usd(model: str, tokens_in: int, tokens_out: int) -> float:
    rates = PRICE_TABLE_PER_MTOKENS.get(model)
    if rates is None:
        return 0.0
    in_rate, out_rate = rates
    return round(
        (tokens_in / 1_000_000) * in_rate + (tokens_out / 1_000_000) * out_rate,
        6,
    )


def _resolve_provider(role: str, settings: Settings) -> tuple[str, str]:
    """Return (provider, model_name) for the requested role ('cheap'|'strong')."""

    pref = (
        settings.cheap_model_provider if role == "cheap" else settings.strong_model_provider
    ).lower()
    if pref == "none":
        raise ProviderUnavailable(f"{role}: provider explicitly disabled.")

    if pref == "anthropic":
        if not settings.anthropic_api_key:
            raise ProviderUnavailable(f"{role}: anthropic forced but no key set.")
        model = settings.anthropic_cheap_model if role == "cheap" else settings.anthropic_strong_model
        return "anthropic", model

    if pref == "openai":
        if not settings.openai_api_key:
            raise ProviderUnavailable(f"{role}: openai forced but no key set.")
        model = settings.openai_cheap_model if role == "cheap" else settings.openai_strong_model
        return "openai", model

    # auto: prefer Anthropic if its key is set, else OpenAI.
    if settings.anthropic_api_key:
        model = settings.anthropic_cheap_model if role == "cheap" else settings.anthropic_strong_model
        return "anthropic", model
    if settings.openai_api_key:
        model = settings.openai_cheap_model if role == "cheap" else settings.openai_strong_model
        return "openai", model

    raise ProviderUnavailable(f"{role}: no provider key configured.")


async def _anthropic_completion(
    model: str,
    system: str,
    user: str,
    settings: Settings,
) -> CompletionResult:
    headers = {
        "x-api-key": settings.anthropic_api_key or "",
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    body = {
        "model": model,
        "max_tokens": settings.llm_max_output_tokens,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }
    async with httpx.AsyncClient(timeout=settings.llm_request_timeout_seconds) as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=body,
        )
        response.raise_for_status()
        data = response.json()

    text_blocks = [b.get("text", "") for b in data.get("content", []) if b.get("type") == "text"]
    text = "".join(text_blocks).strip()
    usage = data.get("usage", {}) or {}
    tokens_in = int(usage.get("input_tokens", 0))
    tokens_out = int(usage.get("output_tokens", 0))
    return CompletionResult(
        text=text,
        model_name=model,
        provider="anthropic",
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        cost_usd=_cost_usd(model, tokens_in, tokens_out),
    )


async def _openai_completion(
    model: str,
    system: str,
    user: str,
    settings: Settings,
) -> CompletionResult:
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key or ''}",
        "Content-Type": "application/json",
    }
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "max_tokens": settings.llm_max_output_tokens,
        "temperature": 0.3,
    }
    async with httpx.AsyncClient(timeout=settings.llm_request_timeout_seconds) as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=body,
        )
        response.raise_for_status()
        data = response.json()

    choice = (data.get("choices") or [{}])[0]
    text = (choice.get("message") or {}).get("content", "").strip()
    usage = data.get("usage", {}) or {}
    tokens_in = int(usage.get("prompt_tokens", 0))
    tokens_out = int(usage.get("completion_tokens", 0))
    return CompletionResult(
        text=text,
        model_name=model,
        provider="openai",
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        cost_usd=_cost_usd(model, tokens_in, tokens_out),
    )


async def cheap_completion(system: str, user: str) -> CompletionResult:
    """Cheap-model completion. Raises ProviderUnavailable if no key is set."""

    settings = get_settings()
    provider, model = _resolve_provider("cheap", settings)
    if provider == "anthropic":
        return await _anthropic_completion(model, system, user, settings)
    return await _openai_completion(model, system, user, settings)


async def strong_completion(system: str, user: str) -> CompletionResult:
    """Strong-model completion. Raises ProviderUnavailable if no key is set."""

    settings = get_settings()
    provider, model = _resolve_provider("strong", settings)
    if provider == "anthropic":
        return await _anthropic_completion(model, system, user, settings)
    return await _openai_completion(model, system, user, settings)
