"""
FHIR R4 client for non-PHI healthcare discovery resources.

The connector uses standard FHIR REST search operations and normalizes
supported resources into the project's shared SearchResult model.

The default development endpoint is the public HAPI FHIR R4 test server.
It must never be used for PHI or confidential information.
"""

from __future__ import annotations

from typing import Any

import httpx

from app.config import get_settings
from connectors.fhir.normalization import normalize_fhir_resource
from models import SearchResult


class FHIRClient:
    """
    Minimal FHIR R4 search client.

    Initial v0.7 scope is intentionally limited to discovery-oriented
    resources that do not require handling patient clinical data.
    """

    SUPPORTED_RESOURCE_TYPES = {
        "Practitioner",
        "PractitionerRole",
        "Organization",
        "Location",
        "HealthcareService",
    }

    def __init__(
        self,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        settings = get_settings()

        self.base_url = (
            base_url or settings.fhir_base_url
        ).rstrip("/")

        self.timeout_seconds = (
            timeout_seconds
            if timeout_seconds is not None
            else settings.fhir_timeout_seconds
        )

        self._http_client = http_client

    def search(
        self,
        resource_type: str,
        *,
        params: dict[str, str | int] | None = None,
        limit: int = 10,
        query_used: str | None = None,
    ) -> list[SearchResult]:
        """
        Search one supported FHIR resource type.

        The connector uses FHIR's standard `_count` parameter to constrain
        the result bundle.

        Unknown or unsupported resource types are rejected deliberately so
        patient/clinical resources cannot accidentally enter this v0.7 path.
        """

        if resource_type not in self.SUPPORTED_RESOURCE_TYPES:
            raise ValueError(
                f"Unsupported FHIR resource type: {resource_type}"
            )

        request_params: dict[str, str | int] = dict(params or {})
        request_params["_count"] = limit

        endpoint = f"{self.base_url}/{resource_type}"

        if self._http_client is not None:
            response = self._http_client.get(
                endpoint,
                params=request_params,
                headers={"Accept": "application/fhir+json"},
            )
        else:
            response = httpx.get(
                endpoint,
                params=request_params,
                headers={"Accept": "application/fhir+json"},
                timeout=self.timeout_seconds,
            )

        response.raise_for_status()
        payload: dict[str, Any] = response.json()

        if payload.get("resourceType") != "Bundle":
            raise RuntimeError(
                "FHIR search did not return a FHIR Bundle."
            )

        results: list[SearchResult] = []

        for entry in payload.get("entry") or []:
            resource = entry.get("resource")

            if not isinstance(resource, dict):
                continue

            if resource.get("resourceType") != resource_type:
                continue

            results.append(
                normalize_fhir_resource(
                    resource,
                    base_url=self.base_url,
                    query_used=query_used,
                )
            )

        return results

    def search_practitioners(
        self,
        *,
        name: str | None = None,
        limit: int = 10,
    ) -> list[SearchResult]:
        params: dict[str, str | int] = {}

        if name:
            params["name"] = name

        return self.search(
            "Practitioner",
            params=params,
            limit=limit,
            query_used=name,
        )

    def search_practitioner_roles(
        self,
        *,
        specialty: str | None = None,
        practitioner: str | None = None,
        organization: str | None = None,
        limit: int = 10,
    ) -> list[SearchResult]:
        params: dict[str, str | int] = {}

        if specialty:
            params["specialty"] = specialty

        if practitioner:
            params["practitioner"] = practitioner

        if organization:
            params["organization"] = organization

        query_parts = [
            item
            for item in [specialty, practitioner, organization]
            if item
        ]

        return self.search(
            "PractitionerRole",
            params=params,
            limit=limit,
            query_used=" | ".join(query_parts) or None,
        )

    def search_organizations(
        self,
        *,
        name: str | None = None,
        limit: int = 10,
    ) -> list[SearchResult]:
        params: dict[str, str | int] = {}

        if name:
            params["name"] = name

        return self.search(
            "Organization",
            params=params,
            limit=limit,
            query_used=name,
        )

    def search_locations(
        self,
        *,
        name: str | None = None,
        city: str | None = None,
        state: str | None = None,
        limit: int = 10,
    ) -> list[SearchResult]:
        params: dict[str, str | int] = {}

        if name:
            params["name"] = name

        if city:
            params["address-city"] = city

        if state:
            params["address-state"] = state

        query_parts = [item for item in [name, city, state] if item]

        return self.search(
            "Location",
            params=params,
            limit=limit,
            query_used=" | ".join(query_parts) or None,
        )

    def search_healthcare_services(
        self,
        *,
        name: str | None = None,
        limit: int = 10,
    ) -> list[SearchResult]:
        params: dict[str, str | int] = {}

        if name:
            params["name"] = name

        return self.search(
            "HealthcareService",
            params=params,
            limit=limit,
            query_used=name,
        )
