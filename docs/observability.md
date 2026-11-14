# OpenTelemetry Observability

The Gemini Healthcare Agentic Platform uses OpenTelemetry to provide
privacy-conscious tracing and operational metrics across the healthcare agent workflow.

> **Privacy-first observability**: Traces record operational metadata such as agent name, workflow stage, model name, counts, timing, retries, and errors. User questions, prompts, model responses, provider names, retrieved documents, grounded answers, patient data, and secrets are intentionally excluded from telemetry.

## Architecture

```text
User Request
    |
    v
Streamlit Healthcare UI :8501
    |
    v
OpenTelemetry Workflow Trace
    |
    +-- Google ADK: Search Planner Agent
    |      |
    |      +-- Gemini Model Call
    |
    +-- Google ADK: Healthcare Research Agent
    |      |
    |      +-- Gemini Model Call
    |      |
    |      +-- MCP Provider Search -> NPPES
    |      +-- MCP PubMed Search -> PubMed
    |      +-- MCP FHIR Search -> FHIR R4
    |
    +-- Google ADK: Evidence & Answer Agent
           |
           +-- Gemini Model Call
           +-- Evidence Ranking
           +-- Grounded Answer
    |
    v
OpenTelemetry Collector :4317 / :4318
    |
    +-- Tempo :3200 -> traces
    +-- Prometheus :9090 -> metrics
    +-- Grafana :3000 -> dashboards
```

## Trace Structure

- `workflow.gemini_healthcare_agentic_platform`: Top-level workflow trace containing the overall execution lifecycle.
- `adk.agent.<agent_name>`: Google ADK agent lifecycle spans for:
  - `search_planner_agent`
  - `healthcare_research_agent`
  - `evidence_answer_agent`
- `gen_ai.model`: Sanitized Gemini model call spans recording model name, token counts, and latency without prompts or responses.
- `mcp.provider_search`: NPPES healthcare provider search tool span.
- `mcp.pubmed_search`: PubMed biomedical literature retrieval tool span.
- `mcp.fhir_search`: FHIR interoperability retrieval tool span.

Note: Evidence ranking is a processing stage inside the Evidence & Answer Agent, not a fourth agent.

## Privacy Boundary and Sanitization

Google ADK and OpenTelemetry SDKs can emit attributes containing raw inputs and outputs.
To protect patient privacy and comply with healthcare standards:

1. `PrivacySafeSpanExporter`: Wraps exporters to sanitize all spans before export. Any forbidden attributes such as `gcp.vertex.agent.llm_request`, `gcp.vertex.agent.llm_response`, `gcp.vertex.agent.tool_call_args`, and `gcp.vertex.agent.tool_response` are stripped.
2. `PrivacySafeObservabilityPlugin`: Custom ADK plugin replacing `AutoTracingPlugin` to ensure prompt texts, grounded answers, provider names, and FHIR payloads are never captured.
3. Telemetry only exports whitelisted operational metadata keys (`workflow.name`, `workflow.stage`, `agent.name`, `gen_ai.model.name`, `gen_ai.model.provider`, `healthcare.intent`, `retrieval.source_type`, `retrieval.result_count`, `evidence.selected_count`, `mcp.tool.name`, `retry.count`, `error.type`).

## Local Observability Stack

The entire observability stack runs locally via Docker Compose:

- **OpenTelemetry Collector** (`:4317` gRPC, `:4318` HTTP): Receives OTLP telemetry from `healthcare-app`, batches traces, exports to Tempo, and provides scrape targets for Prometheus.
- **Grafana Tempo** (`:3200`): Local trace store retaining traces in local volumes.
- **Prometheus** (`:9090`): Collects collector telemetry and operational metrics.
- **Grafana** (`:3000`): Pre-provisioned with Tempo and Prometheus datasources and the pre-built dashboard: **Gemini Healthcare Agentic Platform — Local Agent Observability**. Anonymous access is enabled for seamless local inspection.

### Running the Stack

```bash
./scripts/demo-docker.sh
```

Stop with:

```bash
./scripts/demo-docker-stop.sh
```
