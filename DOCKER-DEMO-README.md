# Docker Demo Runtime

## Purpose

v1.0 packages the accepted healthcare agent application into a reproducible Docker runtime while preserving the existing local execution path.

Docker is an additional runtime option. It does not change the three-agent Google ADK architecture, MCP retrieval layer, evidence ranking, citations, or healthcare grounding rules.

## Architecture

```text
Gemini

Browser
   |
   v
Docker healthcare-app :8501
   |
   v
Google ADK
   |
   v
Gemini API


Gemma on macOS

Browser
   |
   v
Docker healthcare-app :8501
   |
   v
Google ADK
   |
   v
LiteLLM
   |
   v
host.docker.internal:11434
   |
   v
Native Ollama
   |
   v
Gemma
```

## Prerequisites

For both paths:

- Docker Desktop is installed and running.
- `.env` exists locally.
- port `8501` is available, or `DEMO_PORT` is set to another host port.

For Gemini:

- `GEMINI_API_KEY` is configured locally.
- `GEMINI_MODEL` is configured.

For Gemma on macOS:

- Ollama is running natively on macOS.
- the configured `GEMMA_MODEL` is installed.
- Ollama is reachable at `http://localhost:11434`.

## Run

Gemini:

```bash
./scripts/demo-docker.sh gemini
```

Gemma:

```bash
./scripts/demo-docker.sh gemma
```

Open:

```text
http://localhost:8501
```

Stop:

```bash
./scripts/demo-docker-stop.sh
```

## Validation

Validate Compose without printing expanded environment values:

```bash
docker compose config --quiet
```

Check container health:

```bash
docker compose ps
curl -fsS http://localhost:8501/_stcore/health && echo
```

Run the deterministic suite:

```bash
python -m pytest -q
git diff --check
```

v1.0 deterministic checkpoint:

```text
85 passed, 5 skipped, 1 dependency warning
```

The known OpenTelemetry deprecation warning is non-blocking.

## Secrets

`.env` is excluded from the Docker build context by `.dockerignore`.

Do not commit `.env`.

Prefer:

```bash
docker compose config --quiet
```

instead of plain `docker compose config`, because the non-quiet command can print expanded environment values.

## Existing Local Runtime

The existing local runtime remains supported:

```bash
./scripts/demo-local.sh gemini
./scripts/demo-local.sh gemma
./scripts/demo-stop.sh
```

## Healthcare Safety Boundary

Containerization does not change source authority:

```text
NPPES -> provider registry identity / NPI / taxonomy / reported location
PubMed -> general biomedical evidence
FHIR  -> interoperability evidence
```

Docker does not establish provider quality, active licensure, board certification, good standing, service availability, clinical validity, HIPAA compliance, or PHI safety.

> **No evidence -> no claim.**

## Common Failures

### Docker credential helper not found

If Docker Desktop is installed but Docker reports `docker-credential-desktop` is missing, verify that Docker Desktop's CLI directory is available on `PATH`.

### Ollama port already in use

```text
listen tcp 127.0.0.1:11434: bind: address already in use
```

This usually means Ollama is already running. Confirm with:

```bash
curl -fsS http://localhost:11434/api/tags
```

### Gemma model missing

```bash
ollama list
ollama pull <model-name>
```

### Container cannot reach host Ollama

```bash
docker run --rm curlimages/curl:latest   -s http://host.docker.internal:11434/api/tags
```

## Extension Points

Future milestones can add evaluation runners, Kubernetes/GKE deployment, production model-serving topology, OpenTelemetry collectors, and security controls without redesigning the core three-agent workflow.
