from google import genai

from app.config import get_settings


class GeminiClient:
    def __init__(self) -> None:
        settings = get_settings()

        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is not configured. Add it to your local .env file.")

        if not settings.gemini_model:
            raise ValueError("GEMINI_MODEL is not configured. Add it to your local .env file.")

        self.model = settings.gemini_model

        self.client = genai.Client(
            api_key=settings.gemini_api_key,
        )
