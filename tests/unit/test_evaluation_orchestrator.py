from evaluation.models import (
    BenchmarkExecutionResult,
    EvaluationCase,
    EvaluationExpectation,
    EvaluationIntent,
    ExpectationType,
)
from evaluation.orchestrator import evaluate_case, evaluate_runs


def _expectation():
    return [
        EvaluationExpectation(
            name="baseline",
            expectation_type=ExpectationType.REQUIRED,
            description="Synthetic unit-test expectation.",
            value=True,
        )
    ]


def _provider_case():
    return EvaluationCase(
        case_id="provider_test",
        title="Provider test",
        query="Find three cardiologists in Dallas, Texas.",
        intent=EvaluationIntent.PROVIDER_DISCOVERY,
        location="Dallas, TX",
        specialty="Cardiology",
        expectations=_expectation(),
    )


def _provider_run():
    citations = [
        {
            "citation_id": f"C{i}",
            "title": f"Provider {i}",
            "url": f"https://example.test/{i}",
            "source_name": "CMS NPPES / NPI Registry",
            "claim_supported": "Supports provider identity and location.",
        }
        for i in range(1, 4)
    ]
    recommendations = [
        {
            "name": f"Provider {i}",
            "location": "Dallas, TX",
            "credentials": [],
            "services": [],
            "reasons_selected": [
                f"Included because selected NPPES evidence supports "
                f"provider identity and location [C{i}]."
            ],
        }
        for i in range(1, 4)
    ]

    return BenchmarkExecutionResult(
        case_id="provider_test",
        query="Find three cardiologists in Dallas, Texas.",
        model_provider="gemini",
        model_name="test-model",
        status="success",
        latency_seconds=2.5,
        research_output={
            "search_results": [
                {"source_type": "PROVIDER", "title": "Provider 1"},
                {"source_type": "PROVIDER", "title": "Provider 2"},
                {"source_type": "PROVIDER", "title": "Provider 3"},
                {"source_type": "PUBMED", "title": "Study"},
            ],
            "retrieved_sources": 4,
            "deduplicated_sources": 4,
        },
        answer_output={
            "grounded_answer": {
                "answer": (
                    "Three candidate providers are listed from NPPES "
                    "[C1] [C2] [C3]."
                ),
                "recommendations": recommendations,
                "citations": citations,
                "limitations": ["NPPES does not establish provider quality."],
            },
            "selected_evidence_count": 3,
        },
    )


def test_provider_case_produces_paper_ready_counts():
    result = evaluate_case(_provider_case(), _provider_run())
    assert result.retrieved_sources == 4
    assert result.deduplicated_sources == 4
    assert result.selected_evidence_count == 3
    assert result.recommendation_count == 3
    assert result.citation_count == 3
    assert result.latency_seconds == 2.5


def test_provider_case_uses_intent_aware_metrics():
    result = evaluate_case(_provider_case(), _provider_run())
    names = {metric.metric for metric in result.metrics}
    assert "citation_reference_integrity" in names
    assert "retrieved_source_mix_observed" in names


def test_provider_case_can_pass_all_hard_metrics():
    result = evaluate_case(_provider_case(), _provider_run())
    assert result.overall_passed is True


def test_invalid_citation_reference_fails_provider_case():
    run = _provider_run()
    run.answer_output["grounded_answer"]["answer"] += " Unknown [C99]."
    result = evaluate_case(_provider_case(), run)
    metric = next(
        m for m in result.metrics
        if m.metric == "citation_reference_integrity"
    )
    assert metric.passed is False
    assert result.overall_passed is False


def test_unsupported_case_is_scored_as_expected_boundary():
    case = EvaluationCase(
        case_id="unsupported_trials",
        title="Unsupported trials",
        query="Find clinical trials.",
        intent=EvaluationIntent.CLINICAL_TRIALS,
        expectations=_expectation(),
    )
    run = BenchmarkExecutionResult(
        case_id="unsupported_trials",
        query="Find clinical trials.",
        model_provider="gemini",
        status="unsupported",
        error_type="NotImplementedError",
        error_message="CLINICAL_TRIALS is not implemented.",
    )
    result = evaluate_case(case, run)
    assert result.overall_passed is True


def test_failed_supported_case_is_not_scored_as_success():
    case = EvaluationCase(
        case_id="research_failure",
        title="Research failure",
        query="Research childhood dental anxiety.",
        intent=EvaluationIntent.BIOMEDICAL_RESEARCH,
        expectations=_expectation(),
    )
    run = BenchmarkExecutionResult(
        case_id="research_failure",
        query=case.query,
        model_provider="gemma",
        status="error",
        error_type="RuntimeError",
        error_message="synthetic failure",
    )
    result = evaluate_case(case, run)
    assert result.overall_passed is False
    assert [metric.metric for metric in result.metrics] == ["execution_success"]


def test_evaluate_runs_preserves_dataset_order():
    case_one = _provider_case()
    case_two = EvaluationCase(
        case_id="health_test",
        title="Health test",
        query="Explain childhood dental anxiety.",
        intent=EvaluationIntent.HEALTH_INFORMATION,
        expectations=_expectation(),
    )
    run_two = BenchmarkExecutionResult(
        case_id="health_test",
        query=case_two.query,
        model_provider="gemini",
        status="success",
        research_output={
            "search_results": [{"source_type": "PUBMED", "title": "Study"}],
            "retrieved_sources": 1,
            "deduplicated_sources": 1,
        },
        answer_output={
            "grounded_answer": {
                "answer": "General information [C1].",
                "recommendations": [],
                "citations": [
                    {
                        "citation_id": "C1",
                        "title": "Study",
                        "url": "https://example.test/study",
                        "source_name": "PubMed",
                        "claim_supported": "General evidence.",
                    }
                ],
                "limitations": [],
            },
            "selected_evidence_count": 1,
        },
    )

    results = evaluate_runs(
        [case_one, case_two],
        [run_two, _provider_run()],
    )
    assert [result.case_id for result in results] == [
        "provider_test",
        "health_test",
    ]
