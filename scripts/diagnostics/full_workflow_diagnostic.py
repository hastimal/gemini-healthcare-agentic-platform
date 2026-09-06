"""
Diagnostic: run the real three-agent healthcare workflow with the model
configured through MODEL_PROVIDER.

For v0.8 this is primarily used to validate Gemma/Ollama model portability
against the same production Google ADK workflow used by Gemini.

This script intentionally imports the production root_agent rather than
constructing a separate test architecture.

Workflow:

    User Question
        |
        v
    Search Planner Agent
        |
        v
    planner_output
        |
        v
    Healthcare Research Agent
        |
        v
    MCP -> NPPES / PubMed / FHIR
        |
        v
    research_output
        |
        v
    Evidence & Answer Agent
        |
        v
    answer_output
"""

from __future__ import annotations

import asyncio
import time

from google.adk.runners import InMemoryRunner
from google.genai import types

from agents.workflows.healthcare_workflow import root_agent
from app.config import get_settings

QUESTION = (
    "Find three pediatric dentists in Houston for a child who is scared "
    "of going to the dentist. Compare them using trustworthy sources, "
    "provider credentials, services, and location, and explain why you "
    "selected each one."
)

APP_NAME = "v08_model_portability_diagnostic"
USER_ID = "diagnostic-user"
SESSION_ID = "gemma-full-workflow"


def print_model_text(text: str) -> None:
    """Print model reasoning/output without dumping extremely large payloads."""

    max_chars = 2500

    print("\n===== MODEL TEXT =====")

    if len(text) <= max_chars:
        print(text)
        return

    print(text[:max_chars])
    print(f"\n... truncated {len(text) - max_chars} characters ...")


async def main() -> None:
    settings = get_settings()

    print("===== MODEL CONFIGURATION =====")
    print("MODEL_PROVIDER:", settings.model_provider)

    if settings.model_provider.strip().lower() == "gemma":
        print("GEMMA_MODEL:", settings.gemma_model)
        print("OLLAMA_BASE_URL:", settings.ollama_base_url)
    else:
        print("GEMINI_MODEL:", settings.gemini_model)

    print("\n===== PRODUCTION WORKFLOW =====")
    print("root_agent:", root_agent.name)

    sub_agents = getattr(root_agent, "sub_agents", [])

    for index, agent in enumerate(sub_agents, start=1):
        print(f"{index}. {agent.name}")

    runner = InMemoryRunner(
        app_name=APP_NAME,
        agent=root_agent,
    )

    session = await runner.session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )

    message = types.Content(
        role="user",
        parts=[
            types.Part(
                text=QUESTION,
            )
        ],
    )

    print("\n===== RUNNING FULL THREE-AGENT WORKFLOW =====")

    started = time.perf_counter()

    async for event in runner.run_async(
        user_id=session.user_id,
        session_id=session.id,
        new_message=message,
    ):
        author = getattr(event, "author", None)

        if author:
            print(f"\n----- EVENT AUTHOR: {author} -----")

        if not event.content:
            continue

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
                print_model_text(text)

    elapsed = time.perf_counter() - started

    final_session = await runner.session_service.get_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )

    state = final_session.state

    planner_output = state.get("planner_output")
    research_output = state.get("research_output")
    answer_output = state.get("answer_output")

    print("\n")
    print("=" * 72)
    print("FINAL WORKFLOW STATE")
    print("=" * 72)

    print(f"elapsed_seconds: {elapsed:.2f}")

    print("\n===== PLANNER OUTPUT =====")

    if isinstance(planner_output, dict):
        search_plan = planner_output.get("search_plan", {})

        generated_queries = (
            search_plan.get("generated_queries", [])
            if isinstance(search_plan, dict)
            else []
        )

        print("planner_output: PRESENT")
        print("generated_queries:", len(generated_queries))
    else:
        print("planner_output: MISSING")

    print("\n===== RESEARCH OUTPUT =====")

    if isinstance(research_output, dict):
        print("research_output: PRESENT")
        print(
            "retrieved_sources:",
            research_output.get("retrieved_sources"),
        )
        print(
            "deduplicated_sources:",
            research_output.get("deduplicated_sources"),
        )

        search_results = research_output.get("search_results", [])

        print(
            "search_results:",
            len(search_results)
            if isinstance(search_results, list)
            else "INVALID",
        )

        if isinstance(search_results, list):
            source_counts: dict[str, int] = {}

            for result in search_results:
                if not isinstance(result, dict):
                    continue

                source_type = str(
                    result.get("source_type", "unknown")
                )

                source_counts[source_type] = (
                    source_counts.get(source_type, 0) + 1
                )

            print("source_counts:", source_counts)
    else:
        print("research_output: MISSING")

    print("\n===== ANSWER OUTPUT =====")

    if isinstance(answer_output, dict):
        print("answer_output: PRESENT")
        print(
            "selected_evidence_count:",
            answer_output.get("selected_evidence_count"),
        )

        grounded_answer = answer_output.get("grounded_answer")

        if isinstance(grounded_answer, dict):
            print(
                "grounded_answer_keys:",
                sorted(grounded_answer.keys()),
            )

            print("\n===== FINAL GROUNDED ANSWER =====")
            print(
                grounded_answer.get(
                    "answer",
                    "<missing answer>",
                )
            )

            print("\n===== FINAL PROVIDER RECOMMENDATIONS =====")

            for index, recommendation in enumerate(
                grounded_answer.get("recommendations", []),
                start=1,
            ):
                print(f"\nProvider {index}")
                print("name:", recommendation.get("name"))
                print("location:", recommendation.get("location"))
                print(
                    "credentials:",
                    recommendation.get("credentials"),
                )
                print(
                    "services:",
                    recommendation.get("services"),
                )
                print(
                    "reasons_selected:",
                    recommendation.get("reasons_selected"),
                )

            print("\n===== FINAL CITATIONS =====")

            for citation in grounded_answer.get(
                "citations",
                [],
            ):
                print(
                    citation.get("citation_id"),
                    "|",
                    citation.get("source_name"),
                    "|",
                    citation.get("title"),
                )

            print("\n===== FINAL LIMITATIONS =====")

            for limitation in grounded_answer.get(
                "limitations",
                [],
            ):
                print("-", limitation)
        else:
            print(
                "grounded_answer_type:",
                type(grounded_answer).__name__,
            )
    else:
        print("answer_output: MISSING")

    print("\n===== DIAGNOSTIC RESULT =====")

    if (
        isinstance(planner_output, dict)
        and isinstance(research_output, dict)
        and isinstance(answer_output, dict)
    ):
        print("FULL_WORKFLOW_STATE_COMPLETE")
    else:
        print("FULL_WORKFLOW_STATE_INCOMPLETE")


if __name__ == "__main__":
    asyncio.run(main())
