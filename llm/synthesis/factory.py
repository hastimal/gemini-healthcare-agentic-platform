"""
Factory for grounded-answer synthesis providers.
"""

from app.config import get_settings
from llm.synthesis.base import SynthesisClient
from llm.synthesis.gemini import GeminiSynthesisClient
from llm.synthesis.gemma import GemmaSynthesisClient


def get_synthesis_client() -> SynthesisClient:
    """
    Return the synthesis adapter matching MODEL_PROVIDER.

    MODEL_PROVIDER=gemini
        -> Gemini hosted synthesis

    MODEL_PROVIDER=gemma
        -> Gemma through LiteLLM + Ollama
    """

    settings = get_settings()
    provider = settings.model_provider.strip().lower()

    if provider == "gemini":
        return GeminiSynthesisClient()

    if provider == "gemma":
        return GemmaSynthesisClient()

    raise ValueError(
        f"Unsupported MODEL_PROVIDER '{settings.model_provider}'. "
        "Supported providers: gemini, gemma."
    )
