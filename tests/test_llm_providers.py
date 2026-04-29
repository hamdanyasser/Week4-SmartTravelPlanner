"""Provider routing: fallback when no key, real call when present."""

from __future__ import annotations

import pytest

from app.config import get_settings
from app.llm.providers import (
    PRICE_TABLE_PER_MTOKENS,
    ProviderUnavailable,
    _cost_usd,
    _resolve_provider,
)
from app.llm.router import try_strong_synthesis


@pytest.mark.asyncio
async def test_try_strong_synthesis_falls_back_when_no_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    get_settings.cache_clear()

    text, usage = await try_strong_synthesis("system", "user")
    assert text is None
    assert usage.used_fallback is True
    assert usage.cost_usd == 0.0
    assert usage.tokens_in > 0


def test_resolve_provider_auto_picks_anthropic_when_key_set(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("CHEAP_MODEL_PROVIDER", "auto")
    monkeypatch.setenv("STRONG_MODEL_PROVIDER", "auto")
    get_settings.cache_clear()

    provider, model = _resolve_provider("strong", get_settings())
    assert provider == "anthropic"
    assert "claude" in model.lower()


def test_resolve_provider_auto_picks_openai_when_only_openai_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("CHEAP_MODEL_PROVIDER", "auto")
    monkeypatch.setenv("STRONG_MODEL_PROVIDER", "auto")
    get_settings.cache_clear()

    provider, model = _resolve_provider("cheap", get_settings())
    assert provider == "openai"
    assert "gpt" in model.lower()


def test_resolve_provider_raises_when_no_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("CHEAP_MODEL_PROVIDER", "auto")
    monkeypatch.setenv("STRONG_MODEL_PROVIDER", "auto")
    get_settings.cache_clear()

    with pytest.raises(ProviderUnavailable):
        _resolve_provider("strong", get_settings())


def test_resolve_provider_explicit_none(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("STRONG_MODEL_PROVIDER", "none")
    get_settings.cache_clear()

    with pytest.raises(ProviderUnavailable):
        _resolve_provider("strong", get_settings())


def test_cost_table_known_models_have_rates():
    """A small smoke test: every model named in Settings has a price row."""

    settings = get_settings()
    for model in [
        settings.anthropic_cheap_model,
        settings.anthropic_strong_model,
        settings.openai_cheap_model,
        settings.openai_strong_model,
    ]:
        assert model in PRICE_TABLE_PER_MTOKENS, f"missing price row for {model}"


def test_cost_usd_zero_for_unknown_model():
    assert _cost_usd("not-a-real-model", 1000, 1000) == 0.0


def test_cost_usd_scales_with_tokens():
    cost_a = _cost_usd("gpt-4o-mini", 1_000_000, 1_000_000)
    cost_b = _cost_usd("gpt-4o-mini", 2_000_000, 2_000_000)
    assert cost_b > cost_a
    assert round(cost_b / cost_a, 2) == 2.0
