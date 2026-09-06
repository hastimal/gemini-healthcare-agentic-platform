"""
Tools used by the Google ADK Evidence & Answer Agent.

This tool reuses the tested v0.3 evidence-ranking and v0.4
grounding/citation pipeline.

v0.8 uses ADK session state for the authoritative handoff from the
Healthcare Research Agent to the Evidence & Answer Agent.

The LLM therefore does not need to reconstruct a potentially large
research payload as function-call arguments.
"""

from google.adk.tools import ToolContext

from grounding.answering import GroundedAnswerGenerator
from grounding.ranking import EvidenceRanker
from models import SearchPlan, SearchResult, UserQuery


async def build_grounded_healthcare_answer(
    tool_context: ToolContext,
) -> dict:
    """
    Rank evidence and generate the final evidence-grounded answer.

    The authoritative Healthcare Research Agent output is read directly
    from ADK session state under `research_output`.

    The authoritative final answer is then written directly to ADK state
    under `answer_output`.

    This design avoids asking Gemini or Gemma to reconstruct large
    structured objects across agent/tool boundaries.

    Returns:
        A small execution-status payload. The complete grounded answer
        remains in ADK state under `answer_output`.
    """

    research_output = tool_context.state.get("research_output")

    if not isinstance(research_output, dict):
        raise ValueError(
            "research_output is missing from ADK session state. "
            "The Healthcare Research Agent must complete before the "
            "Evidence & Answer Agent."
        )

    required_fields = {
        "user_query",
        "search_plan",
        "search_results",
        "retrieved_sources",
        "deduplicated_sources",
    }

    missing_fields = sorted(
        field
        for field in required_fields
        if field not in research_output
    )

    if missing_fields:
        raise ValueError(
            "research_output is missing required fields: "
            + ", ".join(missing_fields)
        )

    validated_user_query = UserQuery.model_validate(
        research_output["user_query"]
    )

    validated_plan = SearchPlan.model_validate(
        research_output["search_plan"]
    )

    raw_search_results = research_output["search_results"]

    if not isinstance(raw_search_results, list):
        raise ValueError(
            "research_output.search_results must be a list."
        )

    results = [
        SearchResult.model_validate(item)
        for item in raw_search_results
    ]

    retrieved_sources = int(
        research_output["retrieved_sources"]
    )

    deduplicated_sources = int(
        research_output["deduplicated_sources"]
    )

    ranker = EvidenceRanker()

    ranked_evidence = ranker.rank(
        results=results,
        user_query=validated_user_query,
        top_k=5,
    )

    generator = GroundedAnswerGenerator(
        ranker=ranker,
    )

    grounded_answer = await generator.agenerate(
        user_query=validated_user_query,
        plan=validated_plan,
        ranked_evidence=ranked_evidence,
        retrieved_sources=retrieved_sources,
        deduplicated_sources=deduplicated_sources,
    )

    selected_count = sum(
        1
        for evidence in ranked_evidence
        if evidence.selected
    )

    answer_output = {
        "grounded_answer": grounded_answer.model_dump(
            mode="json"
        ),
        "selected_evidence_count": selected_count,
    }

    # Authoritative deterministic handoff.
    #
    # The grounding pipeline, rather than the surrounding LLM, owns the
    # final answer state. This prevents a model from rewriting provider
    # claims, citations, selected-evidence counts, or safety limitations.
    tool_context.state["answer_output"] = answer_output

    # Do not perform another LLM completion to summarize or regenerate the
    # potentially large grounded answer after the function response.
    tool_context.actions.skip_summarization = True

    return {
        "status": "answer_complete",
        "selected_evidence_count": selected_count,
        "answer_output_state_key": "answer_output",
    }
