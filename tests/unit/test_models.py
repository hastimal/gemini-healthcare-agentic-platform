from models import (
    GroundedAnswer,
    ProviderRecommendation,
    SearchIntent,
    SearchPlan,
    SearchQuery,
    SearchTransparency,
    UserQuery,
)


def test_user_query():
    query = UserQuery(
        text="Find three pediatric dentists in Houston",
        location="Houston, TX",
        specialty="pediatric dentistry",
        intent=SearchIntent.PROVIDER_DISCOVERY,
    )

    assert query.location == "Houston, TX"
    assert query.intent == SearchIntent.PROVIDER_DISCOVERY


def test_search_plan():
    user_query = UserQuery(
        text="Find three pediatric dentists in Houston",
        location="Houston, TX",
    )

    plan = SearchPlan(
        original_query=user_query,
        intent=SearchIntent.PROVIDER_DISCOVERY,
        generated_queries=[
            SearchQuery(
                query="pediatric dentists Houston TX",
                purpose="Find relevant providers",
                priority=1,
            )
        ],
    )

    assert len(plan.generated_queries) == 1


def test_grounded_answer():
    answer = GroundedAnswer(
        answer="Three relevant pediatric dentistry options were identified.",
        recommendations=[
            ProviderRecommendation(
                name="Example Pediatric Dentistry",
                location="Houston, TX",
                credentials=["Pediatric dentistry"],
                services=["Child-focused care"],
                reasons_selected=["Matches requested specialty and location"],
                confidence=0.9,
            )
        ],
        transparency=SearchTransparency(
            generated_queries=5,
            retrieved_sources=20,
            deduplicated_sources=15,
            selected_sources=6,
        ),
    )

    assert answer.recommendations[0].confidence == 0.9
    assert answer.transparency.generated_queries == 5
