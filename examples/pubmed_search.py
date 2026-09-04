from connectors.pubmed.client import PubMedClient


def main() -> None:
    client = PubMedClient()

    query = "pediatric dental anxiety behavior management"

    results = client.search(
        query=query,
        max_results=5,
    )

    print()
    print("=== PUBMED SEARCH ===")
    print()
    print(f"Query: {query}")
    print(f"Results: {len(results)}")

    for index, result in enumerate(results, start=1):
        print()
        print(f"{index}. {result.title}")
        print(f"   URL: {result.url}")
        print(f"   PMID: {result.metadata.get('pmid')}")
        print(f"   Journal: {result.metadata.get('journal')}")
        print(f"   Publication: {result.metadata.get('publication_date')}")

        if result.snippet:
            snippet = result.snippet[:300].replace("\n", " ")
            print(f"   Abstract: {snippet}...")


if __name__ == "__main__":
    main()
