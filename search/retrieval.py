from __future__ import annotations

from connectors.provider_search.client import NPPESProviderClient
from connectors.pubmed.client import PubMedClient
from models import SearchPlan, SearchResult, UserQuery
from search.deduplication import deduplicate_results


class HealthcareRetrievalOrchestrator:
    """
    Coordinate retrieval across healthcare evidence sources.

    Current v0.2 retrieval sources:

    1. NPPES
       Used for structured healthcare-provider discovery.

    2. PubMed
       Used for scientific and clinical literature.

    Architecture principle:

        UserQuery
            -> Gemini SearchPlan
            -> Retrieval Orchestrator
            -> Real external sources
            -> SearchResult[]
            -> Deduplication
            -> Evidence Pool

    Gemini plans the research.

    Retrieval tools supply the facts.

    Gemini should NOT invent providers or scientific evidence.
    """

    def __init__(
        self,
        provider_client: NPPESProviderClient | None = None,
        pubmed_client: PubMedClient | None = None,
    ) -> None:
        """
        Allow retrieval clients to be injected.

        This lets production code use real NPPES/PubMed clients while
        unit tests can use fake clients without making network calls.
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
        Execute retrieval for a Gemini-generated SearchPlan.

        The original UserQuery is passed alongside SearchPlan because
        it contains structured user constraints such as specialty.

        Example:

            user_query.specialty = "Pediatric Dentistry"

        That value is passed dynamically to NPPES.

        IMPORTANT:
        The retrieval orchestrator does NOT hard-code a healthcare
        specialty. This makes the architecture reusable for future
        searches such as cardiology, dermatology, etc.

        City and state remain explicit parameters for v0.2 because the
        current UserQuery stores location as a display string such as
        "Houston, TX".

        We will introduce structured location modeling separately
        instead of attempting fragile string parsing here.
        """

        results: list[SearchResult] = []

        # ---------------------------------------------------------
        # PROVIDER DISCOVERY
        # ---------------------------------------------------------
        #
        # Provider discovery is performed when Gemini classified the
        # user's request as provider_discovery.
        #
        # Specialty comes from UserQuery rather than being hard-coded
        # inside this orchestrator.
        if plan.intent.value == "provider_discovery":
            specialty = user_query.specialty

            # Provider discovery requires a specialty.
            #
            # We intentionally fail clearly instead of silently
            # searching for an arbitrary provider type.
            if not specialty:
                raise ValueError("Provider discovery requires user_query.specialty.")

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
        # Not every Gemini-generated query should go to PubMed.
        #
        # Example:
        #
        #     "pediatric dentists Houston TX"
        #
        # belongs primarily to provider discovery.
        #
        # But:
        #
        #     "pediatric dental anxiety behavior management"
        #
        # is appropriate for PubMed.
        #
        # For v0.2 we use transparent keyword routing.
        # Later, ADK agents will make richer tool-use decisions.
        research_queries = [
            search_query
            for search_query in plan.generated_queries
            if self._is_research_query(
                query=search_query.query,
                purpose=search_query.purpose,
            )
        ]

        for search_query in research_queries:
            pubmed_results = self.pubmed_client.search(
                query=search_query.query,
                max_results=pubmed_limit,
            )

            results.extend(pubmed_results)

        # ---------------------------------------------------------
        # DEDUPLICATION
        # ---------------------------------------------------------
        #
        # Multiple fan-out queries can retrieve the same PubMed
        # article or provider.
        #
        # Deduplicate before evidence ranking so repeated retrieval
        # does not artificially increase a source's importance.
        return deduplicate_results(results)

    @staticmethod
    def _is_research_query(
        query: str,
        purpose: str,
    ) -> bool:
        """
        Decide whether a fan-out query belongs in PubMed.

        This is intentionally transparent and simple for v0.2.

        Later, the Healthcare Research Agent built with Google ADK
        will decide which MCP/retrieval tools should handle a query.
        """

        text = f"{query} {purpose}".lower()

        research_keywords = {
            "anxiety",
            "behavior",
            "behaviour",
            "sedation",
            "evidence",
            "study",
            "research",
            "clinical",
            "systematic review",
            "fear",
            "guideline",
        }

        return any(keyword in text for keyword in research_keywords)
