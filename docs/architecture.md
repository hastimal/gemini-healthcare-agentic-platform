# Architecture

## Overview

The Gemini Healthcare Agentic Platform is designed as a layered healthcare AI architecture that separates:

- planning
- retrieval
- healthcare data access
- evidence evaluation
- grounding
- answer generation

The platform intentionally uses exactly three core agents.

FHIR is not a fourth agent.

FHIR, NPPES, and PubMed are data capabilities accessed through MCP-backed tools.

v0.8 adds a model-provider boundary so the same three Google ADK agents can run with hosted Gemini or locally operated Gemma through Ollama and LiteLLM.

---

## High-Level Architecture

```text
User
 |
 v
Search Planner Agent
 |
 v
SearchPlan
 |
 v
Healthcare Research Agent
 |
 v
MCPHealthcareRetrievalOrchestrator
 |        |         |
 v        v         v
Search   Research   FHIR
MCP      MCP        MCP
 |        |          |
 v        v          v
NPPES   PubMed     FHIR R4
                   HAPI test
 \        |         /
  \       |        /
   \      |       /
    v     v      v
      SearchResult[]
           |
           v
Evidence & Answer Agent
           |
           v
Score
 |
 v
Rank
 |
 v
Select Evidence
 |
 v
Build Citations
 |
 v
Grounded Answer
 |
 v
Limitations + Transparency
```

The central design principle is:

> **No evidence → no claim.**

---

# Core Agents

## 1. Search Planner Agent

The Search Planner Agent converts a user request into a structured search plan.

### Input

```text
User healthcare question
```

Example:

```text
Find three pediatric dentists in Houston for a child who is scared of
going to the dentist. Compare them using trustworthy sources, provider
credentials, services, and location, and explain why you selected each one.
```

### Responsibilities

The planner:

- identifies user intent
- extracts structured query information
- identifies specialty or topic
- extracts geographic constraints
- generates query fan-out
- creates a structured `SearchPlan`
- identifies useful source categories
- generates explicit FHIR/interoperability queries when appropriate

### Output

Conceptually:

```text
UserQuery
+
SearchPlan
```

The plan can contain multiple queries with different purposes.

For example:

```text
Provider registry discovery
Professional-directory source discovery
State-license-source discovery
Biomedical evidence retrieval
FHIR interoperability discovery
```

### Important Boundary

The planner performs planning.

It does not itself prove that:

- a credential is valid
- a license is active
- a provider is board certified
- a provider offers a particular service
- a provider is suitable for a particular patient
- a professional directory was successfully retrieved
- a licensing authority was successfully queried

Generating a query for an authoritative source is not equivalent to completing verification against that source.

---

# 2. Healthcare Research Agent

The Healthcare Research Agent executes the structured retrieval plan.

It acts as the boundary between agent reasoning and deterministic healthcare retrieval.

### Input

```text
UserQuery
+
SearchPlan
```

### Responsibilities

The Research Agent:

- validates planner output
- normalizes structured handoff data
- executes healthcare retrieval
- calls MCP-backed healthcare capabilities
- retrieves provider registry evidence
- retrieves biomedical evidence
- retrieves FHIR interoperability evidence
- deduplicates results
- preserves source metadata
- returns normalized `SearchResult` objects

### Output

Conceptually:

```text
SearchResult[]
+
retrieval counts
+
source counts
```

The Research Agent does not produce the final healthcare answer.

---

## Defensive Planner Handoff

v0.8 strengthens the planner-to-research handoff by treating Google ADK session state as the authoritative workflow boundary.

```text
Planner Output
     |
     v
ADK State
     |
     v
Healthcare Research Agent
     |
     v
retrieve_healthcare_evidence()
     |
     v
Tool reads planner_output from state
```

The model no longer needs to reconstruct the full `UserQuery` and `SearchPlan` as tool-call arguments.

The same pattern is used for the Research → Evidence handoff: the Evidence tool reads authoritative `research_output` from ADK state.

This reduces unnecessary model-dependent structured-data transformation while preserving the same three-agent architecture.

---

# 3. Evidence & Answer Agent

The Evidence & Answer Agent receives the normalized evidence and decides what can safely support the answer.

### Input

```text
UserQuery
+
SearchPlan
+
SearchResult[]
```

### Responsibilities

The agent:

- scores evidence
- ranks evidence
- applies evidence-selection rules
- builds deterministic citations
- restricts answer generation to selected evidence
- exposes limitations
- reports retrieval transparency

### Output

Conceptually:

```text
GroundedAnswer
+
citations
+
selected evidence
+
limitations
+
transparency metadata
```

The Evidence & Answer Agent is the final reasoning stage.

It must not convert unsupported assumptions into claims.

---

# MCP Architecture

MCP provides a standardized tool boundary between the agent runtime and healthcare capabilities.

The platform currently uses three healthcare MCP paths.

```text
Healthcare Research Agent
            |
            v
MCPHealthcareRetrievalOrchestrator
       /         |         \
      v          v          v
 Search MCP  Research MCP  FHIR MCP
```

---

## Search MCP

The Search MCP server provides provider-discovery capabilities.

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

The MCP layer standardizes tool invocation.

The NPPES connector remains responsible for communicating with CMS NPPES.

---

## Research MCP

The Research MCP server provides biomedical-literature retrieval.

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

PubMed evidence is used for general scientific context.

It must not be converted into unsupported claims about an individual provider.

---

## FHIR MCP

v0.7 introduces the FHIR MCP server.

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
SearchResult
```

The default development endpoint is:

```text
https://hapi.fhir.org/baseR4
```

This public HAPI FHIR endpoint is used only for development and interoperability testing.

Its records must not be treated as authoritative real-world provider evidence.

---

# FHIR MCP Tools

The v0.7 FHIR MCP server exposes:

```text
search_fhir_practitioners
search_fhir_practitioner_roles
search_fhir_organizations
search_fhir_locations
search_fhir_healthcare_services
```

These tools map to five supported FHIR R4 resource types:

```text
Practitioner
PractitionerRole
Organization
Location
HealthcareService
```

---

# Why FHIR Is Not an Agent

FHIR does not make planning or reasoning decisions.

It is a healthcare interoperability standard and data-access capability.

Therefore the architecture remains:

```text
3 Agents
+
MCP Tools
+
Healthcare Data Sources
```

not:

```text
4 Agents
```

The separation is important because it keeps reasoning responsibilities distinct from data-access responsibilities.

---

# Evidence Architecture

The platform separates evidence roles by source.

```text
                Healthcare Evidence
                       |
        +--------------+--------------+
        |              |              |
        v              v              v
      NPPES          PubMed          FHIR
        |              |              |
        v              v              v
 Provider Registry   Scientific   Interoperability
    Evidence          Evidence       Evidence
```

---

## NPPES Evidence Role

NPPES answers questions such as:

```text
Who is the provider?
What is the NPI?
What taxonomy is reported?
What location is reported?
What license metadata is reported by NPPES?
```

NPPES may support:

- provider identity
- NPI
- taxonomy
- registry location
- NPPES-reported license metadata

NPPES alone does not establish:

- active license status
- good standing
- board certification
- provider quality
- patient satisfaction
- anxiety-management services
- sedation availability
- suitability for a particular patient

---

## PubMed Evidence Role

PubMed answers questions such as:

```text
What scientific evidence applies generally?
What does biomedical literature say about the topic?
What evidence exists about dental anxiety or related interventions?
```

PubMed may support:

- biomedical context
- general scientific evidence
- systematic reviews
- clinical research

PubMed evidence is general scientific evidence unless the publication itself explicitly supports an individual provider-specific claim.

---

## FHIR Evidence Role

FHIR answers interoperability-oriented questions such as:

```text
How are practitioners represented?
How are practitioner roles represented?
How can an organization relate to a practitioner?
How can locations and services be represented?
How are these healthcare resources linked?
```

FHIR can represent relationships among:

```text
Practitioner
     |
     v
PractitionerRole
   /    |      \
  v     v       v
Role Specialty Organization
                 |
                 v
              Location
                 |
                 v
        HealthcareService
```

FHIR structure alone does not establish:

- provider quality
- provider suitability
- active licensure
- board certification
- good standing
- service availability
- patient satisfaction

---

# FHIR Standard Authority vs Record Authority

FHIR itself is an authoritative interoperability standard.

An individual FHIR record is only as authoritative as its publisher and provenance.

Therefore:

```text
FHIR Standard Authority
          !=
FHIR Record Authority
```

For example:

```text
Trusted health-system FHIR server
        |
        v
Potentially authoritative organizational data


Public development FHIR server
        |
        v
Useful for interoperability testing
but not authoritative provider evidence
```

v0.7 uses the public HAPI development server.

FHIR evidence from that server is therefore handled conservatively.

---

# FHIR Resource Scope

v0.7 supports only:

```text
Practitioner
PractitionerRole
Organization
Location
HealthcareService
```

Patient-specific clinical resources are intentionally excluded from the initial milestone.

Examples outside the v0.7 scope include:

```text
Patient
Condition
Observation
Medication
Appointment
```

This keeps v0.7 focused on non-patient healthcare discovery and interoperability.

---

# SearchResult Normalization

All retrieval paths normalize evidence into a shared `SearchResult` representation.

Conceptually:

```text
NPPES Response
      |
      v
SearchResult


PubMed Response
      |
      v
SearchResult


FHIR Resource
      |
      v
SearchResult
```

This gives downstream components a common evidence interface.

FHIR results use:

```text
SourceType.FHIR
```

and identify the retrieval path as:

```text
retrieved_by = "fhir"
```

FHIR-specific metadata remains flat and scalar so it can safely fit the shared search-result model.

Examples include:

```text
fhir_resource_type
fhir_id
fhir_active
```

when those values are available.

---

# FHIR Retrieval Routing

FHIR is intentionally opt-in.

Normal provider-discovery or biomedical queries do not automatically trigger FHIR.

The planner must create an explicit FHIR or interoperability-oriented query.

Conceptually:

```text
Generated Query
      |
      v
Is this explicitly FHIR/interoperability related?
      |
    +---+---+
    |       |
   yes      no
    |       |
    v       v
 FHIR     Skip FHIR
 retrieval
```

This prevents unnecessary FHIR traffic and avoids mixing interoperability data into unrelated retrieval paths.

---

# PractitionerRole Retrieval

For provider-oriented interoperability, v0.7 prefers `PractitionerRole`.

This is useful because `PractitionerRole` can connect:

```text
Practitioner
+
Specialty
+
Organization
+
Location
+
Service context
```

The development retrieval strategy is:

```text
FHIR query
   |
   v
Specialty available?
   |
  yes
   |
   v
Search PractitionerRole
with specialty
   |
   v
Any results?
 /       \
yes       no
 |         |
 v         v
Use      Fallback to
results  unfiltered
         PractitionerRole
```

The fallback exists because the public HAPI test server may not contain records matching a requested free-text specialty.

---

# FHIR Fallback Safety

An unfiltered development fallback proves only that the technical interoperability path works.

It can demonstrate:

```text
ADK
 |
 v
MCP
 |
 v
FHIR Tool
 |
 v
FHIR API
 |
 v
Normalization
 |
 v
Evidence Pipeline
```

It does not prove:

```text
requested specialty
requested location
provider suitability
provider quality
license validity
board certification
service availability
```

Therefore these FHIR test records are not used as provider recommendations.

---

# Deduplication

All normalized results pass through a shared deduplication stage.

```text
Retrieved SearchResult[]
          |
          v
      Deduplicate
          |
          v
Unique SearchResult[]
```

This occurs across the common evidence pipeline before ranking and answer generation.

---

# Evidence Scoring

Evidence scoring considers factors such as:

```text
Source Authority
Relevance
Evidence Quality
```

The exact score is not intended to mean that all records from a standardized source are equally authoritative.

For FHIR in v0.7, the default public HAPI development source receives conservative authority treatment.

Future production FHIR integrations should make authority dependent on the actual publisher and provenance.

---

# Evidence Ranking

The ranking layer receives all normalized evidence.

```text
NPPES
PubMed
FHIR
   |
   v
Score
   |
   v
Rank
```

FHIR evidence can remain visible and scored in the evidence pipeline.

However, for provider-discovery workflows using the public HAPI development server, FHIR records are prevented from taking the evidence slots used to support provider selections.

---

# Provider-Discovery Evidence Selection

The provider-discovery path intentionally preserves a mixed evidence set.

Conceptually:

```text
Selected Evidence
      |
      +--> provider registry evidence
      |
      +--> supporting biomedical evidence
```

In the v0.7 flagship acceptance run:

```text
Selected: 5

NPPES: 3
PubMed: 2
FHIR: 0
```

FHIR evidence was still retrieved and processed.

It was simply not used as evidence supporting the selected providers.

This distinction is intentional:

```text
retrieved
   !=
selected for grounding
```

---

# Grounding Architecture

The grounding layer sits between retrieval and answer generation.

```text
SearchResult[]
      |
      v
Scoring
      |
      v
Ranking
      |
      v
Evidence Selection
      |
      v
Citation Construction
      |
      v
Evidence-Restricted Context
      |
      v
Grounding Policy
      |
      +--> Provider Discovery -> Deterministic Grounding
      |
      +--> Other supported intents -> Configured Synthesis Provider
      |
      v
Grounded Answer
```

The language model should reason only from evidence made available by the grounding layer.

---

# Claim Safety

A claim should only appear when evidence supports it.

Examples:

```text
Evidence:
NPPES shows taxonomy = Pediatric Dentistry

Allowed:
"NPPES reports a pediatric dentistry taxonomy."


Evidence:
Public HAPI PractitionerRole record exists

Not allowed:
"This provider is a qualified pediatric dentist."


Evidence:
PubMed research discusses dental anxiety generally

Allowed:
"Published research describes dental anxiety as an important concern."


Not allowed:
"This specific dentist is good with anxious children."
```

The final system principle remains:

> **No evidence → no claim.**

---

# End-to-End Data Flow

```text
1. User submits healthcare request
            |
            v
2. Search Planner Agent
   - parses intent
   - extracts structured query
   - generates search plan
            |
            v
3. Healthcare Research Agent
   - validates plan
   - executes MCP retrieval
            |
      +-----+-----+
      |     |     |
      v     v     v
   NPPES PubMed  FHIR
      |     |     |
      +-----+-----+
            |
            v
4. Normalize to SearchResult[]
            |
            v
5. Deduplicate
            |
            v
6. Evidence & Answer Agent
   - score
   - rank
   - select
   - cite
            |
            v
7. Grounded answer construction
            |
            v
8. Answer
   - claims
   - citations
   - limitations
   - transparency
```

---

# v0.7 Flagship Acceptance Path

The flagship query exercises the architecture across the three evidence capabilities.

```text
User Query
   |
   v
Search Planner Agent
   |
   v
7 generated queries
   |
   v
Healthcare Research Agent
   |
   +--> NPPES
   |
   +--> PubMed
   |
   +--> FHIR PractitionerRole
   |
   v
19 retrieved results
   |
   v
19 deduplicated results
   |
   v
Evidence & Answer Agent
   |
   v
5 selected evidence records
   |
   +--> 3 NPPES
   |
   +--> 2 PubMed
   |
   +--> 0 public HAPI FHIR records
   |
   v
Grounded Answer
```

The observed run contained:

```text
NPPES retrieved: 10
PubMed retrieved: 6
FHIR retrieved:   3

Total retrieved: 19
Total deduped:    19

Selected NPPES:  3
Selected PubMed: 2
Selected FHIR:   0
```

These are values from one successful acceptance run, not performance guarantees or benchmark metrics.

---

# Async Execution

Google ADK runs tools in an asynchronous environment.

The MCP client path therefore remains async-first.

```text
Google ADK
    |
    v
async Research Agent Tool
    |
    v
await MCPHealthcareRetrievalOrchestrator.retrieve()
    |
    +--> await MCPProviderClient
    |
    +--> await MCPPubMedClient
    |
    +--> await MCPFHIRClient
```

This avoids creating nested synchronous event-loop execution inside the ADK runtime.

---

# Architectural Boundaries

The system deliberately separates responsibilities.

```text
Planning
   |
   v
Search Planner Agent


Retrieval
   |
   v
Healthcare Research Agent


Tool Protocol
   |
   v
MCP


External Healthcare Data
   |
   +--> NPPES
   +--> PubMed
   +--> FHIR


Evidence Evaluation
   |
   v
Evidence & Answer Agent


Model Execution
   |
   +--> Gemini
   |
   +--> Gemma / Ollama

Provider Discovery
   |
   v
Deterministic Evidence-Bound Grounding
```

This separation makes it easier to replace individual layers later without redesigning the whole system.

---

# v0.8 Model Portability

v0.8 introduces two model-execution paths behind the same Google ADK agent architecture.

```text
                         MODEL_PROVIDER
                              |
                 +------------+------------+
                 |                         |
                 v                         v
              Gemini                     Gemma
           Google hosted                  |
                                          v
                                       Ollama
                                          |
                                          v
                                       LiteLLM
                 |                         |
                 +------------+------------+
                              |
                              v
                         Google ADK
                              |
                 +------------+------------+
                 |            |            |
                 v            v            v
              Planner      Research      Evidence
               Agent         Agent         Agent
```

The MCP tools, healthcare connectors, evidence normalization, scoring, ranking, selection, citations, and healthcare safety boundaries remain shared.

## Provider-Discovery Grounding

For the flagship provider-discovery workflow, the final provider answer is deterministic after evidence selection.

```text
Selected Evidence
      |
      v
Deterministic Citations
      |
      v
Provider-Scoped Claim Construction
      |
      v
Grounded Answer
```

Models reason and invoke tools; deterministic code owns high-risk provider claims.

The accepted v0.8 portability claim is scoped to the flagship provider-discovery workflow. The project does not claim identical model behavior, latency, or quality, and it does not claim that all other intents have completed equivalent Gemma acceptance testing.

See `docs/model-portability.md` for the detailed design.

---

# Future Production FHIR Architecture

The public HAPI server is appropriate for interoperability testing but not for production healthcare evidence.

A future trusted FHIR architecture may look like:

```text
Healthcare Research Agent
        |
        v
FHIR MCP Server
        |
        v
FHIR Connector
        |
        v
Authenticated Production FHIR Server
        |
        +--> trusted organization
        |
        +--> provenance
        |
        +--> terminology
        |
        +--> coded specialties
        |
        +--> access controls
```

Evidence authority should then depend on:

```text
Publisher
Provenance
Resource type
Data governance
Trust level
```

rather than treating all FHIR sources as equivalent.

---

# Security and Privacy Boundary

v0.7 intentionally avoids patient-level FHIR resources.

Before expanding into patient-specific clinical data, the platform would need explicit design for areas such as:

```text
Authentication
Authorization
PHI handling
Access control
Auditability
Data minimization
Secrets management
Consent
Logging policy
Prompt-injection defenses
Tool authorization
```

Those concerns are outside the initial v0.7 interoperability milestone.

---

# Design Principles

```text
Exactly three reasoning agents

Tools are not agents

FHIR is interoperability evidence, not provider-quality evidence

Source authority and record authority are different

Planning a verification query is not verification

Biomedical evidence is not provider-specific evidence

Retrieval does not imply grounding

Grounding does not allow unsupported inference

No evidence -> no claim
```

These principles are intended to remain stable as the platform expands.
---

# v0.9 — Generalized Query Planning + Dynamic Retrieval + GUI

## Before v0.9

```text
User Question -> Planner -> Houston/Pediatric Dentistry assumptions -> Retrieval
```

## After v0.9

```text
Any Supported Healthcare Question
        |
        v
Search Planner Agent
(intent + optional location + optional specialty + dynamic queries)
        |
        v
Healthcare Research Agent
   /        |        \
NPPES     PubMed     FHIR
   \        |        /
        v
SearchResult[]
        |
        v
Evidence & Answer Agent
        |
        v
One Streamlit UI -> Gemini OR Gemma/Ollama
```

The LLM planner is the semantic reasoning layer. Deterministic code normalizes and constructs the `SearchPlan`; retrieval follows planner state. Provider discovery derives location and specialty from the current query, with a conservative NPPES specialty resolver for common wording differences. Biomedical research/health-information routes to PubMed; explicit interoperability queries route to FHIR.

Provider discovery remains evidence-restricted. NPPES supports identity/NPI/taxonomy/reported location, not “best” ranking, board certification, active licensure, good standing, clinical quality, or service availability. Public HAPI FHIR data remains interoperability evidence, not provider-quality evidence.

`ui/streamlit_app.py` is the single UI for both model paths. The model is selected before process startup; the UI exposes grounded answer, search plan, evidence, citations, limitations, research state, and the Google ADK event trace.

Final acceptance: 85 passed / 5 skipped deterministic tests; live UI E2E 5/5 Gemini and 5/5 Gemma. See `examples/v0.9-acceptance.md`.
