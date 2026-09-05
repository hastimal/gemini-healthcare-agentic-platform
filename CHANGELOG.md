# Changelog

All notable changes to the **Gemini Healthcare Agentic Platform** are documented here.

This project is developed incrementally. Each milestone introduces a capability needed to evolve from a simple LLM-powered search workflow into a trustworthy, interoperable, and production-ready agentic healthcare AI platform.

---

## [v0.6.0] - 2026-09-05

### MCP Tool Layer

#### Why

The healthcare retrieval layer originally depended on direct Python calls from the agent runtime to individual data-source connectors.

That works inside one application, but tightly couples tools to the implementation.

MCP was introduced to create a standardized tool boundary between agents and healthcare capabilities.

This allows the same healthcare tools to eventually be discovered and invoked by different MCP-compatible agent runtimes without rewriting the underlying NPPES or PubMed integrations.

#### Added

- MCP server for healthcare provider discovery
- MCP server for biomedical literature search
- `find_healthcare_providers` MCP tool
- `search_biomedical_literature` MCP tool
- Async MCP clients compatible with Google ADK
- MCP healthcare retrieval orchestrator
- Unit and integration tests for MCP tools and clients
- MCP architecture documentation

#### Architecture Impact

    BEFORE

    Healthcare Research Agent
            |
            +--> NPPESProviderClient --> CMS NPPES
            |
            +--> PubMedClient ---------> PubMed


    AFTER

    Healthcare Research Agent
            |
            v
    MCP Retrieval Layer
          /     \
         v       v
    Search MCP  Research MCP
         |       |
         v       v
      NPPES    PubMed

The existing healthcare connectors remain responsible for communicating with external data sources. MCP standardizes how agents access those capabilities.

---

## [v0.5.0] - 2026-09-05

### Google ADK Multi-Agent Architecture

#### Why

A single workflow should not be responsible for planning searches, retrieving evidence, evaluating sources, and generating the final answer.

Google ADK was introduced to separate these responsibilities into specialized agents with structured handoffs.

This makes the workflow easier to understand, test, extend, and eventually deploy across different agent runtimes.

#### Added

- Google ADK integration
- Search Planner Agent
- Healthcare Research Agent
- Evidence & Answer Agent
- Sequential multi-agent workflow
- Structured agent handoffs
- Typed planner, research, and answer outputs

#### Architecture Impact

    User Question
          |
          v
    Search Planner Agent
          |
          v
    Healthcare Research Agent
          |
          v
    Evidence & Answer Agent
          |
          v
    Grounded Answer

---

## [v0.4.0] - 2026-09-04

### Grounded Answers & Validated Citations

#### Why

Retrieving and ranking evidence is not sufficient for trustworthy healthcare AI.

An LLM can still introduce claims that are not supported by the retrieved sources.

This milestone established the core safety principle:

**No evidence -> no claim.**

The final answer is generated from selected evidence and validated against deterministic citations.

#### Added

- Grounded answer generation
- Deterministic citation construction
- Evidence-restricted Gemini context
- Structured provider recommendations
- Citation validation
- Explicit limitations
- Conservative handling of healthcare claims

#### Architecture Impact

    Selected Evidence
          |
          v
    Deterministic Citations
          |
          v
    Restricted Gemini Context
          |
          v
    Grounded Draft
          |
          v
    Validation
          |
          v
    Grounded Answer

---

## [v0.3.0] - 2026-09-04

### Evidence Ranking & Diverse Evidence Selection

#### Why

Retrieval can return many sources, but not every source deserves equal influence on the final answer.

The platform needed a deterministic mechanism for evaluating evidence before allowing it into the grounding pipeline.

This milestone introduced evidence scoring, ranking, and diverse evidence selection.

#### Added

- Evidence scoring
- Evidence ranking
- Source-authority evaluation
- Relevance scoring
- Freshness and specificity signals
- Confidence scoring
- Diverse evidence selection

#### Architecture Impact

    Retrieved Sources
           |
           v
    Evidence Scoring
           |
           v
    Evidence Ranking
           |
           v
    Selected Evidence

---

## [v0.2.0] - 2026-09-04

### Real Healthcare Retrieval with PubMed & NPPES

#### Why

Query planning alone cannot produce grounded healthcare answers.

The platform needed authoritative external evidence rather than relying only on model knowledge.

Two complementary healthcare sources were introduced:

- CMS NPPES for provider identity and registry information
- PubMed for biomedical research evidence

Together they established the first real healthcare retrieval layer.

#### Added

- CMS NPPES provider connector
- PubMed biomedical literature connector
- Healthcare retrieval orchestrator
- Search-result normalization
- Result deduplication
- Provider and research routing

#### Architecture Impact

    SearchPlan
        |
        +--> NPPES --> Provider Evidence
        |
        +--> PubMed --> Scientific Evidence

---

## [v0.1.0] - 2026-09-04

### Project Foundation + Gemini Query Planning & Query Fan-Out

#### Why

Healthcare questions are often too complex to represent as a single search query.

The first milestone therefore established the project foundation and introduced Gemini-powered query planning.

Instead of immediately answering a question, Gemini decomposes the request into complementary research queries with explicit intent, purpose, and priority.

This establishes the search-planning layer used by later retrieval and agentic workflows.

#### Added

- Initial Python project structure
- Environment-based configuration
- FastAPI application skeleton
- Gemini integration using the Google Gen AI SDK
- Healthcare query planning
- Query fan-out
- Intent classification
- Query purpose and priority
- Structured `SearchPlan`
- Configurable Gemini model selection
- Initial unit-test structure
- Extensible architecture for agents, connectors, grounding, evaluation, security, and observability

#### Architecture Impact

    User Question
          |
          v
    Gemini Query Planner
          |
          +--> Intent Classification
          |
          +--> Query Decomposition
          |
          v
    SearchPlan
          |
          v
    Query Fan-Out

---

# Architecture Evolution

The releases intentionally build on one another.

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
          FHIR
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

---

# Evidence Model

The platform intentionally separates different types of healthcare evidence.

    NPPES
      -> Who is this provider?
      -> Provider identity and registry information

    FHIR
      -> What healthcare organization, location,
         practitioner, and service structure exists?
      -> Standardized healthcare interoperability

    PubMed
      -> What scientific evidence applies generally?
      -> Biomedical research evidence

    Gemini + Google ADK
      -> Plan, orchestrate, and reason across evidence

    Grounding Layer
      -> Only make claims supported by evidence

This separation is intentional. A provider registry should not be treated as scientific evidence, and biomedical literature should not be used to make unsupported claims about an individual provider.

---

# Planned Milestones

## v0.7.0 - FHIR Healthcare Interoperability

Planned focus:

- FHIR connector
- Standardized FHIR resource handling
- FHIR MCP server
- MCP-based FHIR tool access
- Research Agent integration
- Evidence normalization
- Tests and end-to-end validation

Initial resource scope is expected to focus on non-PHI healthcare discovery resources such as:

- Practitioner
- PractitionerRole
- Organization
- Location
- HealthcareService

## v0.8.0 - Gemini + Gemma / Ollama

Planned focus:

- Model-provider abstraction
- Gemini hosted runtime
- Gemma through Ollama
- Comparable execution across model runtimes

## v0.9.0 - Docker

Planned focus:

- Containerized application runtime
- Containerized MCP services
- Local multi-service development
- Portable model and agent execution

## v1.0.0 - Evaluation Benchmark

Planned focus:

- Citation accuracy
- Groundedness
- Retrieval relevance
- Source authority
- Answer completeness
- Hallucination analysis
- Latency
- Cost

---

The long-term goal is not simply to produce healthcare answers.

The goal is to build and evaluate a **trustworthy agentic AI architecture** in which planning, retrieval, evidence evaluation, tool interoperability, grounding, citations, model execution, and deployment can be independently inspected and improved.
