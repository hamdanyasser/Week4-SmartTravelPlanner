"""Agent helper: compare two destinations side by side.

We deliberately keep the LangGraph from `graph.py` for the canonical
single-destination pipeline and run a leaner direct flow here. The shape is
the same - plan, three tools per destination, synthesize - but with two
parallel candidate tracks instead of one.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.registry import execute_tool
from app.llm.router import extract_trip_plan, final_synthesis_usage
from app.schemas.compare import CompareDestinationsResponse
from app.schemas.rag import DestinationKnowledgeResponse
from app.schemas.tools import (
    ClassifyTravelStyleOutput,
    FetchLiveConditionsOutput,
    ToolExecutionResult,
)
from app.schemas.trip_brief import (
    DestinationCandidate,
    DreamFitScore,
    RealityPressureScore,
    ToolTraceEntry,
    TravelStyle,
    TripBriefMeta,
)


def _country_for(destination: str) -> str:
    """Best-effort country lookup; the synthesizer is allowed to be imperfect here."""

    table = {
        "madeira": "Portugal",
        "azores": "Portugal",
        "canary islands": "Spain",
        "costa rica": "Costa Rica",
        "slovenia": "Slovenia",
    }
    return table.get(destination.casefold(), "?")


def _summary(result: ToolExecutionResult) -> str:
    if not result.ok:
        return result.error.message if result.error else "tool error"
    output = result.output or {}
    if result.tool_name == "classify_travel_style":
        return f"{output.get('predicted_style', '?')} (confidence {output.get('confidence', 0):.2f})"
    if result.tool_name == "fetch_live_conditions":
        return f"pressure {int(output.get('pressure_score', 0))}/100"
    rag_results = output.get("results") or []
    return f"{len(rag_results)} chunks retrieved"


async def _candidate_for(
    query: str,
    destination: str,
    session: AsyncSession | None,
    ml_model: Any | None,
) -> tuple[DestinationCandidate, list[ToolExecutionResult]]:
    country = _country_for(destination)

    rag_payload = {
        "query": f"{destination} {query}",
        "destinations": [destination],
        "top_k": 3,
    }
    classify_payload = {
        "query": query,
        "destination": destination,
        "budget_level": 3,
        "climate_warmth": 4,
        "hiking_score": 4,
        "culture_score": 3,
        "tourism_level": 3,
        "luxury_score": 2,
        "family_score": 3,
        "safety_score": 5,
        "avg_daily_cost_usd": 130,
    }
    live_payload = {
        "query": query,
        "destination": destination,
        "country": country,
        "trip_month": "July",
    }

    rag_result = await execute_tool(
        "retrieve_destination_knowledge", rag_payload, session=session
    )
    classify_result = await execute_tool(
        "classify_travel_style", classify_payload, ml_model=ml_model
    )
    live_result = await execute_tool("fetch_live_conditions", live_payload)
    tool_results = [rag_result, classify_result, live_result]

    rag = (
        DestinationKnowledgeResponse.model_validate(rag_result.output)
        if rag_result.ok and rag_result.output
        else DestinationKnowledgeResponse(query=destination, used_fallback=True)
    )
    ml = (
        ClassifyTravelStyleOutput.model_validate(classify_result.output)
        if classify_result.ok and classify_result.output
        else ClassifyTravelStyleOutput(
            predicted_style=TravelStyle.ADVENTURE,
            confidence=0.5,
            used_fallback=True,
        )
    )
    live = (
        FetchLiveConditionsOutput.model_validate(live_result.output)
        if live_result.ok and live_result.output
        else FetchLiveConditionsOutput(
            destination=destination,
            weather_signal="No live signal.",
            flight_signal="No flight signal.",
            pressure_score=60,
            used_fallback=True,
        )
    )

    rationale = rag.results[0].content[:240] + "..." if rag.results else (
        f"{destination} fits the brief on the dream side; pressure is moderate."
    )
    dream_score = 80 if rag.results else 70
    matched_traits = ["warm", "hiking"] if "warm" in query.lower() or "hike" in query.lower() else [
        "scenery"
    ]

    candidate = DestinationCandidate(
        name=destination,
        country=country,
        travel_style=ml.predicted_style,
        dream_fit=DreamFitScore(
            score=dream_score,
            matched_traits=matched_traits,
            rationale=rationale,
        ),
        reality_pressure=RealityPressureScore(
            score=live.pressure_score,
            weather_signal=live.weather_signal,
            flight_signal=live.flight_signal,
            rationale=live.warning or "Synthesized from live + fallback signals.",
        ),
    )
    return candidate, tool_results


async def compare_destinations(
    query: str,
    destinations: list[str],
    session: AsyncSession | None = None,
    ml_model: Any | None = None,
) -> CompareDestinationsResponse:
    """Run the agent for both destinations and synthesize a comparison."""

    plan_usage = extract_trip_plan(query).cheap_usage  # cheap-step accounting only
    candidate_a, tools_a = await _candidate_for(query, destinations[0], session, ml_model)
    candidate_b, tools_b = await _candidate_for(query, destinations[1], session, ml_model)

    dream_fit_winner = (
        candidate_a.name if candidate_a.dream_fit.score >= candidate_b.dream_fit.score else candidate_b.name
    )
    reality_winner = (
        candidate_a.name
        if candidate_a.reality_pressure.score >= candidate_b.reality_pressure.score
        else candidate_b.name
    )

    if dream_fit_winner == reality_winner:
        verdict = (
            f"{dream_fit_winner} wins on both axes: stronger dream fit and lower "
            f"reality pressure than {(candidate_b if dream_fit_winner == candidate_a.name else candidate_a).name}."
        )
    else:
        verdict = (
            f"This is a real tradeoff: {dream_fit_winner} is the dream-side pick, "
            f"but {reality_winner} survives the reality check more cleanly. "
            "Pick the dream if you can absorb the booking pressure; pick reality if budget "
            "or weather windows are tight."
        )

    all_tools = tools_a + tools_b
    final_usage = final_synthesis_usage(query + " " + verdict)

    trace = [
        ToolTraceEntry(tool=f"{result.tool_name}({i // 3 + 1})", summary=_summary(result))
        for i, result in enumerate(all_tools)
    ]

    return CompareDestinationsResponse(
        query=query,
        candidates=[candidate_a, candidate_b],
        comparison_verdict=verdict,
        dream_fit_winner=dream_fit_winner,
        reality_pressure_winner=reality_winner,
        tools_used=trace,
        meta=TripBriefMeta(
            tokens_in=plan_usage.tokens_in + final_usage.tokens_in,
            tokens_out=plan_usage.tokens_out + final_usage.tokens_out,
            cost_usd=plan_usage.cost_usd + final_usage.cost_usd,
            latency_ms=0,
            cheap_model=plan_usage.model_name,
            strong_model=final_usage.model_name,
        ),
    )
