# gemini-healthcare-agentic-platform

A healthcare-focused Agentic AI platform for exploring trustworthy search, evidence retrieval, grounding, citations, and multi-agent workflows using Gemini, Google ADK, MCP, and healthcare data sources.

The project compares the evolution from traditional retrieval toward agentic healthcare search while keeping evidence provenance, source authority, grounding, and safety boundaries explicit.

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
- evidence ranking
- deterministic citations
- FHIR-oriented healthcare interoperability
- Gemma and local model runtimes
- Docker
- Kubernetes
- evaluation and benchmarking
- observability
- AI security

## Core Agent Architecture

The platform uses three core agents:

```text
Search Planner Agent
        |
        v
Healthcare Research Agent
        |
        v
Evidence & Answer Agent
```

### Search Planner Agent

Responsibilities:

- interpret the user request
- identify search intent
- generate query fan-out
- create a structured research plan

### Healthcare Research Agent

Responsibilities:

- decide which retrieval capabilities are required
- execute provider and biomedical research
- gather evidence
- preserve source metadata
- return structured search results

### Evidence & Answer Agent

Responsibilities:

- score evidence
- rank evidence
- select authoritative sources
- build deterministic citations
- generate a grounded answer
- expose limitations and transparency

## v0.6 — Model Context Protocol

v0.6 introduces MCP as the standardized tool-access layer for healthcare retrieval.

Before v0.6, the Healthcare Research Agent called healthcare connectors directly.

```text
BEFORE v0.6
===========

Healthcare Research Agent
        |
        +--> direct Python --> NPPESProviderClient --> CMS NPPES
        |
        +--> direct Python --> PubMedClient --------> PubMed
```

In v0.6, the same tested connectors are exposed through MCP.

```text
AFTER v0.6
==========

Healthcare Research Agent
        |
        v
MCPHealthcareRetrievalOrchestrator
        |
        +--> MCPProviderClient
        |        |
        |        v
        |   Search MCP Server
        |        |
        |        v
        |   find_healthcare_providers()
        |        |
        |        v
        |   NPPESProviderClient
        |        |
        |        v
        |      CMS NPPES
        |
        +--> MCPPubMedClient
                 |
                 v
            Research MCP Server
                 |
                 v
        search_biomedical_literature()
                 |
                 v
             PubMedClient
                 |
                 v
               PubMed
```

v0.6 does not replace the healthcare connectors.

It exposes the existing tested capabilities as standardized MCP tools that agents can discover and invoke.

## MCP Tools

### Provider Search

Public MCP tool:

```text
find_healthcare_providers
```

Backed by:

```text
NPPESProviderClient --> CMS NPPES
```

### Biomedical Research

Public MCP tool:

```text
search_biomedical_literature
```

Backed by:

```text
PubMedClient --> PubMed
```

## Async Google ADK Integration

Google ADK executes tools inside an asyncio event loop.

v0.6 therefore keeps the MCP path asynchronous:

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
```

The original synchronous retrieval orchestrator remains available for compatibility with earlier versions.

## Grounding Pipeline

MCP changes the tool-access boundary. It does not replace the existing grounding architecture.

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
Deterministic Citations
      |
      v
Grounded Answer
```

The core rule is:

> No evidence → no claim.

## Healthcare Evidence Sources

Current healthcare retrieval includes:

### CMS NPPES

Used for provider discovery and structured provider information.

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

### PubMed

Used for biomedical and scientific evidence.

PubMed may support general scientific context but must not be used as provider-specific evidence unless a source explicitly supports that provider-level claim.

## Flagship Demo Query

```text
Find three pediatric dentists in Houston for a child who is scared of
going to the dentist. Compare them using trustworthy sources, provider
credentials, services, and location, and explain why you selected each one.
```

One successful v0.6 acceptance run produced:

```text
6 generated queries
16 unique retrieved sources
5 selected evidence sources
3 provider candidates
C1-C5 deterministic citations
explicit evidence limitations
```

These counts describe one acceptance run and are not fixed architectural guarantees.

## Repository Structure

Key areas:

```text
agents/
    Google ADK agents, prompts, tools, and workflows

connectors/
    External healthcare data-source clients

grounding/
    Evidence scoring, ranking, citations, and grounded answers

mcp_services/
    MCP servers and MCP client adapters

models/
    Shared structured data models

search/
    Query fan-out, retrieval, MCP orchestration, and deduplication

tests/
    Unit and regression tests

docs/
    Architecture and implementation documentation
```

## Important v0.6 Files

```text
agents/healthcare_research/tools.py

search/mcp_retrieval.py

mcp_services/clients/healthcare.py

mcp_services/search_server/server.py
mcp_services/search_server/tools.py

mcp_services/research_server/server.py
mcp_services/research_server/tools.py

tests/unit/test_mcp_search.py
tests/unit/test_mcp_research.py
tests/unit/test_mcp_clients.py
tests/unit/test_mcp_retrieval.py
```

## Documentation

Detailed MCP architecture:

```text
docs/mcp-architecture.md
```

## Run the Google ADK Workflow

```bash
adk run agents
```

## Run Tests

```bash
ruff check .
python -m pytest -v
```

Current v0.6 regression checkpoint:

```text
25 passed
```

## Roadmap

```text
v0.1  Gemini API + query fan-out
v0.2  Real healthcare retrieval
v0.3  Evidence ranking
v0.4  Grounded answers + citations
v0.5  Google ADK multi-agent architecture
v0.6  MCP tool layer
v0.7  FHIR and healthcare connectors
v0.8  Gemini vs Gemma / Ollama
v0.9  Docker
v1.0  Evaluation benchmark
v1.1  Kubernetes / GKE
v1.2  OpenTelemetry
v1.3  Security
v2.0  Public framework release
```

## Next Milestone

v0.7 will extend the healthcare connector layer with FHIR-oriented capabilities.

FHIR will be treated as another tool/data capability rather than adding another core agent.
