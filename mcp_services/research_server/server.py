"""
Healthcare Research MCP Server.

Exposes biomedical literature retrieval through the Model Context Protocol
while reusing the project's existing PubMed connector.
"""

from mcp.server.mcpserver import MCPServer

from mcp_services.research_server.tools import search_pubmed

mcp = MCPServer(
    "healthcare-research",
    instructions=(
        "Provides biomedical literature retrieval using PubMed. "
        "Scientific literature supports general clinical context and must "
        "not be treated as provider-specific evidence."
    ),
)


@mcp.tool()
def search_biomedical_literature(
    query: str,
    limit: int = 5,
) -> list[dict]:
    """
    Search PubMed for biomedical evidence.

    This MCP tool delegates to the existing PubMed retrieval implementation.
    """

    return search_pubmed(
        query=query,
        limit=limit,
    )


if __name__ == "__main__":
    mcp.run()
