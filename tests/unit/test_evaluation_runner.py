from pathlib import Path

from evaluation.models import BenchmarkExecutionResult
from evaluation.runner import load_benchmark_cases, save_results


def test_load_benchmark_cases() -> None:
    cases = load_benchmark_cases(
        Path("evaluation/datasets/healthcare_benchmark.jsonl")
    )
    assert len(cases) == 11
    assert len({case.case_id for case in cases}) == 11


def test_execution_result_preserves_production_state() -> None:
    result = BenchmarkExecutionResult(
        case_id="provider_test",
        query="Find cardiologists in Dallas, Texas.",
        model_provider="gemini",
        model_name="test-model",
        status="success",
        planner_output={"search_plan": {"generated_queries": [{"query": "q1"}]}},
        research_output={
            "search_results": [{"source_type": "PROVIDER"}],
            "retrieved_sources": 1,
            "deduplicated_sources": 1,
        },
        answer_output={
            "grounded_answer": {
                "answer": "Candidate provider.",
                "recommendations": [{"name": "Example"}],
                "citations": [{"citation_id": "C1"}],
            },
            "selected_evidence_count": 1,
        },
    )
    assert result.planner_output["search_plan"]["generated_queries"][0]["query"] == "q1"
    assert result.research_output["search_results"][0]["source_type"] == "PROVIDER"
    assert result.answer_output["grounded_answer"]["recommendations"][0]["name"] == "Example"


def test_save_results(tmp_path: Path) -> None:
    output = tmp_path / "benchmark.json"
    result = BenchmarkExecutionResult(
        case_id="case_one",
        query="Research childhood dental anxiety.",
        model_provider="gemma",
        model_name="gemma-test",
        status="success",
        latency_seconds=1.25,
    )
    save_results([result], output)
    text = output.read_text()
    assert '"case_id": "case_one"' in text
    assert '"model_provider": "gemma"' in text
    assert '"latency_seconds": 1.25' in text


def test_unsupported_execution_result_is_explicit() -> None:
    result = BenchmarkExecutionResult(
        case_id="unsupported_case",
        query="Find a care program.",
        model_provider="gemini",
        status="unsupported",
        error_type="NotImplementedError",
        error_message="CARE_PROGRAM_DISCOVERY is not implemented.",
    )
    assert result.status == "unsupported"
    assert result.error_type == "NotImplementedError"
