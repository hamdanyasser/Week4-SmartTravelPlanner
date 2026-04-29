"""JSON logging: emits valid JSON + merges extra fields."""

from __future__ import annotations

import io
import json
import logging

from app.logging_config import JsonFormatter, get_logger


def test_json_formatter_emits_required_fields():
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="some.event",
        args=(),
        exc_info=None,
    )
    record.run_id = 7
    record.tool = "classify"

    formatted = JsonFormatter().format(record)
    parsed = json.loads(formatted)
    assert parsed["level"] == "INFO"
    assert parsed["event"] == "some.event"
    assert parsed["logger"] == "test"
    assert parsed["run_id"] == 7
    assert parsed["tool"] == "classify"
    assert parsed["ts"]


def test_logger_adapter_merges_caller_extra():
    buf = io.StringIO()
    handler = logging.StreamHandler(buf)
    handler.setFormatter(JsonFormatter())

    base = logging.getLogger("merge.test")
    base.handlers.clear()
    base.addHandler(handler)
    base.setLevel(logging.INFO)
    base.propagate = False

    log = get_logger("merge.test")
    log.info("agent.start", extra={"run_id": 11, "user_id": None})

    line = buf.getvalue().strip()
    parsed = json.loads(line)
    assert parsed["app"] == "atlasbrief"
    assert parsed["run_id"] == 11
    assert parsed["event"] == "agent.start"
