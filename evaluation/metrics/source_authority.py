from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from evaluation.models import EvaluationMetricResult

AUTHORITATIVE_PROVIDER_TYPES = {"PROVIDER", "NPPES"}


def evaluate_provider_evidence_authority(
    selected_evidence: Iterable[Mapping[str, Any]],
) -> EvaluationMetricResult:
    provider_items = [
        item
        for item in selected_evidence
        if str(item.get("scope", "")).lower() == "provider"
        or str(item.get("source_type", "")).upper() in AUTHORITATIVE_PROVIDER_TYPES
    ]
    invalid = [
        str(item.get("evidence_id") or item.get("id") or "<unknown>")
        for item in provider_items
        if str(item.get("source_type", "")).upper() not in AUTHORITATIVE_PROVIDER_TYPES
    ]
    passed = not invalid
    return EvaluationMetricResult(
        metric="provider_evidence_authority",
        passed=passed,
        score=1.0 if passed else 0.0,
        details=(
            "Selected provider evidence uses provider-registry evidence types."
            if passed
            else f"Provider evidence has non-provider authority types: {invalid}."
        ),
    )


def evaluate_fhir_not_used_as_provider_recommendation(
    selected_evidence: Iterable[Mapping[str, Any]],
) -> EvaluationMetricResult:
    violations = [
        str(item.get("evidence_id") or item.get("id") or "<unknown>")
        for item in selected_evidence
        if str(item.get("source_type", "")).upper() == "FHIR"
        and str(item.get("scope", "")).lower() == "provider_recommendation"
    ]
    passed = not violations
    return EvaluationMetricResult(
        metric="fhir_provider_recommendation_boundary",
        passed=passed,
        score=1.0 if passed else 0.0,
        details=(
            "FHIR test data is not used as provider-recommendation evidence."
            if passed
            else f"FHIR evidence used as provider recommendation evidence: {violations}."
        ),
    )
