"""
Structured contracts used between Google ADK agents.

v0.5 keeps ADK state handoffs as structured Python/JSON-compatible
objects rather than JSON strings nested inside JSON.

This avoids unnecessary serialization and escaping across agent
boundaries while preserving the validated v0.1-v0.4 domain models
inside the underlying tools.
"""

from typing import Any

from pydantic import BaseModel, Field


class PlannerAgentOutput(BaseModel):
    """
    Structured output emitted by the Search Planner Agent.
    """

    user_query: dict[str, Any]
    search_plan: dict[str, Any]


class ResearchAgentOutput(BaseModel):
    """
    Structured output emitted by the Healthcare Research Agent.

    Search results remain structured dictionaries across the ADK
    boundary instead of JSON-encoded strings.
    """

    user_query: dict[str, Any]
    search_plan: dict[str, Any]
    search_results: list[dict[str, Any]] = Field(default_factory=list)
    retrieved_sources: int = 0
    deduplicated_sources: int = 0


class EvidenceAnswerAgentOutput(BaseModel):
    """
    Final structured output emitted by the Evidence & Answer Agent.
    """

    grounded_answer: dict[str, Any]
    selected_evidence_count: int
