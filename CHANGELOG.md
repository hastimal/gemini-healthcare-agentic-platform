# Changelog

All notable changes to the **Gemini Healthcare Agentic Platform** are documented here.

This project is developed incrementally. Each milestone introduces a capability needed to evolve from a simple LLM-powered search workflow into a trustworthy, interoperable, and production-ready agentic healthcare AI platform.

---

## [v1.1.0] - 2026-09-07

### Evaluation Benchmark

#### Why

v1.1 introduces repeatable evaluation for the accepted healthcare agent architecture. The goal is to distinguish deterministic application correctness from model/runtime variability and to preserve measurable evidence without converting a small acceptance set into a general healthcare-AI accuracy claim.

#### Added

- frozen 11-case `evaluation/datasets/healthcare_benchmark.jsonl`
- deterministic evaluation models and workflow expectations
- benchmark runner that captures `planner_output`, `research_output`, and `answer_output`
- production-output adapter for evaluation
- deterministic metrics for retrieval, source authority, citations, grounding, completeness, and provider-safety boundaries
- benchmark orchestrator
- CSV, JSON, and Markdown reporting
- Gemini/Gemma comparison generator
- preserved raw first-run benchmark results under `evaluation/results/`
- model, workflow, metric, and case comparison tables

#### Core Acceptance Set

```text
Provider discovery:        4 cases
Biomedical research:       2 cases
Health information:        1 case
FHIR interoperability:     2 cases
Expected unsupported:      2 cases
Total:                    11 cases
```

#### Measured First-Run Results

```text
Gemini 3.7 Flash:
  11 / 11 core cases passed
  9 / 9 supported workflows completed
  2 / 2 unsupported workflows rejected explicitly

Gemma 4 12B + local Ollama:
  10 / 11 core cases passed
  8 / 9 supported workflows completed
  2 / 2 unsupported workflows rejected explicitly
  1 supported FHIR PractitionerRole case timed out
```

The preserved Gemma failure was a 600-second LiteLLM/Ollama timeout. It was not a deterministic grounding, citation, provider-authority, or provider-safety failure.

#### Evaluation Boundaries

- no LLM-as-judge in the v1.1 baseline
- acceptance pass rate is not a claim of general healthcare-AI accuracy
- unsupported workflows pass only when explicitly rejected
- workflow-specific metrics are evaluated only where applicable
- latency is diagnostic and runtime-dependent
- hosted Gemini and local Gemma/Ollama latency are not directly comparable as model-quality evidence
- first-run failures are preserved rather than replaced by retry results

#### Reproducibility

```bash
python -m evaluation.benchmark --provider gemini
python -m evaluation.benchmark --provider gemma
python -m evaluation.comparison
```

---

## [v1.0.0] - 2026-09-06

### Dockerized Reproducible Demo Runtime

#### Added

- Python 3.11 slim Docker application image
- Docker Compose runtime for the Streamlit healthcare application
- Streamlit container health check
- `./scripts/demo-docker.sh gemini`
- `./scripts/demo-docker.sh gemma`
- `./scripts/demo-docker-stop.sh`
- `.dockerignore` protections for `.env`, virtual environments, caches, logs, and test artifacts
- macOS Docker-to-host Ollama connectivity through `host.docker.internal:11434`
- `DOCKER-DEMO-README.md`

#### Preserved

- exactly three core Google ADK agents
- MCP-backed NPPES, PubMed, and FHIR retrieval
- deterministic provider-discovery grounding
- provider-scoped citations
- existing local Gemini and Gemma demo scripts

#### Runtime Architecture

```text
Gemini:
Browser -> Dockerized Streamlit -> Google ADK -> Gemini API

Gemma on macOS:
Browser -> Dockerized Streamlit -> Google ADK -> LiteLLM
        -> host.docker.internal:11434 -> native Ollama -> Gemma
```

#### Acceptance

```text
Docker + Gemini:              PASS
Docker + Gemma/native Ollama: PASS
Local + Gemma/native Ollama:  PASS
Docker -> host Ollama:        PASS
Streamlit container health:   PASS

Deterministic tests: 85 passed, 5 skipped, 1 dependency warning
```

The OpenTelemetry dependency deprecation warning remains non-blocking. These checks are functional acceptance, not a performance benchmark.

#### Boundaries

Dockerization does not make the application HIPAA compliant, PHI-safe, clinically validated, secure, private, or production-ready by itself. Existing source-authority and grounding rules remain unchanged.

---

## [v0.9.0] - 2026-09-06

### Generalized Query Planning + Dynamic Retrieval + GUI

#### Why

Interactive GUI testing exposed hidden Houston and Pediatric Dentistry assumptions inherited from the flagship acceptance query. v0.9 makes that question a regression case rather than application configuration.

#### Added

- generalized Google ADK planner output: intent, optional location, optional specialty, and generated queries
- deterministic query-plan construction without a hidden direct Gemini dependency
- planner-state-driven retrieval
- U.S. provider-location parsing
- deterministic NPPES specialty resolution for common wording differences
- intent-aware NPPES, PubMed, and explicit FHIR routing
- one Streamlit UI for Gemini and Gemma/Ollama
- structured planner/research/answer observability
- live Streamlit E2E acceptance harness
- generalized planner, location, retrieval, specialty, and UI regression tests

#### Boundaries

Provider discovery returns evidence-supported candidates; it does not establish “best” provider ranking, board certification, active licensure, good standing, clinical quality, or provider-specific service availability. `CARE_PROGRAM_DISCOVERY` and `CLINICAL_TRIALS` remain modeled intents but are not claimed as implemented retrieval paths in v0.9.

#### Acceptance

```text
Deterministic: 85 passed, 5 skipped, 1 dependency warning

Scenario                         Gemini   Gemma
Dallas Cardiology                PASS     PASS
Austin Neurology                 PASS     PASS
Biomedical research              PASS     PASS
FHIR PractitionerRole            PASS     PASS
Houston pediatric dentistry      PASS     PASS
                                 5/5      5/5
```

Manual Streamlit checks were also completed for both model paths. Observed local durations are diagnostics, not benchmarks. Known framework/dependency deprecation warnings remain non-blocking.

---

## [v0.8.0] - 2026-09-06

### Gemini + Gemma / Ollama Model Portability

#### Why

v0.8 introduces model-runtime portability for the Google ADK healthcare multi-agent workflow.

The architectural question is whether the same three-agent workflow can use hosted Gemini or locally operated Gemma while preserving MCP tools, healthcare retrieval, evidence ranking, citations, and safety boundaries.

This is a functional-portability milestone, not a model benchmark.

#### Added

- shared model-provider factory for the three Google ADK agents
- Gemini hosted model path
- Gemma local model path through Ollama and LiteLLM
- synthesis-provider abstraction for model-generated synthesis paths
- Google ADK state-based handoffs for authoritative planner and research outputs
- deterministic provider-discovery grounding
- provider-scoped citation enforcement
- model-factory regression tests
- v0.8 diagnostic scripts
- model-portability documentation
- Gemini and Gemma acceptance documentation

#### State-Based Agent Handoffs

The Research and Evidence tools now read authoritative workflow data from Google ADK session state rather than requiring the model to reconstruct large structured payloads as tool arguments.

This reduces unnecessary model-dependent transformation and improves portability across model runtimes.

#### Provider-Discovery Safety Boundary

For provider discovery, models continue to perform planning and tool invocation.

Deterministic code owns final provider claims, citations, and recommendation assembly from selected evidence.

This preserves the core rule:

**No evidence -> no claim.**

#### Acceptance Validation

The flagship provider-discovery workflow completed on both configured model paths.

Observed final acceptance state for both paths:

```text
Generated queries:       7
Retrieved sources:      19
Deduplicated sources:   19

NPPES:                  10
PubMed:                  6
FHIR:                    3

Selected evidence:       5
```

The Gemma/Ollama acceptance run completed with `GEMINI_API_KEY` and `GOOGLE_API_KEY` unavailable, demonstrating that the accepted Gemma provider-discovery path did not depend on hidden Gemini synthesis.

These values are observations from acceptance runs, not benchmark metrics or performance guarantees.

Final regression checkpoint:

```text
53 passed, 1 warning
```

The existing OpenTelemetry dependency deprecation warning remains non-blocking and is not treated as resolved by v0.8.

The v0.8 acceptance claim is intentionally scoped to the flagship provider-discovery workflow. Synthesis adapters exist for other intents, but v0.8 does not claim that all intents have completed equivalent Gemma acceptance testing.

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
    v0.9  GENERALIZE
          Dynamic Retrieval + GUI
                         |
                         v
    v1.0  CONTAINERIZE
          Docker Runtime
                         |
                         v
    v1.1  MEASURE
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

    Gemini / Gemma + Google ADK
      -> Plan, orchestrate, and reason across evidence

    Grounding Layer
      -> Only make claims supported by evidence

This separation is intentional. A provider registry should not be treated as scientific evidence, and biomedical literature should not be used to make unsupported claims about an individual provider.

---

# Planned Milestones

## v1.2.0 - Kubernetes / GKE

Planned focus:

- Kubernetes deployment
- GKE deployment path
- container orchestration for the accepted application runtime

---

The long-term goal is not simply to produce healthcare answers.

The goal is to build and evaluate a **trustworthy agentic AI architecture** in which planning, retrieval, evidence evaluation, tool interoperability, grounding, citations, model execution, and deployment can be independently inspected and improved.
