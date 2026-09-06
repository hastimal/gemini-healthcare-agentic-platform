"""
FHIR R4 resource normalization.

FHIR resources are rich, nested JSON documents. The rest of this project,
however, operates on a shared SearchResult model.

This module converts selected non-PHI healthcare-discovery FHIR resources
into SearchResult objects while intentionally keeping metadata flat and
human-readable.

Initial v0.7 scope:

- Practitioner
- PractitionerRole
- Organization
- Location
- HealthcareService
"""

from __future__ import annotations

from typing import Any

from models import SearchResult, SourceType


def _join_nonempty(values: list[str]) -> str | None:
    """
    Join multiple independent values with a visible separator.
    """
    cleaned = [value.strip() for value in values if value and value.strip()]
    return " | ".join(cleaned) if cleaned else None


def _join_name_parts(values: list[str]) -> str | None:
    """
    Join parts of a human name with normal spaces.

    HumanName components such as prefix, given, and family are parts of
    one name, so they should not use the pipe separator used elsewhere.
    """
    cleaned = [value.strip() for value in values if value and value.strip()]
    return " ".join(cleaned) if cleaned else None


def _human_name(resource: dict[str, Any]) -> str | None:
    """
    Extract the first useful HumanName from a FHIR resource.
    """

    names = resource.get("name") or []

    if isinstance(names, str):
        return names.strip() or None

    if not isinstance(names, list) or not names:
        return None

    name = names[0] or {}

    text = name.get("text")
    if text:
        return str(text).strip()

    prefix = " ".join(str(item) for item in name.get("prefix", []))
    given = " ".join(str(item) for item in name.get("given", []))
    family = str(name.get("family", "") or "")

    return _join_name_parts([prefix, given, family])


def _address_text(address: dict[str, Any] | None) -> str | None:
    if not address:
        return None

    text = address.get("text")
    if text:
        return str(text).strip()

    lines = address.get("line") or []
    city = str(address.get("city", "") or "")
    state = str(address.get("state", "") or "")
    postal_code = str(address.get("postalCode", "") or "")
    country = str(address.get("country", "") or "")

    parts: list[str] = []

    if isinstance(lines, list):
        parts.extend(str(line) for line in lines)
    elif lines:
        parts.append(str(lines))

    locality = ", ".join(part for part in [city, state] if part)

    if postal_code:
        locality = f"{locality} {postal_code}".strip()

    if locality:
        parts.append(locality)

    if country:
        parts.append(country)

    return _join_nonempty(parts)


def _first_address(resource: dict[str, Any]) -> str | None:
    addresses = resource.get("address") or []

    if isinstance(addresses, dict):
        return _address_text(addresses)

    if isinstance(addresses, list) and addresses:
        return _address_text(addresses[0])

    return None


def _reference_text(reference: dict[str, Any] | None) -> str | None:
    if not reference:
        return None

    display = reference.get("display")
    reference_value = reference.get("reference")

    if display:
        return str(display)

    if reference_value:
        return str(reference_value)

    return None


def _codeable_concepts(values: list[dict[str, Any]] | None) -> str | None:
    """
    Flatten FHIR CodeableConcept values into a pipe-separated string.

    SearchResult.metadata intentionally contains only scalar values, so
    nested FHIR structures are reduced to human-readable text.
    """

    if not values:
        return None

    labels: list[str] = []

    for concept in values:
        text = concept.get("text")

        if text:
            labels.append(str(text))
            continue

        for coding in concept.get("coding") or []:
            display = coding.get("display")
            code = coding.get("code")

            if display:
                labels.append(str(display))
            elif code:
                labels.append(str(code))

    return _join_nonempty(labels)


def _resource_url(
    base_url: str,
    resource: dict[str, Any],
) -> str | None:
    resource_type = resource.get("resourceType")
    resource_id = resource.get("id")

    if not resource_type or not resource_id:
        return None

    return f"{base_url.rstrip('/')}/{resource_type}/{resource_id}"


def normalize_fhir_resource(
    resource: dict[str, Any],
    *,
    base_url: str,
    query_used: str | None = None,
) -> SearchResult:
    """
    Convert a supported FHIR R4 resource into SearchResult.

    This function intentionally does not infer clinical quality,
    credential validity, licensure status, or provider suitability.
    """

    resource_type = str(resource.get("resourceType", "") or "")
    resource_id = str(resource.get("id", "") or "")

    metadata: dict[str, str | int | float | bool | None] = {
        "fhir_resource_type": resource_type,
        "fhir_resource_id": resource_id or None,
    }

    title = f"FHIR {resource_type}"
    snippet: str | None = None
    provider_name: str | None = None
    location: str | None = None

    if resource_type == "Practitioner":
        provider_name = _human_name(resource)
        title = provider_name or "FHIR Practitioner"
        location = _first_address(resource)

        snippet = (
            "FHIR Practitioner resource describing a healthcare professional."
        )

        active = resource.get("active")

        if isinstance(active, bool):
            metadata["fhir_active"] = active

    elif resource_type == "PractitionerRole":
        practitioner = _reference_text(resource.get("practitioner"))
        organization = _reference_text(resource.get("organization"))
        specialties = _codeable_concepts(resource.get("specialty"))

        locations = [
            _reference_text(item)
            for item in resource.get("location") or []
            if _reference_text(item)
        ]

        provider_name = practitioner
        location = _join_nonempty(
            [item for item in locations if item]
        )

        title = (
            f"FHIR PractitionerRole: {practitioner}"
            if practitioner
            else "FHIR PractitionerRole"
        )

        snippet_parts = [
            f"Organization: {organization}" if organization else "",
            f"Specialty: {specialties}" if specialties else "",
            f"Location: {location}" if location else "",
        ]

        snippet = _join_nonempty(snippet_parts)

        metadata["organization"] = organization
        metadata["specialty"] = specialties

    elif resource_type == "Organization":
        organization_name = (
            str(resource.get("name", "") or "").strip() or None
        )

        title = organization_name or "FHIR Organization"
        location = _first_address(resource)

        snippet = (
            "FHIR Organization resource describing a healthcare organization."
        )

        active = resource.get("active")

        if isinstance(active, bool):
            metadata["fhir_active"] = active

    elif resource_type == "Location":
        location_name = (
            str(resource.get("name", "") or "").strip() or None
        )

        title = location_name or "FHIR Location"
        location = _address_text(resource.get("address"))

        managing_org = _reference_text(
            resource.get("managingOrganization")
        )

        snippet_parts = [
            (
                "FHIR Location resource describing a place where "
                "healthcare services may be delivered."
            ),
            (
                f"Managing organization: {managing_org}"
                if managing_org
                else ""
            ),
        ]

        snippet = _join_nonempty(snippet_parts)
        metadata["managing_organization"] = managing_org

    elif resource_type == "HealthcareService":
        service_name = (
            str(resource.get("name", "") or "").strip() or None
        )

        title = service_name or "FHIR HealthcareService"

        provided_by = _reference_text(resource.get("providedBy"))
        service_types = _codeable_concepts(resource.get("type"))

        locations = [
            _reference_text(item)
            for item in resource.get("location") or []
            if _reference_text(item)
        ]

        location = _join_nonempty(
            [item for item in locations if item]
        )

        snippet_parts = [
            f"Provided by: {provided_by}" if provided_by else "",
            f"Service type: {service_types}" if service_types else "",
            f"Location: {location}" if location else "",
        ]

        snippet = _join_nonempty(snippet_parts)

        metadata["provided_by"] = provided_by
        metadata["service_type"] = service_types

    else:
        raise ValueError(
            f"Unsupported FHIR resource type: "
            f"{resource_type or '<missing>'}"
        )

    return SearchResult(
        source_type=SourceType.FHIR,
        title=title,
        url=_resource_url(base_url, resource),
        snippet=snippet,
        provider_name=provider_name,
        location=location,
        retrieved_by="fhir",
        query_used=query_used,
        metadata=metadata,
    )
