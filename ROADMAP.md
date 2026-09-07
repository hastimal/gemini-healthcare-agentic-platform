# Roadmap

```text
v0.1  Gemini query planning + query fan-out
v0.2  NPPES + PubMed retrieval
v0.3  Evidence scoring + ranking
v0.4  Grounded answers + deterministic citations
v0.5  Google ADK three-agent architecture
v0.6  MCP healthcare tool layer
v0.7  FHIR R4 interoperability
v0.8  Gemini + Gemma / Ollama portability
v0.9  Generalized Query Planning + Dynamic Retrieval + GUI
v1.0  Dockerized Reproducible Demo Runtime
v1.1  Evaluation Benchmark
v1.2  Kubernetes / GKE
v1.3  OpenTelemetry
v1.4  Security
v2.0  Reusable Agentic Healthcare Framework
```

## Completed: v1.1

**Evaluation Benchmark**

v1.1 adds a frozen 11-case Core Acceptance Benchmark around the accepted healthcare agent workflow and keeps deterministic application correctness separate from model/runtime variability.

Measured first-run acceptance:

```text
Gemini 3.7 Flash: 11 / 11 core cases
  - 9 / 9 supported workflow completions
  - 2 / 2 expected unsupported boundaries

Gemma 4 12B + local Ollama: 10 / 11 core cases
  - 8 / 9 supported workflow completions
  - 2 / 2 expected unsupported boundaries
  - 1 preserved FHIR PractitionerRole timeout
```

The benchmark evaluates retrieval presence, required source types, citation integrity, claim support, provider evidence authority, FHIR provider-recommendation boundaries, candidate-count expectations, and forbidden provider claims. Latency is retained as runtime diagnostic data rather than a model-superiority claim.

## Next: v1.2

**Kubernetes / GKE**

Deploy the accepted application runtime to Kubernetes / GKE with reproducible configuration, health checks, scaling boundaries, secret handling, and deploy/destroy workflows.
