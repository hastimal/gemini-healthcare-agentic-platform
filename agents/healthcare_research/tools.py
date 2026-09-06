"""
Tools used by the Google ADK Healthcare Research Agent.

The Healthcare Research Agent retrieves evidence through MCP-backed services.

v0.8 made Google ADK workflow state authoritative so Gemini and Gemma no longer
need to reconstruct large structured objects before deterministic retrieval.

v0.9 removes application-level flagship assumptions from retrieval. The
validated UserQuery/SearchPlan now drive location, specialty, intent, and
source routing. The flagship Houston pediatric-dentist query remains an
acceptance example, not configuration.
"""

from __future__ import annotations

from typing import Any

from google.adk.tools import ToolContext

from models import SearchPlan, UserQuery
from search.mcp_retrieval import MCPHealthcareRetrievalOrchestrator


async def retrieve_healthcare_evidence(
    tool_context: ToolContext,
) -> dict[str, Any]:
    """
    Retrieve healthcare evidence using planner output stored in ADK state.

    Safety:
    - NPPES registry data does not establish provider quality.
    - PubMed describes general biomedical evidence unless a source explicitly
      supports a provider-specific claim.
    - Public HAPI FHIR records are interoperability/test examples and must not
      be treated as verified provider recommendations.
    """
    planner_output = tool_context.state.get("planner_output")

    if not planner_output:
        raise ValueError(
            "planner_output is missing from Google ADK workflow state."
        )

    if not isinstance(planner_output, dict):
        raise ValueError(
            "planner_output in Google ADK workflow state must be a dictionary."
        )

    user_query_data = planner_output.get("user_query")
    search_plan_data = planner_output.get("search_plan")

    if not user_query_data:
        raise ValueError(
            "planner_output.user_query is missing from Google ADK workflow state."
        )

    if not search_plan_data:
        raise ValueError(
            "planner_output.search_plan is missing from Google ADK workflow state."
        )

    validated_user_query = UserQuery.model_validate(user_query_data)

    normalized_search_plan = dict(search_plan_data)

    if not normalized_search_plan.get("intent"):
        normalized_search_plan["intent"] = validated_user_query.intent

    if not normalized_search_plan.get("original_query"):
        normalized_search_plan["original_query"] = (
            validated_user_query.model_dump(mode="json")
        )

    validated_plan = SearchPlan.model_validate(normalized_search_plan)

    orchestrator = MCPHealthcareRetrievalOrchestrator()

    # v0.9: no city/state constants here. The orchestrator derives provider
    # geography from validated UserQuery.location when provider discovery
    # actually requires it.
    results = await orchestrator.retrieve(
        user_query=validated_user_query,
        plan=validated_plan,
        provider_limit=10,
        pubmed_limit=3,
        fhir_limit=3,
    )

    research_output = {
        "user_query": validated_user_query.model_dump(mode="json"),
        "search_plan": validated_plan.model_dump(mode="json"),
        "search_results": [
            result.model_dump(mode="json")
            for result in results
        ],
        "retrieved_sources": len(results),
        "deduplicated_sources": len(results),
    }

    tool_context.state["research_output"] = research_output
    tool_context.actions.skip_summarization = True

    return {
        "status": "research_complete",
        "retrieved_sources": research_output["retrieved_sources"],
        "deduplicated_sources": research_output["deduplicated_sources"],
        "research_output_state_key": "research_output",
    }
