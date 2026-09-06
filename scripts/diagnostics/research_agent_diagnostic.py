import asyncio
import time

from google.adk.agents import SequentialAgent
from google.adk.runners import InMemoryRunner
from google.genai import types

from agents.healthcare_research.agent import healthcare_research_agent

USER_QUERY = {
    "text": (
        "Find three pediatric dentists in Houston for a child who is scared "
        "of going to the dentist. Compare them using trustworthy sources, "
        "provider credentials, services, and location, and explain why you "
        "selected each one."
    ),
    "location": "Houston, TX",
    "specialty": "Pediatric Dentistry",
    "intent": "provider_discovery",
}

SEARCH_PLAN = {
    "original_query": USER_QUERY,
    "intent": "provider_discovery",
    "generated_queries": [
        {
            "query": "pediatric dentists Houston TX",
            "purpose": "Identify pediatric dental practices in Houston.",
            "priority": 1,
        },
        {
            "query": (
                "pediatric dentist Houston dental anxiety "
                "nitrous oxide sedation"
            ),
            "purpose": "Find providers with anxiety-management context.",
            "priority": 1,
        },
        {
            "query": (
                "American Academy of Pediatric Dentistry "
                "find a dentist Houston Texas"
            ),
            "purpose": "Professional association directory context.",
            "priority": 2,
        },
        {
            "query": (
                "Texas State Board of Dental Examiners "
                "license verification dentist lookup"
            ),
            "purpose": "Official state licensing source.",
            "priority": 2,
        },
        {
            "query": (
                "pediatric dental anxiety nonpharmacological "
                "behavior guidance"
            ),
            "purpose": "Retrieve biomedical evidence.",
            "priority": 3,
        },
        {
            "query": (
                "pediatric dentistry nitrous oxide sedation systematic review"
            ),
            "purpose": "Retrieve clinical evidence.",
            "priority": 3,
        },
        {
            "query": (
                "FHIR PractitionerRole pediatric dentistry "
                "organization location interoperability"
            ),
            "purpose": "Explore FHIR interoperability structures.",
            "priority": 4,
        },
    ],
    "notes": "Isolated real Research Agent test.",
}

PLANNER_OUTPUT = {
    "user_query": USER_QUERY,
    "search_plan": SEARCH_PLAN,
}

root_agent = SequentialAgent(
    name="isolated_research_workflow",
    sub_agents=[healthcare_research_agent],
)


async def main():
    runner = InMemoryRunner(
        app_name="gemma_research_isolated_app",
        agent=root_agent,
    )

    session = await runner.session_service.create_session(
        app_name="gemma_research_isolated_app",
        user_id="test-user",
        session_id="isolated-research-session",
        state={
            "planner_output": PLANNER_OUTPUT,
        },
    )

    print("===== RUNNING REAL RESEARCH AGENT =====")

    started = time.perf_counter()

    message = types.Content(
        role="user",
        parts=[
            types.Part(
                text=(
                    "The search plan is already available in workflow state. "
                    "Execute the research step."
                )
            )
        ],
    )

    async for event in runner.run_async(
        user_id=session.user_id,
        session_id=session.id,
        new_message=message,
    ):
        if event.content:
            for part in event.content.parts or []:
                function_call = getattr(part, "function_call", None)
                function_response = getattr(part, "function_response", None)
                text = getattr(part, "text", None)

                if function_call:
                    print("\n===== FUNCTION CALL =====")
                    print("name:", function_call.name)
                    print("args:", function_call.args)

                if function_response:
                    print("\n===== FUNCTION RESPONSE =====")
                    print("name:", function_response.name)

                if text:
                    print("\n===== MODEL TEXT =====")
                    print(text)

    elapsed = time.perf_counter() - started

    final_session = await runner.session_service.get_session(
        app_name="gemma_research_isolated_app",
        user_id="test-user",
        session_id="isolated-research-session",
    )

    research_output = final_session.state.get("research_output")

    print("\n===== FINAL =====")
    print(f"elapsed_seconds: {elapsed:.2f}")

    if research_output:
        print(
            "retrieved_sources:",
            research_output.get("retrieved_sources"),
        )
        print(
            "deduplicated_sources:",
            research_output.get("deduplicated_sources"),
        )
        print(
            "search_results:",
            len(research_output.get("search_results", [])),
        )
    else:
        print("research_output: MISSING")


asyncio.run(main())
