"""
Tools used by the Google ADK Healthcare Research Agent.

This module adapts ADK to the already-tested v0.2-v0.4 healthcare
retrieval pipeline.

Structured dictionaries are passed between agents instead of
JSON-encoded strings to avoid nested JSON escaping problems.
"""

from typing import Any

from connectors.provider_search.client import NPPESProviderClient
from connectors.pubmed.client import PubMedClient
from models import SearchPlan, UserQuery
from search.retrieval import HealthcareRetrievalOrchestrator


def retrieve_healthcare_evidence(
    user_query: dict[str, Any],
    search_plan: dict[str, Any],
) -> dict:
    """
    Retrieve provider and biomedical evidence for a validated search plan.

    Args:
        user_query: Structured UserQuery data.
        search_plan: Structured SearchPlan data.

    Returns:
        Structured SearchResult records and transparency counts.
    """

    validated_user_query = UserQuery.model_validate(user_query)
    validated_plan = SearchPlan.model_validate(search_plan)

    orchestrator = HealthcareRetrievalOrchestrator(
        provider_client=NPPESProviderClient(),
        pubmed_client=PubMedClient(),
    )

    results = orchestrator.retrieve(
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
