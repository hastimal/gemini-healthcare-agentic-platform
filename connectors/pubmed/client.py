from __future__ import annotations

import time
import xml.etree.ElementTree as ET
from typing import Any

import httpx

from app.config import get_settings
from models import SearchResult, SourceType

settings = get_settings()


class PubMedClient:
    """
    Lightweight PubMed client using the official NCBI E-utilities API.

    Retrieval flow:

        search query
            -> ESearch
            -> PMID list
            -> EFetch
            -> PubMed XML
            -> normalized SearchResult objects

    Rate limiting
    -------------

    NCBI limits how quickly clients should call E-utilities.

    Without an API key, we deliberately keep requests below the
    anonymous request-rate ceiling.

    With an API key, a shorter delay is allowed.

    The client also automatically retries temporary failures such as:

        429 Too Many Requests
        500 Internal Server Error
        502 Bad Gateway
        503 Service Unavailable
        504 Gateway Timeout

    This is important because an evidence-aware search plan may execute
    multiple PubMed queries during one user request.
    """

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    RETRYABLE_STATUS_CODES = {
        429,
        500,
        502,
        503,
        504,
    }

    MAX_RETRIES = 4

    def __init__(
        self,
        client: httpx.Client | None = None,
    ) -> None:
        """
        Allow HTTP client injection for testing.

        A persistent httpx.Client also gives us connection reuse rather
        than establishing a new connection for every E-utilities call.
        """

        self.client = client or httpx.Client(
            timeout=30.0,
            headers={"User-Agent": ("BeyondRAGHealthcare/0.3")},
        )

        self._last_request_time = 0.0

    def _common_params(self) -> dict[str, str]:
        """
        Build parameters recommended by NCBI.

        `tool` identifies the application.

        `email` gives NCBI a contact address if they need to reach the
        application owner regarding problematic API traffic.

        An NCBI API key is optional.
        """

        params: dict[str, str] = {
            "tool": ("gemini-healthcare-agentic-platform"),
        }

        ncbi_email = getattr(
            settings,
            "ncbi_email",
            None,
        )

        ncbi_api_key = getattr(
            settings,
            "ncbi_api_key",
            None,
        )

        if ncbi_email:
            params["email"] = str(ncbi_email)

        if ncbi_api_key:
            params["api_key"] = str(ncbi_api_key)

        return params

    def _minimum_request_interval(self) -> float:
        """
        Return the minimum delay between E-utilities requests.

        Anonymous NCBI traffic should stay below approximately
        three requests per second.

        0.40 seconds gives us a conservative margin.

        API-key traffic can run faster, but we still maintain a small
        delay so bursty multi-query workflows remain polite.
        """

        ncbi_api_key = getattr(
            settings,
            "ncbi_api_key",
            None,
        )

        if ncbi_api_key:
            return 0.12

        return 0.40

    def _throttle(self) -> None:
        """
        Prevent requests from being sent too quickly.

        This operates across both ESearch and EFetch calls made by this
        PubMedClient instance.
        """

        minimum_interval = self._minimum_request_interval()

        elapsed = time.monotonic() - self._last_request_time

        remaining = minimum_interval - elapsed

        if remaining > 0:
            time.sleep(remaining)

    def _get(
        self,
        url: str,
        params: dict[str, Any],
    ) -> httpx.Response:
        """
        Execute a rate-limited GET request with retry/backoff.

        Exponential backoff schedule is approximately:

            retry 1 -> 1 second
            retry 2 -> 2 seconds
            retry 3 -> 4 seconds
            retry 4 -> 8 seconds

        If NCBI returns a Retry-After header, we respect it when
        possible.
        """

        last_response: httpx.Response | None = None

        for attempt in range(self.MAX_RETRIES + 1):
            self._throttle()

            response = self.client.get(
                url,
                params=params,
            )

            self._last_request_time = time.monotonic()

            last_response = response

            if response.status_code not in self.RETRYABLE_STATUS_CODES:
                response.raise_for_status()
                return response

            # No more retries remain.
            if attempt >= self.MAX_RETRIES:
                break

            retry_after = response.headers.get("Retry-After")

            if retry_after:
                try:
                    delay = float(retry_after)
                except ValueError:
                    delay = float(2**attempt)
            else:
                delay = float(2**attempt)

            # First retry should wait at least one second.
            delay = max(
                delay,
                1.0,
            )

            print(
                "PubMed request temporarily "
                f"failed with HTTP "
                f"{response.status_code}. "
                f"Retrying in {delay:.1f}s..."
            )

            time.sleep(delay)

        if last_response is None:
            raise RuntimeError("PubMed request failed before receiving an HTTP response.")

        last_response.raise_for_status()

        # This line should not normally be reached because
        # raise_for_status() above raises for the failure response.
        return last_response

    def search_ids(
        self,
        query: str,
        max_results: int = 5,
    ) -> list[str]:
        """
        Search PubMed and return matching PMIDs.

        ESearch is used only for discovery.

        Article details are fetched separately in one batched EFetch
        request.
        """

        params: dict[str, Any] = {
            **self._common_params(),
            "db": "pubmed",
            "term": query,
            "retmode": "json",
            "retmax": max_results,
            "sort": "relevance",
        }

        response = self._get(
            f"{self.BASE_URL}/esearch.fcgi",
            params=params,
        )

        payload = response.json()

        return list(
            payload.get(
                "esearchresult",
                {},
            ).get(
                "idlist",
                [],
            )
        )

    def fetch_articles(
        self,
        pmids: list[str],
        query_used: str,
    ) -> list[SearchResult]:
        """
        Fetch details for multiple PubMed records in one EFetch call.

        Batching PMID retrieval materially reduces API traffic compared
        with fetching one article at a time.
        """

        if not pmids:
            return []

        params: dict[str, Any] = {
            **self._common_params(),
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
        }

        response = self._get(
            f"{self.BASE_URL}/efetch.fcgi",
            params=params,
        )

        return self._parse_articles(
            xml_text=response.text,
            query_used=query_used,
        )

    def search(
        self,
        query: str,
        max_results: int = 5,
    ) -> list[SearchResult]:
        """
        Execute a complete PubMed search.

        Flow:

            ESearch -> PMIDs -> batched EFetch -> SearchResult[]
        """

        pmids = self.search_ids(
            query=query,
            max_results=max_results,
        )

        if not pmids:
            return []

        return self.fetch_articles(
            pmids=pmids,
            query_used=query,
        )

    def _parse_articles(
        self,
        xml_text: str,
        query_used: str,
    ) -> list[SearchResult]:
        """
        Parse PubMed XML into the platform's normalized SearchResult
        model.

        Only scalar metadata values are stored because SearchResult
        metadata currently expects scalar values rather than nested
        lists or dictionaries.
        """

        root = ET.fromstring(xml_text)

        results: list[SearchResult] = []

        for article in root.findall(".//PubmedArticle"):
            pmid = self._node_text(article.find(".//MedlineCitation/PMID"))

            title = self._element_text(article.find(".//Article/ArticleTitle"))

            abstract_parts = []

            for node in article.findall(".//Article/Abstract/AbstractText"):
                text = self._element_text(node)

                if text:
                    abstract_parts.append(text)

            abstract = " ".join(abstract_parts).strip()

            journal = self._node_text(article.find(".//Article/Journal/Title"))

            publication_date = self._publication_date(article)

            if not pmid:
                continue

            if not title:
                title = f"PubMed article {pmid}"

            results.append(
                SearchResult(
                    source_type=(SourceType.PUBMED),
                    title=title,
                    url=(f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"),
                    snippet=(abstract[:500] if abstract else None),
                    content=(abstract if abstract else None),
                    retrieved_by="pubmed",
                    query_used=query_used,
                    metadata={
                        "pmid": pmid,
                        "journal": (journal or ""),
                        "publication_date": (publication_date or ""),
                    },
                )
            )

        return results

    @classmethod
    def _element_text(
        cls,
        element: ET.Element | None,
    ) -> str:
        """
        Extract all textual content from an XML element.

        PubMed titles and abstracts may contain nested formatting tags,
        so `.text` alone can lose portions of the content.
        """

        if element is None:
            return ""

        return "".join(element.itertext()).strip()

    @staticmethod
    def _node_text(
        element: ET.Element | None,
    ) -> str:
        """
        Return simple node text safely.
        """

        if element is None or element.text is None:
            return ""

        return element.text.strip()

    @classmethod
    def _publication_date(
        cls,
        article: ET.Element,
    ) -> str:
        """
        Extract the best available publication date.

        PubMed date structures vary between journals, so we first try
        the journal issue date and then fall back to MedlineDate.
        """

        pub_date = article.find(".//Article/Journal/JournalIssue/PubDate")

        if pub_date is None:
            return ""

        year = cls._node_text(pub_date.find("Year"))

        month = cls._node_text(pub_date.find("Month"))

        day = cls._node_text(pub_date.find("Day"))

        if year:
            parts = [
                part
                for part in [
                    year,
                    month,
                    day,
                ]
                if part
            ]

            return " ".join(parts)

        medline_date = cls._node_text(pub_date.find("MedlineDate"))

        return medline_date
