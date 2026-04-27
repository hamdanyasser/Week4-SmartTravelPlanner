"""Trip briefs route — the entry point for the Decision Tension Board.

Day 1: returns a hardcoded golden-demo response so the frontend can be
built against a stable contract.

From Day 6 onward this handler will:
  - persist the request as an `agent_run` row scoped to the current user
  - invoke the LangGraph agent (with its three allowed tools)
  - stream the synthesized verdict back to the client
  - fire the webhook in the background
"""

from fastapi import APIRouter

from app.schemas.trip_brief import (
    TripBriefRequest,
    TripBriefResponse,
    example_stub_response,
)

router = APIRouter(tags=["trip-briefs"])


@router.post("/trip-briefs", response_model=TripBriefResponse)
async def create_trip_brief(payload: TripBriefRequest) -> TripBriefResponse:
    """Generate a Decision Tension Board for the given query.

    Day 1 stub: ignores the query content and returns the golden-demo
    payload. The point is to exercise the request/response shape end-to-end
    so the React frontend has something real to render.
    """
    stub = example_stub_response(payload.query)
    return TripBriefResponse.model_validate(stub)
