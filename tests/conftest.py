"""Pytest fixtures and environment setup for AtlasBrief tests.

These tests do not touch Postgres, Discord, or any real LLM. They cover:
  - Pydantic schema validation (valid + invalid)
  - Each tool in isolation, with a stub model and mocked HTTP
  - One end-to-end agent run with deterministic fallbacks
  - Auth helpers, webhook failure isolation, caching, logging

The brief calls for "at least the critical path." That is what we cover.
"""

from __future__ import annotations

import os
import secrets
import sys
from pathlib import Path

# Make `app.*` importable without installing the backend as a package.
BACKEND_ROOT = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Set required environment variables before any `app.*` import below.
os.environ.setdefault("JWT_SECRET_KEY", secrets.token_urlsafe(32))
os.environ.setdefault("DISCORD_WEBHOOK_URL", "")
os.environ.setdefault("WEBHOOK_ENABLED", "false")
os.environ.setdefault("WEBHOOK_MAX_ATTEMPTS", "1")
os.environ.setdefault("WEBHOOK_TIMEOUT_SECONDS", "0.2")
os.environ.setdefault("WEATHER_LIVE_ENABLED", "false")
os.environ.setdefault("APP_DEBUG", "false")

import pytest  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.tools.fetch_live_conditions import reset_live_conditions_cache  # noqa: E402


@pytest.fixture(autouse=True)
def _isolate_caches() -> None:
    """Clear TTL caches between tests so cache stats start at zero."""

    reset_live_conditions_cache()
    get_settings.cache_clear()


@pytest.fixture
def settings():
    """Return the (cached) Settings singleton for assertions."""

    return get_settings()
