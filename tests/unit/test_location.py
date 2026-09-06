import pytest

from search.location import parse_us_provider_location


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Dallas, TX", ("Dallas", "TX")),
        ("Chicago, Illinois", ("Chicago", "IL")),
        ("Austin Texas", ("Austin", "TX")),
        ("New York, NY", ("New York", "NY")),
    ],
)
def test_parse_us_provider_location(raw, expected):
    assert parse_us_provider_location(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [None, "", "Dallas", "London, UK"],
)
def test_parse_us_provider_location_rejects_incomplete_or_non_us(raw):
    with pytest.raises(ValueError):
        parse_us_provider_location(raw)
