from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from evaluation.models import EvaluationMetricResult


def evaluate_claim_support(
    claims: Iterable[Mapping[str, Any]],
) -> EvaluationMetricResult:
    items = list(claims)
    unsupported = [
        str(claim.get("claim_id") or claim.get("text") or "<unknown>")
        for claim in items
        if not claim.get("evidence_ids")
    ]
    passed = not unsupported
    score = 1.0 if not items else (len(items) - len(unsupported)) / len(items)
    return EvaluationMetricResult(
        metric="claim_support",
        passed=passed,
        score=score,
        details=(
            "Every structured claim has supporting evidence."
            if passed
            else f"Unsupported structured claims: {unsupported}."
        ),
    )


def evaluate_provider_claim_source_boundary(
    claims: Iterable[Mapping[str, Any]],
    evidence_by_id: Mapping[str, Mapping[str, Any]],
) -> EvaluationMetricResult:
    violations: list[str] = []
    for claim in claims:
        if str(claim.get("scope", "")).lower() != "provider":
            continue
        claim_id = str(claim.get("claim_id") or claim.get("text") or "<unknown>")
        evidence_ids = [str(value) for value in claim.get("evidence_ids", [])]
        source_types = {
            str(evidence_by_id.get(eid, {}).get("source_type", "")).upper()
            for eid in evidence_ids
        }
        if "PUBMED" in source_types and not (source_types & {"PROVIDER", "NPPES"}):
            violations.append(claim_id)

    passed = not violations
    return EvaluationMetricResult(
        metric="provider_claim_source_boundary",
        passed=passed,
        score=1.0 if passed else 0.0,
        details=(
            "No provider-specific claim relies only on PubMed evidence."
            if passed
            else f"Provider claims rely only on PubMed/general evidence: {violations}."
        ),
    )
