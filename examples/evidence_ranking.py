from grounding.ranking import EvidenceRanker
from models import UserQuery
from search.query_fanout import QueryFanoutPlanner
from search.retrieval import HealthcareRetrievalOrchestrator


def main() -> None:
    """
    Run the real Beyond RAG v0.3 evidence-ranking pipeline.

    Flow:

        User Question
            -> Gemini Query Planner
            -> SearchPlan
            -> Query Fan-Out
            -> Retrieval Orchestrator
                -> NPPES
                -> PubMed
            -> Deduplication
            -> Evidence Ranking
            -> Selected Evidence

    IMPORTANT:

    This version ranks evidence but intentionally does NOT generate
    final provider recommendations.

    Grounded answer generation and citations belong to v0.4.
    """

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
    print("=== BEYOND RAG: EVIDENCE RANKING ===")
    print()
    print(f"Question: {user_query.text}")

    # -------------------------------------------------------------
    # STEP 1 — GEMINI SEARCH PLANNING
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
        print(f"{index}. {search_query.query}")
        print(f"   Purpose: {search_query.purpose}")
        print(f"   Priority: {search_query.priority}")

    # -------------------------------------------------------------
    # STEP 2 — REAL HEALTHCARE RETRIEVAL
    # -------------------------------------------------------------
    orchestrator = HealthcareRetrievalOrchestrator()

    results = orchestrator.retrieve(
        user_query=user_query,
        plan=plan,
        city="Houston",
        state="TX",
        provider_limit=10,
        pubmed_limit=3,
    )

    print()
    print("--- RETRIEVAL ---")
    print(f"Unique retrieved evidence: {len(results)}")

    # -------------------------------------------------------------
    # STEP 3 — EVIDENCE RANKING
    # -------------------------------------------------------------
    ranker = EvidenceRanker()

    ranked_evidence = ranker.rank(
        user_query=user_query,
        results=results,
        top_k=5,
    )

    print()
    print("--- RANKED EVIDENCE ---")

    for index, evidence in enumerate(
        ranked_evidence,
        start=1,
    ):
        score = evidence.score
        total = ranker.total_score(evidence)

        status = "SELECTED" if evidence.selected else "NOT SELECTED"

        print()
        print(f"{index}. {evidence.result.title}")
        print(f"   Source: {evidence.result.source_type.value}")
        print(f"   Total Score: {total:.4f}")
        print(f"   Relevance: {score.relevance:.4f}")
        print(f"   Authority: {score.authority:.4f}")
        print(f"   Freshness: {score.freshness:.4f}")
        print(f"   Specificity: {score.specificity:.4f}")
        print(f"   Confidence: {score.confidence:.4f}")
        print(f"   Status: {status}")

    selected = [evidence for evidence in ranked_evidence if evidence.selected]

    print()
    print("--- SELECTION SUMMARY ---")
    print(f"Retrieved: {len(results)}")
    print(f"Selected for grounding: {len(selected)}")

    print()
    print("v0.3 stops here. Grounded answers + citations come in v0.4.")


if __name__ == "__main__":
    main()
