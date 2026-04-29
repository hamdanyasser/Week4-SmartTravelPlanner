"""Structured JSON logging for AtlasBrief.

The brief calls out: "Logging with structlog or the stdlib's logger configured
for JSON - no print statements." We pick the stdlib path to keep the
dependency tree small. Every record is emitted as one JSON object on stdout.

Usage:

    from app.logging_config import configure_logging, get_logger
    configure_logging()
    log = get_logger(__name__)
    log.info("agent_run.started", extra={"run_id": 7, "user_id": None})

The `extra=` dict is merged into the JSON record at the top level so log
aggregators (SEQ, Loki, Better Stack) can filter on those fields without
parsing the message.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

_RESERVED_LOG_RECORD_KEYS = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "message",
    "module",
    "msecs",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
    "taskName",
}


class JsonFormatter(logging.Formatter):
    """Emit one JSON object per log record."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_type"] = record.exc_info[0].__name__ if record.exc_info[0] else None
            payload["exc_message"] = str(record.exc_info[1]) if record.exc_info[1] else None
            payload["exc_traceback"] = self.formatException(record.exc_info)

        for key, value in record.__dict__.items():
            if key in _RESERVED_LOG_RECORD_KEYS or key.startswith("_"):
                continue
            try:
                json.dumps(value)
                safe_value = value
            except (TypeError, ValueError):
                safe_value = repr(value)
            payload[key] = safe_value

        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging(level: str = "INFO") -> None:
    """Install the JSON formatter on the root logger.

    Idempotent: calling it twice replaces the handler instead of stacking
    duplicates. We aim at stdout because container runtimes (Docker, Fly,
    Railway) collect stdout into their logging plane for free.
    """

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())

    for noisy in ("uvicorn.access", "httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


class _MergingAdapter(logging.LoggerAdapter):
    """LoggerAdapter that merges its baseline `extra` with the caller's."""

    def process(
        self,
        msg: str,
        kwargs: dict[str, Any],
    ) -> tuple[str, dict[str, Any]]:
        merged: dict[str, Any] = dict(self.extra or {})
        caller_extra = kwargs.get("extra") or {}
        merged.update(caller_extra)
        kwargs["extra"] = merged
        return msg, kwargs


def get_logger(name: str) -> logging.LoggerAdapter:
    """Return a logger that always carries an `app=atlasbrief` field."""

    return _MergingAdapter(logging.getLogger(name), {"app": "atlasbrief"})
