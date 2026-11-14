from __future__ import annotations

import asyncio
import uuid
from collections import Counter
from typing import Any

import streamlit as st
from google.adk.apps import App
from google.adk.runners import InMemoryRunner
from google.genai import types

from agents.workflows.healthcare_workflow import root_agent
from app.config import get_settings
from observability.adk_callbacks import PrivacySafeObservabilityPlugin
from observability.tracing import configure_tracing

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


def _query_texts(generated_queries: list[Any]) -> list[str]:
    output: list[str] = []

    for query in generated_queries:
        if isinstance(query, dict):
            output.append(
                str(
                    query.get("query")
                    or query.get("text")
                    or query
                )
            )
        else:
            output.append(str(query))

    return output


async def _run_workflow(question: str) -> dict[str, Any]:
    session_id = f"ui-{uuid.uuid4()}"

    configure_tracing()

    observability_plugin = PrivacySafeObservabilityPlugin()

    app = App(
        name=APP_NAME,
        root_agent=root_agent,
        plugins=[
            observability_plugin,
        ],
    )

    runner = InMemoryRunner(
        app=app,
    )

    session = await runner.session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=session_id,
    )

    message = types.Content(
        role="user",
        parts=[
            types.Part(
                text=question,
            )
        ],
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
                function_call = getattr(
                    part,
                    "function_call",
                    None,
                )

                function_response = getattr(
                    part,
                    "function_response",
                    None,
                )

                if function_call:
                    event_entry["function_calls"].append(
                        {
                            "name": function_call.name,
                            "args": function_call.args,
                        }
                    )

                if function_response:
                    event_entry["function_responses"].append(
                        {
                            "name": function_response.name,
                        }
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
        "trace_id": observability_plugin.trace_id,
    }


def _render_agent_workflow(
    research: dict[str, Any],
    answer_output: dict[str, Any],
    generated_queries: list[Any],
    search_results: list[dict[str, Any]],
) -> None:
    retrieved_count = research.get(
        "retrieved_sources",
        len(search_results),
    )

    unique_count = research.get(
        "deduplicated_sources",
        len(search_results),
    )

    selected_count = answer_output.get(
        "selected_evidence_count",
        0,
    )

    grounded = answer_output.get(
        "grounded_answer",
        {},
    ) or {}

    recommendation_count = (
        len(
            grounded.get(
                "recommendations",
                [],
            )
            or []
        )
        if isinstance(grounded, dict)
        else 0
    )

    st.subheader("Agent Workflow")

    st.caption(
        "Google ADK 3-Agent Workflow: planning, MCP retrieval, evidence ranking, and grounded synthesis."
    )

    with st.container(border=True):
        st.markdown(
            "**Google ADK 3-Agent Architecture:** "
            "`Search Planner Agent` ➔ `Healthcare Research Agent` ➔ `Evidence & Answer Agent` "
            "*(Evidence Ranking is an internal processing stage)*"
        )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        with st.container(border=True):
            st.markdown("### ① Search Planner Agent")

            st.success("Complete")

            st.metric(
                "Generated queries",
                len(generated_queries),
            )

            st.caption(
                "Plans searches and query fanout from the healthcare question."
            )

            query_texts = _query_texts(generated_queries)
            if query_texts:
                st.markdown("**Query Fan-Out**")
                for index, q in enumerate(query_texts, start=1):
                    st.markdown(f"`↳ {index}` {q}")

    with col2:
        with st.container(border=True):
            st.markdown("### ② Healthcare Research Agent")

            st.success("Complete")

            st.metric(
                "Retrieved",
                retrieved_count,
            )

            st.caption(
                "Executes MCP-backed retrieval across NPPES, PubMed, and FHIR R4."
            )

    with col3:
        with st.container(border=True):
            st.markdown("### ③ Evidence Ranking")

            st.info("Stage")

            st.metric(
                "Selected",
                selected_count,
            )

            st.caption(
                f"{unique_count} unique sources scored/selected (internal stage, not an agent)."
            )

    with col4:
        with st.container(border=True):
            st.markdown("### ④ Evidence & Answer Agent")

            st.success("Complete")

            st.metric(
                "Recommendations",
                recommendation_count,
            )

            st.caption(
                "Produces grounded answer with citations and explicit limitations."
            )

    with st.expander("See workflow details"):
        st.markdown("**Search Planner Agent**")

        query_texts = _query_texts(
            generated_queries
        )

        if query_texts:
            for index, query in enumerate(
                query_texts,
                start=1,
            ):
                st.write(
                    f"{index}. {query}"
                )
        else:
            st.write(
                "No generated queries were returned."
            )

        st.divider()

        st.markdown(
            "**Healthcare Research Agent**"
        )

        counts = _source_counts(
            search_results
        )

        if counts:
            st.write(
                "Retrieved sources: "
                + ", ".join(
                    f"{source_type.upper()}={count}"
                    for source_type, count
                    in sorted(counts.items())
                )
            )
        else:
            st.write(
                "No retrieved source counts were available."
            )

        st.divider()

        st.markdown(
            "**Evidence Ranking**"
        )

        st.write(
            f"Unique evidence: **{unique_count}**"
        )

        st.write(
            f"Selected evidence: **{selected_count}**"
        )

        st.divider()

        st.markdown(
            "**Evidence & Answer Agent**"
        )

        st.write(
            "Grounded answer generated "
            "from selected evidence."
        )


def _render_recommendations(
    grounded: dict[str, Any],
) -> None:
    recommendations = (
        grounded.get(
            "recommendations",
            [],
        )
        or []
    )

    if not recommendations:
        st.info(
            "No provider recommendations were returned."
        )
        return

    for index, recommendation in enumerate(
        recommendations,
        start=1,
    ):
        name = (
            recommendation.get("name")
            or f"Candidate {index}"
        )

        with st.container(border=True):
            st.subheader(
                f"{index}. {name}"
            )

            location = recommendation.get(
                "location"
            )

            if location:
                st.write(
                    f"**Location:** {location}"
                )

            reasons = (
                recommendation.get(
                    "reasons_selected"
                )
                or []
            )

            if reasons:
                st.write(
                    "**Why selected from the "
                    "available evidence:**"
                )

                for reason in reasons:
                    st.write(
                        f"- {reason}"
                    )

            credentials = (
                recommendation.get(
                    "credentials"
                )
                or []
            )

            if credentials:
                st.write(
                    "**Evidence-backed credentials:**"
                )

                for item in credentials:
                    st.write(
                        f"- {item}"
                    )

            services = (
                recommendation.get(
                    "services"
                )
                or []
            )

            if services:
                st.write(
                    "**Evidence-backed services:**"
                )

                for item in services:
                    st.write(
                        f"- {item}"
                    )


def _render_citations(
    grounded: dict[str, Any],
) -> None:
    citations = (
        grounded.get(
            "citations",
            [],
        )
        or []
    )

    if not citations:
        st.info(
            "No citations were returned."
        )
        return

    for citation in citations:
        citation_id = citation.get(
            "citation_id",
            "C?",
        )

        source_name = citation.get(
            "source_name",
            "Unknown source",
        )

        title = citation.get(
            "title",
            "Untitled",
        )

        url = citation.get(
            "url"
        )

        with st.container(border=True):
            st.markdown(
                f"**{citation_id} — {source_name}**"
            )

            st.write(
                title
            )

            if url:
                st.markdown(
                    f"[Open source]({url})"
                )


def _render_results(
    result: dict[str, Any],
    provider: str,
) -> None:
    planner = (
        result.get(
            "planner_output"
        )
        or {}
    )

    research = (
        result.get(
            "research_output"
        )
        or {}
    )

    answer_output = (
        result.get(
            "answer_output"
        )
        or {}
    )

    search_plan = (
        planner.get(
            "search_plan",
            {},
        )
        if isinstance(
            planner,
            dict,
        )
        else {}
    )

    generated_queries = (
        search_plan.get(
            "generated_queries",
            [],
        )
        if isinstance(
            search_plan,
            dict,
        )
        else []
    )

    search_results = (
        research.get(
            "search_results",
            [],
        )
        if isinstance(
            research,
            dict,
        )
        else []
    )

    if not isinstance(
        search_results,
        list,
    ):
        search_results = []

    grounded = (
        answer_output.get(
            "grounded_answer",
            {},
        )
        if isinstance(
            answer_output,
            dict,
        )
        else {}
    )

    if not isinstance(
        grounded,
        dict,
    ):
        grounded = {}

    _render_agent_workflow(
        research=(
            research
            if isinstance(
                research,
                dict,
            )
            else {}
        ),
        answer_output=(
            answer_output
            if isinstance(
                answer_output,
                dict,
            )
            else {}
        ),
        generated_queries=generated_queries,
        search_results=search_results,
    )

    st.divider()

    counts = _source_counts(
        search_results
    )

    metric_cols = st.columns(5)

    metric_cols[0].metric(
        "Queries",
        len(generated_queries),
    )

    metric_cols[1].metric(
        "Retrieved",
        research.get(
            "retrieved_sources",
            len(search_results),
        )
        if isinstance(
            research,
            dict,
        )
        else len(search_results),
    )

    metric_cols[2].metric(
        "Unique",
        research.get(
            "deduplicated_sources",
            len(search_results),
        )
        if isinstance(
            research,
            dict,
        )
        else len(search_results),
    )

    metric_cols[3].metric(
        "Selected",
        answer_output.get(
            "selected_evidence_count",
            0,
        )
        if isinstance(
            answer_output,
            dict,
        )
        else 0,
    )

    metric_cols[4].metric(
        "Model",
        provider.upper(),
    )

    (
        answer_tab,
        plan_tab,
        evidence_tab,
        citations_tab,
        transparency_tab,
    ) = st.tabs(
        [
            "Grounded Answer",
            "Search Plan",
            "Evidence",
            "Citations",
            "Transparency",
        ]
    )

    with answer_tab:
        answer_text = grounded.get(
            "answer"
        )

        if answer_text:
            st.markdown(
                answer_text
            )
        else:
            st.info(
                "No final answer text was returned."
            )

        st.divider()

        st.subheader(
            "Provider Candidates"
        )

        _render_recommendations(
            grounded
        )

    with plan_tab:
        st.subheader(
            "Generated Search Queries"
        )

        query_texts = _query_texts(
            generated_queries
        )

        if query_texts:
            for index, query in enumerate(
                query_texts,
                start=1,
            ):
                st.write(
                    f"{index}. {query}"
                )
        else:
            st.info(
                "No generated queries were found."
            )

        with st.expander(
            "Planner output JSON"
        ):
            st.json(
                planner
            )

    with evidence_tab:
        st.subheader(
            "Retrieved Evidence"
        )

        # Keep complete research state
        # available for transparent demos
        # and end-to-end acceptance testing.
        with st.expander(
            "Research output JSON"
        ):
            st.json(
                research
            )

        cols = st.columns(
            max(
                1,
                min(
                    3,
                    len(counts) or 1,
                ),
            )
        )

        for index, (
            source_type,
            count,
        ) in enumerate(
            sorted(
                counts.items()
            )
        ):
            cols[
                index % len(cols)
            ].metric(
                source_type.upper(),
                count,
            )

        for item in search_results:
            if not isinstance(
                item,
                dict,
            ):
                continue

            with st.expander(
                f"{str(item.get('source_type', 'unknown')).upper()} — "
                f"{item.get('title', 'Untitled evidence')}"
            ):
                st.json(
                    item
                )

    with citations_tab:
        st.subheader(
            "Selected Citations"
        )

        _render_citations(
            grounded
        )

    with transparency_tab:
        st.subheader(
            "Limitations"
        )

        limitations = (
            grounded.get(
                "limitations",
                [],
            )
            or []
        )

        if limitations:
            for limitation in limitations:
                st.warning(
                    limitation
                )
        else:
            st.info(
                "No limitations were returned."
            )

        transparency = grounded.get(
            "transparency"
        )

        if transparency:
            st.subheader(
                "Search Transparency"
            )

            st.json(
                transparency
            )

        with st.expander(
            "Google ADK event trace"
        ):
            st.json(
                result.get(
                    "event_log",
                    [],
                )
            )

        with st.expander(
            "Final answer output JSON"
        ):
            st.json(
                answer_output
            )

    _render_agentops_section(result=result)


def _render_agentops_section(result: dict[str, Any] | None = None) -> None:
    st.divider()

    st.subheader("#5 — AgentOps / Observability")

    st.caption(
        "Local agent telemetry pipeline powered by OpenTelemetry, Tempo, Prometheus, and Grafana."
    )

    with st.container(border=True):
        st.markdown("### Google ADK 3-Agent Workflow")

        st.markdown(
            """
```text
Google ADK Agent Workflow

Search Planner Agent (plan & query fanout)
        ↓
Healthcare Research Agent (MCP retrieval: NPPES, PubMed, FHIR R4)
        ↓
Evidence & Answer Agent (evidence ranking & grounded answer)
```
            """
        )

        st.caption(
            "Evidence Ranking is an internal processing stage inside Evidence & Answer, not a fourth agent."
        )

    trace_id = (result.get("trace_id") if result else None)

    col_trace, col_pipeline = st.columns(2)

    with col_trace:
        with st.container(border=True):
            st.markdown("### Current Trace")
            if trace_id:
                st.success(f"**OpenTelemetry Trace ID:** `{trace_id}`")
                st.caption("Exact trace recorded in Tempo and discoverable in Grafana.")
            else:
                st.info("Run a healthcare research query above to generate and inspect a live trace.")

    with col_pipeline:
        with st.container(border=True):
            st.markdown("### Telemetry Flow")
            st.markdown(
                """
```text
Google ADK ➔ OpenTelemetry ➔ OTel Collector (:4317/:4318)
                               ├── Tempo (:3200) -> traces
                               ├── Prometheus (:9090) -> metrics
                               └── Grafana (:3000) -> dashboards
```
                """
            )

    st.markdown(
        "> **Google ADK UI** provides local agent debugging and event inspection. "
        "**Grafana, Tempo, and Prometheus** provide privacy-safe operational observability "
        "through the project's sanitized OpenTelemetry pipeline."
    )

    dev_col, obs_col = st.columns([1, 2])

    with dev_col:
        with st.container(border=True):
            st.markdown("#### Agent Development")
            st.caption("Local debugging, session state, and step inspection.")
            st.link_button(
                "🛠️ Open Google ADK UI",
                url="http://localhost:8080",
                use_container_width=True,
                help="Google ADK Web UI / Agent Playground",
            )

    with obs_col:
        with st.container(border=True):
            st.markdown("#### AgentOps / Observability")
            st.caption("Privacy-safe operational metrics, dashboards, and distributed traces.")
            obs_row1_col1, obs_row1_col2 = st.columns(2)
            with obs_row1_col1:
                st.link_button(
                    "📊 Grafana Dashboard",
                    url="http://localhost:3000/d/gemini-healthcare-agentic-observability",
                    use_container_width=True,
                    help="Pre-configured local agent observability dashboard",
                )
            with obs_row1_col2:
                st.link_button(
                    "🔬 Explore Traces & Metrics",
                    url="http://localhost:3000/explore",
                    use_container_width=True,
                    help="Grafana Explore view for Tempo traces and Prometheus metrics",
                )

            obs_row2_col1, obs_row2_col2 = st.columns(2)
            with obs_row2_col1:
                st.link_button(
                    "📈 Prometheus",
                    url="http://localhost:9090",
                    use_container_width=True,
                    help="Prometheus operational metrics scraper",
                )
            with obs_row2_col2:
                st.link_button(
                    "🔍 Tempo Health",
                    url="http://localhost:3200/ready",
                    use_container_width=True,
                    help="Distributed trace storage health endpoint (use Grafana Explore to inspect traces)",
                )

    with st.expander("Collector Details & Privacy Boundaries"):
        st.markdown(
            """
**OpenTelemetry Collector Ports:**
- `4318` (OTLP HTTP) — primary application telemetry ingest
- `4317` (OTLP gRPC) — secondary gRPC ingest
- `8888` / `8889` — collector telemetry & pipeline Prometheus scrape endpoints

**Privacy-Safe Observability:**
- User healthcare questions, prompts, system instructions, and grounded answers are **never exported**.
- Model responses, provider names, retrieved documents, FHIR patient data, and API keys are **never exported**.
- Only operational metadata (agent lifecycle, model name, tokens, duration, status, result counts) is exported through `PrivacySafeSpanExporter`.
            """
        )


def main() -> None:
    st.set_page_config(
        page_title=(
            "Beyond RAG — "
            "Healthcare Agentic AI"
        ),
        page_icon="🩺",
        layout="wide",
    )

    settings = get_settings()

    provider = (
        settings.model_provider
        .strip()
        .lower()
    )

    st.title(
        "Beyond RAG — Agentic Healthcare Search"
    )

    st.caption(
        "Google ADK • Gemini / Gemma • MCP • "
        "NPPES • PubMed • FHIR • Grounded citations"
    )

    with st.sidebar:
        st.header(
            "Demo Runtime"
        )

        st.metric(
            "Model provider",
            provider.upper(),
        )

        if provider == "gemma":
            st.write(
                f"**Model:** "
                f"`{settings.gemma_model or 'not configured'}`"
            )

            st.write(
                f"**Ollama:** "
                f"`{settings.ollama_base_url}`"
            )

        else:
            st.write(
                f"**Model:** "
                f"`{settings.gemini_model or 'not configured'}`"
            )

        st.divider()

        st.write(
            "**Three-agent workflow**"
        )

        st.write(
            "1. Search Planner Agent"
        )

        st.write(
            "2. Healthcare Research Agent"
        )

        st.write(
            "3. Evidence & Answer Agent"
        )

        st.divider()

        st.caption(
            "Evidence Ranking is a processing stage "
            "between research and final synthesis. "
            "Provider discovery is evidence-restricted; "
            "NPPES, PubMed, and public FHIR test data "
            "have different authority boundaries."
        )

    question = st.text_area(
        "Healthcare research question",
        value=DEFAULT_QUESTION,
        height=130,
    )

    if st.button(
        "Run 3-Agent Research",
        type="primary",
        use_container_width=True,
    ):
        if not question.strip():
            st.warning(
                "Enter a healthcare research question."
            )
            return

        with st.status(
            "Running Google ADK workflow...",
            expanded=True,
        ) as status:

            st.write(
                "① Search Planner Agent "
                "→ creating research plan"
            )

            st.write(
                "② Healthcare Research Agent "
                "→ invoking MCP-backed retrieval"
            )

            st.write(
                "③ Evidence Ranking "
                "→ scoring and selecting evidence"
            )

            st.write(
                "④ Evidence & Answer Agent "
                "→ generating grounded answer"
            )

            try:
                result = asyncio.run(
                    _run_workflow(
                        question.strip()
                    )
                )

            except Exception as exc:
                status.update(
                    label="Workflow failed",
                    state="error",
                )

                st.exception(
                    exc
                )

                return

            status.update(
                label="Workflow complete",
                state="complete",
            )

        st.session_state[
            "workflow_result"
        ] = result

        st.session_state[
            "workflow_question"
        ] = question.strip()

    result = st.session_state.get(
        "workflow_result"
    )

    if isinstance(
        result,
        dict,
    ):
        st.divider()

        completed_question = (
            st.session_state.get(
                "workflow_question"
            )
        )

        if completed_question:
            st.caption(
                "Completed research question: "
                f"{completed_question}"
            )

        trace_id = result.get("trace_id")
        if trace_id:
            st.caption(
                f"OpenTelemetry Trace ID: `{trace_id}`"
            )

        _render_results(
            result=result,
            provider=provider,
        )
    else:
        _render_agentops_section(result=None)


if __name__ == "__main__":
    main()
