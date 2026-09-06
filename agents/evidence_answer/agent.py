"""
Google ADK Evidence & Answer Agent.

This final specialist agent invokes the tested evidence-ranking,
grounding, citation, and validation pipeline.

v0.8 uses ADK state for the authoritative handoff:

    research_output
        -> Evidence & Answer Agent
        -> build_grounded_healthcare_answer()
        -> answer_output

The grounding tool owns the final structured answer state.
"""

from google.adk import Agent

from agents.evidence_answer.tools import (
    build_grounded_healthcare_answer,
)
from llm.model_factory import get_agent_model

evidence_answer_agent = Agent(
    name="evidence_answer_agent",
    model=get_agent_model(),
    mode="single_turn",
    description=(
        "Invokes the deterministic healthcare evidence-ranking, "
        "grounding, citation, and validation pipeline."
    ),
    instruction="""
You are the Evidence & Answer Agent in a sequential healthcare
evidence workflow.

The Healthcare Research Agent has already completed evidence retrieval.

The authoritative research payload is stored in ADK session state under:

research_output

Your responsibility is ONLY to invoke the existing evidence-ranking,
selection, grounding, citation, and validation pipeline.

You MUST:

1. Call `build_grounded_healthcare_answer` exactly once.
2. Call it with NO arguments.
3. Do not reconstruct research_output.
4. Do not copy search results into the function call.
5. Do not independently rank providers.
6. Do not independently generate the final healthcare answer.
7. Do not invent providers, credentials, services, citations,
   license status, provider capabilities, or medical claims.

The tool reads `research_output` directly from ADK state.

The tool owns:

- evidence scoring
- evidence ranking
- diverse evidence selection
- deterministic citations
- provider allow-list validation
- provider recommendation validation
- evidence limitations
- grounded answer generation
- authoritative `answer_output` state

After the tool completes, your work is complete.

Do not summarize, rewrite, repeat, or regenerate the grounded answer.
""",
    tools=[build_grounded_healthcare_answer],
)
