from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path

from evaluation.models import BenchmarkExecutionResult
from evaluation.orchestrator import evaluate_runs
from evaluation.reporting import write_reports
from evaluation.runner import load_benchmark_cases, run_benchmark

DEFAULT_RESULTS_ROOT = Path("evaluation/results")


def _configure_provider(provider: str) -> None:
    normalized = provider.strip().lower()
    if normalized not in {"gemini", "gemma"}:
        raise ValueError("provider must be 'gemini' or 'gemma'")

    os.environ["MODEL_PROVIDER"] = normalized

    from app.config import get_settings

    cache_clear = getattr(get_settings, "cache_clear", None)
    if callable(cache_clear):
        cache_clear()


def _select_cases(cases, case_id: str | None):
    if case_id is None:
        return cases

    selected = [case for case in cases if case.case_id == case_id]
    if not selected:
        available = ", ".join(case.case_id for case in cases)
        raise ValueError(
            f"unknown benchmark case {case_id!r}. Available cases: {available}"
        )
    return selected


def _output_dir(
    provider: str,
    case_id: str | None,
    results_root: Path = DEFAULT_RESULTS_ROOT,
) -> Path:
    if case_id:
        return results_root / "smoke" / provider / case_id
    return results_root / provider


def _write_raw_results(
    results: list[BenchmarkExecutionResult],
    provider: str,
    output_dir: Path,
) -> Path:
    raw_dir = output_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / f"benchmark-{provider}.json"
    path.write_text(
        json.dumps(
            [result.model_dump(mode="json") for result in results],
            indent=2,
        )
        + "\n"
    )
    return path


async def execute_benchmark(
    *,
    provider: str,
    case_id: str | None = None,
    results_root: Path = DEFAULT_RESULTS_ROOT,
):
    _configure_provider(provider)

    all_cases = load_benchmark_cases()
    cases = _select_cases(all_cases, case_id)

    raw_runs = await run_benchmark(cases)
    research_results = evaluate_runs(cases, raw_runs)

    output_dir = _output_dir(provider, case_id, results_root)
    raw_path = _write_raw_results(raw_runs, provider, output_dir)
    report_paths = write_reports(research_results, output_dir)

    return {
        "provider": provider,
        "case_id": case_id,
        "cases": cases,
        "raw_runs": raw_runs,
        "research_results": research_results,
        "output_dir": output_dir,
        "raw_path": raw_path,
        "report_paths": report_paths,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the v1.1 reproducible healthcare evaluation benchmark."
    )
    parser.add_argument(
        "--provider",
        required=True,
        choices=["gemini", "gemma"],
        help="Model provider/runtime to evaluate.",
    )
    parser.add_argument(
        "--case",
        dest="case_id",
        help="Run one benchmark case as a smoke/acceptance check.",
    )
    parser.add_argument(
        "--results-root",
        type=Path,
        default=DEFAULT_RESULTS_ROOT,
        help="Directory under which benchmark artifacts are written.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()

    result = asyncio.run(
        execute_benchmark(
            provider=args.provider,
            case_id=args.case_id,
            results_root=args.results_root,
        )
    )

    raw_runs = result["raw_runs"]
    research_results = result["research_results"]

    success = sum(run.status == "success" for run in raw_runs)
    unsupported = sum(run.status == "unsupported" for run in raw_runs)
    errors = sum(run.status == "error" for run in raw_runs)
    passed = sum(item.overall_passed is True for item in research_results)
    failed = sum(item.overall_passed is False for item in research_results)

    print("")
    print("v1.1 Evaluation Benchmark")
    print(f"provider: {result['provider']}")
    print(f"cases: {len(raw_runs)}")
    print(f"execution_success: {success}")
    print(f"execution_unsupported: {unsupported}")
    print(f"execution_errors: {errors}")
    print(f"evaluation_passed: {passed}")
    print(f"evaluation_failed: {failed}")
    print(f"raw_results: {result['raw_path']}")
    print(f"reports: {result['output_dir']}")
    print("")


if __name__ == "__main__":
    main()
