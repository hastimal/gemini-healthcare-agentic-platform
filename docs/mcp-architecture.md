# MCP Architecture — v0.6

## Overview

v0.6 introduces a Model Context Protocol (MCP) tool layer into the Gemini Healthcare Agentic Platform.

The goal is not to replace the healthcare connectors introduced in earlier releases. Instead, v0.6 exposes those existing tested capabilities through standardized MCP tools and adds an asynchronous MCP execution path compatible with Google ADK.

The core principle is:

> Existing healthcare connectors remain responsible for accessing healthcare data. MCP becomes the standardized tool-access boundary between agents and those capabilities.

---

## Why MCP?

Before v0.6, the Healthcare Research Agent called the provider and PubMed connectors directly.

```text
BEFORE v0.6
===========

Healthcare Research Agent
        |
        +--> direct Python --> NPPESProviderClient --> CMS NPPES
        |
        +--> direct Python --> PubMedClient --------> PubMed
```

This works, but it tightly couples the agent layer to each connector implementation.

v0.6 introduces MCP between the agent and those capabilities.

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

v0.6 does not replace the healthcare connectors. It exposes the existing tested retrieval capabilities as standardized MCP tools that agents can discover and invoke.

---

## End-to-End Flow

```text
USER QUESTION
     |
     v
Search Planner Agent
     |
     v
Healthcare Research Agent
     |
     v
MCPHealthcareRetrievalOrchestrator
     |
     +------------------------------+
     |                              |
     v                              v
MCPProviderClient             MCPPubMedClient
     |                              |
     v                              v
Search MCP Server             Research MCP Server
     |                              |
     v                              v
find_healthcare_providers     search_biomedical_literature
     |                              |
     v                              v
NPPESProviderClient              PubMedClient
     |                              |
     v                              v
CMS NPPES                       PubMed
     |                              |
     +---------------+--------------+
                     |
                     v
                SearchResult[]
                     |
                     v
              Evidence Ranking
                     |
                     v
            Evidence & Answer Agent
                     |
                     v
              GROUNDED ANSWER
```

---

## Google ADK and Async MCP

Google ADK executes tools inside an asyncio event loop.

Because MCP operations are asynchronous, v0.6 keeps the execution path asynchronous from the ADK tool down to the MCP clients.

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

This avoids creating a nested asyncio event loop.

The original synchronous healthcare retrieval orchestrator remains available for backwards compatibility with earlier versions.

---

## Programmer Mapping

### Google ADK Research Tool

File:

```text
agents/healthcare_research/tools.py
```

Function:

```text
retrieve_healthcare_evidence()
```

The function validates the structured `UserQuery` and `SearchPlan`, invokes MCP-backed retrieval, and returns structured search results to the next ADK agent.

### MCP Retrieval Orchestrator

File:

```text
search/mcp_retrieval.py
```

Class:

```text
MCPHealthcareRetrievalOrchestrator
```

Responsibilities:

- route provider discovery queries
- route biomedical research queries
- invoke async MCP clients
- deduplicate results
- return shared `SearchResult` models

### MCP Clients

File:

```text
mcp_services/clients/healthcare.py
```

Classes:

```text
MCPProviderClient
MCPPubMedClient
```

### Search MCP Server

Files:

```text
mcp_services/search_server/server.py
mcp_services/search_server/tools.py
```

Public MCP tool:

```text
find_healthcare_providers
```

Flow:

```text
find_healthcare_providers()
        |
        v
find_providers()
        |
        v
NPPESProviderClient
        |
        v
CMS NPPES
```

### Research MCP Server

Files:

```text
mcp_services/research_server/server.py
mcp_services/research_server/tools.py
```

Public MCP tool:

```text
search_biomedical_literature
```

Flow:

```text
search_biomedical_literature()
        |
        v
search_pubmed()
        |
        v
PubMedClient
        |
        v
PubMed
```

---

## Existing Grounding Pipeline Is Preserved

MCP changes the tool-access layer. It does not replace the existing evidence and grounding pipeline.

```text
MCP Retrieval
      |
      v
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

The fundamental rule remains:

> No evidence → no claim.

---

## Healthcare Evidence Boundaries

CMS NPPES may support provider identity, NPI, reported location, taxonomy, and NPPES-reported license metadata.

NPPES alone must not be treated as proof of:

- active state licensure
- good standing
- board certification
- clinical quality
- patient satisfaction
- provider-specific anxiety-management expertise
- sedation availability

PubMed supports general biomedical and scientific context.

PubMed evidence must not be used to claim that a specific provider offers a particular treatment or service unless provider-specific evidence independently supports that claim.

---

## v0.6 Acceptance Run

The flagship test query was:

> Find three pediatric dentists in Houston for a child who is scared of going to the dentist. Compare them using trustworthy sources, provider credentials, services, and location, and explain why you selected each one.

One successful v0.6 acceptance run produced:

```text
6 generated queries
16 unique retrieved sources
5 selected evidence sources
3 provider candidates
C1-C5 deterministic citations
explicit limitations
```

These values describe one acceptance run and are not architectural guarantees.

---

## Tests

v0.6 adds MCP-specific tests:

```text
tests/unit/test_mcp_search.py
tests/unit/test_mcp_research.py
tests/unit/test_mcp_clients.py
tests/unit/test_mcp_retrieval.py
```

The complete regression suite currently passes:

```text
25 passed
```

Run:

```bash
ruff check .
python -m pytest -v
```

---

## Running the ADK Workflow

```bash
adk run agents
```

---

## Design Summary

```text
Agents decide what they need.

MCP standardizes how tools are exposed.

Connectors access healthcare data sources.

Models provide the shared evidence contract.

Grounding determines which claims are allowed.
```

---

## Next Milestone

v0.7 will extend the healthcare connector layer, including FHIR-oriented capabilities.

FHIR should be exposed as another tool capability rather than creating another core agent.
