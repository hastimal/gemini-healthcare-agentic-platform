"""
Model factory for Google ADK agents.

v0.8 introduces model-runtime portability while keeping the healthcare
business logic independent from the selected LLM runtime.

Supported providers:

- gemini: Google-hosted Gemini model
- gemma: Gemma running locally through Ollama via ADK LiteLLM

The rest of the application should not need to know which runtime is active.
"""

from google.adk.models.lite_llm import LiteLlm

from app.config import get_settings


def get_agent_model():
    """
    Return the model configuration used by Google ADK agents.

    Gemini:
        Returns the configured Gemini model name directly. Google ADK
        resolves Gemini model strings through its native integration.

    Gemma:
        Returns an ADK LiteLlm instance configured for Ollama.

    Raises:
        ValueError: If the provider or required model configuration is missing.
    """

    settings = get_settings()
    provider = settings.model_provider.strip().lower()

    if provider == "gemini":
        if not settings.gemini_model:
            raise ValueError(
                "GEMINI_MODEL is not configured. "
                "Add it to your local .env file."
            )

        return settings.gemini_model

    if provider == "gemma":
        if not settings.gemma_model:
            raise ValueError(
                "GEMMA_MODEL is not configured. "
                "Add it to your local .env file."
            )

        return LiteLlm(
            model=f"ollama_chat/{settings.gemma_model}",
            api_base=settings.ollama_base_url,
        )

    raise ValueError(
        f"Unsupported MODEL_PROVIDER '{settings.model_provider}'. "
        "Supported providers: gemini, gemma."
    )
