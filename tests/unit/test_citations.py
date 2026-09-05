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


def test_citation_builder_uses_selected_evidence_only():
    """
    Only evidence selected for grounding should receive citations.
    """

    selected_provider = Evidence(
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
            },
        ),
        summary=("Example Pediatric Dentist — Houston, TX"),
        score=_score(),
        selected=True,
    )

    selected_pubmed = Evidence(
        result=SearchResult(
            source_type=SourceType.PUBMED,
            title=("Pediatric dental anxiety systematic review"),
            url=("https://pubmed.ncbi.nlm.nih.gov/12345678/"),
            snippet=("Evidence about pediatric dental anxiety."),
            retrieved_by="pubmed",
            query_used=("pediatric dental anxiety systematic review"),
            metadata={
                "pmid": "12345678",
            },
        ),
        summary=("Evidence about pediatric dental anxiety."),
        score=_score(),
        selected=True,
    )

    unselected = Evidence(
        result=SearchResult(
            source_type=SourceType.WEB,
            title="Unselected Result",
            url="https://example.com",
            retrieved_by="web",
            query_used="example",
            metadata={},
        ),
        summary="Unselected evidence",
        score=_score(),
        selected=False,
    )

    citations = CitationBuilder().build(
        [
            selected_provider,
            selected_pubmed,
            unselected,
        ]
    )

    assert len(citations) == 2

    assert citations[0].citation_id == "C1"
    assert citations[1].citation_id == "C2"

    assert citations[0].source_name == "CMS NPPES / NPI Registry"

    assert citations[1].source_name == "PubMed"


def test_provider_citation_does_not_claim_quality():
    """
    Provider registry citations should describe their limited scope
    rather than imply quality or superiority.
    """

    evidence = Evidence(
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
            },
        ),
        summary=("Example Pediatric Dentist — Houston, TX"),
        score=_score(),
        selected=True,
    )

    citation = CitationBuilder().build([evidence])[0]

    claim = (citation.claim_supported or "").lower()

    assert "best" not in claim
    assert "quality" not in claim
    assert "identity" in claim
