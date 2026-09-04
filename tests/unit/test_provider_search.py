from connectors.provider_search.client import NPPESProviderClient
from models import SourceType

SAMPLE_PROVIDER = {
    "number": "1234567890",
    "enumeration_type": "NPI-1",
    "basic": {
        "first_name": "Jane",
        "last_name": "Smith",
        "credential": "DDS",
    },
    "addresses": [
        {
            "address_purpose": "LOCATION",
            "address_1": "100 Main St",
            "city": "Houston",
            "state": "TX",
            "postal_code": "77001",
            "telephone_number": "7135551234",
        }
    ],
    "taxonomies": [
        {
            "code": "1223P0221X",
            "desc": "Dentist, Pediatric Dentistry",
            "primary": True,
            "license": "TX12345",
            "state": "TX",
        }
    ],
}


def test_normalize_provider():
    client = NPPESProviderClient()

    result = client._normalize_provider(SAMPLE_PROVIDER)

    assert result.source_type == SourceType.PROVIDER
    assert result.provider_name == "Jane Smith DDS"
    assert "Houston" in result.location
    assert result.metadata["npi"] == "1234567890"
    assert result.metadata["taxonomy_description"] == "Dentist, Pediatric Dentistry"
