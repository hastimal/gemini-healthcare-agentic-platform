import xml.etree.ElementTree as ET

import httpx

from app.config import get_settings
from models import SearchResult, SourceType


class PubMedClient:
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    TOOL_NAME = "beyond_rag_healthcare"

    def __init__(self) -> None:
        settings = get_settings()

        self.email = settings.ncbi_email
        self.api_key = settings.ncbi_api_key

        self.client = httpx.Client(
            timeout=20.0,
            headers={
                "User-Agent": "BeyondRAGHealthcare/0.1",
            },
        )

    def _common_params(self) -> dict[str, str]:
        params = {
            "tool": self.TOOL_NAME,
        }

        if self.email:
            params["email"] = self.email

        if self.api_key:
            params["api_key"] = self.api_key

        return params

    def search_ids(
        self,
        query: str,
        max_results: int = 5,
    ) -> list[str]:
        params = {
            **self._common_params(),
            "db": "pubmed",
            "term": query,
            "retmode": "json",
            "retmax": str(max_results),
            "sort": "relevance",
        }

        response = self.client.get(
            f"{self.BASE_URL}/esearch.fcgi",
            params=params,
        )
        response.raise_for_status()

        data = response.json()

        return data.get("esearchresult", {}).get("idlist", [])

    def fetch_articles(
        self,
        pmids: list[str],
        query_used: str,
    ) -> list[SearchResult]:
        if not pmids:
            return []

        params = {
            **self._common_params(),
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
        }

        response = self.client.get(
            f"{self.BASE_URL}/efetch.fcgi",
            params=params,
        )
        response.raise_for_status()

        return self._parse_articles(
            response.text,
            query_used=query_used,
        )

    def search(
        self,
        query: str,
        max_results: int = 5,
    ) -> list[SearchResult]:
        pmids = self.search_ids(
            query=query,
            max_results=max_results,
        )

        return self.fetch_articles(
            pmids=pmids,
            query_used=query,
        )

    def _parse_articles(
        self,
        xml_text: str,
        query_used: str,
    ) -> list[SearchResult]:
        root = ET.fromstring(xml_text)

        results: list[SearchResult] = []

        for article in root.findall(".//PubmedArticle"):
            pmid = article.findtext(".//PMID")

            title_element = article.find(".//ArticleTitle")
            title = (
                "".join(title_element.itertext()).strip()
                if title_element is not None
                else "Untitled PubMed article"
            )

            abstract_parts = []

            for abstract in article.findall(".//Abstract/AbstractText"):
                text = "".join(abstract.itertext()).strip()

                if text:
                    label = abstract.attrib.get("Label")

                    if label:
                        abstract_parts.append(f"{label}: {text}")
                    else:
                        abstract_parts.append(text)

            abstract_text = " ".join(abstract_parts) or None

            journal = article.findtext(".//Journal/Title")

            year = (
                article.findtext(".//PubDate/Year")
                or article.findtext(".//ArticleDate/Year")
                or article.findtext(".//PubDate/MedlineDate")
            )

            url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None

            results.append(
                SearchResult(
                    source_type=SourceType.PUBMED,
                    title=title,
                    url=url,
                    snippet=abstract_text,
                    content=abstract_text,
                    retrieved_by="pubmed",
                    query_used=query_used,
                    metadata={
                        "pmid": pmid,
                        "journal": journal,
                        "publication_date": year,
                    },
                )
            )

        return results
