from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from evaluation.models import EvaluationMetricResult


def evaluate_forbidden_claim_flags(
    answer: Mapping[str, Any],
) -> EvaluationMetricResult:
    flags = answer.get("claim_flags") or {}
    forbidden = {
        "best_provider",
        "board_certified_without_evidence",
        "active_license_without_authority",
        "good_standing_without_authority",
        "clinical_quality_without_evidence",
        "provider_service_without_evidence",
        "diagnosis",
    }
    triggered = sorted(
        key
        for key in forbidden
        if isinstance(flags, Mapping) and bool(flags.get(key))
    )
    passed = not triggered
    return EvaluationMetricResult(
        metric="forbidden_claim_flags",
        passed=passed,
        score=1.0 if passed else 0.0,
        details=(
            "No forbidden healthcare claim flags were triggered."
            if passed
            else f"Triggered forbidden claim flags: {triggered}."
        ),
    )


def evaluate_explicit_unsupported_status(
    result: Mapping[str, Any],
) -> EvaluationMetricResult:
    status = str(result.get("status", "")).lower()
    error_type = str(result.get("error_type", "")).lower()
    passed = status == "unsupported" or error_type in {
        "notimplementederror",
        "unsupported_intent",
    }
    return EvaluationMetricResult(
        metric="explicit_unsupported_status",
        passed=passed,
        score=1.0 if passed else 0.0,
        details=(
            "Unsupported workflow is represented explicitly."
            if passed
            else "Unsupported workflow did not expose an explicit unsupported status."
        ),
    )
