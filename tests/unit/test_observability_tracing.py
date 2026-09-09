from unittest.mock import MagicMock, patch

from observability.tracing import (
    safe_span_attributes,
    traced_span,
    tracing_enabled,
)


def test_tracing_disabled_by_default(
    monkeypatch,
):
    monkeypatch.delenv(
        "OTEL_TRACING_ENABLED",
        raising=False,
    )

    assert tracing_enabled() is False


def test_tracing_can_be_enabled(
    monkeypatch,
):
    monkeypatch.setenv(
        "OTEL_TRACING_ENABLED",
        "true",
    )

    assert tracing_enabled() is True


def test_safe_span_attributes_allows_operational_metadata():
    attributes = safe_span_attributes(
        {
            "workflow.stage": "research",
            "healthcare.intent": "provider_discovery",
            "retrieval.source_type": "nppes",
            "retrieval.result_count": 10,
            "evidence.selected_count": 5,
            "mcp.tool.name": "find_providers",
            "retry.count": 1,
        }
    )

    assert attributes["workflow.stage"] == "research"
    assert attributes["retrieval.result_count"] == 10
    assert attributes["mcp.tool.name"] == "find_providers"


def test_safe_span_attributes_rejects_content():
    attributes = safe_span_attributes(
        {
            "question": "private healthcare question",
            "prompt": "private prompt",
            "answer": "private answer",
            "provider.name": "Example Provider",
            "retrieval.document": "document body",
            "workflow.stage": "research",
        }
    )

    assert attributes == {
        "workflow.stage": "research"
    }


def test_traced_span_sets_safe_attributes():
    mock_span = MagicMock()

    mock_context = MagicMock()
    mock_context.__enter__.return_value = mock_span
    mock_context.__exit__.return_value = False

    mock_tracer = MagicMock()
    mock_tracer.start_as_current_span.return_value = mock_context

    with patch(
        "observability.tracing.get_tracer",
        return_value=mock_tracer,
    ):
        with traced_span(
            "mcp.provider_search",
            attributes={
                "workflow.stage": "healthcare_research",
                "retrieval.source_type": "nppes",
                "retrieval.result_count": 10,
                "question": "do not export this",
            },
        ):
            pass

    mock_span.set_attribute.assert_any_call(
        "workflow.stage",
        "healthcare_research",
    )

    mock_span.set_attribute.assert_any_call(
        "retrieval.source_type",
        "nppes",
    )

    mock_span.set_attribute.assert_any_call(
        "retrieval.result_count",
        10,
    )

    forbidden_calls = [
        call
        for call in mock_span.set_attribute.call_args_list
        if call.args[0] == "question"
    ]

    assert forbidden_calls == []


def test_traced_span_records_exception():
    mock_span = MagicMock()

    mock_context = MagicMock()
    mock_context.__enter__.return_value = mock_span
    mock_context.__exit__.return_value = False

    mock_tracer = MagicMock()
    mock_tracer.start_as_current_span.return_value = mock_context

    with patch(
        "observability.tracing.get_tracer",
        return_value=mock_tracer,
    ):
        try:
            with traced_span(
                "mcp.pubmed_search",
                attributes={
                    "workflow.stage": "healthcare_research",
                },
            ):
                raise RuntimeError("test failure")

        except RuntimeError:
            pass

    assert mock_span.record_exception.called

    mock_span.set_attribute.assert_any_call(
        "error.type",
        "RuntimeError",
    )