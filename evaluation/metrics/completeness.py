from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from evaluation.models import EvaluationMetricResult


def evaluate_required_sections(
    answer: Mapping[str, Any],
    *,
    required_sections: set[str],
) -> EvaluationMetricResult:
    missing = sorted(
        section for section in required_sections
        if answer.get(section) in (None, "", [], {})
    )
    passed = not missing
    score = (
        1.0
        if not required_sections
        else (len(required_sections) - len(missing)) / len(required_sections)
    )
    return EvaluationMetricResult(
        metric="required_answer_sections",
        passed=passed,
        score=score,
        details=(
            "All required structured answer sections are present."
            if passed
            else f"Missing required answer sections: {missing}."
        ),
    )


def evaluate_candidate_count(
    answer: Mapping[str, Any],
    *,
    expected_count: int,
) -> EvaluationMetricResult:
    candidates = answer.get("candidates") or answer.get("providers") or []
    actual = len(candidates)
    passed = actual == expected_count
    return EvaluationMetricResult(
        metric="candidate_count",
        passed=passed,
        score=1.0 if passed else 0.0,
        details=f"Found {actual} candidate(s); expected exactly {expected_count}.",
    )
