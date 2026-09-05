from __future__ import annotations

import json
import re
from pathlib import Path

from google.genai import types
from pydantic import BaseModel, Field

from grounding.citations import CitationBuilder
from grounding.ranking import EvidenceRanker
from llm.gemini.client import GeminiClient
from models.answers import (
    GroundedAnswer,
    ProviderRecommendation,
    SearchTransparency,
)
from models.evidence import Evidence
from models.query import SearchPlan, UserQuery
from models.search import SourceType

PROMPT_PATH = Path(__file__).resolve().parent.parent / "agents" / "prompts" / "grounded_answer.md"


class DraftProviderRecommendation(BaseModel):
    """
    Gemini may choose and explain a provider only from the selected
    provider evidence.

    Credentials, services, location, and confidence are finalized
    deterministically later.
    """

    name: str
    reasons_selected: list[str] = Field(default_factory=list)


class DraftGroundedAnswer(BaseModel):
    """
    Internal Gemini response schema.

    Citations are deliberately excluded because citations are built
    deterministically from retrieved evidence.
    """

    answer: str

    recommendations: list[DraftProviderRecommendation] = Field(default_factory=list)

    limitations: list[str] = Field(default_factory=list)


class GroundedAnswerGenerator:
    """
    Generate an evidence-grounded healthcare answer.

    Safety architecture:

        Selected Evidence
            -> deterministic citations
            -> restricted Gemini context
            -> structured draft
            -> provider validation
            -> citation validation
            -> deterministic final model

    Gemini cannot introduce new providers or citation URLs.
    """

    def __init__(
        self,
        gemini: GeminiClient | None = None,
        ranker: EvidenceRanker | None = None,
        citation_builder: CitationBuilder | None = None,
    ) -> None:
        self.gemini = gemini or GeminiClient()
        self.ranker = ranker or EvidenceRanker()
        self.citation_builder = citation_builder or CitationBuilder()

        self.system_prompt = PROMPT_PATH.read_text(encoding="utf-8")

    def generate(
        self,
        user_query: UserQuery,
        plan: SearchPlan,
        ranked_evidence: list[Evidence],
        retrieved_sources: int,
        deduplicated_sources: int,
    ) -> GroundedAnswer:
        """
        Generate the final grounded answer.

        Only selected evidence is passed to Gemini.
        """

        selected_evidence = [evidence for evidence in ranked_evidence if evidence.selected]

        if not selected_evidence:
            raise ValueError(
                "Grounded answer generation requires at least one selected evidence item."
            )

        citations = self.citation_builder.build(ranked_evidence)

        evidence_context = self._build_evidence_context(
            selected_evidence=selected_evidence,
            citations=citations,
        )

        prompt = f"""
{self.system_prompt}

ORIGINAL USER REQUEST:
{user_query.model_dump_json(indent=2)}

SEARCH PLAN:
{plan.model_dump_json(indent=2)}

SELECTED EVIDENCE:
{json.dumps(evidence_context, indent=2)}

Create the grounded answer now.

Important:
- Use only the supplied selected evidence.
- Use citation IDs such as [C1] directly in answer text and reasons.
- Never invent providers.
- Never invent citations.
- Return only the requested structured response.
"""

        response = self.gemini.client.models.generate_content(
            model=self.gemini.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type=("application/json"),
                response_schema=(DraftGroundedAnswer),
                temperature=0.1,
            ),
        )

        if not response.text:
            raise RuntimeError("Gemini returned an empty grounded-answer response.")

        draft = DraftGroundedAnswer.model_validate_json(response.text)

        self._validate_citation_references(
            draft=draft,
            citations=citations,
        )

        recommendations = self._finalize_recommendations(
            draft=draft,
            selected_evidence=(selected_evidence),
        )

        transparency = SearchTransparency(
            generated_queries=len(plan.generated_queries),
            retrieved_sources=(retrieved_sources),
            deduplicated_sources=(deduplicated_sources),
            selected_sources=len(selected_evidence),
        )

        # Finalize limitations semantically so Gemini-generated
        # evidence-gap warnings are not duplicated by our standard
        # safety limitations.
        limitations = self._finalize_limitations(draft.limitations)

        return GroundedAnswer(
            answer=draft.answer,
            recommendations=recommendations,
            citations=citations,
            transparency=transparency,
            limitations=limitations,
        )

    def _build_evidence_context(
        self,
        selected_evidence: list[Evidence],
        citations: list,
    ) -> list[dict]:
        """
        Convert selected evidence into the only evidence Gemini sees.

        Evidence and citations use matching list order, so C1 maps to
        the first selected evidence item, C2 to the second, etc.
        """

        context: list[dict] = []

        for evidence, citation in zip(
            selected_evidence,
            citations,
            strict=True,
        ):
            result = evidence.result

            context.append(
                {
                    "citation_id": (citation.citation_id),
                    "source_type": (result.source_type.value),
                    "title": result.title,
                    "url": (str(result.url) if result.url else None),
                    "provider_name": (result.provider_name),
                    "location": result.location,
                    "summary": evidence.summary,
                    "metadata": (result.metadata),
                    "evidence_score": (self.ranker.total_score(evidence)),
                    "claim_scope": (citation.claim_supported),
                }
            )

        return context

    def _finalize_recommendations(
        self,
        draft: DraftGroundedAnswer,
        selected_evidence: list[Evidence],
    ) -> list[ProviderRecommendation]:
        """
        Convert Gemini's draft provider selections into deterministic
        ProviderRecommendation objects.

        Gemini may NOT introduce providers outside selected evidence.

        Provider location, identifiers, and confidence come from the
        retrieved evidence rather than Gemini.
        """

        provider_evidence = [
            evidence
            for evidence in selected_evidence
            if evidence.result.source_type == SourceType.PROVIDER
        ]

        allowed = {
            self._normalize_name(evidence.result.provider_name or evidence.result.title): evidence
            for evidence in provider_evidence
        }

        recommendations: list[ProviderRecommendation] = []

        seen_names: set[str] = set()

        for draft_recommendation in draft.recommendations:
            normalized_name = self._normalize_name(draft_recommendation.name)

            evidence = allowed.get(normalized_name)

            if evidence is None:
                raise ValueError(
                    "Gemini attempted to recommend "
                    "a provider that was not present "
                    "in selected evidence: "
                    f"{draft_recommendation.name}"
                )

            if normalized_name in seen_names:
                continue

            seen_names.add(normalized_name)

            result = evidence.result

            # NPI is an identifier, not a professional credential.
            # Therefore we do not place it in `credentials`.
            #
            # We also leave services empty because NPPES does not
            # establish provider-specific anxiety/sedation services.
            recommendations.append(
                ProviderRecommendation(
                    name=(result.provider_name or result.title),
                    location=result.location,
                    credentials=[],
                    services=[],
                    reasons_selected=(draft_recommendation.reasons_selected),
                    confidence=(self.ranker.total_score(evidence)),
                )
            )

        # If Gemini returned fewer provider recommendations than the
        # selected provider evidence, safely backfill using only
        # deterministic provider evidence.
        for evidence in provider_evidence:
            if len(recommendations) >= 3:
                break

            result = evidence.result

            name = result.provider_name or result.title

            normalized_name = self._normalize_name(name)

            if normalized_name in seen_names:
                continue

            citation_id = self._citation_id_for_evidence(
                target=evidence,
                selected_evidence=(selected_evidence),
            )

            recommendations.append(
                ProviderRecommendation(
                    name=name,
                    location=result.location,
                    credentials=[],
                    services=[],
                    reasons_selected=[
                        (
                            "Included because the provider "
                            "appears in the selected NPPES "
                            "provider evidence for the requested "
                            "specialty and location "
                            f"[{citation_id}]."
                        )
                    ],
                    confidence=(self.ranker.total_score(evidence)),
                )
            )

            seen_names.add(normalized_name)

        return recommendations[:3]

    @staticmethod
    def _citation_id_for_evidence(
        target: Evidence,
        selected_evidence: list[Evidence],
    ) -> str:
        """
        Resolve the deterministic citation ID for selected evidence.
        """

        for index, evidence in enumerate(
            selected_evidence,
            start=1,
        ):
            if evidence is target:
                return f"C{index}"

        raise ValueError("Evidence was not found in selected evidence.")

    @staticmethod
    def _validate_citation_references(
        draft: DraftGroundedAnswer,
        citations: list,
    ) -> None:
        """
        Validate every citation reference emitted by Gemini.

        Supported forms:

            [C1]
            [C1, C2]
            [C1, C2, C3]

        We first find bracketed citation groups and then extract every
        C<number> token from each group.

        This ensures that an invalid reference such as [C1, C99]
        cannot hide behind a valid citation.
        """

        valid_ids = {citation.citation_id for citation in citations}

        text_parts = [
            draft.answer,
            *draft.limitations,
        ]

        for recommendation in draft.recommendations:
            text_parts.extend(recommendation.reasons_selected)

        combined_text = "\n".join(text_parts)

        # Find every bracketed section.
        bracket_groups = re.findall(
            r"\[([^\]]+)\]",
            combined_text,
        )

        referenced: set[str] = set()

        for group in bracket_groups:
            # Extract every citation token inside the brackets.
            referenced.update(
                re.findall(
                    r"\bC\d+\b",
                    group,
                )
            )

        invalid = referenced - valid_ids

        if invalid:
            raise ValueError(f"Gemini referenced invalid citation IDs: {sorted(invalid)}")

    @staticmethod
    def _finalize_limitations(
        draft_limitations: list[str],
    ) -> list[str]:
        """
        Return concise, non-duplicative limitations.

        Gemini normally produces evidence-specific limitations.

        We preserve those limitations and add a standard safety
        limitation only when the corresponding evidence-gap category
        is completely absent.

        This is semantic category deduplication rather than exact-string
        deduplication.
        """

        # First remove exact duplicates while preserving order.
        limitations = list(
            dict.fromkeys(
                limitation.strip() for limitation in draft_limitations if limitation.strip()
            )
        )

        combined = " ".join(limitations).lower()

        # ---------------------------------------------------------
        # CATEGORY 1 — Provider registry / verification limitations
        # ---------------------------------------------------------
        #
        # If Gemini already discusses NPPES/provider registry limits,
        # clinical quality, board certification, or licensure, we do
        # not add another generic NPPES warning.
        provider_registry_present = any(
            phrase in combined
            for phrase in [
                "nppes",
                "provider registry",
                "clinical quality",
                "board certification",
                "professional licensure",
                "license status",
                "licensure status",
            ]
        )

        if not provider_registry_present:
            limitations.append(
                "NPPES provider data should not be interpreted "
                "as an independent verification of clinical "
                "quality or professional licensure."
            )

        # ---------------------------------------------------------
        # CATEGORY 2 — Provider-specific service verification
        # ---------------------------------------------------------
        #
        # Sedation/anxiety-management/sensory-service uncertainty is
        # one evidence-gap category. Do not repeat it when Gemini has
        # already described that gap.
        provider_services_present = any(
            phrase in combined
            for phrase in [
                "sedation",
                "anxiety-management",
                "anxiety management",
                "behavior-management",
                "behavior management",
                "sensory",
                "provider-specific",
                "specific services",
            ]
        )

        if not provider_services_present:
            limitations.append(
                "Provider-specific anxiety-management and "
                "sedation services have not yet been independently "
                "verified from provider-specific sources."
            )

        # ---------------------------------------------------------
        # CATEGORY 3 — General scientific evidence vs provider claims
        # ---------------------------------------------------------
        #
        # PubMed/general literature can describe interventions without
        # proving that a particular provider implements them.
        scientific_context_present = any(
            phrase in combined
            for phrase in [
                "pubmed",
                "scientific literature",
                "biomedical literature",
                "general scientific",
                "general clinical",
                "general interventions",
                "specific provider",
                "specific providers",
            ]
        )

        if not scientific_context_present:
            limitations.append(
                "PubMed evidence provides general scientific "
                "context and does not establish that a particular "
                "provider offers the discussed approaches."
            )

        return limitations

    @staticmethod
    def _normalize_name(
        name: str,
    ) -> str:
        """
        Normalize provider names for safe comparison.
        """

        return " ".join(name.lower().split())
