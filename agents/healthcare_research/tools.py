"""
Tools used by the Google ADK Healthcare Research Agent.

v0.6 routes healthcare retrieval through MCP using an asynchronous
retrieval path compatible with Google ADK's asyncio execution model.

Structured dictionaries are passed between agents instead of
JSON-encoded strings to avoid nested JSON escaping problems.
"""

from typing import Any

from models import SearchPlan, UserQuery
from search.mcp_retrieval import MCPHealthcareRetrievalOrchestrator


async def retrieve_healthcare_evidence(
    user_query: dict[str, Any],
    search_plan: dict[str, Any],
) -> dict:
    """
    Retrieve provider and biomedical evidence through MCP.

    Flow:

        Google ADK
            |
            v
        Healthcare Research Agent
            |
            v
        MCPHealthcareRetrievalOrchestrator
            |
            +--> Search MCP Server --> NPPES
            |
            +--> Research MCP Server --> PubMed

    The returned structure remains compatible with the v0.5 agent
    handoff contract.
    """

    validated_user_query = UserQuery.model_validate(user_query)
    validated_plan = SearchPlan.model_validate(search_plan)

    orchestrator = MCPHealthcareRetrievalOrchestrator()

    results = await orchestrator.retrieve(
        user_query=validated_user_query,
        plan=validated_plan,
        city="Houston",
        state="TX",
        provider_limit=10,
        pubmed_limit=3,
    )

    return {
        "user_query": validated_user_query.model_dump(mode="json"),
        "search_plan": validated_plan.model_dump(mode="json"),
        "search_results": [
            result.model_dump(mode="json")
            for result in results
        ],
        "retrieved_sources": len(results),
        "deduplicated_sources": len(results),
    }
