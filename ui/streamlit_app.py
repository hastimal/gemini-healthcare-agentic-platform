from __future__ import annotations

import asyncio
import uuid
from collections import Counter
from typing import Any

import streamlit as st
from google.adk.runners import InMemoryRunner
from google.genai import types

from agents.workflows.healthcare_workflow import root_agent
from app.config import get_settings

DEFAULT_QUESTION = (
    "Find three pediatric dentists in Houston for a child who is scared "
    "of going to the dentist. Compare them using trustworthy sources, "
    "provider credentials, services, and location, and explain why you "
    "selected each one."
)

APP_NAME = "healthcare_agentic_streamlit_demo"
USER_ID = "streamlit-demo-user"


def _source_counts(search_results: list[dict[str, Any]]) -> Counter:
    counts: Counter = Counter()
    for result in search_results:
        if isinstance(result, dict):
            counts[str(result.get("source_type", "unknown"))] += 1
    return counts


async def _run_workflow(question: str) -> dict[str, Any]:
    session_id = f"ui-{uuid.uuid4()}"
    runner = InMemoryRunner(app_name=APP_NAME, agent=root_agent)

    session = await runner.session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=session_id,
    )

    message = types.Content(
        role="user",
        parts=[types.Part(text=question)],
    )

    event_log: list[dict[str, Any]] = []

    async for event in runner.run_async(
        user_id=session.user_id,
        session_id=session.id,
        new_message=message,
    ):
        event_entry: dict[str, Any] = {
            "author": getattr(event, "author", None),
            "function_calls": [],
            "function_responses": [],
        }

        if event.content:
            for part in event.content.parts or []:
                function_call = getattr(part, "function_call", None)
                function_response = getattr(part, "function_response", None)

                if function_call:
                    event_entry["function_calls"].append(
                        {
                            "name": function_call.name,
                            "args": function_call.args,
                        }
                    )

                if function_response:
                    event_entry["function_responses"].append(
                        {"name": function_response.name}
                    )

        if (
            event_entry["author"]
            or event_entry["function_calls"]
            or event_entry["function_responses"]
        ):
            event_log.append(event_entry)

    final_session = await runner.session_service.get_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=session.id,
    )

    state = final_session.state or {}

    return {
        "planner_output": state.get("planner_output"),
        "research_output": state.get("research_output"),
        "answer_output": state.get("answer_output"),
        "event_log": event_log,
    }


def _render_recommendations(grounded: dict[str, Any]) -> None:
    recommendations = grounded.get("recommendations", []) or []
    if not recommendations:
        st.info("No provider recommendations were returned.")
        return

    for index, recommendation in enumerate(recommendations, start=1):
        name = recommendation.get("name") or f"Candidate {index}"
        with st.container(border=True):
            st.subheader(f"{index}. {name}")
            location = recommendation.get("location")
            if location:
                st.write(f"**Location:** {location}")

            reasons = recommendation.get("reasons_selected") or []
            if reasons:
                st.write("**Why selected from the available evidence:**")
                for reason in reasons:
                    st.write(f"- {reason}")

            credentials = recommendation.get("credentials") or []
            services = recommendation.get("services") or []

            if credentials:
                st.write("**Evidence-backed credentials:**")
                for item in credentials:
                    st.write(f"- {item}")

            if services:
                st.write("**Evidence-backed services:**")
                for item in services:
                    st.write(f"- {item}")


def _render_citations(grounded: dict[str, Any]) -> None:
    citations = grounded.get("citations", []) or []
    if not citations:
        st.info("No citations were returned.")
        return

    for citation in citations:
        citation_id = citation.get("citation_id", "C?")
        source_name = citation.get("source_name", "Unknown source")
        title = citation.get("title", "Untitled")
        url = citation.get("url")

        with st.container(border=True):
            st.markdown(f"**{citation_id} — {source_name}**")
            st.write(title)
            if url:
                st.markdown(f"[Open source]({url})")


def main() -> None:
    st.set_page_config(
        page_title="Beyond RAG — Healthcare Agentic AI",
        page_icon="🩺",
        layout="wide",
    )

    settings = get_settings()
    provider = settings.model_provider.strip().lower()

    st.title("Beyond RAG — Agentic Healthcare Search")
    st.caption(
        "Google ADK • Gemini / Gemma • MCP • NPPES • PubMed • FHIR • "
        "Grounded citations"
    )

    with st.sidebar:
        st.header("Demo Runtime")
        st.metric("Model provider", provider.upper())

        if provider == "gemma":
            st.write(f"**Model:** `{settings.gemma_model or 'not configured'}`")
            st.write(f"**Ollama:** `{settings.ollama_base_url}`")
        else:
            st.write(f"**Model:** `{settings.gemini_model or 'not configured'}`")

        st.divider()
        st.write("**Three-agent workflow**")
        st.write("1. Search Planner Agent")
        st.write("2. Healthcare Research Agent")
        st.write("3. Evidence & Answer Agent")

        st.divider()
        st.caption(
            "Provider discovery is evidence-restricted. NPPES, PubMed, and "
            "public FHIR test data have different authority boundaries."
        )

    question = st.text_area(
        "Healthcare research question",
        value=DEFAULT_QUESTION,
        height=130,
    )

    if st.button("Run 3-Agent Research", type="primary", use_container_width=True):
        if not question.strip():
            st.warning("Enter a healthcare research question.")
            return

        with st.status("Running Google ADK workflow...", expanded=True) as status:
            st.write("Search Planner Agent → creating research plan")
            st.write("Healthcare Research Agent → invoking MCP-backed retrieval")
            st.write("Evidence & Answer Agent → ranking and grounding evidence")

            try:
                result = asyncio.run(_run_workflow(question.strip()))
            except Exception as exc:
                status.update(label="Workflow failed", state="error")
                st.exception(exc)
                return

            status.update(label="Workflow complete", state="complete")

        planner = result.get("planner_output") or {}
        research = result.get("research_output") or {}
        answer_output = result.get("answer_output") or {}

        search_plan = (
            planner.get("search_plan", {})
            if isinstance(planner, dict)
            else {}
        )
        generated_queries = (
            search_plan.get("generated_queries", [])
            if isinstance(search_plan, dict)
            else []
        )

        search_results = (
            research.get("search_results", [])
            if isinstance(research, dict)
            else []
        )
        if not isinstance(search_results, list):
            search_results = []

        grounded = (
            answer_output.get("grounded_answer", {})
            if isinstance(answer_output, dict)
            else {}
        )
        if not isinstance(grounded, dict):
            grounded = {}

        counts = _source_counts(search_results)

        metric_cols = st.columns(5)
        metric_cols[0].metric("Queries", len(generated_queries))
        metric_cols[1].metric(
            "Retrieved",
            research.get("retrieved_sources", len(search_results))
            if isinstance(research, dict)
            else len(search_results),
        )
        metric_cols[2].metric(
            "Unique",
            research.get("deduplicated_sources", len(search_results))
            if isinstance(research, dict)
            else len(search_results),
        )
        metric_cols[3].metric(
            "Selected",
            answer_output.get("selected_evidence_count", 0)
            if isinstance(answer_output, dict)
            else 0,
        )
        metric_cols[4].metric("Model", provider.upper())

        answer_tab, plan_tab, evidence_tab, citations_tab, transparency_tab = st.tabs(
            [
                "Grounded Answer",
                "Search Plan",
                "Evidence",
                "Citations",
                "Transparency",
            ]
        )

        with answer_tab:
            answer_text = grounded.get("answer")
            if answer_text:
                st.markdown(answer_text)
            else:
                st.info("No final answer text was returned.")

            st.divider()
            st.subheader("Provider Candidates")
            _render_recommendations(grounded)

        with plan_tab:
            st.subheader("Generated Search Queries")
            if generated_queries:
                for index, query in enumerate(generated_queries, start=1):
                    if isinstance(query, dict):
                        query_text = (
                            query.get("query")
                            or query.get("text")
                            or str(query)
                        )
                    else:
                        query_text = str(query)
                    st.write(f"{index}. {query_text}")
            else:
                st.info("No generated queries were found.")

            with st.expander("Planner output JSON"):
                st.json(planner)

        with evidence_tab:
            st.subheader("Retrieved Evidence")

            # Expose the complete research state for transparent demos
            # and end-to-end acceptance testing.
            with st.expander("Research output JSON"):
                st.json(research)

            cols = st.columns(max(1, min(3, len(counts) or 1)))
            for index, (source_type, count) in enumerate(sorted(counts.items())):
                cols[index % len(cols)].metric(source_type.upper(), count)

            for item in search_results:
                if not isinstance(item, dict):
                    continue
                with st.expander(
                    f"{str(item.get('source_type', 'unknown')).upper()} — "
                    f"{item.get('title', 'Untitled evidence')}"
                ):
                    st.json(item)

        with citations_tab:
            st.subheader("Selected Citations")
            _render_citations(grounded)

        with transparency_tab:
            st.subheader("Limitations")
            limitations = grounded.get("limitations", []) or []
            if limitations:
                for limitation in limitations:
                    st.warning(limitation)
            else:
                st.info("No limitations were returned.")

            transparency = grounded.get("transparency")
            if transparency:
                st.subheader("Search Transparency")
                st.json(transparency)

            with st.expander("Google ADK event trace"):
                st.json(result.get("event_log", []))

            with st.expander("Final answer output JSON"):
                st.json(answer_output)


if __name__ == "__main__":
    main()
