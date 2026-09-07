from __future__ import annotations

import csv
from pathlib import Path

from evaluation.comparison import generate_comparison


def _write(path: Path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _seed(root: Path, provider: str, model: str, fhir_status: str = "success"):
    p = root / provider
    passed = 3 if fhir_status == "success" else 2
    _write(
        p / "summary.csv",
        [
            "model_provider",
            "model_name",
            "cases",
            "evaluated_cases",
            "passed_cases",
            "failed_cases",
            "pass_rate",
            "mean_retrieved_sources",
            "mean_citations",
            "median_latency_seconds",
            "mean_latency_seconds",
        ],
        [
            {
                "model_provider": provider,
                "model_name": model,
                "cases": 3,
                "evaluated_cases": 3,
                "passed_cases": passed,
                "failed_cases": 3 - passed,
                "pass_rate": passed / 3,
                "mean_retrieved_sources": 4,
                "mean_citations": 2,
                "median_latency_seconds": 12,
                "mean_latency_seconds": 13,
            }
        ],
    )
    _write(
        p / "intent-summary.csv",
        [
            "benchmark_intent",
            "model_provider",
            "model_name",
            "cases",
            "passed_cases",
            "pass_rate",
            "mean_retrieved_sources",
            "mean_citations",
            "median_latency_seconds",
        ],
        [
            {
                "benchmark_intent": "PROVIDER_DISCOVERY",
                "model_provider": provider,
                "model_name": model,
                "cases": 1,
                "passed_cases": 1,
                "pass_rate": 1,
                "mean_retrieved_sources": 8,
                "mean_citations": 5,
                "median_latency_seconds": 10,
            },
            {
                "benchmark_intent": "FHIR_INTEROPERABILITY",
                "model_provider": provider,
                "model_name": model,
                "cases": 1,
                "passed_cases": 1 if fhir_status == "success" else 0,
                "pass_rate": 1 if fhir_status == "success" else 0,
                "mean_retrieved_sources": 3 if fhir_status == "success" else 0,
                "mean_citations": 3 if fhir_status == "success" else 0,
                "median_latency_seconds": 20,
            },
            {
                "benchmark_intent": "CLINICAL_TRIALS",
                "model_provider": provider,
                "model_name": model,
                "cases": 1,
                "passed_cases": 1,
                "pass_rate": 1,
                "mean_retrieved_sources": 0,
                "mean_citations": 0,
                "median_latency_seconds": 2,
            },
        ],
    )
    _write(
        p / "metric-summary.csv",
        [
            "model_provider",
            "model_name",
            "metric",
            "evaluated_cases",
            "passed",
            "failed",
            "pass_rate",
            "mean_score",
        ],
        [
            {
                "model_provider": provider,
                "model_name": model,
                "metric": "citation_presence",
                "evaluated_cases": 2 if fhir_status == "success" else 1,
                "passed": 2 if fhir_status == "success" else 1,
                "failed": 0,
                "pass_rate": 1,
                "mean_score": 1,
            }
        ],
    )
    fields = [
        "benchmark_version",
        "case_id",
        "title",
        "query",
        "benchmark_intent",
        "tags",
        "model_provider",
        "model_name",
        "execution_status",
        "overall_passed",
        "hard_metrics",
        "hard_metrics_passed",
        "retrieved_sources",
        "deduplicated_sources",
        "selected_evidence_count",
        "recommendation_count",
        "citation_count",
        "latency_seconds",
        "error_type",
        "error_message",
    ]
    _write(
        p / "case-results.csv",
        fields,
        [
            {
                "benchmark_version": "v1.1-core",
                "case_id": "provider_case",
                "title": "Provider",
                "query": "q",
                "benchmark_intent": "PROVIDER_DISCOVERY",
                "tags": "provider",
                "model_provider": provider,
                "model_name": model,
                "execution_status": "success",
                "overall_passed": True,
                "hard_metrics": 1,
                "hard_metrics_passed": 1,
                "retrieved_sources": 8,
                "deduplicated_sources": 8,
                "selected_evidence_count": 5,
                "recommendation_count": 3,
                "citation_count": 5,
                "latency_seconds": 10,
                "error_type": "",
                "error_message": "",
            },
            {
                "benchmark_version": "v1.1-core",
                "case_id": "fhir_case",
                "title": "FHIR",
                "query": "q",
                "benchmark_intent": "FHIR_INTEROPERABILITY",
                "tags": "fhir",
                "model_provider": provider,
                "model_name": model,
                "execution_status": fhir_status,
                "overall_passed": fhir_status == "success",
                "hard_metrics": 1,
                "hard_metrics_passed": 1 if fhir_status == "success" else 0,
                "retrieved_sources": 3 if fhir_status == "success" else 0,
                "deduplicated_sources": 3 if fhir_status == "success" else 0,
                "selected_evidence_count": 3 if fhir_status == "success" else 0,
                "recommendation_count": 0,
                "citation_count": 3 if fhir_status == "success" else 0,
                "latency_seconds": 20,
                "error_type": "" if fhir_status == "success" else "Timeout",
                "error_message": "",
            },
            {
                "benchmark_version": "v1.1-core",
                "case_id": "unsupported_case",
                "title": "Unsupported",
                "query": "q",
                "benchmark_intent": "CLINICAL_TRIALS",
                "tags": "unsupported",
                "model_provider": provider,
                "model_name": model,
                "execution_status": "unsupported",
                "overall_passed": True,
                "hard_metrics": 1,
                "hard_metrics_passed": 1,
                "retrieved_sources": 0,
                "deduplicated_sources": 0,
                "selected_evidence_count": 0,
                "recommendation_count": 0,
                "citation_count": 0,
                "latency_seconds": 2,
                "error_type": "NotImplementedError",
                "error_message": "expected",
            },
        ],
    )


def test_generate_comparison(tmp_path: Path):
    root = tmp_path / "results"
    _seed(root, "gemini", "gemini-test")
    _seed(root, "gemma", "gemma-test", "error")
    out = generate_comparison(root)
    assert {p.name for p in out.iterdir()} == {
        "model-comparison.csv",
        "workflow-comparison.csv",
        "metric-comparison.csv",
        "case-comparison.csv",
        "model-comparison.md",
    }


def test_timeout_is_preserved(tmp_path: Path):
    root = tmp_path / "results"
    _seed(root, "gemini", "gemini-test")
    _seed(root, "gemma", "gemma-test", "error")
    out = generate_comparison(root)
    rows = list(csv.DictReader((out / "case-comparison.csv").open(encoding="utf-8")))
    fhir = next(r for r in rows if r["case_id"] == "fhir_case")
    assert fhir["gemma_execution_status"] == "error"
    assert fhir["gemma_error_type"] == "Timeout"


def test_markdown_has_latency_caveat(tmp_path: Path):
    root = tmp_path / "results"
    _seed(root, "gemini", "gemini-test")
    _seed(root, "gemma", "gemma-test", "error")
    out = generate_comparison(root)
    md = (out / "model-comparison.md").read_text(encoding="utf-8")
    assert "not model-superiority claims" in md
    assert "Execution errors remain visible" in md
