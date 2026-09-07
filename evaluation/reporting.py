from __future__ import annotations

import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

from evaluation.models import ResearchBenchmarkCaseResult


def _rate(passed: int, evaluated: int) -> float | None:
    return None if evaluated == 0 else passed / evaluated


def _mean(values: list[float]) -> float | None:
    return statistics.fmean(values) if values else None


def _median(values: list[float]) -> float | None:
    return statistics.median(values) if values else None


def _fmt(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def case_rows(results: list[ResearchBenchmarkCaseResult]) -> list[dict[str, Any]]:
    rows = []
    for result in results:
        hard = [m for m in result.metrics if m.passed is not None]
        rows.append(
            {
                "benchmark_version": result.benchmark_version,
                "case_id": result.case_id,
                "title": result.title,
                "query": result.query,
                "benchmark_intent": result.benchmark_intent.value,
                "tags": "|".join(result.tags),
                "model_provider": result.model_provider,
                "model_name": result.model_name,
                "execution_status": result.execution_status,
                "overall_passed": result.overall_passed,
                "hard_metrics": len(hard),
                "hard_metrics_passed": sum(m.passed is True for m in hard),
                "retrieved_sources": result.retrieved_sources,
                "deduplicated_sources": result.deduplicated_sources,
                "selected_evidence_count": result.selected_evidence_count,
                "recommendation_count": result.recommendation_count,
                "citation_count": result.citation_count,
                "latency_seconds": result.latency_seconds,
                "error_type": result.error_type,
                "error_message": result.error_message,
            }
        )
    return rows


def metric_rows(results: list[ResearchBenchmarkCaseResult]) -> list[dict[str, Any]]:
    rows = []
    for result in results:
        for metric in result.metrics:
            rows.append(
                {
                    "benchmark_version": result.benchmark_version,
                    "case_id": result.case_id,
                    "benchmark_intent": result.benchmark_intent.value,
                    "model_provider": result.model_provider,
                    "model_name": result.model_name,
                    "metric": metric.metric,
                    "passed": metric.passed,
                    "score": metric.score,
                    "details": metric.details,
                }
            )
    return rows


def model_summary_rows(results: list[ResearchBenchmarkCaseResult]) -> list[dict[str, Any]]:
    grouped = defaultdict(list)
    for result in results:
        grouped[(result.model_provider, result.model_name)].append(result)

    rows = []
    for (provider, model_name), items in sorted(grouped.items()):
        evaluated = [item for item in items if item.overall_passed is not None]
        passed = sum(item.overall_passed is True for item in evaluated)
        latencies = [item.latency_seconds for item in items if item.latency_seconds is not None]
        rows.append(
            {
                "model_provider": provider,
                "model_name": model_name,
                "cases": len(items),
                "evaluated_cases": len(evaluated),
                "passed_cases": passed,
                "failed_cases": len(evaluated) - passed,
                "pass_rate": _rate(passed, len(evaluated)),
                "mean_retrieved_sources": _mean([float(item.retrieved_sources) for item in items]),
                "mean_citations": _mean([float(item.citation_count) for item in items]),
                "median_latency_seconds": _median(latencies),
                "mean_latency_seconds": _mean(latencies),
            }
        )
    return rows


def intent_summary_rows(results: list[ResearchBenchmarkCaseResult]) -> list[dict[str, Any]]:
    grouped = defaultdict(list)
    for result in results:
        grouped[(result.benchmark_intent.value, result.model_provider, result.model_name)].append(
            result
        )

    rows = []
    for (intent, provider, model_name), items in sorted(grouped.items()):
        evaluated = [item for item in items if item.overall_passed is not None]
        passed = sum(item.overall_passed is True for item in evaluated)
        latencies = [item.latency_seconds for item in items if item.latency_seconds is not None]
        rows.append(
            {
                "benchmark_intent": intent,
                "model_provider": provider,
                "model_name": model_name,
                "cases": len(items),
                "passed_cases": passed,
                "pass_rate": _rate(passed, len(evaluated)),
                "mean_retrieved_sources": _mean([float(item.retrieved_sources) for item in items]),
                "mean_citations": _mean([float(item.citation_count) for item in items]),
                "median_latency_seconds": _median(latencies),
            }
        )
    return rows


def metric_summary_rows(results: list[ResearchBenchmarkCaseResult]) -> list[dict[str, Any]]:
    grouped = defaultdict(list)
    for result in results:
        for metric in result.metrics:
            if metric.passed is not None:
                grouped[(result.model_provider, result.model_name, metric.metric)].append(metric)

    rows = []
    for (provider, model_name, metric_name), metrics in sorted(grouped.items()):
        passed = sum(metric.passed is True for metric in metrics)
        scores = [metric.score for metric in metrics if metric.score is not None]
        rows.append(
            {
                "model_provider": provider,
                "model_name": model_name,
                "metric": metric_name,
                "evaluated_cases": len(metrics),
                "passed": passed,
                "failed": len(metrics) - passed,
                "pass_rate": _rate(passed, len(metrics)),
                "mean_score": _mean(scores),
            }
        )
    return rows


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("")
        return
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(_fmt(value) for value in row) + " |")
    return "\n".join(lines)


def render_markdown(results: list[ResearchBenchmarkCaseResult]) -> str:
    model_rows = model_summary_rows(results)
    intent_rows = intent_summary_rows(results)
    metric_summary = metric_summary_rows(results)

    parts = [
        "# v1.1 Evaluation Benchmark Results",
        "",
        "> Generated from stored benchmark results. Do not edit measured values manually.",
        "",
        "## Model Summary",
        "",
        _markdown_table(
            ["Provider", "Model", "Cases", "Passed", "Pass Rate", "Median Latency (s)"],
            [
                [
                    r["model_provider"],
                    r["model_name"],
                    r["cases"],
                    r["passed_cases"],
                    r["pass_rate"],
                    r["median_latency_seconds"],
                ]
                for r in model_rows
            ],
        ),
        "",
        "## Workflow / Intent Summary",
        "",
        _markdown_table(
            [
                "Intent",
                "Provider",
                "Cases",
                "Passed",
                "Pass Rate",
                "Avg Retrieved",
                "Avg Citations",
                "Median Latency (s)",
            ],
            [
                [
                    r["benchmark_intent"],
                    r["model_provider"],
                    r["cases"],
                    r["passed_cases"],
                    r["pass_rate"],
                    r["mean_retrieved_sources"],
                    r["mean_citations"],
                    r["median_latency_seconds"],
                ]
                for r in intent_rows
            ],
        ),
        "",
        "## Metric Summary",
        "",
        _markdown_table(
            ["Provider", "Metric", "Evaluated", "Passed", "Failed", "Pass Rate", "Mean Score"],
            [
                [
                    r["model_provider"],
                    r["metric"],
                    r["evaluated_cases"],
                    r["passed"],
                    r["failed"],
                    r["pass_rate"],
                    r["mean_score"],
                ]
                for r in metric_summary
            ],
        ),
        "",
        "## Case Results",
        "",
        _markdown_table(
            [
                "Case",
                "Intent",
                "Provider",
                "Status",
                "Passed",
                "Retrieved",
                "Selected",
                "Citations",
                "Latency (s)",
            ],
            [
                [
                    r.case_id,
                    r.benchmark_intent.value,
                    r.model_provider,
                    r.execution_status,
                    r.overall_passed,
                    r.retrieved_sources,
                    r.selected_evidence_count,
                    r.citation_count,
                    r.latency_seconds,
                ]
                for r in results
            ],
        ),
        "",
        "Latency is reported as a diagnostic measurement, not as a model-superiority claim.",
        "",
    ]
    return "\n".join(parts)


def write_reports(results: list[ResearchBenchmarkCaseResult], output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "research_json": output_dir / "research-results.json",
        "case_csv": output_dir / "case-results.csv",
        "metric_csv": output_dir / "metric-results.csv",
        "summary_csv": output_dir / "summary.csv",
        "intent_csv": output_dir / "intent-summary.csv",
        "metric_summary_csv": output_dir / "metric-summary.csv",
        "markdown": output_dir / "results.md",
    }

    paths["research_json"].write_text(
        json.dumps([r.model_dump(mode="json") for r in results], indent=2) + "\n"
    )
    _write_csv(paths["case_csv"], case_rows(results))
    _write_csv(paths["metric_csv"], metric_rows(results))
    _write_csv(paths["summary_csv"], model_summary_rows(results))
    _write_csv(paths["intent_csv"], intent_summary_rows(results))
    _write_csv(paths["metric_summary_csv"], metric_summary_rows(results))
    paths["markdown"].write_text(render_markdown(results))
    return paths
