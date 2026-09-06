"""
MCP tools for FHIR healthcare interoperability.

This layer exposes the project's existing FHIR connector through MCP.

Important design rule:
MCP is only the protocol and tool boundary. FHIRClient continues to own
FHIR REST communication and normalization into the project's shared
SearchResult model.

Initial v0.7 scope is intentionally limited to non-patient,
healthcare-discovery resources:

- Practitioner
- PractitionerRole
- Organization
- Location
- HealthcareService
"""

from connectors.fhir.client import FHIRClient


def find_fhir_practitioners(
    name: str | None = None,
    limit: int = 10,
) -> list[dict]:
    """
    Search FHIR Practitioner resources.

    Practitioner represents healthcare professionals.

    This tool does not establish provider quality, current licensure,
    credential validity, or suitability for a particular patient.
    """

    client = FHIRClient()

    results = client.search_practitioners(
        name=name,
        limit=limit,
    )

    return [result.model_dump(mode="json") for result in results]


def find_fhir_practitioner_roles(
    specialty: str | None = None,
    practitioner: str | None = None,
    organization: str | None = None,
    limit: int = 10,
) -> list[dict]:
    """
    Search FHIR PractitionerRole resources.

    PractitionerRole can connect practitioners with organizations,
    specialties, and locations.

    Relationships are reported exactly as represented by the FHIR source
    and must not be interpreted as independent verification of credentials
    or license standing.
    """

    client = FHIRClient()

    results = client.search_practitioner_roles(
        specialty=specialty,
        practitioner=practitioner,
        organization=organization,
        limit=limit,
    )

    return [result.model_dump(mode="json") for result in results]


def find_fhir_organizations(
    name: str | None = None,
    limit: int = 10,
) -> list[dict]:
    """
    Search FHIR Organization resources.

    Organization represents healthcare-related organizational entities.
    """

    client = FHIRClient()

    results = client.search_organizations(
        name=name,
        limit=limit,
    )

    return [result.model_dump(mode="json") for result in results]


def find_fhir_locations(
    name: str | None = None,
    city: str | None = None,
    state: str | None = None,
    limit: int = 10,
) -> list[dict]:
    """
    Search FHIR Location resources.

    Location describes physical or logical places where healthcare
    services may be delivered.
    """

    client = FHIRClient()

    results = client.search_locations(
        name=name,
        city=city,
        state=state,
        limit=limit,
    )

    return [result.model_dump(mode="json") for result in results]


def find_fhir_healthcare_services(
    name: str | None = None,
    limit: int = 10,
) -> list[dict]:
    """
    Search FHIR HealthcareService resources.

    HealthcareService describes services represented by the FHIR source.

    Presence of a service resource must not be converted into unsupported
    claims about clinical quality or patient suitability.
    """

    client = FHIRClient()

    results = client.search_healthcare_services(
        name=name,
        limit=limit,
    )

    return [result.model_dump(mode="json") for result in results]
