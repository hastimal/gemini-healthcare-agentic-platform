import pytest

from mcp_services.clients import healthcare
from models import SearchResult, SourceType


class FakeToolResult:
    def __init__(
        self,
        records: list[dict],
        *,
        is_error: bool = False,
    ) -> None:
        self.structured_content = {
            "result": records,
        }
        self.is_error = is_error


def _provider_record() -> dict:
    return SearchResult(
        source_type=SourceType.PROVIDER,
        title="Example Provider",
        provider_name="Example Provider",
        retrieved_by="nppes",
    ).model_dump(mode="json")


def _pubmed_record() -> dict:
    return SearchResult(
        source_type=SourceType.PUBMED,
        title="Example PubMed Article",
        retrieved_by="pubmed",
    ).model_dump(mode="json")


def _fhir_record(
    resource_type: str,
    title: str,
) -> dict:
    return SearchResult(
        source_type=SourceType.FHIR,
        title=title,
        retrieved_by="fhir",
        metadata={
            "fhir_resource_type": resource_type,
        },
    ).model_dump(mode="json")


@pytest.mark.asyncio
async def test_mcp_provider_client_calls_expected_tool(
    monkeypatch,
) -> None:
    calls = {}

    class FakeClient:
        def __init__(self, server):
            calls["server"] = server

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def call_tool(self, name, arguments):
            calls["tool"] = name
            calls["arguments"] = arguments

            return FakeToolResult(
                [_provider_record()]
            )

    monkeypatch.setattr(healthcare, "Client", FakeClient)

    client = healthcare.MCPProviderClient()

    results = await client.search(
        taxonomy_description="Pediatric Dentistry",
        city="Houston",
        state="TX",
        limit=3,
    )

    assert calls["tool"] == "find_healthcare_providers"

    assert calls["arguments"] == {
        "specialty": "Pediatric Dentistry",
        "city": "Houston",
        "state": "TX",
        "limit": 3,
    }

    assert len(results) == 1
    assert results[0].source_type == SourceType.PROVIDER


@pytest.mark.asyncio
async def test_mcp_pubmed_client_calls_expected_tool(
    monkeypatch,
) -> None:
    calls = {}

    class FakeClient:
        def __init__(self, server):
            calls["server"] = server

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def call_tool(self, name, arguments):
            calls["tool"] = name
            calls["arguments"] = arguments

            return FakeToolResult(
                [_pubmed_record()]
            )

    monkeypatch.setattr(healthcare, "Client", FakeClient)

    client = healthcare.MCPPubMedClient()

    results = await client.search(
        query="pediatric dental anxiety",
        max_results=4,
    )

    assert calls["tool"] == "search_biomedical_literature"

    assert calls["arguments"] == {
        "query": "pediatric dental anxiety",
        "limit": 4,
    }

    assert len(results) == 1
    assert results[0].source_type == SourceType.PUBMED


@pytest.mark.asyncio
async def test_mcp_fhir_practitioner_client_calls_expected_tool(
    monkeypatch,
) -> None:
    calls = {}

    class FakeClient:
        def __init__(self, server):
            calls["server"] = server

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def call_tool(self, name, arguments):
            calls["tool"] = name
            calls["arguments"] = arguments

            return FakeToolResult(
                [
                    _fhir_record(
                        "Practitioner",
                        "Jane Dentist",
                    )
                ]
            )

    monkeypatch.setattr(healthcare, "Client", FakeClient)

    client = healthcare.MCPFHIRClient()

    results = await client.search_practitioners(
        name="Jane Dentist",
        limit=3,
    )

    assert calls["tool"] == "search_fhir_practitioners"

    assert calls["arguments"] == {
        "name": "Jane Dentist",
        "limit": 3,
    }

    assert len(results) == 1
    assert results[0].source_type == SourceType.FHIR
    assert (
        results[0].metadata["fhir_resource_type"]
        == "Practitioner"
    )


@pytest.mark.asyncio
async def test_mcp_fhir_practitioner_role_client_calls_expected_tool(
    monkeypatch,
) -> None:
    calls = {}

    class FakeClient:
        def __init__(self, server):
            calls["server"] = server

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def call_tool(self, name, arguments):
            calls["tool"] = name
            calls["arguments"] = arguments

            return FakeToolResult(
                [
                    _fhir_record(
                        "PractitionerRole",
                        "FHIR PractitionerRole: Jane Dentist",
                    )
                ]
            )

    monkeypatch.setattr(healthcare, "Client", FakeClient)

    client = healthcare.MCPFHIRClient()

    results = await client.search_practitioner_roles(
        specialty="Pediatric Dentistry",
        practitioner="Practitioner/123",
        organization="Organization/456",
        limit=4,
    )

    assert calls["tool"] == "search_fhir_practitioner_roles"

    assert calls["arguments"] == {
        "specialty": "Pediatric Dentistry",
        "practitioner": "Practitioner/123",
        "organization": "Organization/456",
        "limit": 4,
    }

    assert len(results) == 1
    assert results[0].source_type == SourceType.FHIR


@pytest.mark.asyncio
async def test_mcp_fhir_organization_client_calls_expected_tool(
    monkeypatch,
) -> None:
    calls = {}

    class FakeClient:
        def __init__(self, server):
            calls["server"] = server

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def call_tool(self, name, arguments):
            calls["tool"] = name
            calls["arguments"] = arguments

            return FakeToolResult(
                [
                    _fhir_record(
                        "Organization",
                        "Example Organization",
                    )
                ]
            )

    monkeypatch.setattr(healthcare, "Client", FakeClient)

    client = healthcare.MCPFHIRClient()

    results = await client.search_organizations(
        name="Example Organization",
        limit=2,
    )

    assert calls["tool"] == "search_fhir_organizations"

    assert calls["arguments"] == {
        "name": "Example Organization",
        "limit": 2,
    }

    assert len(results) == 1
    assert results[0].source_type == SourceType.FHIR


@pytest.mark.asyncio
async def test_mcp_fhir_location_client_calls_expected_tool(
    monkeypatch,
) -> None:
    calls = {}

    class FakeClient:
        def __init__(self, server):
            calls["server"] = server

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def call_tool(self, name, arguments):
            calls["tool"] = name
            calls["arguments"] = arguments

            return FakeToolResult(
                [
                    _fhir_record(
                        "Location",
                        "Downtown Clinic",
                    )
                ]
            )

    monkeypatch.setattr(healthcare, "Client", FakeClient)

    client = healthcare.MCPFHIRClient()

    results = await client.search_locations(
        name="Downtown Clinic",
        city="Houston",
        state="TX",
        limit=5,
    )

    assert calls["tool"] == "search_fhir_locations"

    assert calls["arguments"] == {
        "name": "Downtown Clinic",
        "city": "Houston",
        "state": "TX",
        "limit": 5,
    }

    assert len(results) == 1
    assert results[0].source_type == SourceType.FHIR


@pytest.mark.asyncio
async def test_mcp_fhir_healthcare_service_client_calls_expected_tool(
    monkeypatch,
) -> None:
    calls = {}

    class FakeClient:
        def __init__(self, server):
            calls["server"] = server

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def call_tool(self, name, arguments):
            calls["tool"] = name
            calls["arguments"] = arguments

            return FakeToolResult(
                [
                    _fhir_record(
                        "HealthcareService",
                        "Pediatric Dentistry",
                    )
                ]
            )

    monkeypatch.setattr(healthcare, "Client", FakeClient)

    client = healthcare.MCPFHIRClient()

    results = await client.search_healthcare_services(
        name="Pediatric Dentistry",
        limit=6,
    )

    assert calls["tool"] == "search_fhir_healthcare_services"

    assert calls["arguments"] == {
        "name": "Pediatric Dentistry",
        "limit": 6,
    }

    assert len(results) == 1
    assert results[0].source_type == SourceType.FHIR
