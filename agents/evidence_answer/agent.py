"""
Google ADK Evidence & Answer Agent.

This final specialist agent consumes `research_output` and reuses the
tested v0.3 ranking and v0.4 grounding/citation pipeline.

The result is stored under `answer_output`.
"""

from google.adk import Agent

from agents.adk.models import EvidenceAnswerAgentOutput
from agents.evidence_answer.tools import build_grounded_healthcare_answer
from app.config import get_settings

settings = get_settings()


evidence_answer_agent = Agent(
    name="evidence_answer_agent",
    model=settings.gemini_model,
    mode="single_turn",
    description=(
        "Ranks healthcare evidence and produces a validated, "
        "citation-grounded final answer."
    ),
    instruction="""
You are the Evidence & Answer Agent in a sequential healthcare
evidence workflow.

The Healthcare Research Agent has already completed evidence retrieval.

Its structured output is available here:

{research_output}

That object contains:

- user_query
- search_plan
- search_results
- retrieved_sources
- deduplicated_sources

Your responsibility is ONLY to invoke the existing evidence ranking,
selection, grounding, citation, and validation pipeline.

You MUST:

1. Read all five fields from research_output.
2. Call `build_grounded_healthcare_answer` exactly once.
3. Return the tool result using the required structured output schema.

Do not convert the objects into JSON strings.

The grounding tool owns:

- evidence scoring
- evidence ranking
- diverse evidence selection
- deterministic citations
- provider allow-list validation
- provider recommendation validation
- evidence limitations
- grounded answer generation

Do NOT independently invent:

- providers
- credentials
- services
- citations
- license status
- provider capabilities
- medical claims

Return exactly:

- grounded_answer
- selected_evidence_count
""",
    tools=[build_grounded_healthcare_answer],
    output_schema=EvidenceAnswerAgentOutput,
    output_key="answer_output",
)
