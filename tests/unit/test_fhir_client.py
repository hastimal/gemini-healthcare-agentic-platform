import httpx

from connectors.fhir.client import FHIRClient
from models import SourceType


def _mock_transport(request: httpx.Request) -> httpx.Response:
    assert request.headers["accept"] == "application/fhir+json"

    resource_type = request.url.path.rstrip("/").split("/")[-1]

    resources = {
        "Practitioner": {
            "resourceType": "Practitioner",
            "id": "practitioner-1",
            "active": True,
            "name": [
                {
                    "given": ["Jane"],
                    "family": "Dentist",
                }
            ],
            "address": [
                {
                    "line": ["100 Main St"],
                    "city": "Houston",
                    "state": "TX",
                    "postalCode": "77001",
                }
            ],
        },
        "PractitionerRole": {
            "resourceType": "PractitionerRole",
            "id": "role-1",
            "practitioner": {
                "reference": "Practitioner/practitioner-1",
                "display": "Jane Dentist",
            },
            "organization": {
                "reference": "Organization/organization-1",
                "display": "Example Pediatric Dental Group",
            },
            "specialty": [
                {
                    "text": "Pediatric Dentistry",
                }
            ],
            "location": [
                {
                    "reference": "Location/location-1",
                    "display": "Downtown Clinic",
                }
            ],
        },
        "Organization": {
            "resourceType": "Organization",
            "id": "organization-1",
            "active": True,
            "name": "Example Pediatric Dental Group",
            "address": [
                {
                    "line": ["200 Main St"],
                    "city": "Houston",
                    "state": "TX",
                }
            ],
        },
        "Location": {
            "resourceType": "Location",
            "id": "location-1",
            "name": "Downtown Clinic",
            "address": {
                "line": ["300 Main St"],
                "city": "Houston",
                "state": "TX",
            },
            "managingOrganization": {
                "reference": "Organization/organization-1",
                "display": "Example Pediatric Dental Group",
            },
        },
        "HealthcareService": {
            "resourceType": "HealthcareService",
            "id": "service-1",
            "name": "Pediatric Dentistry",
            "providedBy": {
                "reference": "Organization/organization-1",
                "display": "Example Pediatric Dental Group",
            },
            "type": [
                {
                    "text": "Pediatric dental services",
                }
            ],
            "location": [
                {
                    "reference": "Location/location-1",
                    "display": "Downtown Clinic",
                }
            ],
        },
    }

    resource = resources[resource_type]

    return httpx.Response(
        200,
        json={
            "resourceType": "Bundle",
            "type": "searchset",
            "entry": [{"resource": resource}],
        },
    )


def _client() -> FHIRClient:
    transport = httpx.MockTransport(_mock_transport)
    http_client = httpx.Client(transport=transport)

    return FHIRClient(
        base_url="https://example.test/fhir",
        http_client=http_client,
    )


def test_search_practitioners_normalizes_fhir_resource() -> None:
    results = _client().search_practitioners(
        name="Jane Dentist",
        limit=5,
    )

    assert len(results) == 1

    result = results[0]

    assert result.source_type == SourceType.FHIR
    assert result.title == "Jane Dentist"
    assert result.provider_name == "Jane Dentist"
    assert result.location == "100 Main St | Houston, TX 77001"
    assert result.metadata["fhir_resource_type"] == "Practitioner"
    assert result.metadata["fhir_resource_id"] == "practitioner-1"
    assert result.metadata["fhir_active"] is True


def test_search_organizations_normalizes_fhir_resource() -> None:
    results = _client().search_organizations(
        name="Example Pediatric Dental Group",
        limit=5,
    )

    assert len(results) == 1

    result = results[0]

    assert result.source_type == SourceType.FHIR
    assert result.title == "Example Pediatric Dental Group"
    assert result.metadata["fhir_resource_type"] == "Organization"


def test_search_locations_normalizes_fhir_resource() -> None:
    results = _client().search_locations(
        city="Houston",
        state="TX",
        limit=5,
    )

    assert len(results) == 1

    result = results[0]

    assert result.source_type == SourceType.FHIR
    assert result.title == "Downtown Clinic"
    assert result.location == "300 Main St | Houston, TX"
    assert (
        result.metadata["managing_organization"]
        == "Example Pediatric Dental Group"
    )


def test_search_healthcare_services_normalizes_fhir_resource() -> None:
    results = _client().search_healthcare_services(
        name="Pediatric Dentistry",
        limit=5,
    )

    assert len(results) == 1

    result = results[0]

    assert result.source_type == SourceType.FHIR
    assert result.title == "Pediatric Dentistry"
    assert result.location == "Downtown Clinic"
    assert result.metadata["service_type"] == "Pediatric dental services"


def test_rejects_out_of_scope_patient_resource() -> None:
    client = _client()

    try:
        client.search("Patient")
    except ValueError as exc:
        assert "Unsupported FHIR resource type" in str(exc)
    else:
        raise AssertionError("Patient resource should be rejected in v0.7.")


def test_search_practitioner_roles_normalizes_relationships() -> None:
    results = _client().search_practitioner_roles(
        specialty="Pediatric Dentistry",
        limit=5,
    )

    assert len(results) == 1

    result = results[0]

    assert result.source_type == SourceType.FHIR
    assert result.title == "FHIR PractitionerRole: Jane Dentist"
    assert result.provider_name == "Jane Dentist"
    assert result.location == "Downtown Clinic"
    assert result.metadata["organization"] == "Example Pediatric Dental Group"
    assert result.metadata["specialty"] == "Pediatric Dentistry"
