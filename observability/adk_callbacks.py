from __future__ import annotations

from typing import Any

from google.adk.plugins.base_plugin import BasePlugin
from opentelemetry import trace

from observability.tracing import get_tracer, safe_span_attributes


def _model_provider(model_name: str | None) -> str:
    if not model_name:
        return "unknown"

    normalized = model_name.lower()

    if "gemini" in normalized:
        return "gemini"

    if "gemma" in normalized or "ollama" in normalized:
        return "gemma"

    return "unknown"


class PrivacySafeObservabilityPlugin(BasePlugin):
    """
    Privacy-safe OpenTelemetry instrumentation for Google ADK.

    This plugin records operational metadata only.

    It intentionally does not record:
    - user questions
    - prompts
    - model responses
    - provider names
    - retrieved documents
    - grounded answers
    - secrets
    """

    def __init__(self) -> None:
        super().__init__(name="privacy_safe_observability")

        self._tracer = get_tracer()

        self._workflow_context: Any | None = None
        self._trace_id: str | None = None

        self._agent_contexts: dict[str, Any] = {}
        self._model_contexts: dict[str, Any] = {}

    @property
    def trace_id(self) -> str | None:
        """Return the current workflow trace ID as 32-character hex."""
        return self._trace_id

    @staticmethod
    def _agent_key(callback_context: Any) -> str:
        return (
            f"{callback_context.invocation_id}:"
            f"{callback_context.agent_name}"
        )

    @staticmethod
    def _model_key(callback_context: Any) -> str:
        return (
            f"{callback_context.invocation_id}:"
            f"{callback_context.agent_name}:model"
        )

    async def before_run_callback(
        self,
        *,
        invocation_context: Any,
    ) -> None:
        context_manager = self._tracer.start_as_current_span(
            "workflow.gemini_healthcare_agentic_platform"
        )

        span = context_manager.__enter__()

        span_context = span.get_span_context()
        if span_context.trace_id:
            self._trace_id = format(
                span_context.trace_id,
                "032x",
            )

        for key, value in safe_span_attributes(
            {
                "workflow.name": (
                    "gemini_healthcare_agentic_platform"
                ),
                "workflow.stage": "workflow",
            }
        ).items():
            span.set_attribute(key, value)

        self._workflow_context = context_manager

    async def after_run_callback(
        self,
        *,
        invocation_context: Any,
    ) -> None:
        if self._workflow_context is not None:
            self._workflow_context.__exit__(
                None,
                None,
                None,
            )
            self._workflow_context = None

    async def before_agent_callback(
        self,
        *,
        agent: Any,
        callback_context: Any,
    ) -> None:
        key = self._agent_key(callback_context)

        context_manager = self._tracer.start_as_current_span(
            f"adk.agent.{agent.name}"
        )

        span = context_manager.__enter__()

        for attribute, value in safe_span_attributes(
            {
                "workflow.stage": agent.name,
                "agent.name": agent.name,
            }
        ).items():
            span.set_attribute(attribute, value)

        self._agent_contexts[key] = context_manager

    async def after_agent_callback(
        self,
        *,
        agent: Any,
        callback_context: Any,
    ) -> None:
        key = self._agent_key(callback_context)

        context_manager = self._agent_contexts.pop(
            key,
            None,
        )

        if context_manager is not None:
            context_manager.__exit__(
                None,
                None,
                None,
            )

    async def on_agent_error_callback(
        self,
        *,
        agent: Any,
        callback_context: Any,
        error: Exception,
    ) -> None:
        key = self._agent_key(callback_context)

        context_manager = self._agent_contexts.pop(
            key,
            None,
        )

        if context_manager is None:
            return

        span = trace.get_current_span()

        if span.is_recording():
            span.record_exception(error)
            span.set_attribute(
                "error.type",
                type(error).__name__,
            )

        context_manager.__exit__(
            type(error),
            error,
            error.__traceback__,
        )

    async def before_model_callback(
        self,
        *,
        callback_context: Any,
        llm_request: Any,
    ) -> None:
        key = self._model_key(callback_context)

        model_name = getattr(
            llm_request,
            "model",
            None,
        )

        context_manager = self._tracer.start_as_current_span(
            "gen_ai.model"
        )

        span = context_manager.__enter__()

        for attribute, value in safe_span_attributes(
            {
                "agent.name": callback_context.agent_name,
                "gen_ai.model.name": model_name or "unknown",
                "gen_ai.model.provider": _model_provider(
                    model_name
                ),
            }
        ).items():
            span.set_attribute(attribute, value)

        self._model_contexts[key] = context_manager

    async def after_model_callback(
        self,
        *,
        callback_context: Any,
        llm_response: Any,
    ) -> None:
        key = self._model_key(callback_context)

        context_manager = self._model_contexts.pop(
            key,
            None,
        )

        if context_manager is None:
            return

        span = trace.get_current_span()

        model_version = getattr(
            llm_response,
            "model_version",
            None,
        )

        if (
            span.is_recording()
            and model_version
        ):
            span.set_attribute(
                "gen_ai.model.name",
                model_version,
            )

        context_manager.__exit__(
            None,
            None,
            None,
        )

    async def on_model_error_callback(
        self,
        *,
        callback_context: Any,
        llm_request: Any,
        error: Exception,
    ) -> None:
        key = self._model_key(callback_context)

        context_manager = self._model_contexts.pop(
            key,
            None,
        )

        if context_manager is None:
            return

        span = trace.get_current_span()

        if span.is_recording():
            span.record_exception(error)
            span.set_attribute(
                "error.type",
                type(error).__name__,
            )

        context_manager.__exit__(
            type(error),
            error,
            error.__traceback__,
        )
