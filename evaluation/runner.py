from __future__ import annotations

import asyncio
import json
import time
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

from google.adk.runners import InMemoryRunner
from google.genai import types

from app.config import get_settings
from evaluation.models import BenchmarkExecutionResult, EvaluationCase

APP_NAME = "v11_evaluation_benchmark"
USER_ID = "evaluation-benchmark-user"
DEFAULT_DATASET = Path("evaluation/datasets/healthcare_benchmark.jsonl")


def load_benchmark_cases(path: Path = DEFAULT_DATASET) -> list[EvaluationCase]:
    cases: list[EvaluationCase] = []
    with path.open() as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                cases.append(EvaluationCase.model_validate_json(line))
            except Exception as exc:
                raise ValueError(
                    f"Invalid benchmark case at {path}:{line_number}: {exc}"
                ) from exc
    return cases


def _model_configuration() -> tuple[str, str | None]:
    settings = get_settings()
    provider = settings.model_provider.strip().lower()
    if provider == "gemma":
        return provider, settings.gemma_model
    return provider, settings.gemini_model


def _event_entry(event: Any) -> dict[str, Any] | None:
    entry: dict[str, Any] = {
        "author": getattr(event, "author", None),
        "function_calls": [],
        "function_responses": [],
    }
    content = getattr(event, "content", None)
    if content:
        for part in content.parts or []:
            function_call = getattr(part, "function_call", None)
            function_response = getattr(part, "function_response", None)
            if function_call:
                entry["function_calls"].append(
                    {"name": function_call.name, "args": function_call.args}
                )
            if function_response:
                entry["function_responses"].append(
                    {"name": function_response.name}
                )
    if entry["author"] or entry["function_calls"] or entry["function_responses"]:
        return entry
    return None


async def run_case(
    case: EvaluationCase,
    *,
    runner_factory: Callable[..., Any] = InMemoryRunner,
) -> BenchmarkExecutionResult:
    # Import the production workflow lazily so dataset/unit-test operations do not
    # instantiate model-backed agents unnecessarily.
    from agents.workflows.healthcare_workflow import root_agent

    provider, model_name = _model_configuration()
    session_id = f"eval-{case.case_id}-{uuid.uuid4()}"
    runner = runner_factory(app_name=APP_NAME, agent=root_agent)
    event_log: list[dict[str, Any]] = []
    started = time.perf_counter()

    try:
        session = await runner.session_service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=session_id,
        )
        message = types.Content(
            role="user",
            parts=[types.Part(text=case.query)],
        )

        async for event in runner.run_async(
            user_id=session.user_id,
            session_id=session.id,
            new_message=message,
        ):
            entry = _event_entry(event)
            if entry:
                event_log.append(entry)

        final_session = await runner.session_service.get_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=session.id,
        )
        state = final_session.state or {}

        return BenchmarkExecutionResult(
            case_id=case.case_id,
            query=case.query,
            model_provider=provider,
            model_name=model_name,
            status="success",
            planner_output=state.get("planner_output"),
            research_output=state.get("research_output"),
            answer_output=state.get("answer_output"),
            event_log=event_log,
            latency_seconds=time.perf_counter() - started,
        )
    except Exception as exc:
        return BenchmarkExecutionResult(
            case_id=case.case_id,
            query=case.query,
            model_provider=provider,
            model_name=model_name,
            status=(
                "unsupported"
                if isinstance(exc, NotImplementedError)
                else "error"
            ),
            event_log=event_log,
            latency_seconds=time.perf_counter() - started,
            error_type=type(exc).__name__,
            error_message=str(exc),
        )


async def run_benchmark(
    cases: list[EvaluationCase],
) -> list[BenchmarkExecutionResult]:
    # Sequential execution is intentional: it avoids mixing model/tool traffic
    # across benchmark cases and keeps diagnostics easy to audit.
    results: list[BenchmarkExecutionResult] = []
    for case in cases:
        results.append(await run_case(case))
    return results


def save_results(
    results: list[BenchmarkExecutionResult],
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = [result.model_dump(mode="json") for result in results]
    output_path.write_text(json.dumps(payload, indent=2) + "\n")


def main() -> None:
    cases = load_benchmark_cases()
    results = asyncio.run(run_benchmark(cases))
    provider = results[0].model_provider if results else "unknown"
    output_path = Path("evaluation/results") / f"benchmark-{provider}.json"
    save_results(results, output_path)

    succeeded = sum(result.status == "success" for result in results)
    unsupported = sum(result.status == "unsupported" for result in results)
    errors = sum(result.status == "error" for result in results)

    print(f"cases: {len(results)}")
    print(f"success: {succeeded}")
    print(f"unsupported: {unsupported}")
    print(f"errors: {errors}")
    print(f"results: {output_path}")


if __name__ == "__main__":
    main()
