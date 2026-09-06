from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from evaluation.models import EvaluationMetricResult


def evaluate_citation_presence(
    citations: Iterable[Mapping[str, Any] | str],
    *,
    minimum_citations: int = 1,
) -> EvaluationMetricResult:
    items = list(citations)
    passed = len(items) >= minimum_citations
    return EvaluationMetricResult(
        metric="citation_presence",
        passed=passed,
        score=1.0 if passed else 0.0,
        details=f"Found {len(items)} citation(s); minimum required is {minimum_citations}.",
    )


def evaluate_citation_targets(
    citations: Iterable[Mapping[str, Any]],
    selected_evidence_ids: set[str],
) -> EvaluationMetricResult:
    citation_ids = {
        str(citation.get("evidence_id"))
        for citation in citations
        if citation.get("evidence_id") is not None
    }
    unknown = sorted(citation_ids - selected_evidence_ids)
    passed = not unknown
    return EvaluationMetricResult(
        metric="citation_targets_selected_evidence",
        passed=passed,
        score=1.0 if passed else 0.0,
        details=(
            "All structured citations reference selected evidence."
            if passed
            else f"Citations reference non-selected evidence IDs: {unknown}."
        ),
    )
