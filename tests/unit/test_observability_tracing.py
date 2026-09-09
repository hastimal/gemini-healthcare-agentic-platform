from observability.tracing import (
    safe_span_attributes,
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