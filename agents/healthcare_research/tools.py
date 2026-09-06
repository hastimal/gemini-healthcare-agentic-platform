"""
Tools used by the Google ADK Healthcare Research Agent.

The Research Agent receives the structured output produced by the
Search Planner Agent and retrieves evidence through MCP-backed services.

v0.7 retrieval sources:

    NPPES
        Provider registry evidence.

    PubMed
        Biomedical/scientific evidence.

    FHIR
        Healthcare interoperability evidence.

Structured dictionaries are passed between agents instead of
JSON-encoded strings to avoid nested JSON escaping problems.

The tool boundary also performs a small amount of defensive normalization
because an LLM agent may occasionally omit a redundant field while
constructing tool arguments.
"""

from __future__ import annotations

from typing import Any

from models import SearchPlan, UserQuery
from search.mcp_retrieval import MCPHealthcareRetrievalOrchestrator


async def retrieve_healthcare_evidence(
    user_query: dict[str, Any],
    search_plan: dict[str, Any],
) -> dict:
    """
    Retrieve healthcare evidence through MCP.

    Flow:

        Google ADK
            |
            v
        Healthcare Research Agent
            |
            v
        MCPHealthcareRetrievalOrchestrator
            |
            +--> Search MCP Server
            |       |
            |       +--> NPPES
            |
            +--> Research MCP Server
            |       |
            |       +--> PubMed
            |
            +--> FHIR MCP Server
                    |
                    +--> FHIR R4 endpoint

    The returned structure remains compatible with the existing
    ResearchAgentOutput handoff contract.

    Safety:

    - NPPES registry data does not establish provider quality.
    - PubMed evidence describes general biomedical evidence unless a
      source explicitly supports a provider-specific claim.
    - Public HAPI FHIR test records are interoperability examples and
      must not be treated as verified provider recommendations.
    """

    # -------------------------------------------------------------
    # 1. Validate the user query first
    # -------------------------------------------------------------
    #
    # UserQuery is the authoritative structured representation of the
    # original request at this stage.
    validated_user_query = UserQuery.model_validate(user_query)

    # -------------------------------------------------------------
    # 2. Defensively normalize SearchPlan
    # -------------------------------------------------------------
    #
    # The planner produces SearchPlan.intent, but the Healthcare Research
    # Agent is an LLM-mediated tool caller. During a live ADK execution it
    # may occasionally reconstruct the tool arguments and omit a field
    # that appears redundant.
    #
    # We observed this exact case:
    #
    #     planner_output.search_plan.intent
    #         == "provider_discovery"
    #
    # while the dictionary passed into this tool omitted `intent`.
    #
    # Because UserQuery.intent has already been validated and represents
    # the same workflow intent, use it only as a recovery value when the
    # SearchPlan field is absent.
    #
    # We do NOT overwrite an intent that the planner actually supplied.
    normalized_search_plan = dict(search_plan)

    if not normalized_search_plan.get("intent"):
        normalized_search_plan["intent"] = validated_user_query.intent

    # SearchPlan.original_query should also remain structurally aligned
    # with the validated user query. If an LLM-mediated tool call ever
    # omits it, restore the original structured query rather than failing
    # with an opaque downstream validation error.
    if not normalized_search_plan.get("original_query"):
        normalized_search_plan["original_query"] = (
            validated_user_query.model_dump(mode="json")
        )

    validated_plan = SearchPlan.model_validate(
        normalized_search_plan
    )

    # -------------------------------------------------------------
    # 3. Execute MCP-backed retrieval
    # -------------------------------------------------------------
    orchestrator = MCPHealthcareRetrievalOrchestrator()

    results = await orchestrator.retrieve(
        user_query=validated_user_query,
        plan=validated_plan,
        city="Houston",
        state="TX",
        provider_limit=10,
        pubmed_limit=3,
        fhir_limit=3,
    )

    # -------------------------------------------------------------
    # 4. Return structured Research Agent output
    # -------------------------------------------------------------
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
