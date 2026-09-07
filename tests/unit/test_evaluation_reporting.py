from pathlib import Path

from evaluation.models import EvaluationIntent, EvaluationMetricResult, ResearchBenchmarkCaseResult
from evaluation.reporting import (
    case_rows,
    intent_summary_rows,
    metric_rows,
    metric_summary_rows,
    model_summary_rows,
    render_markdown,
    write_reports,
)


def _result(case_id="case_one", intent=EvaluationIntent.PROVIDER_DISCOVERY):
    return ResearchBenchmarkCaseResult(
        case_id=case_id,
        title="Synthetic case",
        query="Synthetic healthcare query",
        benchmark_intent=intent,
        model_provider="gemini",
        model_name="gemini-test",
        execution_status="success",
        latency_seconds=2.0,
        retrieved_sources=10,
        deduplicated_sources=8,
        selected_evidence_count=5,
        recommendation_count=3,
        citation_count=5,
        metrics=[
            EvaluationMetricResult(
                metric="citation_presence", passed=True, score=1.0, details="synthetic"
            ),
            EvaluationMetricResult(
                metric="observed_diagnostic", passed=None, details="not a hard metric"
            ),
        ],
        overall_passed=True,
    )


def test_case_rows_are_flat_and_paper_friendly():
    row = case_rows([_result()])[0]
    assert row["case_id"] == "case_one"
    assert row["benchmark_intent"] == "PROVIDER_DISCOVERY"
    assert row["hard_metrics"] == 1
    assert row["hard_metrics_passed"] == 1


def test_metric_rows_preserve_metric_level_results():
    rows = metric_rows([_result()])
    assert len(rows) == 2
    assert rows[0]["metric"] == "citation_presence"
    assert rows[1]["passed"] is None


def test_model_summary_computes_pass_rate_and_latency():
    rows = model_summary_rows([_result(), _result("case_two")])
    assert len(rows) == 1
    assert rows[0]["cases"] == 2
    assert rows[0]["pass_rate"] == 1.0
    assert rows[0]["median_latency_seconds"] == 2.0


def test_intent_summary_groups_by_workflow():
    rows = intent_summary_rows(
        [
            _result(),
            _result("case_two", EvaluationIntent.BIOMEDICAL_RESEARCH),
        ]
    )
    assert len(rows) == 2


def test_metric_summary_excludes_observation_only_metrics():
    rows = metric_summary_rows([_result()])
    assert len(rows) == 1
    assert rows[0]["metric"] == "citation_presence"
    assert rows[0]["pass_rate"] == 1.0


def test_markdown_contains_publication_tables():
    text = render_markdown([_result()])
    assert "## Model Summary" in text
    assert "## Workflow / Intent Summary" in text
    assert "## Metric Summary" in text
    assert "## Case Results" in text
    assert "model-superiority claim" in text


def test_write_reports_creates_all_expected_artifacts(tmp_path: Path):
    paths = write_reports([_result()], tmp_path)
    assert len(paths) == 7
    assert all(path.exists() for path in paths.values())
    assert "case_one" in paths["case_csv"].read_text()
    assert "citation_presence" in paths["metric_csv"].read_text()
    assert "Model Summary" in paths["markdown"].read_text()
