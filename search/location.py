from __future__ import annotations

import re

US_STATE_ABBREVIATIONS = {
    "alabama": "AL",
    "alaska": "AK",
    "arizona": "AZ",
    "arkansas": "AR",
    "california": "CA",
    "colorado": "CO",
    "connecticut": "CT",
    "delaware": "DE",
    "district of columbia": "DC",
    "florida": "FL",
    "georgia": "GA",
    "hawaii": "HI",
    "idaho": "ID",
    "illinois": "IL",
    "indiana": "IN",
    "iowa": "IA",
    "kansas": "KS",
    "kentucky": "KY",
    "louisiana": "LA",
    "maine": "ME",
    "maryland": "MD",
    "massachusetts": "MA",
    "michigan": "MI",
    "minnesota": "MN",
    "mississippi": "MS",
    "missouri": "MO",
    "montana": "MT",
    "nebraska": "NE",
    "nevada": "NV",
    "new hampshire": "NH",
    "new jersey": "NJ",
    "new mexico": "NM",
    "new york": "NY",
    "north carolina": "NC",
    "north dakota": "ND",
    "ohio": "OH",
    "oklahoma": "OK",
    "oregon": "OR",
    "pennsylvania": "PA",
    "rhode island": "RI",
    "south carolina": "SC",
    "south dakota": "SD",
    "tennessee": "TN",
    "texas": "TX",
    "utah": "UT",
    "vermont": "VT",
    "virginia": "VA",
    "washington": "WA",
    "west virginia": "WV",
    "wisconsin": "WI",
    "wyoming": "WY",
}

US_STATE_CODES = set(US_STATE_ABBREVIATIONS.values())


def parse_us_provider_location(location: str | None) -> tuple[str, str]:
    """
    Normalize a planner-produced US provider location into (city, state).

    Supported examples:
        Dallas, TX
        Dallas, Texas
        Dallas TX

    Provider discovery currently uses NPPES, so v0.9 intentionally requires
    a US city + state. Other healthcare intents do not require a location.
    """
    if not location or not location.strip():
        raise ValueError(
            "Provider discovery requires UserQuery.location as a US city and state "
            "(for example, 'Dallas, TX')."
        )

    value = " ".join(location.strip().split())

    if "," in value:
        city_part, state_part = value.rsplit(",", 1)
        city = city_part.strip()
        state_text = state_part.strip()
    else:
        match = re.match(r"^(?P<city>.+?)\s+(?P<state>[A-Za-z]{2}|[A-Za-z ]+)$", value)
        if not match:
            raise ValueError(
                f"Could not parse provider location '{location}'. "
                "Use a US city and state, for example 'Dallas, TX'."
            )
        city = match.group("city").strip()
        state_text = match.group("state").strip()

    if not city:
        raise ValueError(
            f"Could not parse provider location '{location}'. "
            "A city is required for NPPES provider discovery."
        )

    state_upper = state_text.upper()
    if state_upper in US_STATE_CODES:
        state = state_upper
    else:
        state = US_STATE_ABBREVIATIONS.get(state_text.lower())

    if not state:
        raise ValueError(
            f"Could not parse US state from provider location '{location}'. "
            "Use a two-letter state code or full US state name."
        )

    return city, state
