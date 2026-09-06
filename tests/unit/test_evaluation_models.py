import json
from pathlib import Path

import pytest

from evaluation.models import EvaluationCase, EvaluationIntent


DATASET = Path("evaluation/datasets/healthcare_benchmark.jsonl")


def load_cases() -> list[EvaluationCase]:
    return [
        EvaluationCase.model_validate(json.loads(line))
        for line in DATASET.read_text().splitlines()
        if line.strip()
    ]


def test_benchmark_dataset_loads() -> None:
    cases = load_cases()
    assert len(cases) == 11
    assert len({case.case_id for case in cases}) == len(cases)


def test_provider_cases_require_location_and_specialty() -> None:
    with pytest.raises(ValueError):
        EvaluationCase.model_validate(
            {
                "case_id": "bad_provider_case",
                "title": "Bad provider case",
                "query": "Find a provider",
                "intent": "PROVIDER_DISCOVERY",
                "expectations": [
                    {
                        "name": "candidate_count",
                        "expectation_type": "required",
                        "description": "Return candidates",
                    }
                ],
            }
        )


def test_dataset_contains_supported_and_unsupported_cases() -> None:
    intents = {case.intent for case in load_cases()}
    assert EvaluationIntent.PROVIDER_DISCOVERY in intents
    assert EvaluationIntent.BIOMEDICAL_RESEARCH in intents
    assert EvaluationIntent.HEALTH_INFORMATION in intents
    assert EvaluationIntent.FHIR_INTEROPERABILITY in intents
    assert EvaluationIntent.CARE_PROGRAM_DISCOVERY in intents
    assert EvaluationIntent.CLINICAL_TRIALS in intents


def test_flagship_is_only_one_case() -> None:
    flagship = [case for case in load_cases() if "flagship" in case.tags]
    assert len(flagship) == 1
    assert flagship[0].case_id == "provider_houston_pediatric_dentistry"


def test_unsupported_cases_are_explicit() -> None:
    unsupported = [case for case in load_cases() if "unsupported" in case.tags]
    assert len(unsupported) == 2
    for case in unsupported:
        assert any(
            expectation.name == "explicitly_unsupported"
            for expectation in case.expectations
        )
