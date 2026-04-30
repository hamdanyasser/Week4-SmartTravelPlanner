"""LangSmith tracing wiring: opt-in via env var, no-op otherwise."""

from __future__ import annotations

import os

from app.config import get_settings
from app.tracing import configure_langsmith


def test_configure_langsmith_no_op_when_no_key(monkeypatch):
    monkeypatch.delenv("LANGCHAIN_API_KEY", raising=False)
    monkeypatch.delenv("LANGCHAIN_TRACING_V2", raising=False)
    get_settings.cache_clear()

    active = configure_langsmith()
    assert active is False
    # We must not have set the v2 flag if the key is missing.
    assert os.environ.get("LANGCHAIN_TRACING_V2") in (None, "false", "")


def test_configure_langsmith_sets_envs_when_key_present(monkeypatch):
    monkeypatch.setenv("LANGCHAIN_API_KEY", "ls__test_key")
    monkeypatch.setenv("LANGCHAIN_PROJECT", "atlas-test")
    get_settings.cache_clear()

    active = configure_langsmith()
    assert active is True
    assert os.environ["LANGCHAIN_TRACING_V2"] == "true"
    assert os.environ["LANGCHAIN_API_KEY"] == "ls__test_key"
    assert os.environ["LANGCHAIN_PROJECT"] == "atlas-test"

    # Clean up so the assertion in the previous test isn't polluted on reorder.
    for key in (
        "LANGCHAIN_TRACING_V2",
        "LANGCHAIN_API_KEY",
        "LANGCHAIN_PROJECT",
        "LANGCHAIN_ENDPOINT",
    ):
        os.environ.pop(key, None)
