# Changelog

All notable changes to the **Gemini Healthcare Agentic Platform** are documented here.

This project is developed incrementally. Each milestone introduces a capability needed to evolve from a simple LLM-powered search workflow into a trustworthy, interoperable, and production-ready agentic healthcare AI platform.

---

## [v0.7.0] - 2026-09-05

### FHIR Healthcare Interoperability

#### Why

Provider registry evidence and biomedical literature represent different parts of the healthcare evidence landscape, but neither provides a standardized model for healthcare resource relationships.

v0.7 introduces FHIR R4 as a third healthcare data capability so the platform can explore standardized relationships among practitioners, practitioner roles, organizations, locations, specialties, and healthcare services.

FHIR is added as a tool and data-source capability. It does not introduce another core agent.

#### Added

- FHIR R4 connector
- FHIR resource normalization into the shared `SearchResult` model
- FHIR MCP server
- Async FHIR MCP client
- MCP-based FHIR retrieval through the Healthcare Research Agent
- Explicit FHIR/interoperability query routing
- Public HAPI FHIR R4 development endpoint configuration
- Specialty-filtered `PractitionerRole` retrieval
- Development-server fallback for interoperability-path validation
- FHIR evidence scoring
- Provider-discovery grounding safeguards for public HAPI test records
- Defensive `SearchPlan` normalization at the Google ADK Research Agent tool boundary
- FHIR connector, MCP, retrieval, client, and evidence-ranking regression tests
- FHIR architecture and acceptance documentation

#### Supported FHIR Resources

The initial v0.7 scope supports:

- `Practitioner`
- `PractitionerRole`
- `Organization`
- `Location`
- `HealthcareService`

Patient-specific clinical resources are intentionally outside the initial v0.7 scope.

#### FHIR MCP Tools

The FHIR MCP server exposes:

- `search_fhir_practitioners`
- `search_fhir_practitioner_roles`
- `search_fhir_organizations`
- `search_fhir_locations`
- `search_fhir_healthcare_services`

#### Architecture Impact

    Healthcare Research Agent
              |
              v
    MCPHealthcareRetrievalOrchestrator
         /          |          \
        v           v           v
    Search MCP  Research MCP  FHIR MCP
        |           |           |
        v           v           v
      NPPES       PubMed      FHIR R4

The three evidence paths remain intentionally distinct:

    NPPES
      -> provider registry evidence

    PubMed
      -> general biomedical evidence

    FHIR
      -> healthcare interoperability evidence

#### FHIR Retrieval Behavior

FHIR retrieval is intentionally opt-in.

Ordinary provider and biomedical queries do not automatically trigger FHIR retrieval. A generated query must explicitly indicate FHIR or healthcare interoperability.

For provider-oriented interoperability, v0.7 prefers `PractitionerRole`.

The development workflow first attempts a specialty-filtered `PractitionerRole` lookup.

The public HAPI FHIR test server may not contain records matching a free-text specialty. When that filtered lookup returns no records, the development path may perform an unfiltered `PractitionerRole` lookup.

This fallback exists only to exercise the complete interoperability path:

    Google ADK
        -> Healthcare Research Agent
        -> MCP retrieval
        -> FHIR MCP server
        -> FHIR connector
        -> HAPI FHIR R4
        -> normalized SearchResult

The fallback must not be interpreted as specialty, location, credential, license, quality, service, or provider verification.

#### Evidence Boundaries

FHIR is used for healthcare interoperability evidence.

Public HAPI FHIR test records are not treated as proof of:

- provider quality
- provider suitability
- board certification
- active licensure
- good standing
- requested specialty
- requested location
- provider recommendation
- service availability

The platform intentionally distinguishes:

    FHIR standard authority
              !=
    individual FHIR record authority

The authority of an individual FHIR record depends on its publisher and provenance.

#### Grounding Impact

FHIR evidence participates in retrieval, normalization, deduplication, and scoring.

For provider-discovery workflows, public HAPI FHIR test records are prevented from consuming provider grounding slots.

This allows the FHIR interoperability path to remain observable without treating arbitrary development-server records as provider recommendations.

The grounding principle remains:

**No evidence -> no claim.**

#### Planner Safety

The Search Planner may generate queries identifying professional directories or state licensing authorities that could support later verification.

Generating those queries does not mean the corresponding source was retrieved or that credentials, licensing, disciplinary history, board certification, or services were verified.

The planner prompt now explicitly distinguishes source discovery from completed verification.

#### Google ADK Handoff

During end-to-end validation, an LLM-mediated tool invocation omitted a redundant `SearchPlan.intent` field even though the planner output contained the intent.

The Healthcare Research Agent tool boundary now defensively restores that field from the validated `UserQuery` before validating the `SearchPlan`.

This keeps the handoff structured while avoiding a failure caused by omission of redundant planner state.

#### Acceptance Validation

One successful v0.7 end-to-end acceptance run produced:

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

These counts describe one observed acceptance run. They are not fixed architectural guarantees or benchmark claims.

The pre-release regression checkpoint completed with:

    45 passed

One OpenTelemetry dependency deprecation warning remains visible during the test suite. It is non-blocking and is not treated as resolved by v0.7.

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
