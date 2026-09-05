"""
MCP tools for biomedical research retrieval.

This layer exposes the project's existing PubMed retrieval capability
through MCP.

Important design rule:
MCP is only the tool/protocol boundary. The existing PubMedClient
continues to own communication with NCBI PubMed and normalization of
biomedical literature results.
"""

from connectors.pubmed.client import PubMedClient


def search_pubmed(
    query: str,
    limit: int = 5,
) -> list[dict]:
    """
    Search PubMed for biomedical literature.

    Parameters
    ----------
    query:
        PubMed search query.

    limit:
        Maximum number of normalized PubMed records to return.

    Returns
    -------
    list[dict]
        Normalized biomedical evidence produced by the existing
        PubMedClient.

    Safety boundary
    ---------------
    PubMed evidence supports general scientific context. It must not be
    converted into unsupported provider-specific claims, such as assuming
    a provider offers a treatment or follows a particular clinical protocol.
    """

    client = PubMedClient()

    # Keep the MCP-facing interface consistent with our other tools by using
    # "limit", while the existing PubMed connector uses "max_results".
    results = client.search(
        query=query,
        max_results=limit,
    )

    return [result.model_dump(mode="json") for result in results]
