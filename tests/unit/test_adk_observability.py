from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from observability.adk_callbacks import (
    PrivacySafeObservabilityPlugin,
    _model_provider,
)


def _callback_context(
    agent_name: str = "search_planner_agent",
):
    return SimpleNamespace(
        invocation_id="invocation-123",
        agent_name=agent_name,
    )


def _mock_span_context():
    span = MagicMock()
    span.get_span_context.return_value = SimpleNamespace(
        trace_id=0x1234567890ABCDEF1234567890ABCDEF
    )

    context_manager = MagicMock()
    context_manager.__enter__.return_value = span
    context_manager.__exit__.return_value = False

    return span, context_manager


def test_model_provider_detection():
    assert _model_provider("gemini-3.7-flash") == "gemini"
    assert _model_provider("ollama_chat/gemma3") == "gemma"
    assert _model_provider(None) == "unknown"


@pytest.mark.asyncio
async def test_agent_span_records_safe_metadata_only():
    mock_tracer = MagicMock()
    span, context_manager = _mock_span_context()

    mock_tracer.start_as_current_span.return_value = (
        context_manager
    )

    with patch(
        "observability.adk_callbacks.get_tracer",
        return_value=mock_tracer,
    ):
        plugin = PrivacySafeObservabilityPlugin()

    agent = SimpleNamespace(
        name="search_planner_agent"
    )

    callback_context = _callback_context()

    await plugin.before_agent_callback(
        agent=agent,
        callback_context=callback_context,
    )

    mock_tracer.start_as_current_span.assert_called_with(
        "adk.agent.search_planner_agent"
    )

    span.set_attribute.assert_any_call(
        "agent.name",
        "search_planner_agent",
    )

    await plugin.after_agent_callback(
        agent=agent,
        callback_context=callback_context,
    )

    context_manager.__exit__.assert_called_once_with(
        None,
        None,
        None,
    )


@pytest.mark.asyncio
async def test_model_span_records_model_metadata_without_prompt():
    mock_tracer = MagicMock()
    span, context_manager = _mock_span_context()

    mock_tracer.start_as_current_span.return_value = (
        context_manager
    )

    with patch(
        "observability.adk_callbacks.get_tracer",
        return_value=mock_tracer,
    ):
        plugin = PrivacySafeObservabilityPlugin()

    callback_context = _callback_context()

    llm_request = SimpleNamespace(
        model="gemini-3.7-flash",
        contents=[
            "PRIVATE HEALTHCARE PROMPT"
        ],
    )

    await plugin.before_model_callback(
        callback_context=callback_context,
        llm_request=llm_request,
    )

    span.set_attribute.assert_any_call(
        "gen_ai.model.name",
        "gemini-3.7-flash",
    )

    span.set_attribute.assert_any_call(
        "gen_ai.model.provider",
        "gemini",
    )

    recorded_values = [
        call.args[1]
        for call in span.set_attribute.call_args_list
    ]

    assert "PRIVATE HEALTHCARE PROMPT" not in recorded_values


@pytest.mark.asyncio
async def test_workflow_span_opens_and_closes():
    mock_tracer = MagicMock()
    span, context_manager = _mock_span_context()

    mock_tracer.start_as_current_span.return_value = (
        context_manager
    )

    with patch(
        "observability.adk_callbacks.get_tracer",
        return_value=mock_tracer,
    ):
        plugin = PrivacySafeObservabilityPlugin()

    invocation_context = SimpleNamespace()

    await plugin.before_run_callback(
        invocation_context=invocation_context,
    )

    mock_tracer.start_as_current_span.assert_called_with(
        "workflow.gemini_healthcare_agentic_platform"
    )

    span.set_attribute.assert_any_call(
        "workflow.name",
        "gemini_healthcare_agentic_platform",
    )

    await plugin.after_run_callback(
        invocation_context=invocation_context,
    )

    context_manager.__exit__.assert_called_once_with(
        None,
        None,
        None,
    )
