from __future__ import annotations

from connectors.provider_search.client import NPPESProviderClient
from connectors.pubmed.client import PubMedClient
from models import (
    SearchIntent,
    SearchPlan,
    SearchQuery,
    SearchResult,
    UserQuery,
)
from search.deduplication import deduplicate_results


class HealthcareRetrievalOrchestrator:
    """
    Coordinate retrieval across healthcare data sources.

    v0.2 introduced real NPPES and PubMed retrieval.

    v0.3 improves evidence-aware routing so a provider-discovery
    question can retrieve BOTH:

        1. provider evidence
        2. biomedical/scientific evidence

    This remains deterministic routing.

    Google ADK will later move more retrieval decisions into the
    Healthcare Research Agent.
    """

    RESEARCH_KEYWORDS = {
        "anxiety",
        "anxious",
        "behavior",
        "behaviour",
        "behavioral",
        "behavioural",
        "clinical",
        "evidence",
        "fear",
        "guideline",
        "intervention",
        "literature",
        "outcome",
        "outcomes",
        "research",
        "review",
        "sedation",
        "study",
        "systematic",
        "treatment",
    }

    RESEARCH_PURPOSE_PHRASES = {
        "scientific evidence",
        "clinical evidence",
        "biomedical evidence",
        "research evidence",
        "systematic review",
        "clinical research",
        "behavior management",
        "behaviour management",
        "sedation evidence",
        "anxiety evidence",
    }

    def __init__(
        self,
        provider_client: NPPESProviderClient | None = None,
        pubmed_client: PubMedClient | None = None,
    ) -> None:
        """
        Allow dependency injection so unit tests can use fake clients.

        Production code defaults to the real NPPES and PubMed clients.
        """

        self.provider_client = provider_client or NPPESProviderClient()

        self.pubmed_client = pubmed_client or PubMedClient()

    def retrieve(
        self,
        user_query: UserQuery,
        plan: SearchPlan,
        city: str,
        state: str,
        provider_limit: int = 10,
        pubmed_limit: int = 5,
    ) -> list[SearchResult]:
        """
        Execute retrieval for a healthcare search plan.

        Current v0.3 behavior:

        Provider discovery:
            -> NPPES retrieves provider candidates using the
               structured specialty from UserQuery.

        Scientific/research queries:
            -> PubMed retrieves biomedical literature for each
               evidence-oriented search query.

        Results are combined and deduplicated before being returned.

        NOTE:

        city/state remain explicit parameters for now because
        UserQuery.location is currently a display string such as
        "Houston, TX".

        We intentionally avoid fragile location-string parsing.
        """

        results: list[SearchResult] = []

        # ---------------------------------------------------------
        # PROVIDER DISCOVERY
        # ---------------------------------------------------------
        #
        # NPPES retrieval is driven by structured query fields rather
        # than every generated Gemini query.
        #
        # This prevents us from repeatedly calling NPPES with five
        # variations of essentially the same specialty/location query.
        #
        if (
            user_query.intent == SearchIntent.PROVIDER_DISCOVERY
            or plan.intent == SearchIntent.PROVIDER_DISCOVERY
        ):
            specialty = user_query.specialty

            if not specialty:
                raise ValueError("Provider discovery requires UserQuery.specialty.")

            provider_results = self.provider_client.search(
                taxonomy_description=specialty,
                city=city,
                state=state,
                limit=provider_limit,
            )

            results.extend(provider_results)

        # ---------------------------------------------------------
        # SCIENTIFIC EVIDENCE RETRIEVAL
        # ---------------------------------------------------------
        #
        # SearchPlan queries whose query text OR purpose indicate
        # scientific/clinical research are routed to PubMed.
        #
        # This is intentionally deterministic and explainable.
        #
        # Example:
        #
        #   pediatric dental anxiety behavior management
        #   systematic review
        #
        # should go to PubMed, while:
        #
        #   pediatric dentists Houston TX
        #
        # should not.
        #
        for search_query in plan.generated_queries:
            if not self._is_research_query(search_query):
                continue

            pubmed_results = self.pubmed_client.search(
                query=search_query.query,
                max_results=pubmed_limit,
            )

            results.extend(pubmed_results)

        # ---------------------------------------------------------
        # DEDUPLICATION
        # ---------------------------------------------------------
        #
        # Multiple scientific queries may retrieve the same PMID.
        #
        # Removing duplicates is important because duplicate evidence
        # must not artificially increase its importance in later
        # evidence ranking.
        #
        return deduplicate_results(results)

    @classmethod
    def _is_research_query(
        cls,
        search_query: SearchQuery,
    ) -> bool:
        """
        Decide whether a generated query belongs in PubMed.

        We examine BOTH:

            search_query.query
            search_query.purpose

        Purpose-aware routing is important because Gemini may generate
        a scientifically valid query without using one exact keyword
        we happened to anticipate.

        This remains a lightweight baseline.

        Later, Google ADK will allow the Healthcare Research Agent to
        choose tools dynamically.
        """

        query_text = search_query.query.lower()
        purpose_text = search_query.purpose.lower()

        # Strong signal:
        # the planner explicitly says this query exists to retrieve
        # scientific or clinical evidence.
        if any(phrase in purpose_text for phrase in cls.RESEARCH_PURPOSE_PHRASES):
            return True

        # Secondary signal:
        # biomedical/research terminology appears in either the query
        # itself or its stated purpose.
        combined_text = f"{query_text} {purpose_text}"

        words = set(combined_text.replace("/", " ").replace("-", " ").split())

        if words.intersection(cls.RESEARCH_KEYWORDS):
            return True

        return False
