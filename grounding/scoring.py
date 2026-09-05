from __future__ import annotations

import re
from datetime import datetime

from models import EvidenceScore, SearchResult, SourceType, UserQuery


class EvidenceScorer:
    """
    Deterministic and explainable evidence scorer.

    v0.3 intentionally begins with rule-based scoring instead of asking
    an LLM to decide which evidence is trustworthy.

    This gives us:

    - reproducible ranking
    - transparent scoring behavior
    - a baseline for later LLM/agentic reranking
    - easier debugging and evaluation

    Current dimensions:

        relevance
        authority
        freshness
        specificity
        confidence

    Every component returns a value from 0.0 to 1.0.
    """

    STOP_WORDS = {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "for",
        "from",
        "in",
        "is",
        "it",
        "of",
        "on",
        "or",
        "the",
        "three",
        "to",
        "using",
        "who",
        "with",
    }

    def score(
        self,
        user_query: UserQuery,
        result: SearchResult,
    ) -> EvidenceScore:
        """
        Score one retrieved result against the original user request.
        """

        relevance = self._score_relevance(
            user_query=user_query,
            result=result,
        )

        authority = self._score_authority(result)

        freshness = self._score_freshness(result)

        specificity = self._score_specificity(
            user_query=user_query,
            result=result,
        )

        confidence = self._score_confidence(result)

        return EvidenceScore(
            relevance=relevance,
            authority=authority,
            freshness=freshness,
            specificity=specificity,
            confidence=confidence,
        )

    def weighted_total(
        self,
        score: EvidenceScore,
    ) -> float:
        """
        Calculate the deterministic baseline score.

        Current weighting:

            relevance   35%
            authority   30%
            specificity 15%
            freshness   10%
            confidence  10%

        These are baseline weights, not claims of universal optimality.
        Later evaluation can tune or replace them.
        """

        total = (
            score.relevance * 0.35
            + score.authority * 0.30
            + score.specificity * 0.15
            + score.freshness * 0.10
            + score.confidence * 0.10
        )

        return round(total, 4)

    def _score_relevance(
        self,
        user_query: UserQuery,
        result: SearchResult,
    ) -> float:
        """
        Estimate relevance using lexical overlap.

        IMPORTANT:

        `query_used` is deliberately NOT included here.

        A retrieved document must earn relevance from its own content,
        title, provider information, or source metadata.

        Including the search query that retrieved the document would
        create "query leakage": an irrelevant document could appear
        relevant simply because the retrieval query contained the
        user's terms.
        """

        query_tokens = self._tokens(user_query.text)

        result_text = " ".join(
            value
            for value in [
                result.title,
                result.snippet or "",
                result.content or "",
                result.provider_name or "",
                result.location or "",
            ]
            if value
        )

        result_tokens = self._tokens(result_text)

        if not query_tokens or not result_tokens:
            return 0.0

        overlap = query_tokens.intersection(result_tokens)

        score = len(overlap) / len(query_tokens)

        return round(min(score, 1.0), 4)

    def _score_authority(
        self,
        result: SearchResult,
    ) -> float:
        """
        Score authority of the underlying source.

        Important distinctions:

        - NPPES is authoritative for NPI/provider registry information.
        - NPPES does NOT establish provider quality or independently
          verify that a provider is the best choice.
        - PubMed is authoritative as a biomedical literature index,
          while the strength of individual studies can still vary.
        """

        authority_scores = {
            SourceType.PUBMED: 0.95,
            SourceType.PROVIDER: 0.90,
            SourceType.CLINICAL_TRIAL: 0.92,
            SourceType.CMS: 0.95,
            SourceType.FHIR: 0.90,
            SourceType.WEB: 0.60,
        }

        return authority_scores.get(
            result.source_type,
            0.50,
        )

    def _score_freshness(
        self,
        result: SearchResult,
    ) -> float:
        """
        Estimate freshness from available metadata.

        Missing publication dates receive a neutral baseline rather
        than automatically being considered stale.
        """

        if result.source_type == SourceType.PROVIDER:
            return 0.85

        publication_date = result.metadata.get("publication_date")

        if not publication_date:
            return 0.70

        year = self._extract_year(str(publication_date))

        if year is None:
            return 0.70

        current_year = datetime.now().year
        age = max(current_year - year, 0)

        if age <= 2:
            return 1.00

        if age <= 5:
            return 0.90

        if age <= 10:
            return 0.75

        return 0.60

    def _score_specificity(
        self,
        user_query: UserQuery,
        result: SearchResult,
    ) -> float:
        """
        Measure how specifically the source supports the user's request.

        Provider evidence benefits from exact specialty/location match.

        Scientific literature should be evaluated primarily on topical
        content rather than city/location.

        As with relevance, `query_used` is intentionally excluded to
        prevent retrieval-query leakage.
        """

        result_text = " ".join(
            value
            for value in [
                result.title,
                result.snippet or "",
                result.content or "",
                result.provider_name or "",
                result.location or "",
                str(result.metadata),
            ]
            if value
        ).lower()

        components: list[float] = []

        if user_query.specialty:
            specialty_tokens = self._tokens(user_query.specialty)

            result_tokens = self._tokens(result_text)

            if specialty_tokens:
                specialty_overlap = len(specialty_tokens.intersection(result_tokens)) / len(
                    specialty_tokens
                )

                components.append(specialty_overlap)

        # Location matters strongly for actual provider candidates.
        # It should not penalize PubMed research evidence.
        if user_query.location and result.source_type == SourceType.PROVIDER:
            location = user_query.location.lower()

            location_match = 1.0 if location in result_text else 0.0

            components.append(location_match)

        # Scientific evidence receives topical specificity based on
        # its own content relevance.
        if result.source_type == SourceType.PUBMED:
            components.append(
                self._score_relevance(
                    user_query=user_query,
                    result=result,
                )
            )

        if not components:
            return 0.50

        return round(
            sum(components) / len(components),
            4,
        )

    def _score_confidence(
        self,
        result: SearchResult,
    ) -> float:
        """
        Score confidence based on evidence completeness and traceability.

        Stable identifiers such as NPI and PMID improve traceability.
        """

        score = 0.40

        if result.url:
            score += 0.15

        if result.title:
            score += 0.10

        if result.snippet or result.content:
            score += 0.10

        if result.metadata.get("npi"):
            score += 0.25

        elif result.metadata.get("pmid"):
            score += 0.25

        return round(
            min(score, 1.0),
            4,
        )

    @classmethod
    def _tokens(
        cls,
        text: str,
    ) -> set[str]:
        """
        Normalize text into meaningful lowercase tokens.
        """

        tokens = set(
            re.findall(
                r"[a-z0-9]+",
                text.lower(),
            )
        )

        return tokens.difference(cls.STOP_WORDS)

    @staticmethod
    def _extract_year(
        value: str,
    ) -> int | None:
        """
        Extract a four-digit year from publication metadata.
        """

        match = re.search(
            r"\b(19|20)\d{2}\b",
            value,
        )

        if not match:
            return None

        return int(match.group(0))
