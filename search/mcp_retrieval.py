"""
Async healthcare retrieval orchestration for MCP-backed tools.

v0.9 makes planner state authoritative for retrieval:
- provider location is derived from UserQuery.location
- provider specialty is derived from UserQuery.specialty
- biomedical/health-information intents route to PubMed
- explicit FHIR/interoperability queries route to the matching FHIR MCP tool
- unsupported intents fail explicitly instead of silently becoming provider search

FHIR remains test/interoperability evidence, not proof of provider quality,
licensure, credentials, suitability, or real-world availability.
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
from search.location import parse_us_provider_location
from search.retrieval import HealthcareRetrievalOrchestrator

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

PUBMED_INTENTS = {
    SearchIntent.BIOMEDICAL_RESEARCH,
    SearchIntent.HEALTH_INFORMATION,
}

UNSUPPORTED_RETRIEVAL_INTENTS = {
    SearchIntent.CARE_PROGRAM_DISCOVERY,
    SearchIntent.CLINICAL_TRIALS,
}


class MCPHealthcareRetrievalOrchestrator:
    """
    Async MCP-backed healthcare retrieval orchestrator.

    v0.9 routing:
        PROVIDER_DISCOVERY
            -> NPPES using structured specialty + location
            -> PubMed only for evidence-oriented generated queries

        BIOMEDICAL_RESEARCH / HEALTH_INFORMATION
            -> PubMed for generated queries

        explicit FHIR/interoperability query
            -> matching FHIR MCP resource lookup, at most once

        CARE_PROGRAM_DISCOVERY / CLINICAL_TRIALS
            -> explicit unsupported-retrieval error until a connector is added
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
        provider_limit: int = 10,
        pubmed_limit: int = 5,
        fhir_limit: int = 3,
    ) -> list[SearchResult]:
        """
        Execute MCP-backed retrieval from authoritative planner state.

        Provider discovery currently uses the US NPPES registry. Therefore
        provider queries require UserQuery.location to contain a US city/state.
        Non-provider intents do not require a location.
        """
        results: list[SearchResult] = []

        intent = user_query.intent or plan.intent
        if intent != plan.intent:
            raise ValueError(
                "Planner state intent mismatch: UserQuery.intent and SearchPlan.intent "
                "must agree."
            )

        if intent in UNSUPPORTED_RETRIEVAL_INTENTS:
            raise NotImplementedError(
                f"Retrieval for intent '{intent.value}' is not implemented yet. "
                "The planner may classify this healthcare query, but v0.9 does not "
                "silently route it to NPPES or another unrelated source."
            )

        city: str | None = None
        state: str | None = None

        # -------------------------------------------------------------
        # 1. Provider discovery
        # -------------------------------------------------------------
        if intent == SearchIntent.PROVIDER_DISCOVERY:
            specialty = user_query.specialty
            if not specialty:
                raise ValueError(
                    "Provider discovery requires UserQuery.specialty."
                )

            city, state = parse_us_provider_location(user_query.location)

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
        fhir_retrieved = False

        for search_query in plan.generated_queries:
            # Research-only and health-information intents are themselves a
            # strong enough signal for PubMed. Provider discovery remains
            # selective so ordinary location/provider fan-out does not hit
            # PubMed unnecessarily.
            should_search_pubmed = (
                intent in PUBMED_INTENTS
                or (
                    intent == SearchIntent.PROVIDER_DISCOVERY
                    and HealthcareRetrievalOrchestrator._is_research_query(
                        search_query
                    )
                )
            )

            if should_search_pubmed:
                pubmed_results = await self.pubmed_client.search(
                    query=search_query.query,
                    max_results=pubmed_limit,
                )
                results.extend(pubmed_results)

            if not fhir_retrieved and self._is_fhir_query(search_query):
                fhir_results = await self._retrieve_fhir(
                    search_query=search_query,
                    user_query=user_query,
                    city=city,
                    state=state,
                    limit=fhir_limit,
                )
                results.extend(fhir_results)
                fhir_retrieved = True

        return deduplicate_results(results)

    async def _retrieve_fhir(
        self,
        search_query: SearchQuery,
        user_query: UserQuery,
        city: str | None,
        state: str | None,
        limit: int,
    ) -> list[SearchResult]:
        """
        Route one explicit FHIR query to the most relevant supported resource.

        Public HAPI FHIR data is demonstrative/test data. Returned records must
        not be interpreted as verified providers, licensure, quality, or
        availability evidence.
        """
        text = f"{search_query.query} {search_query.purpose}".lower()

        if "healthcareservice" in text or "healthcare service" in text:
            return await self.fhir_client.search_healthcare_services(limit=limit)

        if "location" in text and "practitionerrole" not in text:
            return await self.fhir_client.search_locations(
                city=city,
                state=state,
                limit=limit,
            )

        if "organization" in text and "practitionerrole" not in text:
            return await self.fhir_client.search_organizations(limit=limit)

        if (
            "practitioner" in text
            and "practitionerrole" not in text
            and "practitioner role" not in text
        ):
            return await self.fhir_client.search_practitioners(limit=limit)

        # Default explicit FHIR/interoperability path remains PractitionerRole,
        # preserving v0.7 behavior while removing specialty/location hardcoding.
        fhir_results = await self.fhir_client.search_practitioner_roles(
            specialty=user_query.specialty,
            limit=limit,
        )

        # Public HAPI development-server fallback: if a specialty-filtered
        # PractitionerRole lookup returns nothing, demonstrate the FHIR path
        # with unfiltered test records. These records are not specialty or
        # provider recommendations.
        if not fhir_results and user_query.specialty:
            fhir_results = await self.fhir_client.search_practitioner_roles(
                limit=limit,
            )

        return fhir_results

    @staticmethod
    def _is_fhir_query(search_query: SearchQuery) -> bool:
        """
        Return True only for explicit FHIR/interoperability queries.
        """
        query_text = search_query.query.lower()
        purpose_text = search_query.purpose.lower()

        if any(
            phrase in purpose_text
            for phrase in FHIR_PURPOSE_PHRASES
        ):
            return True

        return any(
            keyword in query_text
            for keyword in FHIR_KEYWORDS
        )
