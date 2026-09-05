"""
Google ADK Search Planner Agent.

This agent converts the user's request into the existing validated
healthcare SearchPlan and stores the result in `planner_output`.
"""

from google.adk import Agent

from agents.adk.models import PlannerAgentOutput
from agents.search_planner.tools import create_healthcare_search_plan
from app.config import get_settings

settings = get_settings()


search_planner_agent = Agent(
    name="search_planner_agent",
    model=settings.gemini_model,
    mode="single_turn",
    description=(
        "Plans healthcare provider-discovery searches using Gemini query "
        "fan-out and the platform's validated SearchPlan model."
    ),
    instruction="""
You are the Search Planner Agent for a healthcare evidence-search platform.

Your responsibility is ONLY search planning.

You MUST call `create_healthcare_search_plan` exactly once.

Use the user's question as the `question`.

For the flagship workflow:
- location: Houston, TX
- specialty: Pediatric Dentistry

Do not search for providers yourself.
Do not rank providers.
Do not generate healthcare recommendations.
Do not invent search results.

After the tool returns, copy the tool result exactly into these fields:

- user_query
- search_plan

Do not convert these objects into JSON strings.
""",
    tools=[create_healthcare_search_plan],
    output_schema=PlannerAgentOutput,
    output_key="planner_output",
)
