"""Cross-model comparison reporting for the v1.1 evaluation benchmark."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

DEFAULT_PROVIDERS = ("gemini", "gemma")


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Required benchmark report not found: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _as_int(value: str | int | None) -> int:
    return 0 if value in (None, "") else int(float(value))


def _as_float(value: str | float | None) -> float:
    return 0.0 if value in (None, "") else float(value)


def _as_bool(value: str | bool | None) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


def _provider_reports(results_root: Path, provider: str) -> dict[str, list[dict[str, str]]]:
    root = results_root / provider
    return {
        "summary": _read_csv(root / "summary.csv"),
        "intent": _read_csv(root / "intent-summary.csv"),
        "metric": _read_csv(root / "metric-summary.csv"),
        "case": _read_csv(root / "case-results.csv"),
    }


def _provider_order(reports):
    preferred = [p for p in DEFAULT_PROVIDERS if p in reports]
    return preferred + sorted(p for p in reports if p not in preferred)


def build_model_comparison(reports):
    rows = []
    for provider in _provider_order(reports):
        summary_rows = reports[provider]["summary"]
        if len(summary_rows) != 1:
            raise ValueError(f"{provider}: expected exactly one summary row")
        summary = summary_rows[0]
        cases = reports[provider]["case"]
        unsupported = [r for r in cases if r["execution_status"] == "unsupported"]
        supported = [r for r in cases if r["execution_status"] != "unsupported"]
        supported_successes = [r for r in supported if r["execution_status"] == "success"]
        unsupported_passed = [r for r in unsupported if _as_bool(r["overall_passed"])]
        rows.append(
            {
                "model_provider": provider,
                "model_name": summary["model_name"],
                "core_cases": _as_int(summary["cases"]),
                "supported_cases": len(supported),
                "supported_successes": len(supported_successes),
                "expected_unsupported_cases": len(unsupported),
                "expected_unsupported_passed": len(unsupported_passed),
                "overall_passed": _as_int(summary["passed_cases"]),
                "overall_failed": _as_int(summary["failed_cases"]),
                "pass_rate": _as_float(summary["pass_rate"]),
                "median_latency_seconds": _as_float(summary["median_latency_seconds"]),
                "mean_latency_seconds": _as_float(summary["mean_latency_seconds"]),
            }
        )
    return rows


def build_workflow_comparison(reports):
    providers = _provider_order(reports)
    intents = []
    for provider in providers:
        for item in reports[provider]["intent"]:
            if item["benchmark_intent"] not in intents:
                intents.append(item["benchmark_intent"])
    rows = []
    for intent in intents:
        row = {"benchmark_intent": intent}
        for provider in providers:
            match = next(
                (x for x in reports[provider]["intent"] if x["benchmark_intent"] == intent), None
            )
            for key in (
                "cases",
                "passed",
                "pass_rate",
                "mean_retrieved_sources",
                "mean_citations",
                "median_latency_seconds",
            ):
                row[f"{provider}_{key}"] = ""
            if match:
                row.update(
                    {
                        f"{provider}_cases": _as_int(match["cases"]),
                        f"{provider}_passed": _as_int(match["passed_cases"]),
                        f"{provider}_pass_rate": _as_float(match["pass_rate"]),
                        f"{provider}_mean_retrieved_sources": _as_float(
                            match["mean_retrieved_sources"]
                        ),
                        f"{provider}_mean_citations": _as_float(match["mean_citations"]),
                        f"{provider}_median_latency_seconds": _as_float(
                            match["median_latency_seconds"]
                        ),
                    }
                )
        rows.append(row)
    return rows


def build_metric_comparison(reports):
    providers = _provider_order(reports)
    metrics = sorted({r["metric"] for p in providers for r in reports[p]["metric"]})
    rows = []
    for metric in metrics:
        row = {"metric": metric}
        for provider in providers:
            match = next((x for x in reports[provider]["metric"] if x["metric"] == metric), None)
            for key in ("evaluated_cases", "passed", "failed", "pass_rate", "mean_score"):
                row[f"{provider}_{key}"] = ""
            if match:
                row.update(
                    {
                        f"{provider}_evaluated_cases": _as_int(match["evaluated_cases"]),
                        f"{provider}_passed": _as_int(match["passed"]),
                        f"{provider}_failed": _as_int(match["failed"]),
                        f"{provider}_pass_rate": _as_float(match["pass_rate"]),
                        f"{provider}_mean_score": _as_float(match["mean_score"]),
                    }
                )
        rows.append(row)
    return rows


def build_case_comparison(reports):
    providers = _provider_order(reports)
    case_order = [r["case_id"] for r in reports[providers[0]]["case"]]
    for provider in providers[1:]:
        for item in reports[provider]["case"]:
            if item["case_id"] not in case_order:
                case_order.append(item["case_id"])
    rows = []
    for case_id in case_order:
        base = next(r for p in providers for r in reports[p]["case"] if r["case_id"] == case_id)
        row = {
            "case_id": case_id,
            "benchmark_intent": base["benchmark_intent"],
            "title": base["title"],
        }
        for provider in providers:
            match = next((x for x in reports[provider]["case"] if x["case_id"] == case_id), None)
            for key in (
                "model_name",
                "execution_status",
                "overall_passed",
                "retrieved_sources",
                "selected_evidence_count",
                "citation_count",
                "latency_seconds",
                "error_type",
            ):
                row[f"{provider}_{key}"] = ""
            if match:
                row.update(
                    {
                        f"{provider}_model_name": match["model_name"],
                        f"{provider}_execution_status": match["execution_status"],
                        f"{provider}_overall_passed": _as_bool(match["overall_passed"]),
                        f"{provider}_retrieved_sources": _as_int(match["retrieved_sources"]),
                        f"{provider}_selected_evidence_count": _as_int(
                            match["selected_evidence_count"]
                        ),
                        f"{provider}_citation_count": _as_int(match["citation_count"]),
                        f"{provider}_latency_seconds": _as_float(match["latency_seconds"]),
                        f"{provider}_error_type": match.get("error_type", ""),
                    }
                )
        rows.append(row)
    return rows


def _table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    out += ["| " + " | ".join(str(v) for v in row) + " |" for row in rows]
    return "\n".join(out)


def render_markdown(model_rows, workflow_rows, metric_rows, case_rows, providers):
    lines = [
        "# v1.1 Gemini ↔ Gemma Benchmark Comparison",
        "",
        "> Generated from stored benchmark results. Do not edit measured values manually.",
        "",
        "## Model Summary",
        "",
    ]
    lines.append(
        _table(
            [
                "Provider",
                "Model",
                "Core",
                "Supported Success",
                "Expected Unsupported",
                "Passed",
                "Pass Rate",
                "Median Latency (s)",
            ],
            [
                [
                    r["model_provider"],
                    r["model_name"],
                    r["core_cases"],
                    f"{r['supported_successes']}/{r['supported_cases']}",
                    f"{r['expected_unsupported_passed']}/{r['expected_unsupported_cases']}",
                    f"{r['overall_passed']}/{r['core_cases']}",
                    f"{r['pass_rate']:.3f}",
                    f"{r['median_latency_seconds']:.3f}",
                ]
                for r in model_rows
            ],
        )
    )
    lines += ["", "## Workflow / Intent Comparison", ""]
    headers = ["Intent"]
    for p in providers:
        headers += [f"{p} Passed", f"{p} Pass Rate", f"{p} Median Latency (s)"]
    data = []
    for r in workflow_rows:
        vals = [r["benchmark_intent"]]
        for p in providers:
            c, pa, pr, lat = (
                r[f"{p}_cases"],
                r[f"{p}_passed"],
                r[f"{p}_pass_rate"],
                r[f"{p}_median_latency_seconds"],
            )
            vals += [
                "" if c == "" else f"{pa}/{c}",
                "" if pr == "" else f"{pr:.3f}",
                "" if lat == "" else f"{lat:.3f}",
            ]
        data.append(vals)
    lines.append(_table(headers, data))
    lines += ["", "## Metric Comparison", ""]
    headers = ["Metric"]
    for p in providers:
        headers += [f"{p} Passed", f"{p} Pass Rate"]
    data = []
    for r in metric_rows:
        vals = [r["metric"]]
        for p in providers:
            ev, pa, pr = r[f"{p}_evaluated_cases"], r[f"{p}_passed"], r[f"{p}_pass_rate"]
            vals += ["" if ev == "" else f"{pa}/{ev}", "" if pr == "" else f"{pr:.3f}"]
        data.append(vals)
    lines.append(_table(headers, data))
    lines += ["", "## Case Comparison", ""]
    headers = ["Case", "Intent"]
    for p in providers:
        headers += [
            f"{p} Status",
            f"{p} Passed",
            f"{p} Retrieved",
            f"{p} Citations",
            f"{p} Latency (s)",
        ]
    data = []
    for r in case_rows:
        vals = [r["case_id"], r["benchmark_intent"]]
        for p in providers:
            lat = r[f"{p}_latency_seconds"]
            vals += [
                r[f"{p}_execution_status"],
                r[f"{p}_overall_passed"],
                r[f"{p}_retrieved_sources"],
                r[f"{p}_citation_count"],
                "" if lat == "" else f"{lat:.3f}",
            ]
        data.append(vals)
    lines.append(_table(headers, data))
    lines += [
        "",
        "## Interpretation Notes",
        "",
        (
            "- Acceptance pass rates are deterministic benchmark outcomes for this frozen "
            "v1.1 Core Acceptance Set; they are not claims of general healthcare-AI accuracy."
        ),
        (
            "- Expected unsupported workflows pass only when the system rejects them "
            "explicitly rather than silently routing them to an unrelated retrieval source."
        ),
        (
            "- Citation, authority, grounding, and safety metrics are evaluated only "
            "where their workflow contracts apply."
        ),
        (
            "- Latency is a runtime diagnostic. Hosted Gemini API execution and local "
            "Gemma/Ollama execution are different runtime environments, so latency values "
            "are not model-superiority claims."
        ),
        (
            "- Execution errors remain visible in the comparison. They are not replaced "
            "by retry results."
        ),
        "",
    ]
    return "\n".join(lines)


def generate_comparison(results_root: Path, providers: tuple[str, ...] = DEFAULT_PROVIDERS) -> Path:
    reports = {p: _provider_reports(results_root, p) for p in providers}
    provider_order = _provider_order(reports)
    model_rows = build_model_comparison(reports)
    workflow_rows = build_workflow_comparison(reports)
    metric_rows = build_metric_comparison(reports)
    case_rows = build_case_comparison(reports)
    output_dir = results_root / "comparison"
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(output_dir / "model-comparison.csv", model_rows)
    _write_csv(output_dir / "workflow-comparison.csv", workflow_rows)
    _write_csv(output_dir / "metric-comparison.csv", metric_rows)
    _write_csv(output_dir / "case-comparison.csv", case_rows)
    (output_dir / "model-comparison.md").write_text(
        render_markdown(model_rows, workflow_rows, metric_rows, case_rows, provider_order),
        encoding="utf-8",
    )
    return output_dir


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate cross-model v1.1 benchmark comparison reports."
    )
    parser.add_argument("--results-root", default="evaluation/results")
    args = parser.parse_args()
    output_dir = generate_comparison(Path(args.results_root))
    print(f"comparison_output: {output_dir}")
    for name in (
        "model-comparison.csv",
        "workflow-comparison.csv",
        "metric-comparison.csv",
        "case-comparison.csv",
        "model-comparison.md",
    ):
        print(f"generated: {output_dir / name}")


if __name__ == "__main__":
    main()
