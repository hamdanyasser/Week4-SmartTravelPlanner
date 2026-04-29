"""Best-effort persistence for agent runs and tool calls."""

from __future__ import annotations

from contextlib import suppress
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_run import AgentRun
from app.models.tool_call import ToolCall
from app.schemas.tools import ToolExecutionResult
from app.schemas.trip_brief import TripBriefResponse

UTC = timezone.utc


async def _safe_rollback(session: AsyncSession) -> None:
    with suppress(Exception):
        await session.rollback()


async def create_agent_run(
    session: AsyncSession | None,
    query: str,
    user_id: int | None = None,
) -> AgentRun | None:
    """Create an agent run row; return None if DB is unavailable."""

    if session is None:
        return None
    try:
        run = AgentRun(user_id=user_id, query=query, status="started")
        session.add(run)
        await session.commit()
        await session.refresh(run)
        return run
    except Exception:
        await _safe_rollback(session)
        return None


async def fail_agent_run(
    session: AsyncSession | None,
    run: AgentRun | None,
    error: str,
) -> None:
    """Mark a run as failed; never raise into the user path."""

    if session is None or run is None:
        return
    try:
        run.status = "failed"
        run.error = error[:2000]
        run.completed_at = datetime.now(UTC)
        await session.commit()
    except Exception:
        await _safe_rollback(session)


async def finish_agent_run(
    session: AsyncSession | None,
    run: AgentRun | None,
    response: TripBriefResponse,
) -> None:
    """Persist final response JSON if possible."""

    if session is None or run is None:
        return
    try:
        run.status = "completed"
        run.response_json = response.model_dump(mode="json")
        run.tokens_in = response.meta.tokens_in
        run.tokens_out = response.meta.tokens_out
        run.cost_usd = response.meta.cost_usd
        run.completed_at = datetime.now(UTC)
        await session.commit()
    except Exception:
        await _safe_rollback(session)


async def persist_tool_calls(
    session: AsyncSession | None,
    run: AgentRun | None,
    tool_results: list[ToolExecutionResult],
    user_id: int | None = None,
) -> None:
    """Store tool calls without letting DB failure affect the response."""

    if session is None or run is None:
        return
    try:
        for result in tool_results:
            session.add(
                ToolCall(
                    agent_run_id=run.id,
                    user_id=user_id,
                    tool_name=result.tool_name,
                    status="ok" if result.ok else "error",
                    input_json=result.input,
                    output_json=result.output,
                    error=result.error.message if result.error else None,
                )
            )
        await session.commit()
    except Exception:
        await _safe_rollback(session)
