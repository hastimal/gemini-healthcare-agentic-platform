from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.trace import SpanContext, SpanKind, Status, StatusCode, TraceFlags

from observability.privacy_exporter import (
    sanitize_attributes,
    sanitize_span,
)


def _span_context() -> SpanContext:
    return SpanContext(
        trace_id=1,
        span_id=2,
        is_remote=False,
        trace_flags=TraceFlags(1),
        trace_state=None,
    )


def test_sanitize_attributes_keeps_safe_metadata():
    attributes = sanitize_attributes(
        {
            "workflow.stage": "healthcare_research",
            "gen_ai.request.model": "gemini-3.7-flash",
            "gen_ai.usage.input_tokens": 120,
            "mcp.tool.name": "search_biomedical_literature",
        }
    )

    assert attributes["workflow.stage"] == "healthcare_research"
    assert attributes["gen_ai.request.model"] == "gemini-3.7-flash"
    assert attributes["gen_ai.usage.input_tokens"] == 120
    assert attributes["mcp.tool.name"] == "search_biomedical_literature"


def test_sanitize_attributes_removes_sensitive_adk_payloads():
    attributes = sanitize_attributes(
        {
            "gcp.vertex.agent.llm_request": "PRIVATE PROMPT",
            "gcp.vertex.agent.llm_response": "PRIVATE RESPONSE",
            "gcp.vertex.agent.tool_call_args": "PRIVATE TOOL ARGS",
            "gcp.vertex.agent.tool_response": "PRIVATE TOOL RESPONSE",
            "gen_ai.conversation.id": "private-session",
            "workflow.stage": "workflow",
        }
    )

    assert attributes == {
        "workflow.stage": "workflow",
    }


def test_sanitize_span_preserves_trace_structure():
    parent = SpanContext(
        trace_id=1,
        span_id=3,
        is_remote=False,
        trace_flags=TraceFlags(1),
        trace_state=None,
    )

    span = ReadableSpan(
        name="call_llm",
        context=_span_context(),
        parent=parent,
        resource=Resource.create(
            {"service.name": "test-service"}
        ),
        attributes={
            "gen_ai.request.model": "gemini-3.7-flash",
            "gcp.vertex.agent.llm_request": "PRIVATE PROMPT",
        },
        events=(),
        links=(),
        kind=SpanKind.INTERNAL,
        status=Status(StatusCode.OK),
        start_time=100,
        end_time=200,
    )

    sanitized = sanitize_span(span)

    assert sanitized.name == "call_llm"
    assert sanitized.context == span.context
    assert sanitized.parent == span.parent
    assert sanitized.start_time == 100
    assert sanitized.end_time == 200

    assert sanitized.attributes == {
        "gen_ai.request.model": "gemini-3.7-flash",
    }
