from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path

from pydantic import BaseModel, Field

from grounding.citations import CitationBuilder
from grounding.ranking import EvidenceRanker
from llm.synthesis.base import SynthesisClient
from llm.synthesis.factory import get_synthesis_client
from models.answers import (
    GroundedAnswer,
    ProviderRecommendation,
    SearchTransparency,
)
from models.evidence import Evidence
from models.query import SearchIntent, SearchPlan, UserQuery
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
            -> restricted model context
            -> structured draft
            -> provider validation
            -> citation validation
            -> deterministic provider recommendations
            -> deterministic final model

    The configured synthesis model cannot introduce new providers or
    citation URLs into final recommendations.
    """

    def __init__(
        self,
        synthesis: SynthesisClient | None = None,
        ranker: EvidenceRanker | None = None,
        citation_builder: CitationBuilder | None = None,
    ) -> None:
        self.synthesis = synthesis or get_synthesis_client()
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
        Synchronous compatibility wrapper.

        New async Google ADK code should call `agenerate()` directly.
        """

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(
                self.agenerate(
                    user_query=user_query,
                    plan=plan,
                    ranked_evidence=ranked_evidence,
                    retrieved_sources=retrieved_sources,
                    deduplicated_sources=deduplicated_sources,
                )
            )

        raise RuntimeError(
            "GroundedAnswerGenerator.generate() cannot run inside an "
            "active event loop. Use `await agenerate(...)` instead."
        )

    async def agenerate(
        self,
        user_query: UserQuery,
        plan: SearchPlan,
        ranked_evidence: list[Evidence],
        retrieved_sources: int,
        deduplicated_sources: int,
    ) -> GroundedAnswer:
        """
        Generate the final grounded answer using the configured model provider.

        Only selected evidence is passed to the synthesis model.
        """

        selected_evidence = [
            evidence
            for evidence in ranked_evidence
            if evidence.selected
        ]

        if not selected_evidence:
            raise ValueError(
                "Grounded answer generation requires at least one "
                "selected evidence item."
            )

        citations = self.citation_builder.build(
            ranked_evidence
        )

        # ---------------------------------------------------------
        # Safety-critical provider discovery
        # ---------------------------------------------------------
        #
        # Provider discovery does not require another LLM completion.
        #
        # The selected evidence already contains the authoritative
        # provider registry records and supporting scientific sources.
        # Constructing this answer deterministically:
        #
        # - prevents unsupported provider claims,
        # - prevents cross-provider citation leakage,
        # - keeps Gemini and Gemma on the same grounding path,
        # - avoids asking a local model to regenerate a large evidence
        #   payload,
        # - preserves the rule: No evidence -> no claim.
        #
        # Other search intents may continue to use the configured
        # synthesis provider.
        if user_query.intent == SearchIntent.PROVIDER_DISCOVERY:
            return self._generate_provider_discovery_answer(
                plan=plan,
                selected_evidence=selected_evidence,
                citations=citations,
                retrieved_sources=retrieved_sources,
                deduplicated_sources=deduplicated_sources,
            )

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
- Use citation IDs such as [C1] directly in answer text.
- Never invent providers.
- Never invent citations.
- PubMed evidence is general scientific evidence and must not be
  converted into provider-specific claims.
- Provider-specific claims may only use facts explicitly present in
  that provider's selected registry evidence.
- Do not infer active licensure, good standing, board certification,
  clinical quality, anxiety expertise, sedation availability, or
  provider-specific services unless the supplied evidence explicitly
  establishes that claim.
- The application will construct final provider recommendation reasons
  deterministically from provider evidence.
- Return only the requested structured response.
"""

        draft = await self.synthesis.generate(
            prompt=prompt,
            schema=DraftGroundedAnswer,
        )

        self._validate_citation_references(
            draft=draft,
            citations=citations,
        )

        recommendations = self._finalize_recommendations(
            draft=draft,
            selected_evidence=selected_evidence,
        )

        transparency = SearchTransparency(
            generated_queries=len(plan.generated_queries),
            retrieved_sources=retrieved_sources,
            deduplicated_sources=deduplicated_sources,
            selected_sources=len(selected_evidence),
        )

        limitations = self._finalize_limitations(
            draft.limitations
        )

        return GroundedAnswer(
            answer=draft.answer,
            recommendations=recommendations,
            citations=citations,
            transparency=transparency,
            limitations=limitations,
        )

    def _generate_provider_discovery_answer(
        self,
        *,
        plan: SearchPlan,
        selected_evidence: list[Evidence],
        citations: list,
        retrieved_sources: int,
        deduplicated_sources: int,
    ) -> GroundedAnswer:
        """
        Construct provider-discovery answers deterministically.

        Provider identity and location come only from selected provider
        registry evidence.

        PubMed evidence is surfaced only as general scientific context.
        It is never converted into a claim about a specific provider.

        FHIR public test-server records are not part of the selected
        provider-discovery grounding context.
        """

        provider_evidence = [
            evidence
            for evidence in selected_evidence
            if evidence.result.source_type == SourceType.PROVIDER
        ]

        scientific_evidence = [
            evidence
            for evidence in selected_evidence
            if evidence.result.source_type == SourceType.PUBMED
        ]

        if not provider_evidence:
            raise ValueError(
                "Provider discovery requires selected provider evidence."
            )

        answer_parts: list[str] = [
            (
                "The provider registry evidence identified the following "
                "candidate providers for the requested specialty and "
                "location:"
            )
        ]

        provider_lines: list[str] = []

        for evidence in provider_evidence[:3]:
            result = evidence.result

            citation_id = self._citation_id_for_evidence(
                target=evidence,
                selected_evidence=selected_evidence,
            )

            name = result.provider_name or result.title

            if result.location:
                provider_lines.append(
                    f"{name} — NPPES reports a location at "
                    f"{result.location} [{citation_id}]."
                )
            else:
                provider_lines.append(
                    f"{name} appears in the selected NPPES "
                    f"provider evidence [{citation_id}]."
                )

        answer_parts.append(
            " ".join(provider_lines)
        )

        if scientific_evidence:
            scientific_ids = [
                self._citation_id_for_evidence(
                    target=evidence,
                    selected_evidence=selected_evidence,
                )
                for evidence in scientific_evidence
            ]

            formatted_ids = ", ".join(
                f"[{citation_id}]"
                for citation_id in scientific_ids
            )

            answer_parts.append(
                "Selected PubMed sources provide general scientific "
                "context relevant to the healthcare question "
                f"{formatted_ids}. These sources do not establish that "
                "any individual provider offers a particular anxiety-"
                "management, behavior-guidance, sedation, or other "
                "provider-specific service."
            )

        answer_parts.append(
            "These are evidence-supported candidates rather than a "
            "ranking of clinical quality. Current professional licensure, "
            "good standing, clinical quality, and provider-specific "
            "services should be independently verified with authoritative "
            "sources."
        )

        draft = DraftGroundedAnswer(
            answer="\n\n".join(answer_parts),
            recommendations=[],
            limitations=[],
        )

        recommendations = self._finalize_recommendations(
            draft=draft,
            selected_evidence=selected_evidence,
        )

        transparency = SearchTransparency(
            generated_queries=len(plan.generated_queries),
            retrieved_sources=retrieved_sources,
            deduplicated_sources=deduplicated_sources,
            selected_sources=len(selected_evidence),
        )

        limitations = self._finalize_limitations([])

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
        Build provider recommendations deterministically.

        The synthesis model may mention only providers present in selected
        provider evidence, but final provider ordering, reasons, locations,
        credentials, services, citations, and confidence are owned by code.

        This prevents model-generated provider reasons from attaching one
        provider to another provider's citation or from introducing claims
        outside the source-specific evidence boundary.
        """

        provider_evidence = [
            evidence
            for evidence in selected_evidence
            if evidence.result.source_type == SourceType.PROVIDER
        ]

        allowed_names = {
            self._normalize_name(
                evidence.result.provider_name
                or evidence.result.title
            )
            for evidence in provider_evidence
        }

        # Validate any provider names emitted by the synthesis model.
        # They are not used to construct the final recommendation list.
        for draft_recommendation in draft.recommendations:
            normalized_name = self._normalize_name(
                draft_recommendation.name
            )

            if normalized_name not in allowed_names:
                raise ValueError(
                    "Synthesis model attempted to recommend a provider "
                    "that was not present in selected evidence: "
                    f"{draft_recommendation.name}"
                )

        recommendations: list[ProviderRecommendation] = []

        for evidence in provider_evidence[:3]:
            result = evidence.result

            citation_id = self._citation_id_for_evidence(
                target=evidence,
                selected_evidence=selected_evidence,
            )

            recommendations.append(
                ProviderRecommendation(
                    name=(
                        result.provider_name
                        or result.title
                    ),
                    location=result.location,
                    credentials=[],
                    services=[],
                    reasons_selected=(
                        self._build_provider_reasons(
                            evidence=evidence,
                            citation_id=citation_id,
                        )
                    ),
                    confidence=self.ranker.total_score(
                        evidence
                    ),
                )
            )

        return recommendations

    @staticmethod
    def _build_provider_reasons(
        evidence: Evidence,
        citation_id: str,
    ) -> list[str]:
        """
        Build provider-specific reasons only from that provider's evidence.

        NPPES is administrative registry evidence. These reasons deliberately
        avoid claims about clinical quality, board certification, active
        licensure, anxious-child expertise, or service availability.
        """

        result = evidence.result

        reasons = [
            (
                "Included because this provider appears in the selected "
                f"NPPES provider evidence [{citation_id}]."
            )
        ]

        if result.location:
            reasons.append(
                "NPPES reports a practice location at "
                f"{result.location} [{citation_id}]."
            )

        npi = result.metadata.get("npi")

        if npi:
            reasons.append(
                f"NPPES reports NPI {npi} [{citation_id}]."
            )

        taxonomy = result.metadata.get("taxonomy")

        if taxonomy:
            reasons.append(
                "NPPES reports taxonomy metadata: "
                f"{taxonomy} [{citation_id}]."
            )

        return reasons

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
            raise ValueError(f"Synthesis model referenced invalid citation IDs: {sorted(invalid)}")

    @staticmethod
    def _finalize_limitations(
        draft_limitations: list[str],
    ) -> list[str]:
        """
        Return concise, non-duplicative limitations.

        The synthesis model normally produces evidence-specific limitations.

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
        # If the synthesis model already discusses NPPES/provider registry limits,
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
