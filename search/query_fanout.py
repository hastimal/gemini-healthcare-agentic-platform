from pathlib import Path

from google.genai import types

from llm.gemini.client import GeminiClient
from models import SearchPlan, UserQuery

PROMPT_PATH = Path(__file__).resolve().parent.parent / "agents" / "prompts" / "query_agent.md"


def load_planner_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


class QueryFanoutPlanner:
    def __init__(self) -> None:
        self.gemini = GeminiClient()
        self.system_prompt = load_planner_prompt()

    def create_plan(self, user_query: UserQuery) -> SearchPlan:
        prompt = f"""
{self.system_prompt}

USER REQUEST:
{user_query.model_dump_json(indent=2)}

Create the search plan now.
"""

        response = self.gemini.client.models.generate_content(
            model=self.gemini.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=SearchPlan,
                temperature=0.2,
            ),
        )

        if not response.text:
            raise RuntimeError("Gemini returned an empty response.")

        return SearchPlan.model_validate_json(response.text)
