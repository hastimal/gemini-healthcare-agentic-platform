"""
Tools used by the Google ADK Healthcare Research Agent.

The Healthcare Research Agent retrieves evidence through MCP-backed services.

v0.8 architecture change
------------------------

Earlier versions required the LLM-mediated Research Agent to reconstruct
`user_query` and `search_plan` from `planner_output` and then pass those
already-existing objects back as tool arguments.

In v0.8, the retrieval tool reads `planner_output` directly from Google ADK
workflow state through ToolContext.

Why this change?

1. Model portability
   Gemini and Gemma no longer need to reproduce large structured objects
   identically before the deterministic retrieval pipeline can run.

2. Reliability
   The application avoids unnecessary LLM-mediated changes such as omitted,
   renamed, or reconstructed fields in an already-validated workflow object.

3. Performance
   Local models such as Gemma running through Ollama generate a much smaller
   function call because the structured planner state remains in ADK state.

The architectural responsibilities remain unchanged:

    Search Planner Agent
        -> planner_output in ADK state

    Healthcare Research Agent
        -> selects / invokes evidence retrieval

    retrieve_healthcare_evidence
        -> reads planner_output from ADK state
        -> validates domain models
        -> executes MCP-backed retrieval

    MCP
        -> NPPES
        -> PubMed
        -> FHIR

This change does NOT alter:

- the three-agent architecture
- MCP retrieval
- NPPES / PubMed / FHIR connectors
- evidence ranking
- grounding
- citation rules
- healthcare safety boundaries
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

    Expected ADK state:

        planner_output = {
            "user_query": {...},
            "search_plan": {...},
        }

    Flow:

        Google ADK workflow state
            |
            v
        planner_output
            |
            v
        Healthcare Research Agent
            |
            v
        retrieve_healthcare_evidence
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

    Safety:

    - NPPES registry data does not establish provider quality.
    - PubMed evidence describes general biomedical evidence unless a
      source explicitly supports a provider-specific claim.
    - Public HAPI FHIR test records are interoperability examples and
      must not be treated as verified provider recommendations.
    """

    # -------------------------------------------------------------
    # 1. Read planner output directly from Google ADK state
    # -------------------------------------------------------------
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

    # -------------------------------------------------------------
    # 2. Validate the authoritative structured workflow state
    # -------------------------------------------------------------
    validated_user_query = UserQuery.model_validate(user_query_data)

    normalized_search_plan = dict(search_plan_data)

    # Keep a defensive recovery path for legacy / malformed planner state.
    #
    # Unlike the earlier v0.7 implementation, this is no longer compensating
    # for an LLM reconstructing tool arguments. It protects the workflow
    # boundary itself in case persisted planner state is incomplete.
    if not normalized_search_plan.get("intent"):
        normalized_search_plan["intent"] = validated_user_query.intent

    if not normalized_search_plan.get("original_query"):
        normalized_search_plan["original_query"] = (
            validated_user_query.model_dump(mode="json")
        )

    validated_plan = SearchPlan.model_validate(normalized_search_plan)

    # -------------------------------------------------------------
    # 3. Execute the existing MCP-backed retrieval pipeline
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
    # 4. Build the authoritative research output
    # -------------------------------------------------------------
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

    # -------------------------------------------------------------
    # 5. Store deterministic research output directly in ADK state
    # -------------------------------------------------------------
    #
    # v0.8 model-portability change:
    #
    # The MCP-backed retrieval pipeline has already produced the
    # authoritative structured evidence. Do not require Gemini or Gemma
    # to regenerate the same potentially large object after the tool call.
    #
    # The Evidence & Answer Agent can consume this state directly.
    tool_context.state["research_output"] = research_output

    # Prevent ADK from issuing another LLM completion to summarize /
    # reconstruct this large deterministic tool result.
    tool_context.actions.skip_summarization = True

    # Keep the function response intentionally small. The full evidence
    # payload is already available under workflow state["research_output"].
    return {
        "status": "research_complete",
        "retrieved_sources": research_output["retrieved_sources"],
        "deduplicated_sources": research_output["deduplicated_sources"],
        "research_output_state_key": "research_output",
    }
