from models import SearchResult, SourceType


def _fhir_result(
    resource_type: str,
    title: str,
) -> SearchResult:
    return SearchResult(
        source_type=SourceType.FHIR,
        title=title,
        retrieved_by="fhir",
        metadata={
            "fhir_resource_type": resource_type,
        },
    )


def test_fhir_practitioner_tool_delegates_to_connector(monkeypatch) -> None:
    from mcp_services.fhir_server import tools

    calls = {}

    class FakeFHIRClient:
        def search_practitioners(self, *, name=None, limit=10):
            calls["name"] = name
            calls["limit"] = limit

            return [
                _fhir_result(
                    "Practitioner",
                    "Jane Dentist",
                )
            ]

    monkeypatch.setattr(tools, "FHIRClient", FakeFHIRClient)

    results = tools.find_fhir_practitioners(
        name="Jane Dentist",
        limit=3,
    )

    assert calls == {
        "name": "Jane Dentist",
        "limit": 3,
    }

    assert len(results) == 1
    assert results[0]["source_type"] == "fhir"
    assert results[0]["title"] == "Jane Dentist"


def test_fhir_practitioner_role_tool_delegates_to_connector(
    monkeypatch,
) -> None:
    from mcp_services.fhir_server import tools

    calls = {}

    class FakeFHIRClient:
        def search_practitioner_roles(
            self,
            *,
            specialty=None,
            practitioner=None,
            organization=None,
            limit=10,
        ):
            calls["specialty"] = specialty
            calls["practitioner"] = practitioner
            calls["organization"] = organization
            calls["limit"] = limit

            return [
                _fhir_result(
                    "PractitionerRole",
                    "FHIR PractitionerRole: Jane Dentist",
                )
            ]

    monkeypatch.setattr(tools, "FHIRClient", FakeFHIRClient)

    results = tools.find_fhir_practitioner_roles(
        specialty="Pediatric Dentistry",
        practitioner="Practitioner/123",
        organization="Organization/456",
        limit=4,
    )

    assert calls == {
        "specialty": "Pediatric Dentistry",
        "practitioner": "Practitioner/123",
        "organization": "Organization/456",
        "limit": 4,
    }

    assert len(results) == 1
    assert results[0]["source_type"] == "fhir"


def test_fhir_organization_tool_delegates_to_connector(
    monkeypatch,
) -> None:
    from mcp_services.fhir_server import tools

    calls = {}

    class FakeFHIRClient:
        def search_organizations(self, *, name=None, limit=10):
            calls["name"] = name
            calls["limit"] = limit

            return [
                _fhir_result(
                    "Organization",
                    "Example Pediatric Dental Group",
                )
            ]

    monkeypatch.setattr(tools, "FHIRClient", FakeFHIRClient)

    results = tools.find_fhir_organizations(
        name="Example Pediatric Dental Group",
        limit=2,
    )

    assert calls == {
        "name": "Example Pediatric Dental Group",
        "limit": 2,
    }

    assert len(results) == 1


def test_fhir_location_tool_delegates_to_connector(
    monkeypatch,
) -> None:
    from mcp_services.fhir_server import tools

    calls = {}

    class FakeFHIRClient:
        def search_locations(
            self,
            *,
            name=None,
            city=None,
            state=None,
            limit=10,
        ):
            calls["name"] = name
            calls["city"] = city
            calls["state"] = state
            calls["limit"] = limit

            return [
                _fhir_result(
                    "Location",
                    "Downtown Clinic",
                )
            ]

    monkeypatch.setattr(tools, "FHIRClient", FakeFHIRClient)

    results = tools.find_fhir_locations(
        city="Houston",
        state="TX",
        limit=5,
    )

    assert calls == {
        "name": None,
        "city": "Houston",
        "state": "TX",
        "limit": 5,
    }

    assert len(results) == 1


def test_fhir_healthcare_service_tool_delegates_to_connector(
    monkeypatch,
) -> None:
    from mcp_services.fhir_server import tools

    calls = {}

    class FakeFHIRClient:
        def search_healthcare_services(
            self,
            *,
            name=None,
            limit=10,
        ):
            calls["name"] = name
            calls["limit"] = limit

            return [
                _fhir_result(
                    "HealthcareService",
                    "Pediatric Dentistry",
                )
            ]

    monkeypatch.setattr(tools, "FHIRClient", FakeFHIRClient)

    results = tools.find_fhir_healthcare_services(
        name="Pediatric Dentistry",
        limit=5,
    )

    assert calls == {
        "name": "Pediatric Dentistry",
        "limit": 5,
    }

    assert len(results) == 1
