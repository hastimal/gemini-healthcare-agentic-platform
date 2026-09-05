from grounding.ranking import EvidenceRanker
from grounding.scoring import EvidenceScorer
from models import (
    SearchIntent,
    SearchResult,
    SourceType,
    UserQuery,
)


def _user_query() -> UserQuery:
    """
    Shared flagship provider-discovery query.
    """

    return UserQuery(
        text=("Find pediatric dentists in Houston for a child who is anxious about dental visits."),
        location="Houston, TX",
        specialty="Pediatric Dentistry",
        intent=SearchIntent.PROVIDER_DISCOVERY,
    )


def _provider_result(
    name: str = "Example Pediatric Dentist",
    npi: str = "1234567890",
) -> SearchResult:
    """
    Strong structured provider evidence.
    """

    return SearchResult(
        source_type=SourceType.PROVIDER,
        title=name,
        url=(f"https://npiregistry.cms.hhs.gov/provider-view/{npi}"),
        provider_name=name,
        location="Houston, TX",
        retrieved_by="nppes",
        query_used="Pediatric Dentistry",
        metadata={
            "npi": npi,
            "taxonomy": ("Dentist, Pediatric Dentistry"),
            "city": "Houston",
            "state": "TX",
        },
    )


def _pubmed_result(
    title: str = ("Behavior management techniques for pediatric dental anxiety"),
    pmid: str = "12345678",
) -> SearchResult:
    """
    Scientific evidence relevant to pediatric dental anxiety.
    """

    return SearchResult(
        source_type=SourceType.PUBMED,
        title=title,
        url=(f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"),
        snippet=(
            "Clinical evidence examining behavior management "
            "for anxious children receiving pediatric dental care."
        ),
        content=(
            "Clinical evidence examining behavior management "
            "for anxious children receiving pediatric dental care."
        ),
        retrieved_by="pubmed",
        query_used=("pediatric dental anxiety behavior management"),
        metadata={
            "pmid": pmid,
            "publication_date": "2025",
        },
    )


def _weak_web_result() -> SearchResult:
    """
    Generic evidence expected to rank below stronger sources.
    """

    return SearchResult(
        source_type=SourceType.WEB,
        title="General Dental Information",
        url=("https://example.com/dental-information"),
        snippet=("General information about dental care."),
        content=("General information about dental care."),
        retrieved_by="web",
        query_used="dentist",
        metadata={},
    )


def test_evidence_scores_are_bounded():
    """
    Every scoring dimension must remain within 0.0-1.0.
    """

    scorer = EvidenceScorer()

    score = scorer.score(
        user_query=_user_query(),
        result=_provider_result(),
    )

    assert 0.0 <= score.relevance <= 1.0
    assert 0.0 <= score.authority <= 1.0
    assert 0.0 <= score.freshness <= 1.0
    assert 0.0 <= score.specificity <= 1.0
    assert 0.0 <= score.confidence <= 1.0

    total = scorer.weighted_total(score)

    assert 0.0 <= total <= 1.0


def test_authoritative_evidence_beats_generic_web():
    """
    Provider registry evidence should beat generic web content for
    this provider-discovery baseline.
    """

    scorer = EvidenceScorer()

    provider_score = scorer.weighted_total(
        scorer.score(
            user_query=_user_query(),
            result=_provider_result(),
        )
    )

    web_score = scorer.weighted_total(
        scorer.score(
            user_query=_user_query(),
            result=_weak_web_result(),
        )
    )

    assert provider_score > web_score


def test_ranker_orders_evidence_by_score():
    """
    Global ranking must remain score ordered.
    """

    ranker = EvidenceRanker()

    results = [
        _weak_web_result(),
        _pubmed_result(),
        _provider_result(),
    ]

    ranked = ranker.rank(
        user_query=_user_query(),
        results=results,
        top_k=2,
    )

    totals = [ranker.total_score(evidence) for evidence in ranked]

    assert totals == sorted(
        totals,
        reverse=True,
    )


def test_provider_discovery_selects_diverse_evidence():
    """
    A provider-heavy result set must not crowd scientific evidence
    completely out of the selected grounding context.

    For top_k=5 we expect:

        3 provider records
        2 supporting PubMed records
    """

    ranker = EvidenceRanker()

    results = [
        _provider_result(
            "Provider One",
            "1111111111",
        ),
        _provider_result(
            "Provider Two",
            "2222222222",
        ),
        _provider_result(
            "Provider Three",
            "3333333333",
        ),
        _provider_result(
            "Provider Four",
            "4444444444",
        ),
        _provider_result(
            "Provider Five",
            "5555555555",
        ),
        _pubmed_result(
            "Pediatric dental anxiety systematic review",
            "11111111",
        ),
        _pubmed_result(
            "Behavior guidance for anxious pediatric patients",
            "22222222",
        ),
    ]

    ranked = ranker.rank(
        user_query=_user_query(),
        results=results,
        top_k=5,
    )

    selected = [evidence for evidence in ranked if evidence.selected]

    assert len(selected) == 5

    selected_providers = [
        evidence for evidence in selected if evidence.result.source_type == SourceType.PROVIDER
    ]

    selected_pubmed = [
        evidence for evidence in selected if evidence.result.source_type == SourceType.PUBMED
    ]

    assert len(selected_providers) == 3
    assert len(selected_pubmed) == 2


def test_query_used_does_not_create_fake_relevance():
    """
    Retrieval query text must not artificially inflate evidence
    relevance.

    The article itself is unrelated even though query_used contains
    highly relevant pediatric dentistry terms.
    """

    scorer = EvidenceScorer()

    unrelated = SearchResult(
        source_type=SourceType.PUBMED,
        title=("International Symposium on Intensive Care Medicine"),
        url=("https://pubmed.ncbi.nlm.nih.gov/99999999/"),
        snippet=("Conference proceedings covering critical care medicine."),
        content=("Conference proceedings covering critical care medicine."),
        retrieved_by="pubmed",
        query_used=("pediatric dental anxiety behavior management systematic review"),
        metadata={
            "pmid": "99999999",
            "publication_date": "2016",
        },
    )

    score = scorer.score(
        user_query=_user_query(),
        result=unrelated,
    )

    assert score.relevance < 0.10
