from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
    OTLPSpanExporter,
)
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
)

SERVICE_NAME = "gemini-healthcare-agentic-platform"

_ALLOWED_ATTRIBUTE_KEYS = {
    "workflow.stage",
    "healthcare.intent",
    "retrieval.source_type",
    "retrieval.result_count",
    "evidence.selected_count",
    "mcp.tool.name",
    "retry.count",
    "error.type",
}


def tracing_enabled() -> bool:
    value = os.getenv("OTEL_TRACING_ENABLED", "false")
    return value.strip().lower() in {"1", "true", "yes", "on"}


def safe_span_attributes(
    attributes: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if not attributes:
        return {}

    safe: dict[str, Any] = {}

    for key, value in attributes.items():
        if key not in _ALLOWED_ATTRIBUTE_KEYS:
            continue

        if value is None:
            continue

        if isinstance(value, (str, bool, int, float)):
            safe[key] = value

    return safe


def configure_tracing() -> bool:
    if not tracing_enabled():
        return False

    resource = Resource.create(
        {
            "service.name": os.getenv(
                "OTEL_SERVICE_NAME",
                SERVICE_NAME,
            )
        }
    )

    provider = TracerProvider(resource=resource)

    exporter_name = os.getenv(
        "OTEL_TRACES_EXPORTER",
        "console",
    ).strip().lower()

    if exporter_name == "console":
        provider.add_span_processor(
            SimpleSpanProcessor(
                ConsoleSpanExporter()
            )
        )

    elif exporter_name == "otlp":
        provider.add_span_processor(
            BatchSpanProcessor(
                OTLPSpanExporter()
            )
        )

    else:
        raise ValueError(
            f"Unsupported OTEL_TRACES_EXPORTER: {exporter_name}"
        )

    trace.set_tracer_provider(provider)

    return True


def get_tracer():
    return trace.get_tracer(
        "gemini_healthcare_agentic_platform"
    )