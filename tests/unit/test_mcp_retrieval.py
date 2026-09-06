"""
Regression tests for the async MCP healthcare retrieval orchestrator.

v0.7 preserves deterministic NPPES and PubMed routing while adding
explicit, opt-in FHIR interoperability retrieval.
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


class FakeFHIRClient:
    def __init__(self):
        self.calls = []

    async def search_practitioner_roles(
        self,
        specialty=None,
        practitioner=None,
        organization=None,
        limit=10,
    ):
        self.calls.append(
            {
                "specialty": specialty,
                "practitioner": practitioner,
                "organization": organization,
                "limit": limit,
            }
        )

        return [
            SearchResult(
                source_type=SourceType.FHIR,
                title="FHIR PractitionerRole Example",
                url="https://example.com/fhir/PractitionerRole/123",
                snippet=(
                    "FHIR interoperability example linking practitioner, "
                    "specialty, organization, and location."
                ),
                retrieved_by="fhir",
                query_used="FHIR PractitionerRole pediatric dentistry",
                metadata={
                    "fhir_resource_type": "PractitionerRole",
                    "fhir_resource_id": "123",
                },
            )
        ]


def _user_query() -> UserQuery:
    return UserQuery(
        text=(
            "Find pediatric dentists in Houston for a child "
            "with dental anxiety."
        ),
        location="Houston, TX",
        specialty="Pediatric Dentistry",
        intent=SearchIntent.PROVIDER_DISCOVERY,
    )


@pytest.mark.asyncio
async def test_mcp_retrieval_routes_provider_research_and_fhir_queries():
    """
    Provider discovery executes once, biomedical queries go to PubMed,
    and explicit FHIR interoperability queries go to FHIR.
    """

    user_query = _user_query()

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
            SearchQuery(
                query="FHIR PractitionerRole pediatric dentistry",
                purpose=(
                    "Retrieve FHIR interoperability relationships among "
                    "practitioners, specialties, organizations, and locations."
                ),
                priority=3,
            ),
        ],
    )

    provider_client = FakeProviderClient()
    pubmed_client = FakePubMedClient()
    fhir_client = FakeFHIRClient()

    orchestrator = MCPHealthcareRetrievalOrchestrator(
        provider_client=provider_client,
        pubmed_client=pubmed_client,
        fhir_client=fhir_client,
    )

    results = await orchestrator.retrieve(
        user_query=user_query,
        plan=plan,
        city="Houston",
        state="TX",
        provider_limit=10,
        pubmed_limit=3,
        fhir_limit=2,
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

    assert len(fhir_client.calls) == 1
    assert fhir_client.calls[0] == {
        "specialty": "Pediatric Dentistry",
        "practitioner": None,
        "organization": None,
        "limit": 2,
    }

    source_types = {
        result.source_type
        for result in results
    }

    assert SourceType.PROVIDER in source_types
    assert SourceType.PUBMED in source_types
    assert SourceType.FHIR in source_types


@pytest.mark.asyncio
async def test_mcp_retrieval_does_not_call_fhir_without_explicit_fhir_query():
    """
    Ordinary provider and biomedical queries must not trigger FHIR.

    This protects the evidence pipeline from unrelated public test-server
    records entering normal provider discovery.
    """

    user_query = _user_query()

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
                purpose="Retrieve biomedical evidence.",
                priority=2,
            ),
        ],
    )

    provider_client = FakeProviderClient()
    pubmed_client = FakePubMedClient()
    fhir_client = FakeFHIRClient()

    orchestrator = MCPHealthcareRetrievalOrchestrator(
        provider_client=provider_client,
        pubmed_client=pubmed_client,
        fhir_client=fhir_client,
    )

    results = await orchestrator.retrieve(
        user_query=user_query,
        plan=plan,
        city="Houston",
        state="TX",
        provider_limit=10,
        pubmed_limit=3,
        fhir_limit=2,
    )

    assert len(provider_client.calls) == 1
    assert len(pubmed_client.calls) == 1
    assert len(fhir_client.calls) == 0

    assert all(
        result.source_type != SourceType.FHIR
        for result in results
    )


@pytest.mark.asyncio
async def test_mcp_retrieval_calls_fhir_only_once():
    """
    Multiple FHIR-oriented generated queries should produce only one
    FHIR lookup during the v0.7 workflow.
    """

    user_query = _user_query()

    plan = SearchPlan(
        original_query=user_query,
        intent=SearchIntent.PROVIDER_DISCOVERY,
        generated_queries=[
            SearchQuery(
                query="FHIR PractitionerRole pediatric dentistry",
                purpose="Retrieve FHIR interoperability evidence.",
                priority=1,
            ),
            SearchQuery(
                query="FHIR healthcare organization structure",
                purpose="Retrieve standardized healthcare data.",
                priority=2,
            ),
        ],
    )

    provider_client = FakeProviderClient()
    pubmed_client = FakePubMedClient()
    fhir_client = FakeFHIRClient()

    orchestrator = MCPHealthcareRetrievalOrchestrator(
        provider_client=provider_client,
        pubmed_client=pubmed_client,
        fhir_client=fhir_client,
    )

    await orchestrator.retrieve(
        user_query=user_query,
        plan=plan,
        city="Houston",
        state="TX",
        fhir_limit=3,
    )

    assert len(fhir_client.calls) == 1
