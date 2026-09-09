# OpenTelemetry Observability

The Gemini Healthcare Agentic Platform uses OpenTelemetry to provide
privacy-conscious tracing across the healthcare agent workflow.

## Current v1.3 tracing

This contribution adds tracing for the MCP-backed healthcare retrieval layer:

- `mcp.provider_search` - NPPES provider retrieval
- `mcp.pubmed_search` - PubMed biomedical literature retrieval
- `mcp.fhir_search` - FHIR interoperability retrieval

## Privacy

Tracing records operational metadata only.

Allowed examples:

- workflow stage
- healthcare intent
- retrieval source type
- retrieval result count
- evidence selected count
- MCP tool name
- retry count
- error type

The platform does not intentionally export:

- healthcare questions
- prompts
- model responses
- grounded answer text
- provider names
- retrieved documents
- API keys or secrets

## Local tracing

Tracing is disabled by default.

### PowerShell

```powershell
$env:OTEL_TRACING_ENABLED="true"
$env:OTEL_TRACES_EXPORTER="console"
```

### Bash

```bash
export OTEL_TRACING_ENABLED=true
export OTEL_TRACES_EXPORTER=console
```

The console exporter is useful for local development.

The tracing foundation also supports OTLP export for deployment environments.

## Architecture

```text
Healthcare Agent Workflow
        |
        v
MCP Retrieval Layer
        |
        +-- NPPES
        +-- PubMed
        +-- FHIR
        |
        v
OpenTelemetry Spans
        |
        v
OTLP Export
```

## Google Cloud

The next v1.3 integration stage connects OpenTelemetry tracing with:

- Gemini
- Google ADK
- Google Kubernetes Engine (GKE)
- Google Cloud Trace
- Google Cloud Monitoring
- Google Cloud Logging
