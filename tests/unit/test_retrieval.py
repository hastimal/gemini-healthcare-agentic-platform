from models import (
    SearchIntent,
    SearchPlan,
    SearchQuery,
    SearchResult,
    SourceType,
    UserQuery,
)
from search.retrieval import (
    HealthcareRetrievalOrchestrator,
)


class FakeProviderClient:
    """
    Fake NPPES client used to test orchestration without making
    network calls.
    """

    def __init__(self) -> None:
        self.last_taxonomy: str | None = None
        self.last_city: str | None = None
        self.last_state: str | None = None

    def search(
        self,
        taxonomy_description: str,
        city: str,
        state: str,
        limit: int = 10,
    ) -> list[SearchResult]:
        """
        Record arguments so we can verify that the orchestrator passes
        the specialty dynamically from UserQuery.
        """

        self.last_taxonomy = taxonomy_description
        self.last_city = city
        self.last_state = state

        return [
            SearchResult(
                source_type=SourceType.PROVIDER,
                title="Example Pediatric Dentist",
                url=("https://npiregistry.cms.hhs.gov/provider-view/1234567890"),
                provider_name=("Example Pediatric Dentist"),
                location="Houston, TX",
                retrieved_by="nppes",
                query_used=taxonomy_description,
                metadata={
                    "npi": "1234567890",
                    "taxonomy": taxonomy_description,
                },
            )
        ]


class FakePubMedClient:
    """
    Fake PubMed client.

    Every research query intentionally returns the SAME PMID.

    This lets the test confirm that deduplication prevents duplicate
    scientific evidence from appearing multiple times.
    """

    def __init__(self) -> None:
        self.queries: list[str] = []

    def search(
        self,
        query: str,
        max_results: int = 5,
    ) -> list[SearchResult]:
        """
        Record routed PubMed queries and return deterministic evidence.
        """

        self.queries.append(query)

        return [
            SearchResult(
                source_type=SourceType.PUBMED,
                title=("Behavior management for pediatric dental anxiety"),
                url=("https://pubmed.ncbi.nlm.nih.gov/12345678/"),
                snippet=("Evidence about pediatric dental anxiety and behavior management."),
                content=("Evidence about pediatric dental anxiety and behavior management."),
                retrieved_by="pubmed",
                query_used=query,
                metadata={
                    "pmid": "12345678",
                    "publication_date": "2025",
                },
            )
        ]


def _user_query() -> UserQuery:
    """
    Shared provider-discovery query.
    """

    return UserQuery(
        text=("Find pediatric dentists in Houston for a child who is anxious about dental visits."),
        location="Houston, TX",
        specialty="Pediatric Dentistry",
        intent=SearchIntent.PROVIDER_DISCOVERY,
    )


def _search_plan() -> SearchPlan:
    """
    Build a mixed evidence-aware search plan.

    The plan deliberately contains:
    - provider discovery
    - scientific evidence
    - second scientific evidence query

    This models the behavior we now expect from Gemini.
    """

    user_query = _user_query()

    return SearchPlan(
        original_query=user_query,
        intent=SearchIntent.PROVIDER_DISCOVERY,
        generated_queries=[
            SearchQuery(
                query=("pediatric dentists Houston TX"),
                purpose="provider discovery",
                priority=1,
            ),
            SearchQuery(
                query=("pediatric dental anxiety behavior management systematic review"),
                purpose=("scientific evidence for pediatric dental anxiety"),
                priority=1,
            ),
            SearchQuery(
                query=("pediatric dentistry anxious children sedation evidence"),
                purpose=("scientific evidence for sedation approaches"),
                priority=2,
            ),
        ],
    )


def test_retrieval_orchestrator():
    """
    Validate the complete deterministic routing behavior.

    Expected final results:

        1 provider result
        1 unique PubMed result

    Even though TWO research queries are sent to PubMed, our fake
    PubMed client returns the same PMID for both.

    Deduplication should collapse those duplicates.
    """

    provider_client = FakeProviderClient()
    pubmed_client = FakePubMedClient()

    orchestrator = HealthcareRetrievalOrchestrator(
        provider_client=provider_client,
        pubmed_client=pubmed_client,
    )

    results = orchestrator.retrieve(
        user_query=_user_query(),
        plan=_search_plan(),
        city="Houston",
        state="TX",
        provider_limit=10,
        pubmed_limit=5,
    )

    # Dynamic specialty must be preserved.
    assert provider_client.last_taxonomy == "Pediatric Dentistry"

    assert provider_client.last_city == "Houston"
    assert provider_client.last_state == "TX"

    # Only the two evidence-oriented queries should be routed
    # to PubMed.
    assert len(pubmed_client.queries) == 2

    assert "pediatric dentists Houston TX" not in pubmed_client.queries

    # Provider + one deduplicated PubMed article.
    assert len(results) == 2

    source_types = {result.source_type for result in results}

    assert SourceType.PROVIDER in source_types
    assert SourceType.PUBMED in source_types


def test_research_query_routing():
    """
    Verify obvious scientific queries go to PubMed while a simple
    location/provider query does not.
    """

    scientific_query = SearchQuery(
        query=("pediatric dental anxiety behavior management systematic review"),
        purpose=("scientific evidence for pediatric dental anxiety"),
        priority=1,
    )

    provider_query = SearchQuery(
        query="pediatric dentists Houston TX",
        purpose="provider discovery",
        priority=1,
    )

    assert HealthcareRetrievalOrchestrator._is_research_query(scientific_query) is True

    assert HealthcareRetrievalOrchestrator._is_research_query(provider_query) is False


def test_research_routing_by_purpose():
    """
    The query itself may be concise, but an explicit scientific
    evidence purpose should still route it to PubMed.

    This makes routing less dependent on exact query wording.
    """

    query = SearchQuery(
        query="pediatric dentistry anxious children",
        purpose=("scientific evidence for behavior management"),
        priority=2,
    )

    assert HealthcareRetrievalOrchestrator._is_research_query(query) is True
