import pytest

from grounding.answering import (
    DraftGroundedAnswer,
    DraftProviderRecommendation,
    GroundedAnswerGenerator,
)
from grounding.citations import CitationBuilder
from grounding.ranking import EvidenceRanker
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



def test_provider_reasons_are_deterministic_and_provider_scoped():
    """
    Model-generated cross-provider citation reasons must not survive
    final recommendation construction.
    """

    provider_one = _provider()

    provider_two = Evidence(
        result=SearchResult(
            source_type=SourceType.PROVIDER,
            title="Second Pediatric Dentist",
            url=(
                "https://npiregistry.cms.hhs.gov/"
                "provider-view/2222222222"
            ),
            provider_name="Second Pediatric Dentist",
            location="Houston, TX",
            retrieved_by="nppes",
            query_used="Pediatric Dentistry",
            metadata={
                "npi": "2222222222",
                "taxonomy": "Dentist, Pediatric Dentistry",
            },
        ),
        summary="Second Pediatric Dentist — Houston, TX",
        score=_score(),
        selected=True,
    )

    draft = DraftGroundedAnswer(
        answer="Two registry candidates are available [C1, C2].",
        recommendations=[
            DraftProviderRecommendation(
                name="Example Pediatric Dentist",
                reasons_selected=[
                    (
                        "Unsafe model reason incorrectly associates "
                        "the first provider with [C1, C2]."
                    )
                ],
            ),
            DraftProviderRecommendation(
                name="Second Pediatric Dentist",
                reasons_selected=[
                    "Second provider [C2]."
                ],
            ),
        ],
        limitations=[],
    )

    generator = GroundedAnswerGenerator.__new__(
        GroundedAnswerGenerator
    )
    generator.ranker = EvidenceRanker()

    recommendations = generator._finalize_recommendations(
        draft=draft,
        selected_evidence=[
            provider_one,
            provider_two,
        ],
    )

    assert len(recommendations) == 2

    first_reasons = " ".join(
        recommendations[0].reasons_selected
    )

    second_reasons = " ".join(
        recommendations[1].reasons_selected
    )

    assert "[C1]" in first_reasons
    assert "[C2]" not in first_reasons

    assert "[C2]" in second_reasons
    assert "[C1]" not in second_reasons

    assert recommendations[0].credentials == []
    assert recommendations[0].services == []
    assert recommendations[1].credentials == []
    assert recommendations[1].services == []


class _FailIfCalledSynthesis:
    """
    Test double proving provider discovery never invokes synthesis.
    """

    async def generate(self, *, prompt, schema):
        raise AssertionError(
            "Provider discovery must not call model synthesis."
        )


@pytest.mark.asyncio
async def test_provider_discovery_does_not_call_model_synthesis():
    """
    Safety-critical provider discovery is assembled deterministically.
    """

    from models import SearchIntent, SearchPlan, SearchQuery, UserQuery

    provider = _provider()

    user_query = UserQuery(
        text="Find pediatric dentists in Houston",
        location="Houston, TX",
        specialty="Pediatric Dentistry",
        intent=SearchIntent.PROVIDER_DISCOVERY,
    )

    plan = SearchPlan(
        original_query=user_query,
        intent=SearchIntent.PROVIDER_DISCOVERY,
        generated_queries=[
            SearchQuery(
                query="pediatric dentist Houston TX",
                purpose="Provider discovery",
                priority=1,
            )
        ],
    )

    generator = GroundedAnswerGenerator(
        synthesis=_FailIfCalledSynthesis(),
    )

    answer = await generator.agenerate(
        user_query=user_query,
        plan=plan,
        ranked_evidence=[provider],
        retrieved_sources=1,
        deduplicated_sources=1,
    )

    assert len(answer.recommendations) == 1

    assert (
        answer.recommendations[0].name
        == "Example Pediatric Dentist"
    )

    assert answer.recommendations[0].credentials == []
    assert answer.recommendations[0].services == []

    assert "[C1]" in answer.answer

    assert (
        "clinical quality"
        in answer.answer.lower()
    )


@pytest.mark.asyncio
async def test_provider_discovery_recommendation_uses_own_citation():
    """
    Provider recommendation reasons must remain scoped to that provider.
    """

    from models import SearchIntent, SearchPlan, SearchQuery, UserQuery

    provider = _provider()

    user_query = UserQuery(
        text="Find pediatric dentists in Houston",
        location="Houston, TX",
        specialty="Pediatric Dentistry",
        intent=SearchIntent.PROVIDER_DISCOVERY,
    )

    plan = SearchPlan(
        original_query=user_query,
        intent=SearchIntent.PROVIDER_DISCOVERY,
        generated_queries=[
            SearchQuery(
                query="pediatric dentist Houston TX",
                purpose="Provider discovery",
                priority=1,
            )
        ],
    )

    generator = GroundedAnswerGenerator(
        synthesis=_FailIfCalledSynthesis(),
    )

    answer = await generator.agenerate(
        user_query=user_query,
        plan=plan,
        ranked_evidence=[provider],
        retrieved_sources=1,
        deduplicated_sources=1,
    )

    reasons = " ".join(
        answer.recommendations[0].reasons_selected
    )

    assert "[C1]" in reasons
    assert "[C2]" not in reasons
