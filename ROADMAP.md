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

## Completed: v1.0

**Dockerized Reproducible Demo Runtime**

v1.0 packages the accepted v0.9 application into a reproducible Docker runtime while preserving the local runtime and existing healthcare evidence semantics.

Validated paths:

```text
Local  -> Gemini
Local  -> Gemma / Ollama
Docker -> Gemini
Docker -> Gemma / native Ollama on macOS
```

The Docker Gemma path uses `host.docker.internal:11434` to reach native Ollama on macOS.

## Next: v1.1

**Evaluation Benchmark**

Add repeatable evaluation around supported workflows while keeping deterministic application correctness separate from model/runtime variability.
