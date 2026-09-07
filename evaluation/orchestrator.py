from __future__ import annotations

from evaluation.adapters.production import (
    citations,
    grounded_answer,
    invalid_citation_references,
    normalized_answer_view,
    provider_claims_view,
    recommendations,
    research_results,
    selected_evidence_view,
)
from evaluation.metrics.citations import evaluate_citation_presence
from evaluation.metrics.completeness import evaluate_candidate_count
from evaluation.metrics.grounding import evaluate_claim_support
from evaluation.metrics.retrieval import (
    evaluate_retrieval_presence,
    evaluate_source_type_presence,
)
from evaluation.metrics.safety import (
    evaluate_explicit_unsupported_status,
    evaluate_forbidden_claim_flags,
)
from evaluation.metrics.source_authority import (
    evaluate_fhir_not_used_as_provider_recommendation,
    evaluate_provider_evidence_authority,
)
from evaluation.models import (
    EvaluationIntent,
    EvaluationMetricResult,
    ResearchBenchmarkCaseResult,
)


def _metric(name, *, passed, score=None, details=None):
    return EvaluationMetricResult(
        metric=name,
        passed=passed,
        score=score,
        details=details,
    )


def _execution_metric(run):
    passed = run.status == "success"
    return _metric(
        "execution_success",
        passed=passed,
        score=1.0 if passed else 0.0,
        details=f"execution_status={run.status}",
    )


def _citation_reference_integrity(run):
    invalid = sorted(invalid_citation_references(run))
    passed = not invalid
    return _metric(
        "citation_reference_integrity",
        passed=passed,
        score=1.0 if passed else 0.0,
        details=(
            "All user-visible citation references resolve."
            if passed
            else "Unknown citation references: " + ", ".join(invalid)
        ),
    )


def _source_types(results):
    observed = set()
    for item in results:
        source_type = str(item.get("source_type") or "").upper()
        if source_type:
            observed.add(source_type)
    return observed


def _research_counts(run):
    research = run.research_output if isinstance(run.research_output, dict) else {}
    results = research_results(run)

    retrieved = research.get("retrieved_sources", len(results))
    deduplicated = research.get("deduplicated_sources", len(results))

    try:
        retrieved_count = int(retrieved)
    except (TypeError, ValueError):
        retrieved_count = len(results)

    try:
        deduplicated_count = int(deduplicated)
    except (TypeError, ValueError):
        deduplicated_count = len(results)

    return retrieved_count, deduplicated_count


def _selected_count(run):
    answer = run.answer_output if isinstance(run.answer_output, dict) else {}
    value = answer.get("selected_evidence_count", len(citations(run)))
    try:
        return int(value)
    except (TypeError, ValueError):
        return len(citations(run))


def _provider_metrics(run):
    results = research_results(run)
    answer = normalized_answer_view(run)
    selected = selected_evidence_view(run)
    claims = provider_claims_view(run)

    metrics = [
        evaluate_retrieval_presence(results, minimum_results=1),
        evaluate_source_type_presence(results, required_source_types=["PROVIDER"]),
        evaluate_citation_presence(citations(run), minimum_citations=1),
        _citation_reference_integrity(run),
        evaluate_claim_support(claims),
        evaluate_provider_evidence_authority(selected),
        evaluate_fhir_not_used_as_provider_recommendation(selected),
        evaluate_candidate_count(answer, expected_count=3),
        evaluate_forbidden_claim_flags(answer),
    ]

    metrics.append(
        _metric(
            "retrieved_source_mix_observed",
            passed=None,
            details="Observed source types: " + ", ".join(sorted(_source_types(results))),
        )
    )
    return metrics


def _research_metrics(run):
    results = research_results(run)
    return [
        evaluate_retrieval_presence(results, minimum_results=1),
        evaluate_source_type_presence(results, required_source_types=["PUBMED"]),
        evaluate_citation_presence(citations(run), minimum_citations=1),
        _citation_reference_integrity(run),
    ]


def _health_information_metrics(run):
    results = research_results(run)
    return [
        evaluate_retrieval_presence(results, minimum_results=1),
        evaluate_citation_presence(citations(run), minimum_citations=1),
        _citation_reference_integrity(run),
    ]


def _fhir_metrics(run):
    results = research_results(run)
    return [
        evaluate_retrieval_presence(results, minimum_results=1),
        evaluate_source_type_presence(results, required_source_types=["FHIR"]),
        evaluate_citation_presence(citations(run), minimum_citations=1),
        _citation_reference_integrity(run),
        evaluate_fhir_not_used_as_provider_recommendation(selected_evidence_view(run)),
    ]


def _unsupported_metrics(run):
    payload = {
        "status": run.status,
        "error_type": run.error_type,
        "error_message": run.error_message,
    }
    return [evaluate_explicit_unsupported_status(payload)]


def _hard_metric_pass(metrics):
    hard = [metric.passed for metric in metrics if metric.passed is not None]
    if not hard:
        return None
    return all(hard)


def evaluate_case(case, run):
    if case.case_id != run.case_id:
        raise ValueError(
            f"case/result mismatch: {case.case_id!r} != {run.case_id!r}"
        )

    if case.intent in {
        EvaluationIntent.CARE_PROGRAM_DISCOVERY,
        EvaluationIntent.CLINICAL_TRIALS,
    }:
        metrics = _unsupported_metrics(run)
    elif run.status != "success":
        metrics = [_execution_metric(run)]
    elif case.intent == EvaluationIntent.PROVIDER_DISCOVERY:
        metrics = _provider_metrics(run)
    elif case.intent == EvaluationIntent.BIOMEDICAL_RESEARCH:
        metrics = _research_metrics(run)
    elif case.intent == EvaluationIntent.HEALTH_INFORMATION:
        metrics = _health_information_metrics(run)
    elif case.intent == EvaluationIntent.FHIR_INTEROPERABILITY:
        metrics = _fhir_metrics(run)
    else:
        metrics = [_execution_metric(run)]

    retrieved, deduplicated = _research_counts(run)

    return ResearchBenchmarkCaseResult(
        case_id=case.case_id,
        title=case.title,
        query=case.query,
        benchmark_intent=case.intent,
        tags=case.tags,
        model_provider=run.model_provider,
        model_name=run.model_name,
        execution_status=run.status,
        latency_seconds=run.latency_seconds,
        retrieved_sources=retrieved,
        deduplicated_sources=deduplicated,
        selected_evidence_count=_selected_count(run),
        recommendation_count=len(recommendations(run)),
        citation_count=len(citations(run)),
        metrics=metrics,
        overall_passed=_hard_metric_pass(metrics),
        error_type=run.error_type,
        error_message=run.error_message,
        diagnostics={
            "metric_count": len(metrics),
            "hard_metric_count": sum(
                metric.passed is not None for metric in metrics
            ),
            "grounded_answer_present": bool(grounded_answer(run)),
        },
    )


def evaluate_runs(cases, runs):
    by_case_id = {run.case_id: run for run in runs}
    missing = [case.case_id for case in cases if case.case_id not in by_case_id]
    if missing:
        raise ValueError(
            "Missing execution results for benchmark cases: " + ", ".join(missing)
        )
    return [evaluate_case(case, by_case_id[case.case_id]) for case in cases]
