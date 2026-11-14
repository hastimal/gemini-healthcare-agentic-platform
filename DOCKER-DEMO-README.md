# Docker Demo Runtime & Observability

## Purpose

v1.3 delivers complete local agent observability for the Gemini-powered healthcare agent application using Docker Compose.

The local stack includes:
- `healthcare-app` (Streamlit UI on port 8501)
- `otel-collector` (OpenTelemetry Collector on ports 4317 / 4318)
- `tempo` (Grafana Tempo distributed tracing backend on port 3200)
- `prometheus` (Prometheus metrics scraper on port 9090)
- `grafana` (Grafana visualization on port 3000)

> **Privacy-first observability**: Traces record operational metadata such as agent name, workflow stage, model name, counts, timing, retries, and errors. User questions, prompts, model responses, provider names, retrieved documents, grounded answers, patient data, and secrets are intentionally excluded from telemetry.

## Architecture

```text
User Request
    |
    v
Streamlit Healthcare UI :8501
    |
    v
Google ADK 3-Agent Workflow
    |
    +-- Search Planner Agent
    |      +-- Gemini model call
    |
    +-- Healthcare Research Agent
    |      +-- Gemini model call
    |      +-- MCP Provider Search -> NPPES
    |      +-- MCP PubMed Search -> PubMed
    |      +-- MCP FHIR Search -> FHIR R4
    |
    +-- Evidence & Answer Agent
           +-- Gemini model call
           +-- Evidence Ranking
           +-- Grounded Answer
    |
    v
OpenTelemetry SDK
    |
    v
OpenTelemetry Collector :4317 / :4318
    |
    +-- Tempo :3200 (traces)
    +-- Prometheus :9090 (metrics)
    +-- Grafana :3000 (Tempo + Prometheus datasources)
```

## Quick Start

### 1. Configure Gemini in `.env`

Ensure your `.env` contains:
```bash
GEMINI_API_KEY=<your-api-key>
GEMINI_MODEL=gemini-3.7-flash
MODEL_PROVIDER=gemini
```

### 2. Start the Full Stack

```bash
./scripts/demo-docker.sh
```
or
```bash
./scripts/demo-docker.sh gemini
```

All 5 services build, launch, and await health checks before announcing:
```text
============================================================
 Gemini Healthcare Agentic Platform READY
============================================================
 Healthcare UI: http://localhost:8501
 Grafana:       http://localhost:3000
 Prometheus:    http://localhost:9090
 Tempo:         http://localhost:3200

 Model: GEMINI
 Gemini model: <configured model>

 Logs:
 docker compose logs -f

 Stop:
 ./scripts/demo-docker-stop.sh
============================================================
```

### 3. Trace Exploration & Observability

1. Submit a query in the Streamlit UI at `http://localhost:8501`.
2. Observe the displayed `OpenTelemetry Trace ID`.
3. Open Grafana at `http://localhost:3000`:
   - Pre-configured dashboard: `http://localhost:3000/d/gemini-healthcare-agentic-observability`
   - Grafana Explore (Tempo traces & Prometheus metrics): `http://localhost:3000/explore`

> **Security Note:** `GF_AUTH_ANONYMOUS_ORG_ROLE=Editor` is enabled only for the localhost developer demo so Grafana Explore works without login. Do not use anonymous Editor access when Grafana is publicly exposed or deployed to a shared environment.

### 4. Stop the Stack

```bash
./scripts/demo-docker-stop.sh
```
