from models import UserQuery
from search.query_fanout import QueryFanoutPlanner


def main() -> None:
    user_query = UserQuery(
        text=(
            "Find three pediatric dentists in Houston for a child "
            "who is anxious about dental visits. Compare them using "
            "trustworthy sources, provider credentials, services, "
            "and location, and explain why you selected each one."
        ),
        location="Houston, TX",
        specialty="pediatric dentistry",
    )

    planner = QueryFanoutPlanner()

    plan = planner.create_plan(user_query)

    print()
    print("=== SEARCH PLAN ===")
    print()

    print(f"Intent: {plan.intent.value}")
    print(f"Original query: {plan.original_query.text}")
    print()

    print("Generated queries:")

    for index, query in enumerate(plan.generated_queries, start=1):
        print()
        print(f"{index}. {query.query}")
        print(f"   Purpose: {query.purpose}")
        print(f"   Priority: {query.priority}")


if __name__ == "__main__":
    main()
