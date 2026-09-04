from connectors.pubmed.client import PubMedClient
from models import SourceType

SAMPLE_XML = """
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>12345678</PMID>
      <Article>
        <ArticleTitle>
          Managing dental anxiety in pediatric patients
        </ArticleTitle>
        <Abstract>
          <AbstractText>
            This study evaluates approaches to pediatric dental anxiety.
          </AbstractText>
        </Abstract>
        <Journal>
          <Title>Journal of Pediatric Dentistry</Title>
          <JournalIssue>
            <PubDate>
              <Year>2025</Year>
            </PubDate>
          </JournalIssue>
        </Journal>
      </Article>
    </MedlineCitation>
  </PubmedArticle>
</PubmedArticleSet>
"""


def test_parse_pubmed_article():
    client = PubMedClient()

    results = client._parse_articles(
        SAMPLE_XML,
        query_used="pediatric dental anxiety",
    )

    assert len(results) == 1

    result = results[0]

    assert result.source_type == SourceType.PUBMED
    assert result.metadata["pmid"] == "12345678"
    assert "Managing dental anxiety" in result.title
    assert result.query_used == "pediatric dental anxiety"
