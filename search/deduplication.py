from __future__ import annotations

from models import SearchResult


def deduplicate_results(
    results: list[SearchResult],
) -> list[SearchResult]:
    """
    Remove duplicate retrieval results while preserving result order.

    Why this matters:
    The same provider or scientific article can be retrieved multiple
    times from different fan-out queries.

    Without deduplication, duplicate evidence could incorrectly receive
    more weight during our future evidence-ranking stage.

    Current strategy:
    - Provider -> deduplicate using NPI.
    - PubMed -> deduplicate using PMID.
    - Other sources -> deduplicate using normalized URL.
    - Final fallback -> source type + normalized title.
    """

    unique_results: list[SearchResult] = []
    seen_keys: set[str] = set()

    for result in results:
        key = _deduplication_key(result)

        # Skip evidence that we have already seen.
        if key in seen_keys:
            continue

        seen_keys.add(key)
        unique_results.append(result)

    return unique_results


def _deduplication_key(
    result: SearchResult,
) -> str:
    """
    Build the most reliable deduplication key available.

    Stable identifiers are preferred over text because provider names,
    article titles, snippets, and URLs may have formatting differences.
    """

    # NPI is the preferred stable identifier for provider records.
    npi = result.metadata.get("npi")

    if npi:
        return f"provider:npi:{npi}"

    # PMID is the preferred stable identifier for PubMed articles.
    pmid = result.metadata.get("pmid")

    if pmid:
        return f"pubmed:pmid:{pmid}"

    # URL is our next-best identifier for other retrieved evidence.
    if result.url:
        normalized_url = result.url.rstrip("/").lower()
        return f"url:{normalized_url}"

    # Last-resort fallback when no stable identifier or URL exists.
    normalized_title = result.title.strip().lower()

    return f"title:{result.source_type.value}:{normalized_title}"
