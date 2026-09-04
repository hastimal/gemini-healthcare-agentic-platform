from __future__ import annotations

import httpx

from models import SearchResult, SourceType


class NPPESProviderClient:
    """
    Client for provider discovery using the CMS NPPES / NPI Registry.

    NPPES is useful for:
    - Provider name
    - NPI
    - Provider taxonomy / specialty
    - Practice location
    - NPPES-reported license fields

    Important:
    NPPES does NOT prove that a professional license is currently active.
    We will verify state licensing separately later.
    """

    BASE_URL = "https://npiregistry.cms.hhs.gov/api/"

    def __init__(self) -> None:
        """
        Create one reusable HTTP client for NPPES requests.
        """
        self.client = httpx.Client(
            timeout=20.0,
            headers={
                "User-Agent": "BeyondRAGHealthcare/0.2",
            },
        )

    def search(
        self,
        taxonomy_description: str,
        city: str,
        state: str,
        limit: int = 10,
    ) -> list[SearchResult]:
        """
        Search NPPES and return clean provider results.

        NPPES may return records that do not exactly match the
        displayed practice location or selected taxonomy.

        Example search:

            Pediatric Dentistry + Houston + TX

        Raw NPPES results may still include:
        - Dallas providers
        - Columbus providers
        - General Practice-only records

        We therefore:
        1. Retrieve more candidates than requested.
        2. Normalize the records.
        3. Apply our own exact city/state/specialty validation.
        4. Return only clean matching results.

        After filtering, we should no longer see:
        - Dallas providers
        - Columbus providers
        - General Practice-only providers

        in our Houston Pediatric Dentistry result set.
        """

        # Retrieve extra candidates because some raw NPPES results
        # may be discarded by our strict post-filtering.
        api_limit = min(max(limit * 3, 20), 200)

        params = {
            "version": "2.1",
            "taxonomy_description": taxonomy_description,
            "city": city,
            "state": state,
            "limit": api_limit,
        }

        response = self.client.get(
            self.BASE_URL,
            params=params,
        )
        response.raise_for_status()

        data = response.json()

        # Normalize raw NPPES records into our shared SearchResult model.
        results = [self._normalize_provider(provider) for provider in data.get("results", [])]

        # Apply exact validation after NPPES retrieval.
        filtered = [
            result
            for result in results
            if self._matches_search(
                result=result,
                taxonomy_description=taxonomy_description,
                city=city,
                state=state,
            )
        ]

        return filtered[:limit]

    def _normalize_provider(
        self,
        provider: dict,
    ) -> SearchResult:
        """
        Convert a raw NPPES provider record into SearchResult.

        A provider may have:
        - multiple addresses
        - multiple taxonomies
        - individual-provider data
        - organization-provider data

        We normalize all of that into one consistent result.
        """

        basic = provider.get("basic", {})
        addresses = provider.get("addresses", [])
        taxonomies = provider.get("taxonomies", [])

        first_name = basic.get("first_name")
        last_name = basic.get("last_name")
        credential = basic.get("credential")
        organization_name = basic.get("organization_name")

        # NPPES contains both individuals and organizations.
        if organization_name:
            provider_name = organization_name
        else:
            provider_name = " ".join(
                part
                for part in [
                    first_name,
                    last_name,
                    credential,
                ]
                if part
            )

        # Prefer actual practice LOCATION address over mailing address.
        practice_address = self._practice_address(addresses)
        location = self._format_location(practice_address)

        # A provider may have several taxonomy entries.
        #
        # Example:
        # Primary taxonomy: General Practice
        # Secondary taxonomy: Pediatric Dentistry
        #
        # Since our search is for pediatric dentistry, prefer the
        # Pediatric Dentistry taxonomy when one exists.
        pediatric_taxonomy = next(
            (
                taxonomy
                for taxonomy in taxonomies
                if "pediatric dentistry" in str(taxonomy.get("desc") or "").lower()
            ),
            None,
        )

        # Use primary taxonomy only as a fallback.
        primary_taxonomy = next(
            (taxonomy for taxonomy in taxonomies if taxonomy.get("primary") is True),
            taxonomies[0] if taxonomies else {},
        )

        selected_taxonomy = pediatric_taxonomy or primary_taxonomy

        taxonomy_description = selected_taxonomy.get("desc")
        taxonomy_code = selected_taxonomy.get("code")
        license_number = selected_taxonomy.get("license")
        license_state = selected_taxonomy.get("state")

        npi = provider.get("number")

        url = f"https://npiregistry.cms.hhs.gov/provider-view/{npi}" if npi else None

        snippet_parts = [
            provider_name,
            taxonomy_description,
            location,
        ]

        snippet = " | ".join(part for part in snippet_parts if part)

        # SearchResult.metadata currently supports simple scalar values.
        #
        # Therefore, DO NOT store a nested list/dictionary here.
        #
        # Instead of:
        #     "all_taxonomies": [{...}, {...}]
        #
        # store all taxonomy descriptions as a pipe-separated string.
        #
        # Example:
        #     "Dentist, General Practice | Dentist, Pediatric Dentistry"
        #
        # This keeps SearchResult validation clean while still preserving
        # enough taxonomy information for filtering.
        all_taxonomy_descriptions = " | ".join(
            str(taxonomy.get("desc") or "") for taxonomy in taxonomies if taxonomy.get("desc")
        )

        return SearchResult(
            source_type=SourceType.PROVIDER,
            title=provider_name,
            url=url,
            snippet=snippet,
            provider_name=provider_name,
            location=location,
            retrieved_by="nppes",
            query_used=taxonomy_description or "",
            metadata={
                "npi": npi,
                "enumeration_type": provider.get("enumeration_type"),
                "taxonomy_code": taxonomy_code,
                "taxonomy_description": taxonomy_description,
                # This is only an NPPES-reported license value.
                # Do not treat it as verified active licensure yet.
                "license_number": license_number,
                "license_state": license_state,
                "phone": practice_address.get("telephone_number"),
                # Keep structured location fields for exact filtering.
                "city": practice_address.get("city"),
                "state": practice_address.get("state"),
                "postal_code": practice_address.get("postal_code"),
                # Store taxonomies as a simple string because metadata
                # currently does not allow nested lists/dictionaries.
                "all_taxonomy_descriptions": (all_taxonomy_descriptions),
            },
        )

    @staticmethod
    def _matches_search(
        result: SearchResult,
        taxonomy_description: str,
        city: str,
        state: str,
    ) -> bool:
        """
        Strictly validate city, state, and specialty.

        A provider is accepted only when:

        1. Practice city exactly matches requested city.
        2. Practice state exactly matches requested state.
        3. One of the provider taxonomies matches the requested specialty.

        This removes records such as:
        - Columbus, OH
        - Dallas, TX
        - General Practice-only providers

        from a Houston Pediatric Dentistry search.
        """

        result_city = str(result.metadata.get("city") or "").strip().lower()

        result_state = str(result.metadata.get("state") or "").strip().lower()

        requested_city = city.strip().lower()
        requested_state = state.strip().lower()

        all_taxonomies = str(result.metadata.get("all_taxonomy_descriptions") or "").lower()

        # Match against all taxonomy descriptions, not only
        # the provider's primary taxonomy.
        taxonomy_match = taxonomy_description.strip().lower() in all_taxonomies

        return result_city == requested_city and result_state == requested_state and taxonomy_match

    @staticmethod
    def _practice_address(
        addresses: list[dict],
    ) -> dict:
        """
        Prefer the provider's LOCATION address.

        NPPES can also contain mailing addresses, and those may belong
        to another city or state.
        """

        for address in addresses:
            if address.get("address_purpose") == "LOCATION":
                return address

        return addresses[0] if addresses else {}

    @staticmethod
    def _format_location(
        address: dict,
    ) -> str | None:
        """
        Convert the structured NPPES address into readable text.
        """

        if not address:
            return None

        line1 = address.get("address_1")
        city = address.get("city")
        state = address.get("state")
        postal_code = address.get("postal_code")

        city_state = ", ".join(part for part in [city, state] if part)

        parts = [
            line1,
            city_state,
            postal_code,
        ]

        location = " ".join(part for part in parts if part)

        return location or None
