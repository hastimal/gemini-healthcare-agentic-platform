"""
Healthcare Search MCP Server.

Exposes provider discovery as a Model Context Protocol tool while reusing
the project's existing CMS NPPES connector.
"""

from mcp.server.mcpserver import MCPServer

from mcp_services.search_server.tools import find_providers

mcp = MCPServer(
    "healthcare-search",
    instructions=(
        "Provides healthcare provider discovery using public CMS NPPES "
        "registry data. Registry information supports provider identity, "
        "reported location, NPI, and taxonomy. It must not be treated as "
        "proof of clinical quality, active license standing, or "
        "provider-specific services."
    ),
)


@mcp.tool()
def find_healthcare_providers(
    specialty: str,
    city: str,
    state: str,
    limit: int = 10,
) -> list[dict]:
    """
    Find healthcare providers from CMS NPPES.

    This MCP tool delegates to the existing provider-search implementation.
    """

    return find_providers(
        specialty=specialty,
        city=city,
        state=state,
        limit=limit,
    )


if __name__ == "__main__":
    mcp.run()
