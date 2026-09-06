"""
Gemma structured synthesis adapter.

Gemma runs through Ollama and is accessed with LiteLLM.
"""

import json
import re
from typing import Any, TypeVar

from litellm import acompletion
from pydantic import BaseModel

from app.config import get_settings

SchemaT = TypeVar("SchemaT", bound=BaseModel)


class GemmaSynthesisClient:
    """Generate structured grounded drafts with local Gemma."""

    async def generate(
        self,
        *,
        prompt: str,
        schema: type[SchemaT],
    ) -> SchemaT:
        settings = get_settings()

        if not settings.gemma_model:
            raise ValueError(
                "GEMMA_MODEL is not configured. "
                "Add it to your local .env file."
            )

        if not settings.ollama_base_url:
            raise ValueError(
                "OLLAMA_BASE_URL is not configured."
            )

        response = await acompletion(
            model=f"ollama_chat/{settings.gemma_model}",
            base_url=settings.ollama_base_url,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            temperature=0.1,
            response_format=schema,
            timeout=600,
        )

        if not response.choices:
            raise RuntimeError(
                "Gemma returned no grounded-answer choices."
            )

        message = response.choices[0].message

        parsed = getattr(message, "parsed", None)

        if parsed is not None:
            if isinstance(parsed, schema):
                return parsed

            return schema.model_validate(parsed)

        content = getattr(message, "content", None)

        if not content:
            raise RuntimeError(
                "Gemma returned an empty grounded-answer response."
            )

        text = self._content_to_text(content)
        text = self._strip_code_fence(text)

        try:
            return schema.model_validate_json(text)
        except Exception:
            # Some OpenAI-compatible adapters may return a JSON object
            # serialized through an intermediate representation.
            parsed_json = json.loads(text)
            return schema.model_validate(parsed_json)

    @staticmethod
    def _content_to_text(content: Any) -> str:
        if isinstance(content, str):
            return content

        if isinstance(content, list):
            parts: list[str] = []

            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                    continue

                if isinstance(item, dict):
                    text = item.get("text")
                    if text:
                        parts.append(str(text))
                    continue

                text = getattr(item, "text", None)
                if text:
                    parts.append(str(text))

            return "".join(parts)

        return str(content)

    @staticmethod
    def _strip_code_fence(text: str) -> str:
        value = text.strip()

        match = re.fullmatch(
            r"```(?:json)?\s*(.*?)\s*```",
            value,
            flags=re.DOTALL | re.IGNORECASE,
        )

        if match:
            return match.group(1).strip()

        return value
