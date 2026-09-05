import pytest

from grounding.answering import (
    DraftGroundedAnswer,
    DraftProviderRecommendation,
    GroundedAnswerGenerator,
)
from grounding.citations import CitationBuilder
from models import (
    Evidence,
    EvidenceScore,
    SearchResult,
    SourceType,
)


def _score() -> EvidenceScore:
    return EvidenceScore(
        relevance=0.8,
        authority=0.9,
        freshness=0.9,
        specificity=0.8,
        confidence=1.0,
    )


def _provider() -> Evidence:
    return Evidence(
        result=SearchResult(
            source_type=SourceType.PROVIDER,
            title="Example Pediatric Dentist",
            url=("https://npiregistry.cms.hhs.gov/provider-view/1234567890"),
            provider_name=("Example Pediatric Dentist"),
            location="Houston, TX",
            retrieved_by="nppes",
            query_used="Pediatric Dentistry",
            metadata={
                "npi": "1234567890",
                "taxonomy": ("Dentist, Pediatric Dentistry"),
            },
        ),
        summary=("Example Pediatric Dentist — Houston, TX"),
        score=_score(),
        selected=True,
    )


def test_invalid_citation_reference_is_rejected():
    """
    Gemini must not be able to invent citation IDs.
    """

    evidence = _provider()

    citations = CitationBuilder().build([evidence])

    draft = DraftGroundedAnswer(
        answer=("Example answer using an invalid citation [C99]."),
        recommendations=[],
        limitations=[],
    )

    with pytest.raises(
        ValueError,
        match="invalid citation",
    ):
        (
            GroundedAnswerGenerator._validate_citation_references(
                draft=draft,
                citations=citations,
            )
        )


def test_valid_citation_reference_is_allowed():
    """
    A citation created from selected evidence should validate.
    """

    evidence = _provider()

    citations = CitationBuilder().build([evidence])

    draft = DraftGroundedAnswer(
        answer=("The provider appears in the selected registry evidence [C1]."),
        recommendations=[
            DraftProviderRecommendation(
                name=("Example Pediatric Dentist"),
                reasons_selected=[("Listed in the selected provider evidence [C1].")],
            )
        ],
        limitations=[],
    )

    (
        GroundedAnswerGenerator._validate_citation_references(
            draft=draft,
            citations=citations,
        )
    )


def test_grouped_invalid_citation_is_rejected():
    """
    Invalid citations must also be detected inside grouped forms
    such as [C1, C99].
    """

    evidence = _provider()

    citations = CitationBuilder().build([evidence])

    draft = DraftGroundedAnswer(
        answer=("Provider evidence is available [C1, C99]."),
        recommendations=[],
        limitations=[],
    )

    with pytest.raises(
        ValueError,
        match="invalid citation",
    ):
        (
            GroundedAnswerGenerator._validate_citation_references(
                draft=draft,
                citations=citations,
            )
        )


def test_duplicate_limitations_are_not_added():
    """
    Standard limitations should not be repeated when Gemini already
    returned a limitation covering the same evidence gap.
    """

    limitations = GroundedAnswerGenerator._finalize_limitations(
        [
            (
                "Provider registry records (NPPES) "
                "do not assess clinical quality "
                "or board certification."
            ),
            ("Specific sedation services have not been independently verified."),
            (
                "Scientific literature describes "
                "general interventions rather than "
                "specific provider services."
            ),
        ]
    )

    assert len(limitations) == 3
