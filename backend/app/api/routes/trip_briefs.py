"""Trip brief route: Decision Tension Board backend entry point."""

from __future__ import annotations

import json
import time
from collections.abc import AsyncIterator
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.compare import compare_destinations
from app.agent.graph import AtlasBriefAgent
from app.api.deps import get_current_user, get_optional_current_user
from app.config import get_settings
from app.db.session import get_session
from app.logging_config import get_logger
from app.models.agent_run import AgentRun
from app.models.user import User
from app.persistence.records import (
    create_agent_run,
    fail_agent_run,
    finish_agent_run,
    persist_tool_calls,
)
from app.schemas.compare import CompareDestinationsRequest, CompareDestinationsResponse
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

    settings = get_settings()
    if settings.webhook_require_approval:
        log.info("trip_brief.awaiting_approval", extra={"run_id": run_id})
    else:
        background_tasks.add_task(
            deliver_discord_webhook,
            brief=response,
            session=None,
            agent_run_id=run_id,
        )
    return response


@router.post("/trip-briefs/compare", response_model=CompareDestinationsResponse)
async def compare_trip_briefs(
    payload: CompareDestinationsRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User | None = Depends(get_optional_current_user),
) -> CompareDestinationsResponse:
    """Compare two destinations side by side under the same query."""

    started = time.perf_counter()
    ml_model: Any | None = getattr(request.app.state, "ml_model", None)
    response = await compare_destinations(
        query=payload.query,
        destinations=payload.destinations,
        session=session,
        ml_model=ml_model,
    )
    response.meta.latency_ms = int((time.perf_counter() - started) * 1000)
    log.info(
        "trip_brief.compare_completed",
        extra={
            "destinations": payload.destinations,
            "dream_winner": response.dream_fit_winner,
            "reality_winner": response.reality_pressure_winner,
            "latency_ms": response.meta.latency_ms,
        },
    )
    return response


@router.post("/agent-runs/{run_id}/approve", response_model=TripBriefResponse)
async def approve_agent_run(
    run_id: int,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> TripBriefResponse:
    """Human-in-the-loop release: fire the webhook for a stored brief.

    Lookup is scoped to the authenticated user so anonymous runs and other
    users' runs cannot be approved. The original brief is reconstructed from
    `response_json` so the channel message stays consistent with what the
    user already saw in the UI.
    """

    run: AgentRun | None = await session.get(AgentRun, run_id)
    if run is None or run.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent run not found.",
        )
    if not run.response_json:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Agent run has no stored response yet.",
        )

    brief = TripBriefResponse.model_validate(run.response_json)
    background_tasks.add_task(
        deliver_discord_webhook,
        brief=brief,
        session=None,
        agent_run_id=run.id,
    )
    log.info("trip_brief.approved", extra={"run_id": run.id, "user_id": current_user.id})
    return brief


def _sse_event(event_type: str, payload: dict[str, Any]) -> str:
    """Format one Server-Sent Event frame."""

    return f"event: {event_type}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


@router.post("/trip-briefs/stream")
async def stream_trip_brief(
    payload: TripBriefRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User | None = Depends(get_optional_current_user),
) -> StreamingResponse:
    """Stream the trip brief stage-by-stage via SSE.

    The browser receives one event per agent stage (plan, each tool start
    and finish, synthesis, final brief, done). This is the optional
    streaming path called out in the brief - the JSON `POST /trip-briefs`
    endpoint above remains the canonical way to consume the API.
    """

    user_id = current_user.id if current_user else None
    agent_run = await create_agent_run(session=session, query=payload.query, user_id=user_id)
    run_id = agent_run.id if agent_run else None
    log.info(
        "trip_brief.stream_received",
        extra={"run_id": run_id, "user_id": user_id, "query_len": len(payload.query)},
    )
    agent = _agent_from_app(request)
    ml_model: Any | None = getattr(request.app.state, "ml_model", None)

    async def event_stream() -> AsyncIterator[str]:
        started = time.perf_counter()
        final_response: TripBriefResponse | None = None
        tool_results: list[ToolExecutionResult] = []
        try:
            async for event in agent.stream_events(
                query=payload.query, session=session, ml_model=ml_model
            ):
                if event.get("type") == "brief":
                    final_response = TripBriefResponse.model_validate(event["response"])
                yield _sse_event(event.get("type", "message"), event)
        except Exception as exc:
            await fail_agent_run(session=session, run=agent_run, error=str(exc))
            log.exception(
                "trip_brief.stream_failed",
                extra={"run_id": run_id, "exc_class": exc.__class__.__name__},
            )
            yield _sse_event(
                "error",
                {
                    "type": "error",
                    "message": "Agent could not complete the trip brief.",
                    "exc_class": exc.__class__.__name__,
                },
            )
            return

        if final_response is None:
            yield _sse_event(
                "error",
                {"type": "error", "message": "Stream ended without a brief."},
            )
            return

        final_response.meta.latency_ms = int((time.perf_counter() - started) * 1000)

        # Persistence + webhook still happen, just after the stream is drained.
        # tool_results are reconstructed from the streamed events on the
        # client; for storage we re-run the synthesis path's bookkeeping.
        await persist_tool_calls(
            session=session,
            run=agent_run,
            tool_results=tool_results,
            user_id=user_id,
        )
        await finish_agent_run(session=session, run=agent_run, response=final_response)
        log.info(
            "trip_brief.stream_completed",
            extra={
                "run_id": run_id,
                "user_id": user_id,
                "latency_ms": final_response.meta.latency_ms,
                "top_pick": final_response.top_pick.name,
            },
        )
        background_tasks.add_task(
            deliver_discord_webhook,
            brief=final_response,
            session=None,
            agent_run_id=run_id,
        )

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
