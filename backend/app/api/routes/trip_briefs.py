"""Trip brief route: Decision Tension Board backend entry point."""

from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.graph import AtlasBriefAgent
from app.api.deps import get_optional_current_user
from app.db.session import get_session, get_session_factory
from app.logging_config import get_logger
from app.models.user import User
from app.persistence.records import (
    create_agent_run,
    fail_agent_run,
    finish_agent_run,
    persist_tool_calls,
)
from app.schemas.tools import ToolExecutionResult
from app.schemas.trip_brief import TripBriefRequest, TripBriefResponse
from app.webhooks.dispatcher import deliver_discord_webhook

router = APIRouter(tags=["trip-briefs"])
log = get_logger(__name__)


def _agent_from_app(request: Request) -> AtlasBriefAgent:
    agent = getattr(request.app.state, "agent", None)
    if isinstance(agent, AtlasBriefAgent):
        return agent
    return AtlasBriefAgent()


async def _deliver_webhook_with_session(
    brief: TripBriefResponse,
    agent_run_id: int | None,
) -> None:
    """Deliver a webhook with a fresh DB session for delivery logging."""

    session_factory = get_session_factory()
    async with session_factory() as webhook_session:
        await deliver_discord_webhook(
            brief=brief,
            session=webhook_session,
            agent_run_id=agent_run_id,
        )


@router.post("/trip-briefs", response_model=TripBriefResponse)
async def create_trip_brief(
    payload: TripBriefRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User | None = Depends(get_optional_current_user),
) -> TripBriefResponse:
    """Generate a Decision Tension Board with safe fallbacks.

    Persistence and webhook delivery are best-effort. A database or webhook
    outage must not prevent the user from receiving a brief. The agent itself
    is the only mandatory path - if it raises, we surface a 500 honestly
    rather than silently returning a hand-picked stub.
    """

    user_id = current_user.id if current_user else None
    agent_run = await create_agent_run(session=session, query=payload.query, user_id=user_id)
    run_id = agent_run.id if agent_run else None
    log.info(
        "trip_brief.received",
        extra={"run_id": run_id, "user_id": user_id, "query_len": len(payload.query)},
    )
    agent = _agent_from_app(request)
    ml_model: Any | None = getattr(request.app.state, "ml_model", None)

    started = time.perf_counter()
    tool_results: list[ToolExecutionResult] = []
    try:
        state = await agent.run_state(
            query=payload.query,
            session=session,
            ml_model=ml_model,
        )
        response = state["response"]
        tool_results = state.get("tool_results", [])
    except Exception as exc:
        await fail_agent_run(session=session, run=agent_run, error=str(exc))
        log.exception(
            "trip_brief.agent_failed",
            extra={"run_id": run_id, "exc_class": exc.__class__.__name__},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Agent could not complete the trip brief.",
        ) from exc

    response.meta.latency_ms = int((time.perf_counter() - started) * 1000)

    await persist_tool_calls(
        session=session,
        run=agent_run,
        tool_results=tool_results,
        user_id=user_id,
    )
    await finish_agent_run(session=session, run=agent_run, response=response)

    log.info(
        "trip_brief.completed",
        extra={
            "run_id": run_id,
            "user_id": user_id,
            "latency_ms": response.meta.latency_ms,
            "tokens_in": response.meta.tokens_in,
            "tokens_out": response.meta.tokens_out,
            "cost_usd": response.meta.cost_usd,
            "tools": [r.tool_name for r in tool_results],
            "tool_errors": [r.tool_name for r in tool_results if not r.ok],
            "top_pick": response.top_pick.name,
        },
    )

    background_tasks.add_task(
        _deliver_webhook_with_session,
        response,
        run_id,
    )
    return response
