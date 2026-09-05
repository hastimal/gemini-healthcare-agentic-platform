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

    v0.3 uses two distinct concepts:

    1. Ranking
       Every evidence item receives a deterministic weighted score.

    2. Selection
       Evidence is selected with source diversity so one source type
       does not consume the entire grounding context.

    This is especially important for provider discovery.

    A provider recommendation may require:

        provider identity evidence
            +
        scientific/supporting evidence

    rather than five nearly identical registry records.
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

        `selected=True` indicates which items are intended to move
        into the grounding stage.
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

        # Global ranking remains score-based so evaluation can inspect
        # the strongest evidence independently of selection policy.
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
        Select a diverse evidence set.

        For provider discovery, reserve approximately:

            60% provider evidence
            40% supporting/non-provider evidence

        With top_k=5 this becomes:

            3 providers
            2 supporting evidence items

        If one category does not contain enough results, remaining
        slots are filled with the highest-ranked unselected evidence.

        This policy prevents a large provider registry result set from
        completely crowding scientific evidence out of the grounding
        context.
        """

        if top_k <= 0:
            return

        intent = user_query.intent

        # Some callers may not explicitly populate UserQuery.intent.
        # In that case provider records in the evidence pool are a
        # strong signal that we are handling provider discovery.
        has_provider_results = any(
            item.result.source_type == SourceType.PROVIDER for item in evidence_items
        )

        provider_discovery = intent == SearchIntent.PROVIDER_DISCOVERY or has_provider_results

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

        supporting = [
            evidence
            for evidence in evidence_items
            if evidence.result.source_type != SourceType.PROVIDER
        ]

        selected_count = 0

        # Select strongest provider candidates first.
        for evidence in providers[:provider_target]:
            evidence.selected = True
            selected_count += 1

        # Reserve supporting slots for sources such as PubMed.
        for evidence in supporting[:supporting_target]:
            evidence.selected = True
            selected_count += 1

        # If either category had insufficient evidence, backfill using
        # the strongest remaining evidence regardless of source type.
        if selected_count < top_k:
            for evidence in evidence_items:
                if evidence.selected:
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

        v0.3 deliberately avoids LLM-generated evidence summaries.
        Grounded synthesis belongs to v0.4.
        """

        if result.snippet:
            return result.snippet

        if result.content:
            return result.content[:500]

        if result.provider_name and result.location:
            return f"{result.provider_name} — {result.location}"

        return result.title
