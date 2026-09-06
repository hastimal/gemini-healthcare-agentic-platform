import inspect

import pytest

from agents.search_planner.tools import create_healthcare_search_plan
from models import SearchIntent, UserQuery
from search.query_fanout import QueryFanoutPlanner


def test_provider_plan_is_not_hardcoded_to_houston_or_dentistry():
    result = create_healthcare_search_plan(
        question="Find cardiologists in Dallas",
        intent="provider_discovery",
        location="Dallas, TX",
        specialty="Cardiology",
        generated_queries=[
            "cardiologists Dallas TX",
            "cardiology providers Dallas TX",
            "cardiology provider registry Dallas TX",
        ],
    )

    assert result["user_query"]["intent"] == "provider_discovery"
    assert result["user_query"]["location"] == "Dallas, TX"
    assert result["user_query"]["specialty"] == "Cardiology"
    assert result["search_plan"]["intent"] == "provider_discovery"
    assert len(result["search_plan"]["generated_queries"]) == 3


def test_arbitrary_provider_specialty_and_location_are_preserved():
    result = create_healthcare_search_plan(
        question="Find neuro-ophthalmologists in Chicago",
        intent="provider_discovery",
        location="Chicago, IL",
        specialty="Neuro-Ophthalmology",
        generated_queries=["neuro-ophthalmologists Chicago IL"],
    )

    assert result["user_query"]["location"] == "Chicago, IL"
    assert result["user_query"]["specialty"] == "Neuro-Ophthalmology"
    assert "Houston" not in str(result)
    assert "Pediatric Dentistry" not in str(result)


def test_biomedical_research_does_not_require_location_or_specialty():
    result = create_healthcare_search_plan(
        question="What does research say about childhood dental anxiety?",
        intent="biomedical_research",
        location=None,
        specialty=None,
        generated_queries=[
            "childhood dental anxiety systematic review",
            "pediatric dental anxiety behavior guidance",
        ],
    )

    assert result["user_query"]["intent"] == "biomedical_research"
    assert result["user_query"]["location"] is None
    assert result["user_query"]["specialty"] is None
    assert result["search_plan"]["intent"] == "biomedical_research"


def test_health_information_can_plan_fhir_without_provider_assumptions():
    result = create_healthcare_search_plan(
        question="Explain FHIR PractitionerRole",
        intent="health_information",
        generated_queries=[
            "FHIR PractitionerRole healthcare interoperability",
            "FHIR PractitionerRole organization location specialty",
        ],
    )

    assert result["user_query"]["intent"] == "health_information"
    assert result["user_query"]["location"] is None
    assert result["user_query"]["specialty"] is None
    assert "Houston" not in str(result)


def test_invalid_intent_is_rejected():
    with pytest.raises(ValueError):
        create_healthcare_search_plan(
            question="Find something in healthcare",
            intent="unsupported_intent",
            generated_queries=["healthcare query"],
        )


def test_query_fanout_planner_requires_intent():
    planner = QueryFanoutPlanner()
    user_query = UserQuery(text="Explain hypertension")

    with pytest.raises(ValueError, match="intent is required"):
        planner.create_plan(user_query, ["hypertension overview"])


def test_query_fanout_deduplicates_and_caps_queries():
    planner = QueryFanoutPlanner()
    user_query = UserQuery(
        text="Find neurologists in Austin",
        location="Austin, TX",
        specialty="Neurology",
        intent=SearchIntent.PROVIDER_DISCOVERY,
    )

    queries = ["neurologists Austin TX", "Neurologists Austin TX"] + [
        f"neurology query {index}" for index in range(20)
    ]
    plan = planner.create_plan(user_query, queries)

    assert len(plan.generated_queries) == planner.MAX_GENERATED_QUERIES
    assert plan.generated_queries[0].query == "neurologists Austin TX"


def test_query_fanout_has_no_direct_gemini_dependency():
    source = inspect.getsource(QueryFanoutPlanner)

    assert "GeminiClient" not in source
    assert "generate_content" not in source


def test_fallback_plan_remains_available_for_legacy_callers():
    planner = QueryFanoutPlanner()
    user_query = UserQuery(
        text="Find oncologists in Seattle",
        location="Seattle, WA",
        specialty="Oncology",
        intent=SearchIntent.PROVIDER_DISCOVERY,
    )

    plan = planner.create_plan(user_query)

    assert len(plan.generated_queries) == 1
    assert plan.generated_queries[0].query == "Oncology Seattle, WA"
