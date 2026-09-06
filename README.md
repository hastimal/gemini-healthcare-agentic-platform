# gemini-healthcare-agentic-platform

A healthcare-focused Agentic AI platform for exploring trustworthy search, evidence retrieval, grounding, citations, multi-agent workflows, Model Context Protocol (MCP), FHIR healthcare interoperability, and model portability using Gemini, Gemma, and Google ADK.

The project explores the evolution from traditional retrieval toward agentic healthcare search while keeping evidence provenance, source authority, interoperability boundaries, grounding, and safety explicit.

---

## Current Release

**v0.8 — Gemini + Gemma / Ollama**

v0.8 introduces model-runtime portability while preserving the same Google ADK three-agent healthcare architecture.

The reasoning agents can now use either:

- **Gemini** — hosted Google model path
- **Gemma + Ollama** — local Gemma path through LiteLLM

Both paths reuse the same Google ADK workflow, MCP healthcare tools, NPPES/PubMed/FHIR retrieval, evidence ranking, deterministic citations, and healthcare safety boundaries.

For provider discovery, final provider claims are assembled deterministically from selected evidence. Models continue to plan and invoke tools, while deterministic code owns the safety-critical provider claim boundary.

> **No evidence → no claim.**

The v0.8 acceptance scope is the flagship provider-discovery workflow. v0.8 does not claim that every intent has been proven portable or that Gemini and Gemma have equivalent runtime characteristics.

---

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
v0.9  CONTAINERIZE
      Docker
                    |
                    v
v1.0  MEASURE
      Evaluation Benchmark
```

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
    Google ADK agents, prompts, tools, and workflows

app/
    Application configuration

connectors/
    External healthcare data-source connectors

connectors/fhir/
    FHIR R4 client and normalization

grounding/
    Evidence scoring, ranking, citations, and grounded answers

mcp_services/
    MCP servers and MCP client adapters

mcp_services/fhir_server/
    FHIR MCP server and tools

models/
    Shared structured data models

search/
    Query fan-out, retrieval, MCP orchestration, and deduplication

tests/
    Unit and regression tests

docs/
    Architecture and integration documentation

examples/
    Acceptance-run documentation and examples
```

---

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

Overall architecture:

```text
docs/architecture.md
```

FHIR architecture and integration:

```text
docs/fhir-integration.md
```

MCP architecture:

```text
docs/mcp-architecture.md
```

v0.7 acceptance run:

```text
examples/v0.7-acceptance.md
```

v0.8 model portability:

```text
docs/model-portability.md
```

v0.8 acceptance:

```text
examples/v0.8-acceptance.md
```

---

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

v0.9  Docker

v1.0  Evaluation benchmark

v1.1  Kubernetes / GKE

v1.2  OpenTelemetry

v1.3  Security

v2.0  Public framework release
```

---

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

## v0.9 — Docker

The next milestone will containerize the application and supporting services while preserving the v0.8 model-provider abstraction.

---

# Project Goal

The long-term goal is not simply to produce healthcare answers.

The goal is to build and evaluate a **trustworthy agentic AI architecture** in which planning, retrieval, evidence evaluation, healthcare interoperability, tool access, grounding, citations, model execution, deployment, observability, and security can be independently inspected and improved.
