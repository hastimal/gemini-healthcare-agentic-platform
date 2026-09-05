from unittest.mock import Mock, patch

from mcp_services.search_server.tools import find_providers
from models.search import SearchResult, SourceType


def test_find_providers_uses_existing_nppes_client():
    mock_result = SearchResult(
        source_type=SourceType.PROVIDER,
        title="TEST PEDIATRIC DENTIST",
        url="https://example.com/provider",
        snippet="Test provider",
        content=None,
        provider_name="TEST PEDIATRIC DENTIST",
        location="123 TEST ST HOUSTON, TX 77001",
        retrieved_by="nppes",
        query_used="Dentist, Pediatric Dentistry",
        metadata={
            "npi": "1234567890",
            "taxonomy_description": "Dentist, Pediatric Dentistry",
            "city": "HOUSTON",
            "state": "TX",
        },
    )

    mock_client = Mock()
    mock_client.search.return_value = [mock_result]

    with patch(
        "mcp_services.search_server.tools.NPPESProviderClient",
        return_value=mock_client,
    ):
        results = find_providers(
            specialty="Pediatric Dentistry",
            city="Houston",
            state="TX",
            limit=3,
        )

    mock_client.search.assert_called_once_with(
        taxonomy_description="Pediatric Dentistry",
        city="Houston",
        state="TX",
        limit=3,
    )

    assert len(results) == 1
    assert results[0]["provider_name"] == "TEST PEDIATRIC DENTIST"
    assert results[0]["source_type"] == "provider"
    assert results[0]["metadata"]["npi"] == "1234567890"
