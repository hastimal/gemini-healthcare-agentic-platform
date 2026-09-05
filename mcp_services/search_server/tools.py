"""
MCP tools for healthcare provider discovery.

This layer exposes the project's existing NPPES provider-search capability
through MCP.

Important design rule:
MCP is only the tool/protocol boundary. The existing NPPESProviderClient
continues to own communication with CMS NPPES and normalization of provider
records.
"""

from connectors.provider_search.client import NPPESProviderClient


def find_providers(
    specialty: str,
    city: str,
    state: str,
    limit: int = 10,
) -> list[dict]:
    """
    Find healthcare providers using CMS NPPES.

    Parameters
    ----------
    specialty:
        Provider specialty, for example "Pediatric Dentistry".

    city:
        City to search, for example "Houston".

    state:
        Two-letter state code, for example "TX".

    limit:
        Maximum number of normalized provider records to return.

    Returns
    -------
    list[dict]
        Normalized provider records produced by the existing
        NPPESProviderClient.

    Safety boundary
    ---------------
    NPPES can support provider identity, NPI, reported location, and taxonomy.
    It does not independently prove clinical quality, active license standing,
    patient satisfaction, or provider-specific treatment availability.
    """

    client = NPPESProviderClient()

    # The existing connector uses the NPPES API field name
    # "taxonomy_description" rather than the user-facing term "specialty".
    results = client.search(
        taxonomy_description=specialty,
        city=city,
        state=state,
        limit=limit,
    )

    return [result.model_dump(mode="json") for result in results]
