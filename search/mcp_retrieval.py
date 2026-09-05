"""
Async healthcare retrieval orchestration for MCP-backed tools.

This module preserves the deterministic retrieval behavior introduced
in earlier versions while providing an async execution path suitable
for Google ADK and MCP.

The original HealthcareRetrievalOrchestrator remains unchanged so the
existing synchronous pipeline and historical tests continue to work.
"""

from __future__ import annotations

from mcp_services.clients.healthcare import MCPProviderClient, MCPPubMedClient
from models import SearchIntent, SearchPlan, SearchResult, UserQuery
from search.deduplication import deduplicate_results
from search.retrieval import HealthcareRetrievalOrchestrator


class MCPHealthcareRetrievalOrchestrator:
    """
    Async MCP-backed healthcare retrieval orchestrator.

    Routing semantics intentionally match HealthcareRetrievalOrchestrator:

    - Provider discovery retrieves provider candidates once.
    - Research-oriented generated queries are routed to PubMed.
    - Combined evidence is deduplicated before returning.
    """

    def __init__(
        self,
        provider_client: MCPProviderClient | None = None,
        pubmed_client: MCPPubMedClient | None = None,
    ) -> None:
        self.provider_client = provider_client or MCPProviderClient()
        self.pubmed_client = pubmed_client or MCPPubMedClient()

    async def retrieve(
        self,
        user_query: UserQuery,
        plan: SearchPlan,
        city: str,
        state: str,
        provider_limit: int = 10,
        pubmed_limit: int = 5,
    ) -> list[SearchResult]:
        """
        Execute MCP-backed provider and biomedical retrieval.
        """

        results: list[SearchResult] = []

        # Provider discovery remains deterministic and is performed once.
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

        # Preserve the existing research-query routing rules from the
        # synchronous orchestrator rather than duplicating those rules.
        for search_query in plan.generated_queries:
            if not HealthcareRetrievalOrchestrator._is_research_query(
                search_query
            ):
                continue

            pubmed_results = await self.pubmed_client.search(
                query=search_query.query,
                max_results=pubmed_limit,
            )

            results.extend(pubmed_results)

        return deduplicate_results(results)
