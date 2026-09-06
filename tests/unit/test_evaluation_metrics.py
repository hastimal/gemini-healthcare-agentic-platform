from evaluation.metrics.citations import evaluate_citation_presence, evaluate_citation_targets
from evaluation.metrics.completeness import evaluate_candidate_count, evaluate_required_sections
from evaluation.metrics.grounding import evaluate_claim_support, evaluate_provider_claim_source_boundary
from evaluation.metrics.retrieval import evaluate_retrieval_presence, evaluate_source_type_presence
from evaluation.metrics.safety import evaluate_explicit_unsupported_status, evaluate_forbidden_claim_flags
from evaluation.metrics.source_authority import (
    evaluate_fhir_not_used_as_provider_recommendation,
    evaluate_provider_evidence_authority,
)


def test_retrieval_presence_passes_and_fails() -> None:
    assert evaluate_retrieval_presence([{"id": "1"}]).passed is True
    assert evaluate_retrieval_presence([], minimum_results=1).passed is False


def test_required_source_types() -> None:
    results = [{"source_type": "NPPES"}, {"source_type": "PUBMED"}]
    assert evaluate_source_type_presence(results, required_source_types={"NPPES", "PUBMED"}).passed is True


def test_citation_targets_selected_evidence() -> None:
    citations = [{"evidence_id": "E1"}, {"evidence_id": "E2"}]
    assert evaluate_citation_presence(citations, minimum_citations=2).passed is True
    assert evaluate_citation_targets(citations, {"E1", "E2"}).passed is True
    assert evaluate_citation_targets(citations, {"E1"}).passed is False


def test_claim_support_detects_unsupported_claim() -> None:
    claims = [
        {"claim_id": "C1", "evidence_ids": ["E1"]},
        {"claim_id": "C2", "evidence_ids": []},
    ]
    result = evaluate_claim_support(claims)
    assert result.passed is False
    assert result.score == 0.5


def test_provider_claim_cannot_rely_only_on_pubmed() -> None:
    claims = [{"claim_id": "C1", "scope": "provider", "evidence_ids": ["E1"]}]
    evidence = {"E1": {"source_type": "PUBMED"}}
    assert evaluate_provider_claim_source_boundary(claims, evidence).passed is False

    evidence["E2"] = {"source_type": "NPPES"}
    claims[0]["evidence_ids"] = ["E1", "E2"]
    assert evaluate_provider_claim_source_boundary(claims, evidence).passed is True


def test_provider_evidence_authority() -> None:
    selected = [
        {"evidence_id": "E1", "source_type": "NPPES", "scope": "provider"},
        {"evidence_id": "E2", "source_type": "PROVIDER", "scope": "provider"},
    ]
    assert evaluate_provider_evidence_authority(selected).passed is True


def test_fhir_boundary() -> None:
    selected = [{"evidence_id": "F1", "source_type": "FHIR", "scope": "interoperability"}]
    assert evaluate_fhir_not_used_as_provider_recommendation(selected).passed is True

    selected[0]["scope"] = "provider_recommendation"
    assert evaluate_fhir_not_used_as_provider_recommendation(selected).passed is False


def test_required_answer_sections() -> None:
    answer = {"answer": "text", "citations": [{"evidence_id": "E1"}]}
    assert evaluate_required_sections(answer, required_sections={"answer", "citations"}).passed is True
    assert evaluate_required_sections(answer, required_sections={"answer", "citations", "limitations"}).passed is False


def test_candidate_count() -> None:
    answer = {"candidates": [{}, {}, {}]}
    assert evaluate_candidate_count(answer, expected_count=3).passed is True
    assert evaluate_candidate_count(answer, expected_count=2).passed is False


def test_forbidden_claim_flags() -> None:
    safe = {"claim_flags": {"best_provider": False, "diagnosis": False}}
    unsafe = {"claim_flags": {"best_provider": True}}
    assert evaluate_forbidden_claim_flags(safe).passed is True
    assert evaluate_forbidden_claim_flags(unsafe).passed is False


def test_explicit_unsupported_status() -> None:
    assert evaluate_explicit_unsupported_status({"status": "unsupported"}).passed is True
    assert evaluate_explicit_unsupported_status({"error_type": "NotImplementedError"}).passed is True
    assert evaluate_explicit_unsupported_status({"status": "success"}).passed is False
