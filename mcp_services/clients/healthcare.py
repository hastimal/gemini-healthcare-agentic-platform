"""
Async MCP-backed healthcare retrieval clients.

Google ADK executes tools inside an asyncio event loop. Therefore MCP
operations exposed to the ADK workflow must remain asynchronous instead
of attempting to create a nested event loop.

These adapters return the project's shared SearchResult models so the
existing ranking, grounding, citation, and answer pipeline remains
unchanged.
"""

from __future__ import annotations

from typing import Any

from mcp import Client

from mcp_services.research_server.server import mcp as research_mcp
from mcp_services.search_server.server import mcp as search_mcp
from models import SearchResult


def _extract_results(result: Any) -> list[SearchResult]:
    """
    Convert structured MCP tool output into shared SearchResult models.
    """

    structured = result.structured_content or {}
    records = structured.get("result", [])

    return [
        SearchResult.model_validate(record)
        for record in records
    ]


class MCPProviderClient:
    """
    Async provider client backed by the Search MCP Server.
    """

    async def search(
        self,
        taxonomy_description: str,
        city: str,
        state: str,
        limit: int = 10,
    ) -> list[SearchResult]:
        async with Client(search_mcp) as client:
            result = await client.call_tool(
                "find_healthcare_providers",
                {
                    "specialty": taxonomy_description,
                    "city": city,
                    "state": state,
                    "limit": limit,
                },
            )

        if result.is_error:
            raise RuntimeError(
                "Search MCP Server returned an error while retrieving providers."
            )

        return _extract_results(result)


class MCPPubMedClient:
    """
    Async biomedical research client backed by the Research MCP Server.
    """

    async def search(
        self,
        query: str,
        max_results: int = 5,
    ) -> list[SearchResult]:
        async with Client(research_mcp) as client:
            result = await client.call_tool(
                "search_biomedical_literature",
                {
                    "query": query,
                    "limit": max_results,
                },
            )

        if result.is_error:
            raise RuntimeError(
                "Research MCP Server returned an error while retrieving "
                "PubMed evidence."
            )

        return _extract_results(result)
