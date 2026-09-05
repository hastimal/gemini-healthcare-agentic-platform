from grounding.answering import (
    GroundedAnswerGenerator,
)
from grounding.ranking import EvidenceRanker
from models import UserQuery
from search.query_fanout import QueryFanoutPlanner
from search.retrieval import (
    HealthcareRetrievalOrchestrator,
)


def main() -> None:
    """
    Run the complete Beyond RAG v0.4 pipeline.

    Flow:

        User Question
            -> Gemini Query Planner
            -> Query Fan-Out
            -> NPPES + PubMed Retrieval
            -> Deduplication
            -> Evidence Ranking
            -> Diverse Evidence Selection
            -> Citation Construction
            -> Gemini Grounded Synthesis
            -> GroundedAnswer
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
    print("=== BEYOND RAG: GROUNDED ANSWER ===")
    print()
    print(f"Question: {user_query.text}")

    # -------------------------------------------------------------
    # STEP 1 — QUERY PLANNING
    # -------------------------------------------------------------
    planner = QueryFanoutPlanner()

    plan = planner.create_plan(user_query)

    print()
    print("--- SEARCH PLAN ---")
    print(f"Generated queries: {len(plan.generated_queries)}")

    # -------------------------------------------------------------
    # STEP 2 — RETRIEVAL
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
    print(f"Unique evidence: {len(results)}")

    # -------------------------------------------------------------
    # STEP 3 — RANKING + DIVERSE SELECTION
    # -------------------------------------------------------------
    ranker = EvidenceRanker()

    ranked_evidence = ranker.rank(
        user_query=user_query,
        results=results,
        top_k=5,
    )

    selected = [evidence for evidence in ranked_evidence if evidence.selected]

    print()
    print("--- SELECTED EVIDENCE ---")

    for index, evidence in enumerate(
        selected,
        start=1,
    ):
        print(f"C{index}: {evidence.result.title}")

        print(f"    Source: {evidence.result.source_type.value}")

        print(f"    Score: {ranker.total_score(evidence):.4f}")

    # -------------------------------------------------------------
    # STEP 4 — GROUNDED ANSWER
    # -------------------------------------------------------------
    generator = GroundedAnswerGenerator(ranker=ranker)

    answer = generator.generate(
        user_query=user_query,
        plan=plan,
        ranked_evidence=ranked_evidence,
        retrieved_sources=len(results),
        deduplicated_sources=len(results),
    )

    print()
    print("--- GROUNDED ANSWER ---")
    print()
    print(answer.answer)

    print()
    print("--- PROVIDER OPTIONS ---")

    for index, recommendation in enumerate(
        answer.recommendations,
        start=1,
    ):
        print()
        print(f"{index}. {recommendation.name}")

        print(f"   Location: {recommendation.location}")

        print(f"   Confidence: {recommendation.confidence:.4f}")

        for reason in recommendation.reasons_selected:
            print(f"   - {reason}")

    print()
    print("--- CITATIONS ---")

    for citation in answer.citations:
        print()
        print(f"[{citation.citation_id}] {citation.title}")

        print(f"    Source: {citation.source_name}")

        if citation.url:
            print(f"    URL: {citation.url}")

    print()
    print("--- LIMITATIONS ---")

    for limitation in answer.limitations:
        print(f"- {limitation}")

    print()
    print("--- TRANSPARENCY ---")
    print(f"Generated queries: {answer.transparency.generated_queries}")
    print(f"Retrieved sources: {answer.transparency.retrieved_sources}")
    print(f"Deduplicated sources: {answer.transparency.deduplicated_sources}")
    print(f"Selected sources: {answer.transparency.selected_sources}")


if __name__ == "__main__":
    main()
