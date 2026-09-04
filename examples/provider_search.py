from connectors.provider_search.client import NPPESProviderClient


def main() -> None:
    client = NPPESProviderClient()

    results = client.search(
        taxonomy_description="Pediatric Dentistry",
        city="Houston",
        state="TX",
        limit=10,
    )

    print()
    print("=== NPPES PROVIDER SEARCH ===")
    print()
    print("Specialty: Pediatric Dentistry")
    print("Location: Houston, TX")
    print(f"Results: {len(results)}")

    for index, result in enumerate(results, start=1):
        print()
        print(f"{index}. {result.provider_name}")
        print(f"   Location: {result.location}")
        print(f"   NPI: {result.metadata.get('npi')}")
        print(f"   Taxonomy: {result.metadata.get('taxonomy_description')}")
        print(
            "   License: "
            f"{result.metadata.get('license_number')} "
            f"({result.metadata.get('license_state')})"
        )
        print(f"   URL: {result.url}")


if __name__ == "__main__":
    main()
