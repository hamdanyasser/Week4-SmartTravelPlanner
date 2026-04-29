"""Explicit allowlist for the AtlasBrief tools."""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.logging_config import get_logger
from app.schemas.rag import DestinationKnowledgeQuery
from app.schemas.tools import (
    ClassifyTravelStyleInput,
    FetchLiveConditionsInput,
    ToolError,
    ToolExecutionResult,
)
from app.tools.classify_travel_style import classify_travel_style
from app.tools.fetch_live_conditions import fetch_live_conditions
from app.tools.retrieve_destination_knowledge import retrieve_destination_knowledge

log = get_logger(__name__)

ToolHandler = Callable[..., Awaitable[Any]]


@dataclass(frozen=True)
class ToolSpec:
    name: str
    input_model: type
    handler: ToolHandler


TOOL_SPECS: dict[str, ToolSpec] = {
    "retrieve_destination_knowledge": ToolSpec(
        name="retrieve_destination_knowledge",
        input_model=DestinationKnowledgeQuery,
        handler=retrieve_destination_knowledge,
    ),
    "classify_travel_style": ToolSpec(
        name="classify_travel_style",
        input_model=ClassifyTravelStyleInput,
        handler=classify_travel_style,
    ),
    "fetch_live_conditions": ToolSpec(
        name="fetch_live_conditions",
        input_model=FetchLiveConditionsInput,
        handler=fetch_live_conditions,
    ),
}

ALLOWED_TOOL_NAMES = frozenset(TOOL_SPECS.keys())


async def execute_tool(
    tool_name: str,
    payload: dict[str, Any],
    session: AsyncSession | None = None,
    ml_model: Any | None = None,
) -> ToolExecutionResult:
    """Validate and run an allowlisted tool.

    Any exception becomes a structured recoverable error so the agent can still
    return a user-facing brief.
    """

    if tool_name not in TOOL_SPECS:
        log.warning(
            "tool.refused",
            extra={"tool": tool_name, "reason": "not_in_allowlist"},
        )
        return ToolExecutionResult(
            tool_name=tool_name,
            ok=False,
            input=payload,
            error=ToolError(
                tool_name=tool_name,
                message="Tool is not in the explicit allowlist.",
            ),
        )

    spec = TOOL_SPECS[tool_name]
    started = time.perf_counter()
    try:
        request = spec.input_model.model_validate(payload)
        if tool_name == "retrieve_destination_knowledge":
            output = await spec.handler(request, session=session)
        elif tool_name == "classify_travel_style":
            output = await spec.handler(request, model=ml_model)
        else:
            output = await spec.handler(request)
        latency_ms = int((time.perf_counter() - started) * 1000)
        log.info("tool.ok", extra={"tool": tool_name, "latency_ms": latency_ms})
        return ToolExecutionResult(
            tool_name=tool_name,
            ok=True,
            input=request.model_dump(mode="json"),
            output=output.model_dump(mode="json"),
        )
    except Exception as exc:
        latency_ms = int((time.perf_counter() - started) * 1000)
        log.warning(
            "tool.error",
            extra={
                "tool": tool_name,
                "latency_ms": latency_ms,
                "exc_class": exc.__class__.__name__,
                "exc": str(exc)[:300],
            },
        )
        return ToolExecutionResult(
            tool_name=tool_name,
            ok=False,
            input=payload,
            error=ToolError(
                tool_name=tool_name,
                message=f"{exc.__class__.__name__}: {exc}",
            ),
        )
