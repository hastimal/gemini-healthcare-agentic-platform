"""
Tools used by the Google ADK Search Planner Agent.

The tool reuses the existing v0.1 Gemini QueryFanoutPlanner while
returning structured objects suitable for ADK state handoff.
"""

from models import SearchIntent, UserQuery
from search.query_fanout import QueryFanoutPlanner


def create_healthcare_search_plan(
    question: str,
    location: str = "Houston, TX",
    specialty: str = "Pediatric Dentistry",
) -> dict:
    """
    Create a structured healthcare search plan.

    Args:
        question: The user's healthcare discovery question.
        location: Geographic location for provider discovery.
        specialty: Requested healthcare specialty.

    Returns:
        Structured UserQuery and SearchPlan dictionaries.
    """

    user_query = UserQuery(
        text=question,
        location=location,
        specialty=specialty,
        intent=SearchIntent.PROVIDER_DISCOVERY,
    )

    planner = QueryFanoutPlanner()
    plan = planner.create_plan(user_query)

    return {
        "user_query": user_query.model_dump(mode="json"),
        "search_plan": plan.model_dump(mode="json"),
    }
