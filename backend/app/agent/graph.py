"""Minimal LangGraph agent for the Decision Tension Board."""

from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.registry import execute_tool
from app.agent.synthesize import synthesize_trip_brief
from app.llm.router import extract_trip_plan
from app.schemas.llm import TripPlan
from app.schemas.tools import ToolExecutionResult
from app.schemas.trip_brief import TripBriefResponse


class AgentState(TypedDict, total=False):
    query: str
    session: AsyncSession | None
    ml_model: Any | None
    plan: TripPlan
    tool_results: list[ToolExecutionResult]
    response: TripBriefResponse


class AtlasBriefAgent:
    """A tiny graph: plan -> exactly three tools -> synthesize."""

    def __init__(self) -> None:
        graph = StateGraph(AgentState)
        graph.add_node("plan_step", self._plan)
        graph.add_node("tools_step", self._tools)
        graph.add_node("synthesize_step", self._synthesize)
        graph.set_entry_point("plan_step")
        graph.add_edge("plan_step", "tools_step")
        graph.add_edge("tools_step", "synthesize_step")
        graph.add_edge("synthesize_step", END)
        self._graph = graph.compile()

    async def _plan(self, state: AgentState) -> AgentState:
        return {"plan": extract_trip_plan(state["query"])}

    async def _tools(self, state: AgentState) -> AgentState:
        plan = state["plan"]
        session = state.get("session")
        ml_model = state.get("ml_model")
        tool_payloads = [
            (
                "retrieve_destination_knowledge",
                {"query": plan.rag_query, "destinations": [plan.destination], "top_k": 3},
            ),
            (
                "classify_travel_style",
                {
                    "query": state["query"],
                    "destination": plan.destination,
                    **plan.feature_profile,
                },
            ),
            (
                "fetch_live_conditions",
                {
                    "query": state["query"],
                    "destination": plan.destination,
                    "country": plan.country,
                    "trip_month": "July",
                },
            ),
        ]
        results = [
            await execute_tool(
                name,
                payload,
                session=session,
                ml_model=ml_model,
            )
            for name, payload in tool_payloads
        ]
        return {"tool_results": results}

    async def _synthesize(self, state: AgentState) -> AgentState:
        response = synthesize_trip_brief(
            query=state["query"],
            plan=state["plan"],
            tool_results=state["tool_results"],
        )
        return {"response": response}

    async def run(
        self,
        query: str,
        session: AsyncSession | None = None,
        ml_model: Any | None = None,
    ) -> TripBriefResponse:
        """Run the graph and return only the final response."""

        result = await self.run_state(query=query, session=session, ml_model=ml_model)
        return result["response"]

    async def run_state(
        self,
        query: str,
        session: AsyncSession | None = None,
        ml_model: Any | None = None,
    ) -> AgentState:
        """Run the graph and return response plus intermediate tool results."""

        result = await self._graph.ainvoke(
            {"query": query, "session": session, "ml_model": ml_model}
        )
        return result
