from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter
from opentelemetry.trace import Status

# Export only operational metadata that is explicitly approved.
#
# This intentionally excludes:
# - gcp.vertex.agent.llm_request
# - gcp.vertex.agent.llm_response
# - gcp.vertex.agent.tool_call_args
# - gcp.vertex.agent.tool_response
# - prompts / questions / answers
# - retrieved healthcare content
# - provider names
# - conversation/session/user identifiers
_SAFE_EXPORT_ATTRIBUTES = {
    # Our workflow metadata
    "workflow.name",
    "workflow.stage",
    "agent.name",
    "healthcare.intent",
    "retrieval.source_type",
    "retrieval.result_count",
    "evidence.selected_count",
    "mcp.tool.name",
    "retry.count",
    "error.type",

    # Model metadata
    "gen_ai.model.name",
    "gen_ai.model.provider",
    "gen_ai.system",
    "gen_ai.operation.name",
    "gen_ai.request.model",
    "gen_ai.agent.name",
    "gen_ai.response.finish_reasons",

    # Usage metadata
    "gen_ai.usage.input_tokens",
    "gen_ai.usage.output_tokens",
    "gen_ai.usage.reasoning.output_tokens",

    # Tool metadata
    "gen_ai.tool.name",
    "gen_ai.tool.type",

    # MCP protocol metadata
    "mcp.method.name",
    "mcp.protocol.version",
}


def sanitize_attributes(
    attributes: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Return only explicitly approved telemetry attributes."""
    if not attributes:
        return {}

    return {
        key: value
        for key, value in attributes.items()
        if key in _SAFE_EXPORT_ATTRIBUTES
    }


def sanitize_span(span: ReadableSpan) -> ReadableSpan:
    """
    Create a privacy-safe copy of an OpenTelemetry span.

    Trace IDs, span IDs, parent relationships, timing, span kind,
    instrumentation scope, and non-descriptive status are preserved.

    Potentially sensitive attributes, events, links, and status descriptions
    are intentionally removed before export.
    """

    status = Status(
        status_code=span.status.status_code,
    )

    return ReadableSpan(
        name=span.name,
        context=span.context,
        parent=span.parent,
        resource=span.resource,
        attributes=sanitize_attributes(span.attributes),
        events=(),
        links=(),
        kind=span.kind,
        status=status,
        start_time=span.start_time,
        end_time=span.end_time,
        instrumentation_scope=span.instrumentation_scope,
    )


class PrivacySafeSpanExporter(SpanExporter):
    """
    Sanitize every span before forwarding it to another exporter.

    This creates a final privacy boundary before telemetry reaches
    Console, OTLP, GKE, or Google Cloud Observability.
    """

    def __init__(
        self,
        delegate: SpanExporter,
    ) -> None:
        self._delegate = delegate

    def export(
        self,
        spans: Sequence[ReadableSpan],
    ):
        sanitized = [
            sanitize_span(span)
            for span in spans
        ]

        return self._delegate.export(sanitized)

    def shutdown(self) -> None:
        self._delegate.shutdown()

    def force_flush(
        self,
        timeout_millis: int = 30000,
    ) -> bool:
        return self._delegate.force_flush(
            timeout_millis=timeout_millis,
        )
