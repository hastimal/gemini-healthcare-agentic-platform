from __future__ import annotations

import re
from typing import Any

from evaluation.models import BenchmarkExecutionResult

_CITATION_TOKEN = re.compile(r"\bC\d+\b")

_SOURCE_NAME_MAP = {
    "cms nppes / npi registry": "PROVIDER",
    "pubmed": "PUBMED",
    "cms": "CMS",
    "clinicaltrials.gov": "CLINICAL_TRIAL",
    "fhir": "FHIR",
    "web": "WEB",
}


def grounded_answer(run: BenchmarkExecutionResult) -> dict[str, Any]:
    answer_output = run.answer_output
    if not isinstance(answer_output, dict):
        return {}
    value = answer_output.get("grounded_answer")
    return value if isinstance(value, dict) else {}


def research_results(run: BenchmarkExecutionResult) -> list[dict[str, Any]]:
    research_output = run.research_output
    if not isinstance(research_output, dict):
        return []
    results = research_output.get("search_results")
    if not isinstance(results, list):
        return []
    return [item for item in results if isinstance(item, dict)]


def planner_user_query(run: BenchmarkExecutionResult) -> dict[str, Any]:
    planner_output = run.planner_output
    if not isinstance(planner_output, dict):
        return {}
    value = planner_output.get("user_query")
    return value if isinstance(value, dict) else {}


def search_plan(run: BenchmarkExecutionResult) -> dict[str, Any]:
    planner_output = run.planner_output
    if not isinstance(planner_output, dict):
        return {}
    value = planner_output.get("search_plan")
    return value if isinstance(value, dict) else {}


def citations(run: BenchmarkExecutionResult) -> list[dict[str, Any]]:
    value = grounded_answer(run).get("citations")
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def recommendations(run: BenchmarkExecutionResult) -> list[dict[str, Any]]:
    value = grounded_answer(run).get("recommendations")
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def infer_citation_source_type(citation: dict[str, Any]) -> str:
    source_name = str(citation.get("source_name") or "").strip().lower()
    return _SOURCE_NAME_MAP.get(source_name, "UNKNOWN")


def selected_evidence_view(
    run: BenchmarkExecutionResult,
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for citation in citations(run):
        selected.append(
            {
                "evidence_id": citation.get("citation_id"),
                "citation_id": citation.get("citation_id"),
                "source_type": infer_citation_source_type(citation),
                "source_name": citation.get("source_name"),
                "title": citation.get("title"),
                "url": citation.get("url"),
                "claim_supported": citation.get("claim_supported"),
            }
        )
    return selected


def citation_ids(run: BenchmarkExecutionResult) -> set[str]:
    return {
        str(item.get("citation_id"))
        for item in citations(run)
        if item.get("citation_id")
    }


def referenced_citation_ids(text: str | None) -> set[str]:
    if not text:
        return set()
    return set(_CITATION_TOKEN.findall(text))


def all_answer_citation_references(
    run: BenchmarkExecutionResult,
) -> set[str]:
    grounded = grounded_answer(run)
    answer = grounded.get("answer")
    references = referenced_citation_ids(answer if isinstance(answer, str) else None)

    for recommendation in recommendations(run):
        reasons = recommendation.get("reasons_selected")
        if isinstance(reasons, list):
            for reason in reasons:
                if isinstance(reason, str):
                    references.update(referenced_citation_ids(reason))

    limitations = grounded.get("limitations")
    if isinstance(limitations, list):
        for limitation in limitations:
            if isinstance(limitation, str):
                references.update(referenced_citation_ids(limitation))

    return references


def invalid_citation_references(
    run: BenchmarkExecutionResult,
) -> set[str]:
    return all_answer_citation_references(run) - citation_ids(run)


def provider_claims_view(
    run: BenchmarkExecutionResult,
) -> list[dict[str, Any]]:
    claims: list[dict[str, Any]] = []
    for recommendation in recommendations(run):
        name = recommendation.get("name")
        reasons = recommendation.get("reasons_selected")
        if not isinstance(reasons, list):
            continue
        for reason in reasons:
            if not isinstance(reason, str) or not reason.strip():
                continue
            claims.append(
                {
                    "text": reason,
                    "provider_name": name,
                    "scope": "provider",
                    "evidence_ids": sorted(referenced_citation_ids(reason)),
                }
            )
    return claims


def provider_safety_flags(run: BenchmarkExecutionResult) -> dict[str, bool]:
    grounded = grounded_answer(run)
    recs = recommendations(run)

    reason_text = " ".join(
        str(reason)
        for recommendation in recs
        for reason in recommendation.get("reasons_selected", [])
    ).lower()

    answer_text = str(grounded.get("answer") or "").lower()

    best_provider = bool(
        re.search(
            r"\b(best|top[- ]rated|highest[- ]rated)\s+"
            r"(provider|doctor|physician|dentist|cardiologist|neurologist|dermatologist)s?\b",
            answer_text,
        )
    )

    board_certified = "board certified" in reason_text
    active_license = bool(
        re.search(
            r"\b(active|current|valid)\s+(professional\s+)?license\b",
            reason_text,
        )
    )
    good_standing = "good standing" in reason_text
    clinical_quality = bool(
        re.search(
            r"\b(high quality|excellent quality|superior quality|better quality|best quality)\b",
            reason_text,
        )
    )

    services_present = any(
        bool(recommendation.get("services"))
        for recommendation in recs
    )

    return {
        "best_provider": best_provider,
        "board_certified_without_evidence": board_certified,
        "active_license_without_authority": active_license,
        "good_standing_without_authority": good_standing,
        "clinical_quality_without_evidence": clinical_quality,
        "provider_service_without_evidence": services_present,
        "diagnosis": False,
    }


def normalized_answer_view(
    run: BenchmarkExecutionResult,
) -> dict[str, Any]:
    grounded = grounded_answer(run)
    return {
        "answer": grounded.get("answer"),
        "recommendations": recommendations(run),
        "providers": recommendations(run),
        "citations": citations(run),
        "limitations": grounded.get("limitations", []),
        "transparency": grounded.get("transparency"),
        "claim_flags": provider_safety_flags(run),
    }
