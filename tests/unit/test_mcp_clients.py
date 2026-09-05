"""
Tests for the async MCP-backed healthcare clients.

These tests protect the Google ADK -> async MCP boundary introduced
in v0.6 without making live calls to CMS NPPES or PubMed.
"""

from types import SimpleNamespace

import pytest

import mcp_services.clients.healthcare as healthcare_clients
from models import SourceType


class FakeMCPClient:
    """
    Minimal async MCP Client replacement used by unit tests.
    """

    def __init__(self, server, result):
        self.server = server
        self.result = result
        self.tool_name = None
        self.arguments = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        return False

    async def call_tool(self, tool_name, arguments):
        self.tool_name = tool_name
        self.arguments = arguments
        return self.result


@pytest.mark.asyncio
async def test_mcp_provider_client_calls_search_mcp(monkeypatch):
    """
    Provider retrieval should call the Search MCP tool asynchronously
    and convert its structured output into SearchResult models.
    """

    mcp_result = SimpleNamespace(
        is_error=False,
        structured_content={
            "result": [
                {
                    "source_type": "provider",
                    "title": "TEST PEDIATRIC DENTIST DDS",
                    "url": "https://example.com/provider/123",
                    "snippet": "Pediatric dentist in Houston",
                    "provider_name": "TEST PEDIATRIC DENTIST DDS",
                    "location": "Houston, TX",
                    "retrieved_by": "nppes",
                    "query_used": "Dentist, Pediatric Dentistry",
                    "metadata": {
                        "npi": "1234567890",
                        "taxonomy_description": "Dentist, Pediatric Dentistry",
                    },
                }
            ]
        },
    )

    created_clients = []

    def fake_client_factory(server):
        client = FakeMCPClient(server, mcp_result)
        created_clients.append(client)
        return client

    monkeypatch.setattr(
        healthcare_clients,
        "Client",
        fake_client_factory,
    )

    client = healthcare_clients.MCPProviderClient()

    results = await client.search(
        taxonomy_description="Pediatric Dentistry",
        city="Houston",
        state="TX",
        limit=3,
    )

    assert len(results) == 1
    assert results[0].source_type == SourceType.PROVIDER
    assert results[0].provider_name == "TEST PEDIATRIC DENTIST DDS"

    assert len(created_clients) == 1
    assert created_clients[0].tool_name == "find_healthcare_providers"
    assert created_clients[0].arguments == {
        "specialty": "Pediatric Dentistry",
        "city": "Houston",
        "state": "TX",
        "limit": 3,
    }


@pytest.mark.asyncio
async def test_mcp_pubmed_client_calls_research_mcp(monkeypatch):
    """
    Biomedical retrieval should call the Research MCP tool
    asynchronously and return SearchResult models.
    """

    mcp_result = SimpleNamespace(
        is_error=False,
        structured_content={
            "result": [
                {
                    "source_type": "pubmed",
                    "title": "Pediatric Dental Anxiety Study",
                    "url": "https://pubmed.ncbi.nlm.nih.gov/12345678/",
                    "snippet": "Study of pediatric dental anxiety.",
                    "content": "Biomedical evidence about pediatric dental anxiety.",
                    "retrieved_by": "pubmed",
                    "query_used": "pediatric dental anxiety",
                    "metadata": {
                        "pmid": "12345678",
                        "journal": "Pediatric Dentistry",
                    },
                }
            ]
        },
    )

    created_clients = []

    def fake_client_factory(server):
        client = FakeMCPClient(server, mcp_result)
        created_clients.append(client)
        return client

    monkeypatch.setattr(
        healthcare_clients,
        "Client",
        fake_client_factory,
    )

    client = healthcare_clients.MCPPubMedClient()

    results = await client.search(
        query="pediatric dental anxiety",
        max_results=3,
    )

    assert len(results) == 1
    assert results[0].source_type == SourceType.PUBMED
    assert results[0].title == "Pediatric Dental Anxiety Study"

    assert len(created_clients) == 1
    assert (
        created_clients[0].tool_name
        == "search_biomedical_literature"
    )
    assert created_clients[0].arguments == {
        "query": "pediatric dental anxiety",
        "limit": 3,
    }
