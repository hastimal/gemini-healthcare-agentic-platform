"""
Regression tests for the async MCP healthcare retrieval orchestrator.

The test verifies that v0.6 preserves the deterministic routing
behavior of the original synchronous retrieval pipeline.
"""

import pytest

from models import (
    SearchIntent,
    SearchPlan,
    SearchQuery,
    SearchResult,
    SourceType,
    UserQuery,
)
from search.mcp_retrieval import MCPHealthcareRetrievalOrchestrator


class FakeProviderClient:
    def __init__(self):
        self.calls = []

    async def search(
        self,
        taxonomy_description,
        city,
        state,
        limit=10,
    ):
        self.calls.append(
            {
                "taxonomy_description": taxonomy_description,
                "city": city,
                "state": state,
                "limit": limit,
            }
        )

        return [
            SearchResult(
                source_type=SourceType.PROVIDER,
                title="TEST PEDIATRIC DENTIST DDS",
                url="https://example.com/provider/123",
                snippet="Pediatric dentist in Houston",
                provider_name="TEST PEDIATRIC DENTIST DDS",
                location="Houston, TX",
                retrieved_by="nppes",
                query_used="Dentist, Pediatric Dentistry",
                metadata={"npi": "1234567890"},
            )
        ]


class FakePubMedClient:
    def __init__(self):
        self.calls = []

    async def search(
        self,
        query,
        max_results=5,
    ):
        self.calls.append(
            {
                "query": query,
                "max_results": max_results,
            }
        )

        return [
            SearchResult(
                source_type=SourceType.PUBMED,
                title="Pediatric Dental Anxiety Study",
                url="https://pubmed.ncbi.nlm.nih.gov/12345678/",
                snippet="Evidence about pediatric dental anxiety.",
                content="Biomedical evidence about anxiety management.",
                retrieved_by="pubmed",
                query_used=query,
                metadata={"pmid": "12345678"},
            )
        ]


@pytest.mark.asyncio
async def test_mcp_retrieval_routes_provider_and_research_queries():
    """
    Provider discovery should execute once while only biomedical
    generated queries are routed to PubMed.
    """

    user_query = UserQuery(
        text=(
            "Find pediatric dentists in Houston for a child "
            "with dental anxiety."
        ),
        location="Houston, TX",
        specialty="Pediatric Dentistry",
        intent=SearchIntent.PROVIDER_DISCOVERY,
    )

    plan = SearchPlan(
        original_query=user_query,
        intent=SearchIntent.PROVIDER_DISCOVERY,
        generated_queries=[
            SearchQuery(
                query="pediatric dentist Houston TX",
                purpose="Identify local pediatric dental providers.",
                priority=1,
            ),
            SearchQuery(
                query="pediatric dental anxiety behavior guidance",
                purpose=(
                    "Retrieve biomedical evidence about pediatric "
                    "dental anxiety."
                ),
                priority=2,
            ),
        ],
    )

    provider_client = FakeProviderClient()
    pubmed_client = FakePubMedClient()

    orchestrator = MCPHealthcareRetrievalOrchestrator(
        provider_client=provider_client,
        pubmed_client=pubmed_client,
    )

    results = await orchestrator.retrieve(
        user_query=user_query,
        plan=plan,
        city="Houston",
        state="TX",
        provider_limit=10,
        pubmed_limit=3,
    )

    assert len(provider_client.calls) == 1
    assert provider_client.calls[0] == {
        "taxonomy_description": "Pediatric Dentistry",
        "city": "Houston",
        "state": "TX",
        "limit": 10,
    }

    assert len(pubmed_client.calls) == 1
    assert pubmed_client.calls[0] == {
        "query": "pediatric dental anxiety behavior guidance",
        "max_results": 3,
    }

    assert len(results) == 2

    source_types = {
        result.source_type
        for result in results
    }

    assert SourceType.PROVIDER in source_types
    assert SourceType.PUBMED in source_types
