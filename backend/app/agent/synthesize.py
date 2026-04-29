"""Turn tool results into the existing TripBriefResponse contract."""

from __future__ import annotations

from app.llm.router import try_strong_synthesis
from app.schemas.llm import TripPlan
from app.schemas.rag import DestinationKnowledgeResponse
from app.schemas.tools import (
    ClassifyTravelStyleOutput,
    FetchLiveConditionsOutput,
    ToolExecutionResult,
)
from app.schemas.trip_brief import (
    CounterfactualCard,
    DestinationCandidate,
    DreamFitScore,
    RealityPressureScore,
    ToolTraceEntry,
    TravelStyle,
    TripBriefMeta,
    TripBriefResponse,
)

SYNTHESIS_SYSTEM_PROMPT = (
    "You are AtlasBrief, an executive-style travel briefing agent. "
    "Given a user query and three tool outputs (RAG evidence, ML travel-style "
    "classification, live conditions), return ONE paragraph (max 90 words) "
    "that names the tradeoff between the dream side (RAG + ML) and the "
    "reality side (weather + flights). Be concrete and decisive; never "
    "hedge with 'might' or 'could'."
)


def _tool_output(
    results: list[ToolExecutionResult],
    tool_name: str,
) -> dict | None:
    for result in results:
        if result.tool_name == tool_name and result.ok:
            return result.output
    return None


def _summarize_tool(result: ToolExecutionResult) -> str:
    """Produce a per-tool human summary the timeline and Evidence drawer can show."""

    if not result.ok:
        return result.error.message if result.error else "unknown error"

    output = result.output or {}

    if result.tool_name == "retrieve_destination_knowledge":
        rag_results = output.get("results") or []
        used_fallback = output.get("used_fallback", False)
        if rag_results:
            top = rag_results[0]
            destinations = sorted({row.get("destination", "?") for row in rag_results})
            label = ", ".join(destinations[:3])
            mode = "local fallback" if used_fallback else "pgvector"
            return (
                f"{len(rag_results)} chunks via {mode}; top: {top.get('destination', '?')} "
                f"({top.get('source_title', 'source')}); covered: {label}"
            )
        return "No RAG chunks matched; using deterministic narrative fallback."

    if result.tool_name == "classify_travel_style":
        style = output.get("predicted_style", "?")
        confidence = output.get("confidence", 0.0)
        used_fallback = output.get("used_fallback", False)
        mode = "rule fallback" if used_fallback else "joblib model"
        return f"Predicted {style} ({mode}, confidence {float(confidence):.2f})"

    if result.tool_name == "fetch_live_conditions":
        pressure = output.get("pressure_score", 0)
        weather = output.get("weather_signal", "")
        used_fallback = output.get("used_fallback", False)
        mode = "deterministic fallback" if used_fallback else "live weather"
        return f"Pressure {int(pressure)}/100 ({mode}); {weather}"

    return "completed"


def _trace(results: list[ToolExecutionResult]) -> list[ToolTraceEntry]:
    return [
        ToolTraceEntry(tool=result.tool_name, summary=_summarize_tool(result))
        for result in results
    ]


def _build_synthesis_user_prompt(
    query: str,
    plan: TripPlan,
    rag: DestinationKnowledgeResponse,
    ml: ClassifyTravelStyleOutput,
    live: FetchLiveConditionsOutput,
) -> str:
    """Compact user prompt for the strong synthesis step."""

    rag_snippet = (rag.results[0].content[:400] + "...") if rag.results else "no rag evidence"
    return (
        f"Query: {query}\n"
        f"Pick: {plan.destination} ({plan.country}). Counterfactual: {plan.counterfactual_destination}.\n"
        f"Matched traits: {', '.join(plan.matched_traits) or 'none'}.\n"
        f"RAG evidence: {rag_snippet}\n"
        f"ML predicted travel style: {ml.predicted_style.value} (confidence {ml.confidence:.2f}, "
        f"used_fallback={ml.used_fallback}).\n"
        f"Live weather: {live.weather_signal}\n"
        f"Live flights: {live.flight_signal}\n"
        f"Pressure score: {int(live.pressure_score)}/100 (used_fallback={live.used_fallback}).\n"
        "Write ONE paragraph naming the dream-vs-reality tradeoff and a clear recommendation."
    )


async def synthesize_trip_brief(
    query: str,
    plan: TripPlan,
    tool_results: list[ToolExecutionResult],
) -> TripBriefResponse:
    """Create the Decision Tension Board from tool outputs.

    Uses the real strong-model provider if a key is set; otherwise emits the
    deterministic verdict so local demos never depend on network calls.
    """

    rag_raw = _tool_output(tool_results, "retrieve_destination_knowledge")
    ml_raw = _tool_output(tool_results, "classify_travel_style")
    live_raw = _tool_output(tool_results, "fetch_live_conditions")

    rag = (
        DestinationKnowledgeResponse.model_validate(rag_raw)
        if rag_raw
        else DestinationKnowledgeResponse(
            query=plan.rag_query,
            used_fallback=True,
            message="RAG tool failed; using deterministic narrative fallback.",
        )
    )
    ml = (
        ClassifyTravelStyleOutput.model_validate(ml_raw)
        if ml_raw
        else ClassifyTravelStyleOutput(
            predicted_style=TravelStyle.ADVENTURE,
            confidence=0.5,
            used_fallback=True,
            warning="ML tool failed; used Adventure fallback.",
        )
    )
    live = (
        FetchLiveConditionsOutput.model_validate(live_raw)
        if live_raw
        else FetchLiveConditionsOutput(
            destination=plan.destination,
            weather_signal="Conditions require confirmation before booking.",
            flight_signal="Flight pressure depends on booking timing.",
            pressure_score=60,
            used_fallback=True,
            warning="Live tool failed; used generic fallback.",
        )
    )

    evidence = rag.results[0].content if rag.results else ""
    dream_score = 86 if plan.destination == "Madeira" else 75
    if ml.predicted_style != TravelStyle.ADVENTURE:
        dream_score -= 8

    rationale = (
        "RAG evidence points to warm island hiking, quieter northern/interior "
        "routes, and manageable logistics."
    )
    if evidence:
        rationale = evidence[:260].rstrip() + "..."

    user_prompt = _build_synthesis_user_prompt(query, plan, rag, ml, live)
    provider_text, final_usage = await try_strong_synthesis(
        SYNTHESIS_SYSTEM_PROMPT,
        user_prompt,
        step="synthesize_trip_brief",
    )

    if provider_text:
        final_verdict = provider_text
    else:
        final_verdict = (
            f"{plan.destination} is the strongest pick because the dream side is "
            f"clear: {', '.join(plan.matched_traits)}. The reality side is not "
            f"ignored: {live.flight_signal.lower()} The tension is manageable, "
            "so the recommendation is to book early and keep one weather-flex day."
        )
        if live.pressure_score < 55:
            final_verdict = (
                f"{plan.destination} still fits the dream, but reality pressure is "
                f"meaningful: {live.weather_signal} {live.flight_signal} Treat this "
                "as a cautious recommendation, not a carefree one."
            )

    total_tokens_in = plan.cheap_usage.tokens_in + final_usage.tokens_in
    total_tokens_out = plan.cheap_usage.tokens_out + final_usage.tokens_out
    total_cost = plan.cheap_usage.cost_usd + final_usage.cost_usd

    return TripBriefResponse(
        query=query,
        top_pick=DestinationCandidate(
            name=plan.destination,
            country=plan.country,
            travel_style=ml.predicted_style,
            dream_fit=DreamFitScore(
                score=max(0, min(100, dream_score)),
                matched_traits=plan.matched_traits,
                rationale=rationale,
            ),
            reality_pressure=RealityPressureScore(
                score=live.pressure_score,
                weather_signal=live.weather_signal,
                flight_signal=live.flight_signal,
                rationale=live.warning or "Live and fallback signals were synthesized.",
            ),
        ),
        runners_up=[],
        final_verdict=final_verdict,
        counterfactual=CounterfactualCard(
            obvious_pick=plan.counterfactual_destination,
            why_not_chosen=plan.counterfactual_reason,
        ),
        tools_used=_trace(tool_results),
        meta=TripBriefMeta(
            tokens_in=total_tokens_in,
            tokens_out=total_tokens_out,
            cost_usd=total_cost,
            latency_ms=0,
            cheap_model=plan.cheap_usage.model_name,
            strong_model=final_usage.model_name,
        ),
    )
