import os
from pathlib import Path

import pytest

from evaluation.benchmark import (
    _configure_provider,
    _output_dir,
    _select_cases,
    _write_raw_results,
    build_parser,
)
from evaluation.models import (
    BenchmarkExecutionResult,
    EvaluationCase,
    EvaluationExpectation,
    EvaluationIntent,
    ExpectationType,
)


def _case(case_id: str) -> EvaluationCase:
    return EvaluationCase(
        case_id=case_id,
        title=f"Case {case_id}",
        query="Synthetic healthcare query.",
        intent=EvaluationIntent.HEALTH_INFORMATION,
        expectations=[
            EvaluationExpectation(
                name="synthetic",
                expectation_type=ExpectationType.REQUIRED,
                description="Synthetic test expectation.",
                value=True,
            )
        ],
    )


def test_select_cases_returns_requested_case_only():
    cases = [_case("case_one"), _case("case_two")]
    selected = _select_cases(cases, "case_two")
    assert [case.case_id for case in selected] == ["case_two"]


def test_select_cases_rejects_unknown_case():
    with pytest.raises(ValueError, match="unknown benchmark case"):
        _select_cases([_case("case_one")], "missing_case")


def test_smoke_output_does_not_overwrite_full_run_directory(tmp_path: Path):
    smoke = _output_dir("gemini", "case_one", tmp_path)
    full = _output_dir("gemini", None, tmp_path)
    assert smoke == tmp_path / "smoke" / "gemini" / "case_one"
    assert full == tmp_path / "gemini"
    assert smoke != full


def test_write_raw_results_creates_provider_named_json(tmp_path: Path):
    run = BenchmarkExecutionResult(
        case_id="case_one",
        query="Synthetic healthcare query.",
        model_provider="gemini",
        model_name="test-model",
        status="success",
        latency_seconds=1.0,
    )
    path = _write_raw_results([run], "gemini", tmp_path)
    assert path == tmp_path / "raw" / "benchmark-gemini.json"
    assert path.exists()
    assert '"case_id": "case_one"' in path.read_text()


def test_configure_provider_sets_environment():
    original = os.environ.get("MODEL_PROVIDER")
    try:
        _configure_provider("gemma")
        assert os.environ["MODEL_PROVIDER"] == "gemma"
    finally:
        if original is None:
            os.environ.pop("MODEL_PROVIDER", None)
        else:
            os.environ["MODEL_PROVIDER"] = original


def test_configure_provider_rejects_unknown_provider():
    with pytest.raises(ValueError, match="provider must be"):
        _configure_provider("unknown")


def test_cli_parser_accepts_provider_and_case():
    parser = build_parser()
    args = parser.parse_args(
        [
            "--provider",
            "gemini",
            "--case",
            "provider_houston_pediatric_dentistry",
        ]
    )
    assert args.provider == "gemini"
    assert args.case_id == "provider_houston_pediatric_dentistry"
