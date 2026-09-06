"""
Google ADK Healthcare Research Agent.

This agent consumes planner state and invokes deterministic MCP-backed
evidence retrieval.

v0.8 model-portability architecture
-----------------------------------

The Search Planner Agent stores structured planner data in Google ADK state.

The Healthcare Research Agent invokes the retrieval tool without asking the
LLM to reconstruct planner objects as function-call arguments.

The retrieval tool then stores the authoritative structured evidence directly
under `research_output` in ADK workflow state and skips post-tool
summarization.

This prevents Gemini or locally hosted Gemma from unnecessarily regenerating
large deterministic retrieval payloads.
"""

from google.adk import Agent

from agents.healthcare_research.tools import retrieve_healthcare_evidence
from llm.model_factory import get_agent_model

healthcare_research_agent = Agent(
    name="healthcare_research_agent",
    model=get_agent_model(),
    mode="single_turn",
    description=(
        "Retrieves healthcare evidence through MCP-backed NPPES, PubMed, "
        "and FHIR services using the structured plan already stored in "
        "Google ADK workflow state."
    ),
    instruction="""
You are the Healthcare Research Agent in a sequential healthcare
evidence workflow.

The Search Planner Agent has already completed its task and stored its
structured output in Google ADK workflow state.

Your responsibility is ONLY evidence retrieval.

You MUST:

1. Call `retrieve_healthcare_evidence` exactly once.
2. Do not provide user_query or search_plan as tool arguments.
3. The tool reads the authoritative planner data directly from ADK state.
4. The tool stores the authoritative research result directly in ADK state
   under `research_output`.
5. Do not reconstruct, repeat, summarize, or rewrite the retrieved evidence.

Do not create a new search plan.
Do not modify the supplied search plan.
Do not invent providers.
Do not invent PubMed studies.
Do not invent FHIR evidence.
Do not rank evidence.
Do not decide which provider is best.
Do not generate the final healthcare answer.

After calling the tool, your work is complete.
""",
    tools=[retrieve_healthcare_evidence],
)
