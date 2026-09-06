from unittest.mock import patch

import pytest

from app.config import Settings
from llm.model_factory import get_agent_model


def test_get_agent_model_returns_gemini_model_name():
    settings = Settings(
        model_provider="gemini",
        gemini_model="gemini-test-model",
    )

    with patch("llm.model_factory.get_settings", return_value=settings):
        model = get_agent_model()

    assert model == "gemini-test-model"


def test_get_agent_model_requires_gemini_model():
    settings = Settings(
        model_provider="gemini",
        gemini_model=None,
    )

    with patch("llm.model_factory.get_settings", return_value=settings):
        with pytest.raises(ValueError, match="GEMINI_MODEL"):
            get_agent_model()


def test_get_agent_model_returns_gemma_litellm():
    settings = Settings(
        model_provider="gemma",
        gemma_model="gemma4:test",
        ollama_base_url="http://localhost:11434",
    )

    with patch("llm.model_factory.get_settings", return_value=settings):
        model = get_agent_model()

    assert model.model == "ollama_chat/gemma4:test"


def test_get_agent_model_requires_gemma_model():
    settings = Settings(
        model_provider="gemma",
        gemma_model=None,
    )

    with patch("llm.model_factory.get_settings", return_value=settings):
        with pytest.raises(ValueError, match="GEMMA_MODEL"):
            get_agent_model()


def test_get_agent_model_rejects_unknown_provider():
    settings = Settings(
        model_provider="unknown",
    )

    with patch("llm.model_factory.get_settings", return_value=settings):
        with pytest.raises(ValueError, match="Unsupported MODEL_PROVIDER"):
            get_agent_model()
