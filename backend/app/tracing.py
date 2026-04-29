"""Optional LangSmith tracing wiring.

LangChain reads its tracing config from environment variables. We translate
our typed `Settings` into those env vars at startup so the user only has to
paste `LANGCHAIN_API_KEY` into `backend/.env` and traces start showing up
on smith.langchain.com - no other code changes needed.

When no key is set, this is a no-op.
"""

from __future__ import annotations

import os

from app.config import get_settings
from app.logging_config import get_logger

log = get_logger(__name__)


def configure_langsmith() -> bool:
    """Set the LangChain env vars and return whether tracing is active."""

    settings = get_settings()
    if not settings.langchain_api_key:
        return False

    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
    os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project
    os.environ["LANGCHAIN_ENDPOINT"] = settings.langchain_endpoint
    log.info(
        "langsmith.enabled",
        extra={
            "project": settings.langchain_project,
            "endpoint": settings.langchain_endpoint,
        },
    )
    return True
