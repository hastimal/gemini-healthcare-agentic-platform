from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from evaluation.models import EvaluationMetricResult


def evaluate_retrieval_presence(
    results: Iterable[Mapping[str, Any]],
    *,
    minimum_results: int = 1,
) -> EvaluationMetricResult:
    items = list(results)
    passed = len(items) >= minimum_results
    return EvaluationMetricResult(
        metric="retrieval_presence",
        passed=passed,
        score=1.0 if passed else 0.0,
        details=f"Retrieved {len(items)} result(s); minimum required is {minimum_results}.",
    )


def evaluate_source_type_presence(
    results: Iterable[Mapping[str, Any]],
    *,
    required_source_types: set[str],
) -> EvaluationMetricResult:
    observed = {
        str(item.get("source_type", "")).upper()
        for item in results
        if item.get("source_type")
    }
    required = {value.upper() for value in required_source_types}
    missing = sorted(required - observed)
    passed = not missing
    return EvaluationMetricResult(
        metric="required_source_types",
        passed=passed,
        score=1.0 if passed else 0.0,
        details=(
            f"Observed source types: {sorted(observed)}."
            if passed
            else f"Missing required source types: {missing}; observed: {sorted(observed)}."
        ),
    )
