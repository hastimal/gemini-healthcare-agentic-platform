"""
Gemini structured synthesis adapter.
"""

from typing import TypeVar

from google import genai
from google.genai import types
from pydantic import BaseModel

from app.config import get_settings

SchemaT = TypeVar("SchemaT", bound=BaseModel)


class GeminiSynthesisClient:
    """Generate structured grounded drafts with Gemini."""

    async def generate(
        self,
        *,
        prompt: str,
        schema: type[SchemaT],
    ) -> SchemaT:
        settings = get_settings()

        if not settings.gemini_api_key:
            raise ValueError(
                "GEMINI_API_KEY is not configured. "
                "Add it to your local .env file."
            )

        if not settings.gemini_model:
            raise ValueError(
                "GEMINI_MODEL is not configured. "
                "Add it to your local .env file."
            )

        async with genai.Client(
            api_key=settings.gemini_api_key,
        ).aio as client:
            response = await client.models.generate_content(
                model=settings.gemini_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema,
                    temperature=0.1,
                ),
            )

        if not response.text:
            raise RuntimeError(
                "Gemini returned an empty grounded-answer response."
            )

        return schema.model_validate_json(response.text)
