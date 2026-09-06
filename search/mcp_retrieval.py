"""
Async healthcare retrieval orchestration for MCP-backed tools.

This module preserves the deterministic retrieval behavior introduced
in earlier versions while providing an async execution path suitable
for Google ADK and MCP.

v0.7 extends the MCP retrieval path with FHIR interoperability evidence.

FHIR is intentionally treated as an interoperability/data-structure
source rather than proof of provider quality, licensure, or suitability.

The original synchronous HealthcareRetrievalOrchestrator remains
unchanged so historical retrieval behavior and tests remain intact.
"""

from __future__ import annotations

from mcp_services.clients.healthcare import (
    MCPFHIRClient,
    MCPProviderClient,
    MCPPubMedClient,
)
from models import (
    SearchIntent,
    SearchPlan,
    SearchQuery,
    SearchResult,
    UserQuery,
)
from search.deduplication import deduplicate_results
from search.retrieval import HealthcareRetrievalOrchestrator

# FHIR retrieval is intentionally opt-in.
#
# Ordinary healthcare/provider queries must not automatically trigger
# FHIR retrieval simply because they contain generic healthcare words.
#
# These terms identify queries that explicitly ask for FHIR or
# interoperability-oriented evidence.
FHIR_KEYWORDS = {
    "fhir",
    "interoperability",
    "practitionerrole",
    "practitioner role",
    "healthcare structure",
    "healthcare organization",
    "healthcare service",
}


FHIR_PURPOSE_PHRASES = {
    "fhir interoperability",
    "healthcare interoperability",
    "structured healthcare data",
    "standardized healthcare data",
    "fhir practitioner role",
    "fhir practitionerrole",
}


class MCPHealthcareRetrievalOrchestrator:
    """
    Async MCP-backed healthcare retrieval orchestrator.

    Current v0.7 routing:

        Provider discovery
            -> Search MCP
            -> NPPES

        Biomedical/research query
            -> Research MCP
            -> PubMed

        Explicit FHIR/interoperability query
            -> FHIR MCP
            -> FHIR R4 server

    FHIR retrieval is performed at most once per workflow.

    Important safety boundary:

    FHIR records from the public HAPI test server are used to demonstrate
    standardized healthcare interoperability. They are not treated as
    independent verification of provider quality, active licensure,
    credentials, specialty suitability, or real-world service availability.
    """

    def __init__(
        self,
        provider_client: MCPProviderClient | None = None,
        pubmed_client: MCPPubMedClient | None = None,
        fhir_client: MCPFHIRClient | None = None,
    ) -> None:
        self.provider_client = provider_client or MCPProviderClient()
        self.pubmed_client = pubmed_client or MCPPubMedClient()
        self.fhir_client = fhir_client or MCPFHIRClient()

    async def retrieve(
        self,
        user_query: UserQuery,
        plan: SearchPlan,
        city: str,
        state: str,
        provider_limit: int = 10,
        pubmed_limit: int = 5,
        fhir_limit: int = 3,
    ) -> list[SearchResult]:
        """
        Execute MCP-backed healthcare retrieval.

        Provider candidates are retrieved once for provider-discovery
        workflows.

        Generated research queries are routed to PubMed according to the
        deterministic routing rules inherited from the synchronous
        HealthcareRetrievalOrchestrator.

        Explicit FHIR/interoperability queries trigger one FHIR lookup.
        """

        results: list[SearchResult] = []

        # -------------------------------------------------------------
        # 1. Provider discovery
        # -------------------------------------------------------------
        #
        # Provider discovery remains deterministic and occurs once.
        #
        # NPPES establishes registry identity/taxonomy/location evidence.
        # It does not independently establish provider quality, board
        # certification, active licensure, or suitability.
        if (
            user_query.intent == SearchIntent.PROVIDER_DISCOVERY
            or plan.intent == SearchIntent.PROVIDER_DISCOVERY
        ):
            specialty = user_query.specialty

            if not specialty:
                raise ValueError(
                    "Provider discovery requires UserQuery.specialty."
                )

            provider_results = await self.provider_client.search(
                taxonomy_description=specialty,
                city=city,
                state=state,
                limit=provider_limit,
            )

            results.extend(provider_results)

        # -------------------------------------------------------------
        # 2. Generated-query routing
        # -------------------------------------------------------------

        # FHIR should execute at most once during one retrieval workflow,
        # even if Gemini generates multiple interoperability queries.
        fhir_retrieved = False

        for search_query in plan.generated_queries:

            # ---------------------------------------------------------
            # PubMed research routing
            # ---------------------------------------------------------
            #
            # Reuse the deterministic research classifier from the
            # synchronous pipeline instead of creating a second,
            # potentially divergent PubMed-routing policy.
            if HealthcareRetrievalOrchestrator._is_research_query(
                search_query
            ):
                pubmed_results = await self.pubmed_client.search(
                    query=search_query.query,
                    max_results=pubmed_limit,
                )

                results.extend(pubmed_results)

            # ---------------------------------------------------------
            # FHIR interoperability routing
            # ---------------------------------------------------------
            #
            # FHIR retrieval is independent from PubMed routing.
            # A generated query may be biomedical, interoperability-
            # oriented, neither, or theoretically both.
            if (
                not fhir_retrieved
                and self._is_fhir_query(search_query)
            ):
                # First attempt the semantically useful specialty-filtered
                # PractitionerRole lookup.
                #
                # On a real healthcare FHIR server, PractitionerRole
                # specialty may contain coded values that can be searched
                # according to that publisher's terminology configuration.
                fhir_results = (
                    await self.fhir_client.search_practitioner_roles(
                        specialty=user_query.specialty,
                        limit=fhir_limit,
                    )
                )

                # -----------------------------------------------------
                # Public HAPI development-server fallback
                # -----------------------------------------------------
                #
                # The project's default development endpoint is the
                # public HAPI FHIR R4 test server.
                #
                # We validated that a free-text search such as:
                #
                #     specialty="Pediatric Dentistry"
                #
                # can legitimately return zero PractitionerRole records,
                # while the same public endpoint contains unfiltered
                # PractitionerRole test records.
                #
                # Therefore, when the specialty-filtered lookup returns
                # nothing, v0.7 falls back to an unfiltered
                # PractitionerRole request.
                #
                # The purpose of this fallback is ONLY to demonstrate the
                # complete interoperability path:
                #
                #     Google ADK
                #         -> Healthcare Research Agent
                #         -> MCP retrieval
                #         -> FHIR MCP server
                #         -> FHIRClient
                #         -> HAPI FHIR R4
                #         -> normalized SearchResult
                #
                # These fallback records must NOT be interpreted as:
                #
                # - matching the requested specialty
                # - matching the requested location
                # - recommended providers
                # - proof of licensure
                # - proof of credentials
                # - proof of clinical quality
                # - proof of service availability
                #
                # The evidence-ranking layer separately prevents public
                # HAPI FHIR records from consuming provider-recommendation
                # grounding slots.
                if (
                    not fhir_results
                    and user_query.specialty
                ):
                    fhir_results = (
                        await self.fhir_client.search_practitioner_roles(
                            limit=fhir_limit,
                        )
                    )

                results.extend(fhir_results)

                # Mark FHIR retrieval complete even when the public test
                # server returns no data. This prevents multiple generated
                # FHIR queries from repeatedly hitting the endpoint during
                # one workflow.
                fhir_retrieved = True

        # -------------------------------------------------------------
        # 3. Shared deduplication
        # -------------------------------------------------------------
        #
        # Provider NPIs, PubMed PMIDs, and normalized URLs continue to use
        # the shared deterministic deduplication layer.
        return deduplicate_results(results)

    @staticmethod
    def _is_fhir_query(
        search_query: SearchQuery,
    ) -> bool:
        """
        Return True only for explicit FHIR/interoperability queries.

        FHIR is deliberately opt-in in v0.7.

        Generic provider or biomedical searches should continue through
        NPPES/PubMed without automatically invoking a FHIR server.
        """

        query_text = search_query.query.lower()
        purpose_text = search_query.purpose.lower()

        # Purpose is usually the strongest signal because Gemini describes
        # why the generated query exists.
        if any(
            phrase in purpose_text
            for phrase in FHIR_PURPOSE_PHRASES
        ):
            return True

        # Query text provides a second explicit signal.
        return any(
            keyword in query_text
            for keyword in FHIR_KEYWORDS
        )
