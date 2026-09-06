from __future__ import annotations

from grounding.scoring import EvidenceScorer
from models import (
    Evidence,
    SearchIntent,
    SearchResult,
    SourceType,
    UserQuery,
)


class EvidenceRanker:
    """
    Convert SearchResult objects into scored and selected Evidence.

    Ranking and selection are intentionally separate:

    1. Every evidence item receives a deterministic score.
    2. Selection decides which evidence enters the grounding context.

    v0.7 introduces FHIR interoperability evidence.

    For provider-discovery answers, FHIR evidence remains ranked and
    observable but does not consume the provider/scientific grounding
    slots by default. This prevents arbitrary public test-server records
    from displacing provider registry or biomedical evidence.
    """

    def __init__(
        self,
        scorer: EvidenceScorer | None = None,
    ) -> None:
        self.scorer = scorer or EvidenceScorer()

    def rank(
        self,
        user_query: UserQuery,
        results: list[SearchResult],
        top_k: int = 5,
    ) -> list[Evidence]:
        """
        Score, rank, and select evidence.

        All evidence remains in the returned list.

        `selected=True` indicates which evidence is allowed to move into
        the grounded-answer synthesis stage.
        """

        evidence_items: list[Evidence] = []

        for result in results:
            score = self.scorer.score(
                user_query=user_query,
                result=result,
            )

            evidence = Evidence(
                result=result,
                summary=self._build_summary(result),
                claims=[],
                score=score,
                selected=False,
            )

            evidence_items.append(evidence)

        evidence_items.sort(
            key=lambda item: self.scorer.weighted_total(item.score),
            reverse=True,
        )

        self._select_evidence(
            user_query=user_query,
            evidence_items=evidence_items,
            top_k=top_k,
        )

        return evidence_items

    def total_score(
        self,
        evidence: Evidence,
    ) -> float:
        """
        Return the deterministic weighted score.
        """

        return self.scorer.weighted_total(evidence.score)

    def _select_evidence(
        self,
        user_query: UserQuery,
        evidence_items: list[Evidence],
        top_k: int,
    ) -> None:
        """
        Select evidence for grounded-answer synthesis.

        Provider discovery reserves approximately:

            3 provider registry records
            2 scientific/supporting records

        FHIR records remain part of the ranked evidence collection but
        are excluded from the default provider-recommendation grounding
        context in v0.7.

        Why:

        The current FHIR endpoint is a public interoperability test
        server. Its records demonstrate FHIR resource structures and
        relationships but must not be treated as independent evidence
        about NPPES provider quality, licensure, or suitability.
        """

        if top_k <= 0:
            return

        intent = user_query.intent

        has_provider_results = any(
            item.result.source_type == SourceType.PROVIDER
            for item in evidence_items
        )

        provider_discovery = (
            intent == SearchIntent.PROVIDER_DISCOVERY
            or has_provider_results
        )

        if not provider_discovery:
            for evidence in evidence_items[:top_k]:
                evidence.selected = True

            return

        provider_target = min(
            3,
            top_k,
        )

        supporting_target = max(
            top_k - provider_target,
            0,
        )

        providers = [
            evidence
            for evidence in evidence_items
            if evidence.result.source_type == SourceType.PROVIDER
        ]

        # Scientific/supporting evidence for the provider recommendation.
        #
        # FHIR is deliberately excluded here in v0.7 because the public
        # test-server records are interoperability examples rather than
        # independent provider-recommendation evidence.
        supporting = [
            evidence
            for evidence in evidence_items
            if evidence.result.source_type
            not in {
                SourceType.PROVIDER,
                SourceType.FHIR,
            }
        ]

        selected_count = 0

        for evidence in providers[:provider_target]:
            evidence.selected = True
            selected_count += 1

        for evidence in supporting[:supporting_target]:
            evidence.selected = True
            selected_count += 1

        # Backfill provider/scientific evidence first.
        #
        # FHIR remains intentionally outside the provider recommendation
        # grounding context for this release.
        if selected_count < top_k:
            for evidence in evidence_items:
                if evidence.selected:
                    continue

                if evidence.result.source_type == SourceType.FHIR:
                    continue

                evidence.selected = True
                selected_count += 1

                if selected_count >= top_k:
                    break

    @staticmethod
    def _build_summary(
        result: SearchResult,
    ) -> str:
        """
        Create a deterministic evidence summary.

        Grounded synthesis belongs to the answer-generation layer.
        """

        if result.snippet:
            return result.snippet

        if result.content:
            return result.content[:500]

        if result.provider_name and result.location:
            return f"{result.provider_name} — {result.location}"

        return result.title
