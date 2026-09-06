"""
v0.9 regression tests for dynamic MCP healthcare retrieval.
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
                title=f"TEST {taxonomy_description.upper()}",
                url="https://example.com/provider/123",
                snippet=f"{taxonomy_description} in {city}, {state}",
                provider_name=f"TEST {taxonomy_description.upper()}",
                location=f"{city}, {state}",
                retrieved_by="nppes",
                query_used=taxonomy_description,
                metadata={"npi": "1234567890"},
            )
        ]


class FakePubMedClient:
    def __init__(self):
        self.calls = []

    async def search(self, query, max_results=5):
        self.calls.append({"query": query, "max_results": max_results})
        return [
            SearchResult(
                source_type=SourceType.PUBMED,
                title=f"Research: {query}",
                url="https://pubmed.ncbi.nlm.nih.gov/12345678/",
                snippet="Biomedical evidence.",
                content="Biomedical evidence.",
                retrieved_by="pubmed",
                query_used=query,
                metadata={"pmid": "12345678"},
            )
        ]


class FakeFHIRClient:
    def __init__(self):
        self.calls = []

    def _result(self, resource_type):
        return [
            SearchResult(
                source_type=SourceType.FHIR,
                title=f"FHIR {resource_type} Example",
                url=f"https://example.com/fhir/{resource_type}/123",
                snippet="FHIR interoperability example.",
                retrieved_by="fhir",
                query_used=resource_type,
                metadata={"fhir_resource_type": resource_type},
            )
        ]

    async def search_practitioner_roles(
        self,
        specialty=None,
        practitioner=None,
        organization=None,
        limit=10,
    ):
        self.calls.append(
            ("PractitionerRole", specialty, practitioner, organization, limit)
        )
        return self._result("PractitionerRole")

    async def search_practitioners(self, name=None, limit=10):
        self.calls.append(("Practitioner", name, limit))
        return self._result("Practitioner")

    async def search_organizations(self, name=None, limit=10):
        self.calls.append(("Organization", name, limit))
        return self._result("Organization")

    async def search_locations(
        self,
        name=None,
        city=None,
        state=None,
        limit=10,
    ):
        self.calls.append(("Location", name, city, state, limit))
        return self._result("Location")

    async def search_healthcare_services(self, name=None, limit=10):
        self.calls.append(("HealthcareService", name, limit))
        return self._result("HealthcareService")


def make_plan(user_query, generated_queries):
    return SearchPlan(
        original_query=user_query,
        intent=user_query.intent,
        generated_queries=generated_queries,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("location", "specialty", "city", "state"),
    [
        ("Dallas, TX", "Cardiology", "Dallas", "TX"),
        ("Austin, Texas", "Neurology", "Austin", "TX"),
        ("Chicago, IL", "Oncology", "Chicago", "IL"),
    ],
)
async def test_provider_discovery_uses_dynamic_location_and_specialty(
    location,
    specialty,
    city,
    state,
):
    user_query = UserQuery(
        text=f"Find {specialty} providers in {location}",
        location=location,
        specialty=specialty,
        intent=SearchIntent.PROVIDER_DISCOVERY,
    )
    plan = make_plan(
        user_query,
        [
            SearchQuery(
                query=f"{specialty} {location}",
                purpose="Identify local healthcare providers.",
                priority=1,
            )
        ],
    )

    provider = FakeProviderClient()
    pubmed = FakePubMedClient()
    fhir = FakeFHIRClient()
    orchestrator = MCPHealthcareRetrievalOrchestrator(provider, pubmed, fhir)

    results = await orchestrator.retrieve(user_query=user_query, plan=plan)

    assert provider.calls == [
        {
            "taxonomy_description": specialty,
            "city": city,
            "state": state,
            "limit": 10,
        }
    ]
    assert pubmed.calls == []
    assert fhir.calls == []
    assert any(r.source_type == SourceType.PROVIDER for r in results)


@pytest.mark.asyncio
async def test_biomedical_research_routes_to_pubmed_without_provider_location():
    user_query = UserQuery(
        text="What does research say about childhood dental anxiety?",
        intent=SearchIntent.BIOMEDICAL_RESEARCH,
    )
    plan = make_plan(
        user_query,
        [
            SearchQuery(
                query="childhood dental anxiety systematic review",
                purpose="Retrieve biomedical research.",
                priority=1,
            )
        ],
    )

    provider = FakeProviderClient()
    pubmed = FakePubMedClient()
    fhir = FakeFHIRClient()
    orchestrator = MCPHealthcareRetrievalOrchestrator(provider, pubmed, fhir)

    results = await orchestrator.retrieve(user_query=user_query, plan=plan)

    assert provider.calls == []
    assert len(pubmed.calls) == 1
    assert fhir.calls == []
    assert any(r.source_type == SourceType.PUBMED for r in results)


@pytest.mark.asyncio
async def test_health_information_routes_to_pubmed_without_provider_assumptions():
    user_query = UserQuery(
        text="What is atrial fibrillation?",
        intent=SearchIntent.HEALTH_INFORMATION,
    )
    plan = make_plan(
        user_query,
        [
            SearchQuery(
                query="atrial fibrillation overview",
                purpose="Retrieve health information evidence.",
                priority=1,
            )
        ],
    )

    provider = FakeProviderClient()
    pubmed = FakePubMedClient()
    fhir = FakeFHIRClient()
    orchestrator = MCPHealthcareRetrievalOrchestrator(provider, pubmed, fhir)

    await orchestrator.retrieve(user_query=user_query, plan=plan)

    assert provider.calls == []
    assert len(pubmed.calls) == 1


@pytest.mark.asyncio
async def test_explicit_fhir_practitioner_role_does_not_require_houston():
    user_query = UserQuery(
        text="Explain FHIR PractitionerRole",
        intent=SearchIntent.HEALTH_INFORMATION,
    )
    plan = make_plan(
        user_query,
        [
            SearchQuery(
                query="FHIR PractitionerRole",
                purpose="Retrieve FHIR interoperability evidence.",
                priority=1,
            )
        ],
    )

    provider = FakeProviderClient()
    pubmed = FakePubMedClient()
    fhir = FakeFHIRClient()
    orchestrator = MCPHealthcareRetrievalOrchestrator(provider, pubmed, fhir)

    results = await orchestrator.retrieve(user_query=user_query, plan=plan)

    assert provider.calls == []
    assert fhir.calls == [
        ("PractitionerRole", None, None, None, 3)
    ]
    assert any(r.source_type == SourceType.FHIR for r in results)


@pytest.mark.asyncio
async def test_fhir_healthcare_service_routes_to_healthcare_service_tool():
    user_query = UserQuery(
        text="Show FHIR HealthcareService examples",
        intent=SearchIntent.HEALTH_INFORMATION,
    )
    plan = make_plan(
        user_query,
        [
            SearchQuery(
                query="FHIR HealthcareService",
                purpose="Retrieve FHIR healthcare service interoperability evidence.",
                priority=1,
            )
        ],
    )

    fhir = FakeFHIRClient()
    orchestrator = MCPHealthcareRetrievalOrchestrator(
        FakeProviderClient(),
        FakePubMedClient(),
        fhir,
    )

    await orchestrator.retrieve(user_query=user_query, plan=plan)

    assert ("HealthcareService", None, 3) in fhir.calls


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "intent",
    [
        SearchIntent.CARE_PROGRAM_DISCOVERY,
        SearchIntent.CLINICAL_TRIALS,
    ],
)
async def test_unsupported_intents_fail_explicitly_instead_of_misrouting(intent):
    user_query = UserQuery(
        text="Healthcare query requiring an unsupported connector",
        intent=intent,
    )
    plan = make_plan(
        user_query,
        [
            SearchQuery(
                query="unsupported healthcare retrieval",
                purpose="Retrieve relevant evidence.",
                priority=1,
            )
        ],
    )

    provider = FakeProviderClient()
    orchestrator = MCPHealthcareRetrievalOrchestrator(
        provider,
        FakePubMedClient(),
        FakeFHIRClient(),
    )

    with pytest.raises(NotImplementedError, match=intent.value):
        await orchestrator.retrieve(user_query=user_query, plan=plan)

    assert provider.calls == []


@pytest.mark.asyncio
async def test_provider_discovery_requires_location():
    user_query = UserQuery(
        text="Find cardiologists",
        specialty="Cardiology",
        intent=SearchIntent.PROVIDER_DISCOVERY,
    )
    plan = make_plan(
        user_query,
        [
            SearchQuery(
                query="cardiologists",
                purpose="Identify healthcare providers.",
                priority=1,
            )
        ],
    )

    orchestrator = MCPHealthcareRetrievalOrchestrator(
        FakeProviderClient(),
        FakePubMedClient(),
        FakeFHIRClient(),
    )

    with pytest.raises(ValueError, match="location"):
        await orchestrator.retrieve(user_query=user_query, plan=plan)


@pytest.mark.asyncio
async def test_intent_mismatch_is_rejected():
    user_query = UserQuery(
        text="Research childhood dental anxiety",
        intent=SearchIntent.BIOMEDICAL_RESEARCH,
    )
    plan = SearchPlan(
        original_query=user_query,
        intent=SearchIntent.PROVIDER_DISCOVERY,
        generated_queries=[
            SearchQuery(
                query="childhood dental anxiety",
                purpose="Research evidence.",
                priority=1,
            )
        ],
    )

    orchestrator = MCPHealthcareRetrievalOrchestrator(
        FakeProviderClient(),
        FakePubMedClient(),
        FakeFHIRClient(),
    )

    with pytest.raises(ValueError, match="intent mismatch"):
        await orchestrator.retrieve(user_query=user_query, plan=plan)
