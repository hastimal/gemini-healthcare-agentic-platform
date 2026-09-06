# gemini-healthcare-agentic-platform

A healthcare-focused Agentic AI platform for exploring trustworthy search, evidence retrieval, grounding, citations, multi-agent workflows, Model Context Protocol (MCP), FHIR healthcare interoperability, and model portability using Gemini, Gemma, and Google ADK.

The project explores the evolution from traditional retrieval toward agentic healthcare search while keeping evidence provenance, source authority, interoperability boundaries, grounding, and safety explicit.

---

## Current Release

**v1.0 — Dockerized Reproducible Demo Runtime**

v1.0 packages the accepted v0.9 healthcare agent workflow into a reproducible Docker application runtime without changing the three-agent architecture, MCP retrieval paths, healthcare evidence semantics, or deterministic provider-grounding boundary.

The same Streamlit application can now be launched in Docker with either **Gemini** or **Gemma + Ollama**:

```bash
./scripts/demo-docker.sh gemini
./scripts/demo-docker.sh gemma
```

On macOS, the Gemma Docker path intentionally keeps Ollama native on the host and connects from the application container through `host.docker.internal:11434`. This preserves the existing native Apple Silicon model runtime while containerizing the healthcare application itself.

The original local runtime remains supported:

```bash
./scripts/demo-local.sh gemini
./scripts/demo-local.sh gemma
```

Provider discovery remains evidence-restricted. NPPES supports provider identity, NPI, taxonomy, and reported location; it does not establish that a provider is “best”, board certified, actively licensed, in good standing, or offers a requested service.

Containerization does not change healthcare evidence authority, privacy, security, or compliance guarantees.

> **No evidence → no claim.**

The original Houston pediatric-dentist question remains an acceptance/regression example. It is not application configuration.

## Project Direction

The platform is being built incrementally:

```text
SEARCH
  |
  v
EVIDENCE
  |
  v
AGENTS
  |
  v
TOOLS
  |
  v
HEALTHCARE DATA
  |
  v
OPEN MODELS
  |
  v
CONTAINERS
  |
  v
BENCHMARK
  |
  v
KUBERNETES
  |
  v
OBSERVABILITY
  |
  v
SECURITY
```

The long-term goal is to explore how trustworthy Agentic AI systems can combine:

- Gemini
- Google ADK
- Model Context Protocol (MCP)
- healthcare search
- biomedical literature
- FHIR R4 healthcare interoperability
- evidence ranking
- deterministic citations
- grounded answer generation
- Gemma and local model runtimes
- Docker
- Kubernetes
- evaluation and benchmarking
- observability
- AI security

---

## Core Agent Architecture

The platform intentionally uses exactly three core agents:

```text
User Healthcare Question
          |
          v
+----------------------+
| Search Planner Agent |
| Gemini/Gemma + ADK  |
+----------+-----------+
           |
           v
       SearchPlan
           |
           v
+---------------------------+
| Healthcare Research Agent |
+-------------+-------------+
              |
              v
  MCP Retrieval Orchestrator
        /       |       \
       v        v        v
 Search MCP Research MCP FHIR MCP
       |        |        |
       v        v        v
    NPPES    PubMed    FHIR R4
        \       |       /
         \      |      /
          v     v     v
           SearchResult[]
                |
                v
+-------------------------+
| Evidence & Answer Agent |
+------------+------------+
             |
             v
      Score -> Rank
             |
             v
     Evidence Selection
             |
             v
 Deterministic Citations
             |
             v
      Grounded Answer
```

### 1. Search Planner Agent

Responsibilities:

- interpret the user request
- identify search intent
- generate query fan-out
- create a structured research plan
- identify potential authoritative sources
- generate FHIR interoperability queries when appropriate

The planner may identify professional directories or licensing authorities that could support later verification.

**Generating a verification-oriented query does not mean that verification has been performed.**

### 2. Healthcare Research Agent

Responsibilities:

- execute deterministic healthcare retrieval
- invoke MCP-backed healthcare capabilities
- gather provider registry evidence
- gather biomedical evidence
- gather FHIR interoperability evidence
- preserve source metadata
- normalize retrieved evidence into shared models
- return structured search results

### 3. Evidence & Answer Agent

Responsibilities:

- score evidence
- rank evidence
- select appropriate grounding sources
- build deterministic citations
- generate evidence-restricted answers
- expose limitations and transparency

The core grounding rule is:

> **No evidence → no claim.**

---

## Architecture Evolution

```text
v0.1  PLAN
      Gemini Query Planning + Query Fan-Out
                    |
                    v
v0.2  RETRIEVE
      NPPES + PubMed
                    |
                    v
v0.3  EVALUATE
      Evidence Scoring + Ranking
                    |
                    v
v0.4  GROUND
      Citations + Claim Validation
                    |
                    v
v0.5  ORCHESTRATE
      Google ADK Multi-Agent System
                    |
                    v
v0.6  STANDARDIZE
      MCP Tool Layer
                    |
                    v
v0.7  INTEROPERATE
      FHIR R4
                    |
                    v
v0.8  PORT
      Gemini + Gemma / Ollama
                    |
                    v
v0.9  GENERALIZE
      Dynamic Planning + Retrieval + GUI
                    |
                    v
v1.0  CONTAINERIZE
      Dockerized Reproducible Demo Runtime
                    |
                    v
v1.1  MEASURE
      Evaluation Benchmark
                    |
                    v
v1.2  ORCHESTRATE
      Kubernetes / GKE
                    |
                    v
v1.3  OBSERVE
      OpenTelemetry
                    |
                    v
v1.4  SECURE
      Security
                    |
                    v
v2.0  FRAMEWORK
      Reusable Agentic Healthcare Framework
```

---

# v1.0 — Dockerized Reproducible Demo Runtime

v1.0 adds Docker as an additional runtime option around the accepted v0.9 application.

```text
Gemini
Browser
   |
   v
Dockerized Streamlit App :8501
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
Dockerized Streamlit App :8501
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

The Docker layer does not replace the local runtime and does not introduce another agent. The platform still uses exactly three core agents and the same MCP-backed NPPES, PubMed, and FHIR retrieval architecture.

### Docker Quick Start

Run Gemini:

```bash
./scripts/demo-docker.sh gemini
```

Run Gemma:

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

For safe Compose validation without expanding `.env` values into terminal output:

```bash
docker compose config --quiet
```

See `DOCKER-DEMO-README.md` for architecture, prerequisites, validation, troubleshooting, and extension notes.

---

# v0.9 — Generalized Query Planning + Dynamic Retrieval + GUI

The flagship query is a test case, not application configuration.

```text
Any Supported Healthcare Question
        |
        v
Search Planner Agent
(intent + optional location + optional specialty + query fan-out)
        |
        v
Healthcare Research Agent
   /        |        \
NPPES     PubMed     FHIR
   \        |        /
        v
Evidence & Answer Agent
(authority-aware ranking + deterministic provider safety + citations)
        |
        v
One Streamlit UI
   /          \
Gemini     Gemma/Ollama
```

Run the GUI with `./scripts/demo-local.sh gemini` or `./scripts/demo-local.sh gemma`. Run live acceptance with `./scripts/test-ui.sh gemini` or `./scripts/test-ui.sh gemma`. See `examples/v0.9-acceptance.md`.

---

# v0.7 — FHIR Healthcare Interoperability

v0.7 adds FHIR R4 to the MCP-backed healthcare retrieval architecture.

```text
Healthcare Research Agent
            |
            v
MCPHealthcareRetrievalOrchestrator
            |
      +-----+-----+
      |     |     |
      v     v     v
   Search Research FHIR
    MCP     MCP    MCP
     |       |      |
     v       v      v
   NPPES   PubMed  FHIR R4
```

The default development FHIR endpoint is:

```text
https://hapi.fhir.org/baseR4
```

This is a **public HAPI FHIR R4 test server**.

It is used in v0.7 to demonstrate healthcare interoperability and the complete ADK → MCP → FHIR execution path.

Public HAPI records are test/development data and must not be treated as authoritative real-world provider evidence.

---

## FHIR Resource Scope

v0.7 intentionally limits FHIR access to non-patient healthcare discovery and interoperability resources.

Supported resource types:

```text
Practitioner
PractitionerRole
Organization
Location
HealthcareService
```

The initial v0.7 scope intentionally does not expose patient-specific clinical resources such as:

```text
Patient
Condition
Observation
Medication
Appointment
```

This keeps the first FHIR milestone focused on healthcare discovery and interoperability rather than patient-level clinical data.

---

## Why PractitionerRole?

`PractitionerRole` is particularly useful for healthcare discovery because it can represent relationships among:

```text
              Practitioner
                   |
                   v
            PractitionerRole
             /      |      \
            v       v       v
       Specialty Organization Location
                         |
                         v
                HealthcareService
```

This makes it useful for exploring standardized healthcare relationships without treating the FHIR record itself as evidence of provider quality.

---

## FHIR MCP Tools

The FHIR MCP server exposes five tools:

```text
search_fhir_practitioners
search_fhir_practitioner_roles
search_fhir_organizations
search_fhir_locations
search_fhir_healthcare_services
```

The architecture is:

```text
Healthcare Research Agent
        |
        v
MCPFHIRClient
        |
        v
FHIR MCP Server
        |
        v
FHIR MCP Tool
        |
        v
FHIRClient
        |
        v
FHIR R4 Server
        |
        v
FHIR Resource
        |
        v
Normalized SearchResult
```

---

## FHIR Retrieval Strategy

FHIR retrieval is intentionally **opt-in**.

Ordinary provider and biomedical queries do not automatically trigger FHIR retrieval.

A generated query must explicitly indicate FHIR or healthcare interoperability.

Examples:

```text
FHIR PractitionerRole pediatric dentistry interoperability

FHIR healthcare organization practitioner role structure

healthcare interoperability PractitionerRole specialty organization location
```

For provider-oriented interoperability queries, v0.7 prefers `PractitionerRole`.

### Specialty-Filtered Lookup

The workflow first attempts:

```text
PractitionerRole
    +
requested specialty
```

For example:

```text
Pediatric Dentistry
```

### Public HAPI Development Fallback

The public HAPI test server may not contain `PractitionerRole` records matching a free-text specialty.

When the specialty-filtered development lookup returns no records, v0.7 may perform an unfiltered `PractitionerRole` request.

```text
FHIR interoperability query
          |
          v
Specialty-filtered PractitionerRole
          |
       results?
       /     \
     yes      no
      |        |
      |        v
      |   Unfiltered PractitionerRole
      |        |
      +----+---+
           |
           v
   Normalized FHIR Evidence
```

The purpose of this fallback is only to demonstrate the complete interoperability path:

```text
Google ADK
    |
    v
Healthcare Research Agent
    |
    v
MCP Retrieval
    |
    v
FHIR MCP Server
    |
    v
FHIRClient
    |
    v
HAPI FHIR R4
    |
    v
Normalized SearchResult
```

Fallback records must **not** be interpreted as:

- matching the requested specialty
- matching the requested location
- recommended providers
- proof of licensure
- proof of credentials
- proof of board certification
- proof of clinical quality
- proof of service availability

---

# Healthcare Evidence Model

The platform intentionally separates different types of healthcare evidence.

```text
NPPES
  |
  +--> Who is this provider?
  +--> NPI
  +--> taxonomy
  +--> registry location
  +--> NPPES-reported license metadata


PubMed
  |
  +--> What scientific evidence applies generally?
  +--> biomedical literature
  +--> systematic reviews
  +--> general clinical context


FHIR
  |
  +--> How is healthcare information structured?
  +--> practitioner relationships
  +--> organization relationships
  +--> location relationships
  +--> healthcare service relationships


Gemini + Google ADK
  |
  +--> plan
  +--> orchestrate
  +--> reason across evidence


Grounding Layer
  |
  +--> allow only evidence-supported claims
```

This separation is intentional.

A provider registry should not be treated as biomedical evidence.

Biomedical literature should not be used to make unsupported claims about an individual provider.

A FHIR record should not automatically be treated as authoritative evidence about provider quality or suitability.

---

## CMS NPPES

CMS NPPES is used for provider discovery and provider registry information.

NPPES may support:

- provider identity
- NPI
- reported location
- taxonomy / specialty
- NPPES-reported license metadata

NPPES alone must not be treated as proof of:

- active state licensure
- good standing
- board certification
- provider quality
- patient satisfaction
- specific anxiety-management services
- sedation availability

---

## PubMed

PubMed is used for biomedical and scientific evidence.

PubMed may support:

- general scientific context
- biomedical research
- systematic reviews
- evidence about healthcare interventions

PubMed evidence must not be converted into provider-specific claims unless the cited evidence explicitly supports that individual provider-level claim.

---

## FHIR

FHIR is used for standardized healthcare interoperability evidence.

FHIR can represent relationships among:

- practitioners
- practitioner roles
- specialties
- organizations
- locations
- healthcare services

FHIR structure alone does not establish:

- provider quality
- provider suitability
- board certification
- current license status
- good standing
- service availability
- patient satisfaction

---

## Standard Authority vs Record Authority

FHIR is an authoritative healthcare interoperability standard.

That does **not** mean every record returned by every FHIR server is authoritative real-world evidence.

```text
FHIR Standard Authority
          !=
FHIR Record Authority
```

Record authority depends on the publisher and provenance of the FHIR data.

Because v0.7 uses the public HAPI test server for development, its records receive conservative treatment.

---

# MCP Tool Layer

## Provider Search

```text
Healthcare Research Agent
        |
        v
MCPProviderClient
        |
        v
Search MCP Server
        |
        v
find_healthcare_providers
        |
        v
NPPESProviderClient
        |
        v
CMS NPPES
```

## Biomedical Research

```text
Healthcare Research Agent
        |
        v
MCPPubMedClient
        |
        v
Research MCP Server
        |
        v
search_biomedical_literature
        |
        v
PubMedClient
        |
        v
PubMed
```

## FHIR Interoperability

```text
Healthcare Research Agent
        |
        v
MCPFHIRClient
        |
        v
FHIR MCP Server
        |
        v
FHIR MCP Tools
        |
        v
FHIRClient
        |
        v
FHIR R4
```

MCP standardizes how agents access these capabilities.

The underlying healthcare connectors remain responsible for communicating with their respective external data sources.

---

# Async Google ADK Integration

Google ADK executes tools inside an asyncio event loop.

The MCP healthcare retrieval path therefore remains asynchronous:

```text
Google ADK
    |
    v
async retrieve_healthcare_evidence()
    |
    v
await MCPHealthcareRetrievalOrchestrator.retrieve()
    |
    +--> await MCPProviderClient.search()
    |
    +--> await MCPPubMedClient.search()
    |
    +--> await MCPFHIRClient.search_practitioner_roles()
```

The Research Agent tool boundary also performs defensive normalization of the structured planner handoff.

This protects the workflow when an LLM-mediated tool invocation omits a redundant field that can be safely recovered from the validated `UserQuery`.

---

# Grounding Pipeline

MCP and FHIR extend retrieval capabilities. They do not replace the grounding architecture.

```text
SearchResult[]
      |
      v
Evidence Scoring
      |
      v
Evidence Ranking
      |
      v
Evidence Selection
      |
      v
Deterministic Citations
      |
      v
Evidence-Restricted Grounding
      |
      v
Grounded Answer
```

The core rule remains:

> **No evidence → no claim.**

---

## FHIR Grounding Safety

Public HAPI FHIR records can participate in retrieval, normalization, scoring, and observability.

For provider-discovery workflows, they are prevented from consuming the grounding slots intended for provider evidence.

```text
Retrieved Evidence
       |
       +--> NPPES
       |
       +--> PubMed
       |
       +--> FHIR
              |
              v
        scored / observable
              |
              X
     provider grounding slot
```

This allows the platform to demonstrate FHIR interoperability without accidentally presenting arbitrary public test-server records as provider recommendations.

---

# Flagship Demo Query

```text
Find three pediatric dentists in Houston for a child who is scared of
going to the dentist. Compare them using trustworthy sources, provider
credentials, services, and location, and explain why you selected each one.
```

One successful v0.7 acceptance run produced:

```text
Generated queries:       7

Retrieved sources:      19
Deduplicated sources:   19

NPPES:                  10
PubMed:                  6
FHIR:                    3

Selected evidence:       5

NPPES selected:           3
PubMed selected:          2
FHIR selected:            0
```

The FHIR records successfully exercised:

```text
ADK
 |
 v
Research Agent
 |
 v
MCP
 |
 v
FHIR MCP
 |
 v
FHIR R4
 |
 v
Normalization
 |
 v
Evidence Pipeline
```

while remaining outside the provider-discovery grounding set.

These numbers describe **one acceptance run**.

They are not fixed architectural guarantees, performance benchmarks, or claims about future executions.

See:

```text
examples/v0.7-acceptance.md
```

---

# Repository Structure

```text
agents/
    Google ADK three-agent workflow

connectors/
    NPPES, PubMed, FHIR and supporting healthcare connectors

llm/
    Gemini/Gemma model selection and synthesis adapters

mcp_services/
    MCP servers and healthcare tool wrappers

search/
    query planning, dynamic retrieval, ranking, grounding

ui/
    Streamlit demo application

scripts/
    local and Docker demo/test helpers

tests/
    deterministic regression and integration coverage

examples/
    acceptance-run documentation and examples

Dockerfile
    reproducible Python/Streamlit application image

docker-compose.yml
    Docker application runtime configuration

DOCKER-DEMO-README.md
    v1.0 Docker runbook and architecture notes
```

# Important v0.7 Files

```text
agents/healthcare_research/tools.py
agents/prompts/query_agent.md

app/config.py

connectors/fhir/__init__.py
connectors/fhir/client.py
connectors/fhir/normalization.py

grounding/scoring.py
grounding/ranking.py

mcp_services/clients/healthcare.py

mcp_services/fhir_server/server.py
mcp_services/fhir_server/tools.py

search/deduplication.py
search/mcp_retrieval.py

tests/unit/test_fhir_client.py
tests/unit/test_mcp_fhir.py
tests/unit/test_mcp_clients.py
tests/unit/test_mcp_retrieval.py
tests/unit/test_evidence_ranking.py
```

---

# Documentation

Core project documentation:

```text
README.md
ROADMAP.md
CHANGELOG.md
LEARNING_GUIDE.md
docs/architecture.md
GUI-DEMO-README.md
UI-E2E-README.md
DOCKER-DEMO-README.md
```

Acceptance examples:

```text
examples/v0.8-acceptance.md
examples/v0.9-acceptance.md
```

v1.0 Docker runtime:

```text
DOCKER-DEMO-README.md
```

# Run the Google ADK Workflow

```bash
adk run agents
```

Example query:

```text
Find three pediatric dentists in Houston for a child who is scared of
going to the dentist. Compare them using trustworthy sources, provider
credentials, services, and location, and explain why you selected each one.
```

---

# Run Tests

```bash
ruff check .
pytest -q
git diff --check
```

Current v0.8 regression checkpoint:

```text
53 passed, 1 warning
```

One OpenTelemetry dependency deprecation warning may currently appear during the test suite.

It is non-blocking and is not treated as resolved by v0.8.

---

# Roadmap

```text
v0.1  Gemini API + query fan-out

v0.2  Real healthcare retrieval

v0.3  Evidence ranking

v0.4  Grounded answers + citations

v0.5  Google ADK multi-agent architecture

v0.6  MCP tool layer

v0.7  FHIR healthcare interoperability

v0.8  Gemini + Gemma / Ollama

v0.9  Generalized Query Planning + Dynamic Retrieval + GUI

v1.0  Dockerized Reproducible Demo Runtime

v1.1  Evaluation Benchmark

v1.2  Kubernetes / GKE

v1.3  OpenTelemetry

v1.4  Security

v2.0  Reusable Agentic Healthcare Framework
```

# v0.8 Model Portability

The current milestone demonstrates one Google ADK healthcare agent architecture with two model paths:

```text
MODEL_PROVIDER
     |
  +--+--+
  |     |
  v     v
Gemini Gemma
        |
        v
      Ollama
        |
        v
      LiteLLM
  \     /
   \   /
 Google ADK
     |
 Same 3 Agents
```

The flagship provider-discovery workflow has been accepted on both paths. The Gemma acceptance run completed with Gemini credentials unavailable.

See `docs/model-portability.md` and `examples/v0.8-acceptance.md` for the architecture and observed acceptance results.

---

# Next Milestone

## v1.1 — Evaluation Benchmark

The next milestone will add repeatable evaluation around supported workflows and evidence behavior.

The benchmark should measure platform behavior without turning one acceptance run into a model-quality or latency guarantee. It should preserve the same healthcare evidence boundaries and distinguish deterministic application correctness from model/runtime variability.

# Project Goal

The long-term goal is not simply to produce healthcare answers.

The goal is to build and evaluate a **trustworthy agentic AI architecture** in which planning, retrieval, evidence evaluation, healthcare interoperability, tool access, grounding, citations, model execution, deployment, observability, and security can be independently inspected and improved.
