from evaluation.adapters.production import (
    all_answer_citation_references,
    citations,
    grounded_answer,
    infer_citation_source_type,
    invalid_citation_references,
    normalized_answer_view,
    planner_user_query,
    provider_claims_view,
    provider_safety_flags,
    recommendations,
    research_results,
    search_plan,
    selected_evidence_view,
)
from evaluation.models import BenchmarkExecutionResult


def _run() -> BenchmarkExecutionResult:
    return BenchmarkExecutionResult(
        case_id="provider_houston_pediatric_dentistry",
        query="Find pediatric dentists in Houston.",
        model_provider="gemini",
        model_name="test-model",
        status="success",
        planner_output={
            "user_query": {
                "text": "Find pediatric dentists in Houston.",
                "location": "Houston, TX",
                "specialty": "Pediatric Dentistry",
                "intent": "provider_discovery",
            },
            "search_plan": {
                "generated_queries": [{"query": "pediatric dentists Houston"}]
            },
        },
        research_output={
            "search_results": [
                {
                    "source_type": "provider",
                    "title": "Provider One",
                    "location": "Houston, TX",
                },
                {
                    "source_type": "pubmed",
                    "title": "Dental anxiety study",
                },
            ],
            "retrieved_sources": 2,
            "deduplicated_sources": 2,
        },
        answer_output={
            "grounded_answer": {
                "answer": (
                    "Provider One appears in NPPES [C1]. "
                    "PubMed provides general context [C2]."
                ),
                "recommendations": [
                    {
                        "name": "Provider One",
                        "location": "Houston, TX",
                        "credentials": [],
                        "services": [],
                        "reasons_selected": [
                            "Included because this provider appears in the "
                            "selected NPPES provider evidence [C1]."
                        ],
                        "confidence": 0.8,
                    }
                ],
                "citations": [
                    {
                        "citation_id": "C1",
                        "title": "Provider One",
                        "url": "https://example.test/provider",
                        "source_name": "CMS NPPES / NPI Registry",
                        "claim_supported": "Supports provider identity.",
                    },
                    {
                        "citation_id": "C2",
                        "title": "Dental anxiety study",
                        "url": "https://example.test/pubmed",
                        "source_name": "PubMed",
                        "claim_supported": "Supports general scientific context.",
                    },
                ],
                "transparency": {
                    "generated_queries": 1,
                    "retrieved_sources": 2,
                    "deduplicated_sources": 2,
                    "selected_sources": 2,
                },
                "limitations": [
                    "Provider-specific services should be independently verified."
                ],
            },
            "selected_evidence_count": 2,
        },
    )


def test_reads_production_state_without_rewriting_it() -> None:
    run = _run()
    assert planner_user_query(run)["location"] == "Houston, TX"
    assert search_plan(run)["generated_queries"][0]["query"]
    assert len(research_results(run)) == 2
    assert grounded_answer(run)["answer"]
    assert len(recommendations(run)) == 1
    assert len(citations(run)) == 2


def test_selected_evidence_view_uses_production_citations() -> None:
    selected = selected_evidence_view(_run())
    assert [item["evidence_id"] for item in selected] == ["C1", "C2"]
    assert [item["source_type"] for item in selected] == ["PROVIDER", "PUBMED"]


def test_source_type_mapping_is_conservative() -> None:
    assert infer_citation_source_type(
        {"source_name": "CMS NPPES / NPI Registry"}
    ) == "PROVIDER"
    assert infer_citation_source_type({"source_name": "FHIR"}) == "FHIR"
    assert infer_citation_source_type({"source_name": "Something New"}) == "UNKNOWN"


def test_citation_reference_validation_uses_visible_answer_payload() -> None:
    run = _run()
    assert all_answer_citation_references(run) == {"C1", "C2"}
    assert invalid_citation_references(run) == set()

    run.answer_output["grounded_answer"]["answer"] += " Unsupported [C99]."
    assert invalid_citation_references(run) == {"C99"}


def test_provider_claims_are_structured_recommendation_reasons_only() -> None:
    claims = provider_claims_view(_run())
    assert len(claims) == 1
    assert claims[0]["scope"] == "provider"
    assert claims[0]["evidence_ids"] == ["C1"]


def test_provider_safety_flags_are_clear_for_safe_output() -> None:
    flags = provider_safety_flags(_run())
    assert not any(flags.values())


def test_provider_safety_flags_detect_structured_service_claims() -> None:
    run = _run()
    run.answer_output["grounded_answer"]["recommendations"][0]["services"] = [
        "Sedation dentistry"
    ]
    assert provider_safety_flags(run)["provider_service_without_evidence"]


def test_normalized_answer_preserves_recommendations_with_provider_alias() -> None:
    view = normalized_answer_view(_run())
    assert view["providers"] == view["recommendations"]
    assert view["claim_flags"]["best_provider"] is False


def test_safe_provider_disclaimer_does_not_trigger_forbidden_claim_flags():
    run = _run()
    grounded = run.answer_output["grounded_answer"]
    grounded["answer"] = (
        "These are candidate providers, not a ranking of clinical quality. "
        "Current professional licensure, good standing, clinical quality, "
        "and provider-specific services should be independently verified."
    )

    flags = provider_safety_flags(run)

    assert flags["best_provider"] is False
    assert flags["good_standing_without_authority"] is False
    assert flags["clinical_quality_without_evidence"] is False
    assert flags["active_license_without_authority"] is False

