from models import SourceType, UserQuery
from search.query_fanout import QueryFanoutPlanner
from search.retrieval import HealthcareRetrievalOrchestrator


def main() -> None:
    """
    Run the first real end-to-end Beyond RAG retrieval pipeline.

    Flow:

        User Question
            -> Gemini
            -> SearchPlan
            -> Query Fan-Out
            -> Retrieval Orchestrator
                -> NPPES
                -> PubMed
            -> Normalize
            -> Deduplicate
            -> Evidence Pool

    Important:
    We intentionally stop before ranking providers or generating
    recommendations.

    Evidence ranking and grounded answer generation are later
    milestones.
    """

    # Our flagship demo query.
    #
    # Specialty is structured explicitly so the retrieval layer does
    # not need to hard-code "Pediatric Dentistry".
    user_query = UserQuery(
        text=(
            "Find three pediatric dentists in Houston for a child "
            "who is anxious about dental visits. Compare them using "
            "trustworthy sources, provider credentials, services, "
            "and location, and explain why you selected each one."
        ),
        location="Houston, TX",
        specialty="Pediatric Dentistry",
    )

    print()
    print("=== BEYOND RAG: RETRIEVAL PIPELINE ===")
    print()
    print(f"Question: {user_query.text}")
    print(f"Specialty: {user_query.specialty}")
    print(f"Location: {user_query.location}")

    # -------------------------------------------------------------
    # STEP 1 — GEMINI QUERY PLANNING
    # -------------------------------------------------------------
    planner = QueryFanoutPlanner()
    plan = planner.create_plan(user_query)

    print()
    print("--- SEARCH PLAN ---")
    print(f"Intent: {plan.intent.value}")
    print(f"Generated queries: {len(plan.generated_queries)}")

    for index, search_query in enumerate(
        plan.generated_queries,
        start=1,
    ):
        print()
        print(f"{index}. {search_query.query}")
        print(f"   Purpose: {search_query.purpose}")
        print(f"   Priority: {search_query.priority}")

    # -------------------------------------------------------------
    # STEP 2 — REAL HEALTHCARE RETRIEVAL
    # -------------------------------------------------------------
    #
    # Specialty comes dynamically from UserQuery.
    #
    # City/state are explicit for v0.2 because location is currently
    # represented as a display string in UserQuery.
    orchestrator = HealthcareRetrievalOrchestrator()

    results = orchestrator.retrieve(
        user_query=user_query,
        plan=plan,
        city="Houston",
        state="TX",
        provider_limit=10,
        pubmed_limit=3,
    )

    provider_results = [result for result in results if result.source_type == SourceType.PROVIDER]

    pubmed_results = [result for result in results if result.source_type == SourceType.PUBMED]

    print()
    print("--- RETRIEVAL SUMMARY ---")
    print(f"Total unique evidence: {len(results)}")
    print(f"Provider records: {len(provider_results)}")
    print(f"PubMed records: {len(pubmed_results)}")

    # -------------------------------------------------------------
    # PROVIDER EVIDENCE
    # -------------------------------------------------------------
    print()
    print("--- PROVIDER CANDIDATES ---")

    for index, result in enumerate(
        provider_results,
        start=1,
    ):
        print()
        print(f"{index}. {result.provider_name}")
        print(f"   Location: {result.location}")
        print(f"   NPI: {result.metadata.get('npi')}")
        print(f"   Source: {result.url}")

    # -------------------------------------------------------------
    # SCIENTIFIC EVIDENCE
    # -------------------------------------------------------------
    print()
    print("--- SCIENTIFIC EVIDENCE ---")

    for index, result in enumerate(
        pubmed_results,
        start=1,
    ):
        print()
        print(f"{index}. {result.title}")
        print(f"   PMID: {result.metadata.get('pmid')}")
        print(f"   Source: {result.url}")


if __name__ == "__main__":
    main()
