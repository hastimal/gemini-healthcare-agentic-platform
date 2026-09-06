from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "ui" / "streamlit_app.py"

LIVE_ENABLED = os.getenv("RUN_LIVE_UI_E2E") == "1"
MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "gemini").strip().lower()
UI_TIMEOUT = int(os.getenv("UI_E2E_TIMEOUT", "300" if MODEL_PROVIDER == "gemini" else "900"))


pytestmark = pytest.mark.skipif(
    not LIVE_ENABLED,
    reason="Set RUN_LIVE_UI_E2E=1 or use ./scripts/test-ui.sh <gemini|gemma>.",
)


def _decode_json_value(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def _walk(value: Any):
    value = _decode_json_value(value)
    yield value

    if isinstance(value, dict):
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _json_payloads(app: AppTest) -> list[Any]:
    payloads: list[Any] = []
    for element in app.json:
        payloads.append(_decode_json_value(element.value))
    return payloads


def _find_dict(app: AppTest, predicate) -> dict[str, Any]:
    for payload in _json_payloads(app):
        for value in _walk(payload):
            if isinstance(value, dict) and predicate(value):
                return value

    raise AssertionError(
        "Expected structured JSON was not exposed by the Streamlit UI. "
        "The UI should continue to render planner/research/answer raw JSON "
        "for transparent end-to-end acceptance testing."
    )


def _planner_output(app: AppTest) -> dict[str, Any]:
    return _find_dict(
        app,
        lambda value: (
            isinstance(value.get("user_query"), dict)
            and isinstance(value.get("search_plan"), dict)
        ),
    )


def _research_output(app: AppTest) -> dict[str, Any]:
    return _find_dict(
        app,
        lambda value: (
            isinstance(value.get("search_results"), list)
            and "retrieved_sources" in value
            and "deduplicated_sources" in value
        ),
    )


def _answer_output(app: AppTest) -> dict[str, Any]:
    output = _find_dict(
        app,
        lambda value: (
            isinstance(value.get("grounded_answer"), dict)
            and "selected_evidence_count" in value
        ),
    )

    grounded = output["grounded_answer"]

    assert isinstance(grounded.get("answer"), str)
    assert isinstance(grounded.get("citations"), list)
    assert isinstance(grounded.get("transparency"), dict)
    assert isinstance(grounded.get("limitations"), list)

    return grounded


def _source_types(research: dict[str, Any]) -> set[str]:
    return {
        str(result.get("source_type"))
        for result in research.get("search_results", [])
        if isinstance(result, dict) and result.get("source_type")
    }


def _run_ui_query(question: str) -> tuple[AppTest, dict, dict, dict]:
    app = AppTest.from_file(APP, default_timeout=UI_TIMEOUT)

    app.run(timeout=30)
    assert not app.exception, f"UI failed during initial render: {list(app.exception)}"

    assert len(app.text_area) >= 1, (
        "Expected ui/streamlit_app.py to expose the healthcare question "
        "through st.text_area."
    )
    assert len(app.button) >= 1, (
        "Expected ui/streamlit_app.py to expose a run/search button."
    )

    app.text_area[0].set_value(question)

    preferred_tokens = ("run", "search", "research", "ask")
    submit = next(
        (
            button
            for button in app.button
            if any(token in button.label.lower() for token in preferred_tokens)
        ),
        app.button[0],
    )

    submit.click()
    app.run(timeout=UI_TIMEOUT)

    assert not app.exception, (
        f"UI raised an exception for query: {question}\n"
        f"{list(app.exception)}"
    )

    planner = _planner_output(app)
    research = _research_output(app)
    answer = _answer_output(app)

    assert answer["answer"].strip()
    assert answer["transparency"]
    assert isinstance(answer["citations"], list)
    assert isinstance(answer["limitations"], list)

    return app, planner, research, answer


@pytest.mark.parametrize(
    ("question", "expected_location", "expected_specialty"),
    [
        ("Find cardiologists in Dallas, TX", "Dallas", "Cardiology"),
        ("Find neurologists in Austin, TX", "Austin", "Neurology"),
    ],
)
def test_ui_generalizes_provider_location_and_specialty(
    question: str,
    expected_location: str,
    expected_specialty: str,
):
    _, planner, research, answer = _run_ui_query(question)

    user_query = planner["user_query"]

    assert user_query["intent"] == "provider_discovery"
    assert expected_location.lower() in (user_query.get("location") or "").lower()
    assert expected_specialty.lower() in (user_query.get("specialty") or "").lower()

    # Regression guard: the previous flagship assumptions must not leak.
    assert "houston" not in (user_query.get("location") or "").lower()
    assert "pediatric dentistry" not in (user_query.get("specialty") or "").lower()

    source_types = _source_types(research)
    assert "provider" in source_types

    assert answer["transparency"]["retrieved_sources"] >= 1


def test_ui_biomedical_research_does_not_force_provider_discovery():
    question = "What does research say about childhood dental anxiety?"
    _, planner, research, answer = _run_ui_query(question)

    user_query = planner["user_query"]

    assert user_query["intent"] in {
        "biomedical_research",
        "health_information",
    }
    assert not user_query.get("location")
    # assert not user_query.get("specialty")

    source_types = _source_types(research)
    assert "pubmed" in source_types
    assert "provider" not in source_types

    assert answer["transparency"]["retrieved_sources"] >= 1


def test_ui_explicit_fhir_query_uses_fhir_without_houston_assumption():
    question = (
        "Explain FHIR PractitionerRole and how it represents "
        "provider relationships."
    )
    _, planner, research, answer = _run_ui_query(question)

    user_query = planner["user_query"]

    assert user_query["intent"] != "provider_discovery"
    assert "houston" not in (user_query.get("location") or "").lower()

    source_types = _source_types(research)
    assert "fhir" in source_types
    assert "provider" not in source_types

    assert answer["transparency"]["retrieved_sources"] >= 1


def test_ui_flagship_query_remains_a_regression_case_not_configuration():
    question = (
        "Find three pediatric dentists in Houston for a child who is scared "
        "of going to the dentist. Compare them using trustworthy sources, "
        "provider credentials, services, and location, and explain why you "
        "selected each one."
    )
    _, planner, research, answer = _run_ui_query(question)

    user_query = planner["user_query"]

    assert user_query["intent"] == "provider_discovery"
    assert "houston" in (user_query.get("location") or "").lower()
    assert "pediatric" in (user_query.get("specialty") or "").lower()
    assert "dent" in (user_query.get("specialty") or "").lower()

    source_types = _source_types(research)
    assert "provider" in source_types

    # Preserve v0.8 safety expectations for provider recommendations.
    for recommendation in answer.get("recommendations", []):
        assert isinstance(recommendation.get("credentials", []), list)
        assert isinstance(recommendation.get("services", []), list)
