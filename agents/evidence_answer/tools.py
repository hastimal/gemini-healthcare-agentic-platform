"""
Tools used by the Google ADK Evidence & Answer Agent.

This tool reuses the tested v0.3 evidence-ranking and v0.4
grounding/citation pipeline.

ADK passes structured dictionaries into this tool rather than
JSON-encoded strings.
"""

from typing import Any

from grounding.answering import GroundedAnswerGenerator
from grounding.ranking import EvidenceRanker
from models import SearchPlan, SearchResult, UserQuery


def build_grounded_healthcare_answer(
    user_query: dict[str, Any],
    search_plan: dict[str, Any],
    search_results: list[dict[str, Any]],
    retrieved_sources: int,
    deduplicated_sources: int,
) -> dict:
    """
    Rank evidence and generate the final evidence-grounded answer.

    Args:
        user_query: Structured UserQuery data.
        search_plan: Structured SearchPlan data.
        search_results: Structured SearchResult records.
        retrieved_sources: Retrieval transparency count.
        deduplicated_sources: Deduplication transparency count.

    Returns:
        Structured GroundedAnswer and selected evidence count.
    """

    validated_user_query = UserQuery.model_validate(user_query)
    validated_plan = SearchPlan.model_validate(search_plan)

    results = [
        SearchResult.model_validate(item)
        for item in search_results
    ]

    ranker = EvidenceRanker()

    ranked_evidence = ranker.rank(
        results=results,
        user_query=validated_user_query,
        top_k=5,
    )

    generator = GroundedAnswerGenerator(
        ranker=ranker,
    )

    grounded_answer = generator.generate(
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

    return {
        "grounded_answer": grounded_answer.model_dump(mode="json"),
        "selected_evidence_count": selected_count,
    }
