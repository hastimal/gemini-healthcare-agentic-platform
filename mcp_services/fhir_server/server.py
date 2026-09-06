"""
Healthcare FHIR MCP Server.

Exposes selected FHIR R4 healthcare interoperability resources through
Model Context Protocol while reusing the project's existing FHIR connector.

The v0.7 server intentionally excludes patient clinical resources and is
designed for non-PHI healthcare discovery and interoperability examples.
"""

from mcp.server.mcpserver import MCPServer

from mcp_services.fhir_server.tools import (
    find_fhir_healthcare_services,
    find_fhir_locations,
    find_fhir_organizations,
    find_fhir_practitioner_roles,
    find_fhir_practitioners,
)

mcp = MCPServer(
    "healthcare-fhir",
    instructions=(
        "Provides access to selected non-patient FHIR R4 healthcare "
        "resources including Practitioner, PractitionerRole, Organization, "
        "Location, and HealthcareService. FHIR relationships must not be "
        "treated as independent proof of provider quality, current license "
        "standing, credentials, or patient suitability. Patient clinical "
        "resources are intentionally outside the v0.7 scope."
    ),
)


@mcp.tool()
def search_fhir_practitioners(
    name: str | None = None,
    limit: int = 10,
) -> list[dict]:
    """
    Search FHIR Practitioner resources.
    """

    return find_fhir_practitioners(
        name=name,
        limit=limit,
    )


@mcp.tool()
def search_fhir_practitioner_roles(
    specialty: str | None = None,
    practitioner: str | None = None,
    organization: str | None = None,
    limit: int = 10,
) -> list[dict]:
    """
    Search FHIR PractitionerRole resources.
    """

    return find_fhir_practitioner_roles(
        specialty=specialty,
        practitioner=practitioner,
        organization=organization,
        limit=limit,
    )


@mcp.tool()
def search_fhir_organizations(
    name: str | None = None,
    limit: int = 10,
) -> list[dict]:
    """
    Search FHIR Organization resources.
    """

    return find_fhir_organizations(
        name=name,
        limit=limit,
    )


@mcp.tool()
def search_fhir_locations(
    name: str | None = None,
    city: str | None = None,
    state: str | None = None,
    limit: int = 10,
) -> list[dict]:
    """
    Search FHIR Location resources.
    """

    return find_fhir_locations(
        name=name,
        city=city,
        state=state,
        limit=limit,
    )


@mcp.tool()
def search_fhir_healthcare_services(
    name: str | None = None,
    limit: int = 10,
) -> list[dict]:
    """
    Search FHIR HealthcareService resources.
    """

    return find_fhir_healthcare_services(
        name=name,
        limit=limit,
    )


if __name__ == "__main__":
    mcp.run()
