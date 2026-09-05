from unittest.mock import Mock, patch

from mcp_services.research_server.tools import search_pubmed
from models.search import SearchResult, SourceType


def test_search_pubmed_uses_existing_pubmed_client():
    mock_result = SearchResult(
        source_type=SourceType.PUBMED,
        title="Pediatric Dental Anxiety Study",
        url="https://pubmed.ncbi.nlm.nih.gov/12345678/",
        snippet="Study about pediatric dental anxiety.",
        content="Biomedical evidence about pediatric dental anxiety.",
        provider_name=None,
        location=None,
        retrieved_by="pubmed",
        query_used="pediatric dental anxiety",
        metadata={
            "pmid": "12345678",
            "journal": "Test Journal",
            "publication_date": "2026",
        },
    )

    mock_client = Mock()
    mock_client.search.return_value = [mock_result]

    with patch(
        "mcp_services.research_server.tools.PubMedClient",
        return_value=mock_client,
    ):
        results = search_pubmed(
            query="pediatric dental anxiety",
            limit=3,
        )

    mock_client.search.assert_called_once_with(
        query="pediatric dental anxiety",
        max_results=3,
    )

    assert len(results) == 1
    assert results[0]["title"] == "Pediatric Dental Anxiety Study"
    assert results[0]["source_type"] == "pubmed"
    assert results[0]["metadata"]["pmid"] == "12345678"
