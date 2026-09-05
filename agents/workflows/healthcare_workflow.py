"""
v0.5 Google ADK healthcare multi-agent workflow.

Execution:

User
  -> Search Planner Agent
  -> Healthcare Research Agent
  -> Evidence & Answer Agent

Google ADK 2.8.0 uses SequentialAgent for this workflow in the
currently installed environment.
"""

from google.adk.agents import SequentialAgent

from agents.evidence_answer.agent import evidence_answer_agent
from agents.healthcare_research.agent import healthcare_research_agent
from agents.search_planner.agent import search_planner_agent

root_agent = SequentialAgent(
    name="gemini_healthcare_agentic_workflow",
    description=(
        "A three-agent healthcare evidence workflow that plans searches, "
        "retrieves provider and biomedical evidence, and produces a "
        "validated grounded answer."
    ),
    sub_agents=[
        search_planner_agent,
        healthcare_research_agent,
        evidence_answer_agent,
    ],
)
