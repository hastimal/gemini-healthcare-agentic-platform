"""
Google ADK Healthcare Research Agent.

This agent consumes `planner_output`, retrieves real healthcare evidence,
and stores structured results under `research_output`.
"""

from google.adk import Agent

from agents.adk.models import ResearchAgentOutput
from agents.healthcare_research.tools import retrieve_healthcare_evidence
from app.config import get_settings

settings = get_settings()


healthcare_research_agent = Agent(
    name="healthcare_research_agent",
    model=settings.gemini_model,
    mode="single_turn",
    description=(
        "Retrieves healthcare provider evidence from CMS NPPES and "
        "supporting biomedical evidence from PubMed."
    ),
    instruction="""
You are the Healthcare Research Agent in a sequential healthcare
evidence workflow.

The Search Planner Agent has already completed its task.

Its structured output is available here:

{planner_output}

That object contains:

- user_query
- search_plan

Your responsibility is ONLY evidence retrieval.

You MUST:

1. Read `user_query` from planner_output.
2. Read `search_plan` from planner_output.
3. Call `retrieve_healthcare_evidence` exactly once.
4. Return the tool result using the required structured output schema.

Do not convert the objects into JSON strings.

Do not create a new search plan.
Do not modify the supplied search plan.
Do not invent providers.
Do not invent PubMed studies.
Do not rank evidence.
Do not decide which provider is best.
Do not generate the final healthcare answer.

Return exactly:

- user_query
- search_plan
- search_results
- retrieved_sources
- deduplicated_sources
""",
    tools=[retrieve_healthcare_evidence],
    output_schema=ResearchAgentOutput,
    output_key="research_output",
)
