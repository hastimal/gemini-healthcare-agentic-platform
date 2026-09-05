from models import (
    SearchIntent,
    SearchPlan,
    SearchQuery,
    SearchResult,
    SourceType,
    UserQuery,
)
from search.retrieval import HealthcareRetrievalOrchestrator


class FakeProviderClient:
    """
    Fake NPPES client used only for unit testing.

    Unit tests should not depend on external APIs or network access.
    """

    def search(
        self,
        taxonomy_description: str,
        city: str,
        state: str,
        limit: int,
    ) -> list[SearchResult]:
        # Confirm that specialty flows dynamically from UserQuery.
        #
        # The retrieval orchestrator should NOT hard-code
        # "Pediatric Dentistry".
        assert taxonomy_description == "Pediatric Dentistry"

        return [
            SearchResult(
                source_type=SourceType.PROVIDER,
                title="Example Pediatric Dentist",
                url=("https://npiregistry.cms.hhs.gov/provider-view/1234567890"),
                provider_name="Example Pediatric Dentist",
                location="Houston, TX",
                retrieved_by="nppes",
                query_used=taxonomy_description,
                metadata={
                    "npi": "1234567890",
                    "city": city,
                    "state": state,
                },
            )
        ]


class FakePubMedClient:
    """
    Fake PubMed client used only for unit testing.

    We intentionally return the SAME PMID for every research query.

    This verifies that our deduplication layer removes duplicate
    scientific evidence before it reaches the evidence pool.
    """

    def search(
        self,
        query: str,
        max_results: int,
    ) -> list[SearchResult]:
        return [
            SearchResult(
                source_type=SourceType.PUBMED,
                title="Pediatric Dental Anxiety Study",
                url=("https://pubmed.ncbi.nlm.nih.gov/12345678/"),
                snippet="Example research evidence.",
                content="Example research evidence.",
                retrieved_by="pubmed",
                query_used=query,
                metadata={
                    "pmid": "12345678",
                },
            )
        ]


def test_retrieval_orchestrator():
    """
    Validate the complete v0.2 retrieval path:

        UserQuery
            -> SearchPlan
            -> NPPES
            -> PubMed
            -> combine
            -> deduplicate

    Two research queries deliberately retrieve the same PMID.

    Expected final evidence:

        1 provider
        1 unique PubMed article

    Total = 2 unique SearchResult objects.
    """

    user_query = UserQuery(
        text=("Find pediatric dentists in Houston for a child with dental anxiety."),
        location="Houston, TX",
        specialty="Pediatric Dentistry",
    )

    plan = SearchPlan(
        # IMPORTANT:
        # SearchPlan.original_query expects the complete UserQuery model,
        # NOT user_query.text.
        #
        # This preserves structured fields such as:
        # - location
        # - specialty
        # - intent
        original_query=user_query,
        intent=SearchIntent.PROVIDER_DISCOVERY,
        generated_queries=[
            SearchQuery(
                query=("pediatric dental anxiety behavior management"),
                purpose=("Find evidence for managing dental anxiety in children"),
                priority=1,
            ),
            SearchQuery(
                query=("pediatric dentistry sedation anxious children"),
                purpose=("Find research about sedation and anxiety management"),
                priority=2,
            ),
        ],
        notes="Unit-test search plan",
    )

    orchestrator = HealthcareRetrievalOrchestrator(
        provider_client=FakeProviderClient(),
        pubmed_client=FakePubMedClient(),
    )

    results = orchestrator.retrieve(
        user_query=user_query,
        plan=plan,
        city="Houston",
        state="TX",
    )

    # FakePubMedClient returned the same PMID twice.
    #
    # Deduplication should leave:
    #
    # 1 provider
    # 1 PubMed article
    #
    # Total = 2 unique results.
    assert len(results) == 2

    provider_results = [result for result in results if result.source_type == SourceType.PROVIDER]

    pubmed_results = [result for result in results if result.source_type == SourceType.PUBMED]

    assert len(provider_results) == 1
    assert len(pubmed_results) == 1

    assert provider_results[0].metadata["npi"] == "1234567890"

    assert pubmed_results[0].metadata["pmid"] == "12345678"


def test_research_query_routing():
    """
    Verify our temporary v0.2 routing logic.

    Research/evidence-oriented queries should be routed to PubMed.

    Simple provider-location queries should NOT be routed to PubMed.

    Later, Google ADK will replace this lightweight routing logic
    with dynamic agent/tool selection.
    """

    assert HealthcareRetrievalOrchestrator._is_research_query(
        query="pediatric dental anxiety behavior management",
        purpose="Find clinical evidence",
    )

    assert not HealthcareRetrievalOrchestrator._is_research_query(
        query="pediatric dentists Houston TX",
        purpose="Find local pediatric dentists",
    )
