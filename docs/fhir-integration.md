# FHIR Integration

## Overview

v0.7 adds FHIR R4 healthcare interoperability to the Gemini Healthcare Agentic Platform.

FHIR is integrated as a healthcare data capability behind MCP.

It is not a new agent.

The architecture remains:

```text
Search Planner Agent
        |
        v
Healthcare Research Agent
        |
        v
MCPHealthcareRetrievalOrchestrator
        |
        v
FHIR MCP Server
        |
        v
FHIRClient
        |
        v
FHIR R4 Server
        |
        v
Normalized SearchResult
        |
        v
Evidence & Answer Agent
```

The v0.7 FHIR implementation is designed to answer a technical question:

> Can the agentic healthcare platform discover, retrieve, normalize, score, and safely handle standardized FHIR interoperability records without confusing them with authoritative provider recommendation evidence?

---

# FHIR Version

The implementation targets:

```text
FHIR R4
FHIR version: 4.0.1
```

The default development endpoint is:

```text
https://hapi.fhir.org/baseR4
```

This is a public HAPI FHIR test server.

It is used only for:

- development
- interoperability testing
- MCP validation
- end-to-end architecture validation

It must not be treated as an authoritative real-world provider directory.

---

# Important HAPI Test Server Boundary

The public HAPI FHIR server contains arbitrary development and test records.

Records may:

- be incomplete
- contain synthetic or experimental data
- change over time
- disappear
- fail to match real-world provider information
- use inconsistent terminology
- lack complete provenance

Therefore:

```text
Successful FHIR retrieval
        !=
Verified provider evidence
```

and:

```text
FHIR resource exists
        !=
Provider should be recommended
```

The current development endpoint must not be used for PHI, confidential information, or production clinical workflows.

---

# Supported Resource Types

v0.7 intentionally supports five non-patient healthcare discovery and interoperability resources.

```text
Practitioner
PractitionerRole
Organization
Location
HealthcareService
```

---

## Practitioner

`Practitioner` represents a person involved in healthcare delivery.

It can contain information such as:

```text
identifier
name
telecom
address
qualification
active
```

The platform normalizes only information that is actually present in the resource.

It does not infer professional quality, credential validity, or license standing.

---

## PractitionerRole

`PractitionerRole` describes a practitioner's role in relation to healthcare organizations, specialties, locations, and services.

Conceptually:

```text
Practitioner
     |
     v
PractitionerRole
   /    |       \
  v     v        v
Specialty Organization Location
                     |
                     v
             HealthcareService
```

For provider-oriented interoperability queries, v0.7 prefers `PractitionerRole`.

---

## Organization

`Organization` represents a healthcare organization or related organizational entity.

Possible examples include:

```text
hospital
clinic
practice
health system
department
other healthcare organization
```

The presence of an Organization resource does not establish that it is currently operating, authoritative, or suitable for recommendation.

---

## Location

`Location` represents a physical or logical place where healthcare services may occur.

Possible information includes:

```text
name
address
status
position
managing organization
```

The platform does not infer that a Location resource matches the user's requested geography unless the evidence explicitly supports that match.

---

## HealthcareService

`HealthcareService` represents healthcare services offered by an organization or location.

It may include:

```text
service type
specialty
location
contact information
availability information
```

The platform must not convert the existence of a HealthcareService resource into an unsupported claim that a specific provider currently offers that service.

---

# Resources Intentionally Excluded in v0.7

Patient-specific clinical resources are outside the initial milestone.

Examples include:

```text
Patient
Condition
Observation
Medication
MedicationRequest
Appointment
Encounter
DiagnosticReport
Procedure
CarePlan
```

This is intentional.

The first FHIR milestone focuses on healthcare discovery and interoperability rather than patient-level clinical workflows.

---

# Code Structure

The v0.7 FHIR implementation is primarily located in:

```text
connectors/fhir/
    __init__.py
    client.py
    normalization.py

mcp_services/fhir_server/
    server.py
    tools.py

mcp_services/clients/
    healthcare.py

search/
    mcp_retrieval.py

app/
    config.py
```

Tests are located in:

```text
tests/unit/test_fhir_client.py
tests/unit/test_mcp_fhir.py
tests/unit/test_mcp_clients.py
tests/unit/test_mcp_retrieval.py
tests/unit/test_evidence_ranking.py
```

---

# Configuration

FHIR configuration is defined through application settings.

The default base URL is:

```text
https://hapi.fhir.org/baseR4
```

The configured HTTP timeout is:

```text
20 seconds
```

The connector sends:

```text
Accept: application/fhir+json
```

for FHIR resource retrieval.

---

# FHIR Connector

The FHIR connector is responsible for direct communication with the FHIR R4 endpoint.

Conceptually:

```text
FHIRClient
    |
    v
HTTP GET
    |
    v
FHIR Bundle
    |
    v
Bundle.entry[]
    |
    v
FHIR Resources
    |
    v
Normalization
    |
    v
SearchResult[]
```

The connector accepts only the resource types explicitly supported by v0.7.

---

# Resource Whitelist

The client uses an explicit resource whitelist.

Allowed:

```text
Practitioner
PractitionerRole
Organization
Location
HealthcareService
```

Unsupported resource types are rejected.

For example:

```text
Patient
```

is intentionally outside the v0.7 connector scope.

This boundary helps prevent accidental expansion into patient-level FHIR access.

---

# FHIR Search Methods

The connector exposes convenience methods corresponding to the supported resources.

Conceptually:

```text
search_practitioners(...)
search_practitioner_roles(...)
search_organizations(...)
search_locations(...)
search_healthcare_services(...)
```

Each method uses the shared FHIR request and normalization pipeline.

---

# FHIR Response Handling

FHIR searches normally return a `Bundle`.

Conceptually:

```json
{
  "resourceType": "Bundle",
  "entry": [
    {
      "resource": {
        "resourceType": "PractitionerRole"
      }
    }
  ]
}
```

The connector:

```text
receives Bundle
     |
     v
iterates Bundle.entry
     |
     v
extracts resource
     |
     v
checks supported resource type
     |
     v
normalizes resource
     |
     v
returns SearchResult
```

---

# SearchResult Normalization

All FHIR records are normalized into the platform's shared `SearchResult` model.

FHIR results use:

```text
SourceType.FHIR
```

and:

```text
retrieved_by = "fhir"
```

This allows FHIR evidence to participate in the same downstream pipeline as NPPES and PubMed results.

---

# FHIR Metadata

FHIR-specific metadata is intentionally kept flat and scalar.

Examples include:

```text
fhir_resource_type
fhir_id
fhir_active
```

depending on what the resource contains.

The normalization layer does not create unsupported interpretations.

For example:

```text
FHIR active = true
```

must not be transformed into:

```text
provider has a currently valid professional license
```

The FHIR `active` field and professional licensing status are different concepts.

---

# Resource URLs

Normalized FHIR evidence can retain resource-specific URLs derived from the configured FHIR endpoint.

Conceptually:

```text
https://hapi.fhir.org/baseR4/Practitioner/<id>

https://hapi.fhir.org/baseR4/PractitionerRole/<id>
```

These URLs support traceability and deduplication.

---

# FHIR MCP Server

FHIR access is exposed to the agent runtime through MCP.

The server is implemented with the official MCP SDK.

The v0.7 server uses:

```python
from mcp.server.mcpserver import MCPServer
```

and creates:

```python
MCPServer("healthcare-fhir")
```

FHIR is therefore exposed as a standardized tool capability rather than directly coupling the agent to the connector.

---

# FHIR MCP Tools

The server exposes exactly five v0.7 tools:

```text
search_fhir_practitioners

search_fhir_practitioner_roles

search_fhir_organizations

search_fhir_locations

search_fhir_healthcare_services
```

The relationship is:

```text
MCP Tool
   |
   v
FHIRClient convenience method
   |
   v
FHIR R4 server
   |
   v
normalized SearchResult[]
```

---

# MCP FHIR Client

The agent-side FHIR client is implemented in:

```text
mcp_services/clients/healthcare.py
```

The client uses the official MCP client API asynchronously.

Conceptually:

```python
from mcp import Client

async with Client(mcp) as client:
    result = await client.call_tool(...)
```

The async design is important because Google ADK already operates inside an asyncio event loop.

---

# Why Async-First?

The runtime path is:

```text
Google ADK
    |
    v
async Research Agent tool
    |
    v
async MCP client
    |
    v
FHIR MCP server
    |
    v
FHIR connector
```

Using async MCP access avoids attempting to start a second synchronous event loop inside an already-running ADK event loop.

---

# FHIR MCP Client Methods

The MCP healthcare client exposes methods corresponding to the five FHIR MCP tools.

Conceptually:

```text
search_fhir_practitioners()

search_fhir_practitioner_roles()

search_fhir_organizations()

search_fhir_locations()

search_fhir_healthcare_services()
```

Tool results are converted back into normalized `SearchResult` instances.

---

# Tool Error Handling

MCP tool errors are treated as errors rather than silently converted into successful empty evidence.

Conceptually:

```text
MCP tool call
    |
    v
tool reports error?
   /       \
 yes        no
  |          |
  v          v
raise       parse results
error
```

This prevents a broken tool call from appearing identical to a legitimate "zero results found" response.

---

# Retrieval Orchestration

FHIR participates in the shared healthcare MCP retrieval orchestrator.

```text
MCPHealthcareRetrievalOrchestrator
         |
         +--> NPPES provider retrieval
         |
         +--> PubMed research retrieval
         |
         +--> FHIR interoperability retrieval
```

The orchestrator preserves the separation between the three evidence capabilities.

---

# FHIR Routing Is Explicit

FHIR retrieval is intentionally opt-in.

Normal provider queries do not automatically trigger FHIR.

Normal biomedical queries do not automatically trigger FHIR.

The generated search plan must contain an explicit FHIR or interoperability-oriented query.

Conceptually:

```text
SearchPlan query
      |
      v
Contains explicit FHIR /
interoperability intent?
      |
   +--+--+
   |     |
  yes    no
   |     |
   v     v
FHIR   no FHIR
route  request
```

This reduces unnecessary calls and keeps interoperability evidence separate from ordinary provider retrieval.

---

# Provider Retrieval Remains NPPES-Based

For the flagship provider-discovery workflow:

```text
provider discovery
      |
      v
NPPES
```

FHIR is not used as a replacement for NPPES provider discovery.

This distinction is important.

NPPES and FHIR serve different evidence roles.

---

# Biomedical Retrieval Remains PubMed-Based

Biomedical research queries continue to route through PubMed.

```text
biomedical research
       |
       v
PubMed
```

FHIR does not replace biomedical literature.

---

# FHIR Interoperability Routing

Explicit interoperability-oriented queries can route to FHIR.

Example:

```text
FHIR PractitionerRole pediatric dentistry interoperability
```

The route is:

```text
SearchPlan
    |
    v
FHIR query detected
    |
    v
MCPFHIRClient
    |
    v
search_fhir_practitioner_roles
    |
    v
FHIR MCP Server
    |
    v
FHIRClient
    |
    v
HAPI FHIR R4
```

---

# Why PractitionerRole Is Preferred

For provider-oriented interoperability, `PractitionerRole` is more useful than `Practitioner` alone because it can represent role relationships.

```text
Practitioner
     |
     v
PractitionerRole
   /    |       \
  v     v        v
Specialty Organization Location
```

This allows the architecture to explore how FHIR models provider context.

It does not imply that all returned `PractitionerRole` resources are authoritative provider records.

---

# Specialty-Filtered Search

When a specialty is available in the structured query, the v0.7 retrieval path first attempts a specialty-filtered `PractitionerRole` search.

Conceptually:

```text
specialty = Pediatric Dentistry
        |
        v
FHIR PractitionerRole search
with specialty filter
```

The exact behavior of public FHIR servers depends on their implementation and available data.

---

# Zero-Result Behavior

A valid specialty-filtered query can legitimately return zero results.

For example:

```text
Pediatric Dentistry
        |
        v
HAPI PractitionerRole search
        |
        v
0 results
```

This does not mean:

```text
no pediatric dentists exist
```

It only means the public development FHIR server did not return matching records for that query.

---

# Development Fallback

To verify the complete FHIR architecture, v0.7 includes a development fallback.

When:

```text
explicit FHIR query
+
provider-oriented interoperability
+
specialty available
+
specialty-filtered PractitionerRole returns 0
```

the retrieval path may perform:

```text
unfiltered PractitionerRole search
```

with the configured small result limit.

The purpose is to demonstrate:

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
FHIR connector
 |
 v
FHIR server
 |
 v
normalization
 |
 v
SearchResult[]
```

---

# What the Fallback Does Not Mean

The fallback must not be interpreted as proving:

```text
specialty match
location match
license status
board certification
provider quality
provider suitability
service availability
recommendation suitability
```

The returned test records are architecture evidence, not provider recommendation evidence.

---

# FHIR Result Limit

The v0.7 orchestrator uses a small FHIR limit for development retrieval.

The current flagship path uses:

```text
fhir_limit = 3
```

This is sufficient to demonstrate interoperability without flooding the evidence pipeline with arbitrary development records.

---

# Deduplication

FHIR results pass through the same shared deduplication layer as other normalized evidence.

Conceptually:

```text
NPPES results
PubMed results
FHIR results
      |
      v
combined SearchResult[]
      |
      v
deduplicate
      |
      v
unique SearchResult[]
```

FHIR URLs include the resource type and resource ID, which provides a stable basis for deduplication within a run.

---

# Evidence Scoring

FHIR evidence is scored by the shared grounding pipeline.

However, standardized format does not automatically mean authoritative record content.

For the public HAPI development source, v0.7 uses a conservative authority baseline.

Current development scoring assigns:

```text
FHIR source authority baseline = 0.65
```

This value represents conservative treatment of the public test source.

It must not be generalized to all FHIR servers.

---

# Future Publisher-Aware Authority

A production implementation should not assign one permanent authority score to every FHIR source.

Instead:

```text
FHIR authority
      |
      v
depends on publisher
      |
      +--> trusted health system
      +--> government source
      +--> payer
      +--> provider organization
      +--> public test server
      +--> unknown publisher
```

Future scoring should incorporate provenance and publisher trust.

---

# Provider-Discovery Grounding Safety

FHIR evidence can be:

```text
retrieved
normalized
deduplicated
scored
ranked
observed
```

without being selected to support provider recommendations.

For provider discovery:

```text
FHIR public test record
       |
       v
retained in evidence
       |
       v
scored
       |
       X
provider selection slot
```

This is intentional.

---

# Why FHIR Is Excluded From Provider Grounding Slots

The public HAPI development server is useful for proving interoperability.

It is not suitable for proving:

```text
who should be recommended
which provider is best
whether a provider has an active license
whether a provider is board certified
whether a provider offers anxiety-management services
```

Therefore provider-discovery grounding continues to prioritize authoritative evidence appropriate to the claim type.

---

# Evidence Roles

The current evidence responsibilities are:

```text
NPPES
  |
  v
Provider registry evidence


PubMed
  |
  v
General biomedical evidence


FHIR
  |
  v
Healthcare interoperability evidence
```

These roles should remain distinct.

---

# Example: Safe Interpretation

Suppose FHIR returns:

```text
PractitionerRole
specialty = some value
active = true
```

Allowed interpretation:

```text
"The retrieved FHIR record contains an active field set to true."
```

Not allowed:

```text
"The provider currently holds an active state license."
```

The latter requires authoritative licensing evidence.

---

# Example: HAPI Fallback

Suppose the user requests:

```text
Pediatric Dentistry
Houston, Texas
```

and the specialty-filtered HAPI request returns no records.

The development fallback may retrieve three arbitrary PractitionerRole resources.

Allowed interpretation:

```text
"The FHIR interoperability path returned three PractitionerRole
test records from the public HAPI development server."
```

Not allowed:

```text
"These are pediatric dentists in Houston."
```

unless those facts are independently supported.

---

# v0.7 Flagship Acceptance Run

The flagship query was:

```text
Find three pediatric dentists in Houston for a child who is scared of
going to the dentist. Compare them using trustworthy sources, provider
credentials, services, and location, and explain why you selected each one.
```

One successful v0.7 end-to-end run produced:

```text
Generated queries:       7

Retrieved:               19
Deduplicated:            19

NPPES:                   10
PubMed:                   6
FHIR:                     3
```

The FHIR path used the PractitionerRole development fallback because the specialty-filtered public HAPI query returned zero matching records.

---

# Acceptance Grounding Result

The final selected evidence was:

```text
Selected total: 5

NPPES:  3
PubMed: 2
FHIR:   0
```

This demonstrates the intended behavior:

```text
FHIR path works
        |
        v
FHIR evidence exists
        |
        v
FHIR evidence is visible
        |
        v
FHIR evidence does not become
provider recommendation evidence
```

The observed counts are acceptance-run values, not fixed benchmark claims.

---

# Running the Full ADK Workflow

From the repository root:

```bash
adk run agents
```

Then submit an appropriate healthcare query.

For example:

```text
Find three pediatric dentists in Houston for a child who is scared of
going to the dentist. Compare them using trustworthy sources, provider
credentials, services, and location, and explain why you selected each one.
```

---

# Testing

Run:

```bash
ruff check .
pytest -q
git diff --check
```

The latest v0.7 pre-release checkpoint completed with:

```text
45 passed
```

One OpenTelemetry dependency deprecation warning may appear.

It is currently non-blocking and is not treated as resolved by v0.7.

---

# FHIR-Focused Unit Tests

The FHIR connector tests cover areas such as:

```text
supported resource handling
FHIR Bundle parsing
resource normalization
unsupported resource rejection
```

The MCP FHIR tests cover:

```text
tool discovery
tool invocation
normalized tool output
```

The MCP client tests cover:

```text
async client behavior
FHIR tool result extraction
tool error behavior
```

The retrieval tests cover:

```text
explicit FHIR routing
PractitionerRole routing
specialty-filtered retrieval
fallback behavior
deduplication
```

The evidence-ranking tests cover:

```text
FHIR scoring
FHIR retention
provider-discovery selection safety
3 provider + 2 PubMed selection preservation
```

---

# Common Development Behaviors

## Specialty Search Returns Zero Results

This can be expected with the public HAPI development server.

It does not indicate that the connector is broken.

Verify whether the development fallback returns normalized PractitionerRole records.

---

## Different HAPI Results Across Runs

The public test server is mutable.

Records may change or be purged.

Do not write architecture assumptions that depend on a specific test record always existing.

---

## OpenTelemetry Warning

The current test suite may emit an OpenTelemetry-related `SelectableGroups` deprecation warning.

This warning is unrelated to the core v0.7 FHIR functionality.

It is currently non-blocking.

Do not claim it has been fixed unless the underlying dependency behavior is actually changed and verified.

---

## MCP Tool Error

A tool error should raise an error rather than silently appear as an empty successful search.

Check:

```text
FHIR server startup
tool name
tool arguments
connector request
FHIR endpoint
HTTP response
```

---

## Unsupported Resource Type

If a request attempts to access a resource outside the v0.7 whitelist, the connector should reject it.

For example:

```text
Patient
```

is intentionally unsupported.

---

# Safety Boundaries

The v0.7 FHIR integration does not perform:

```text
diagnosis
treatment recommendation
clinical decision support
patient-specific reasoning
license verification
board-certification verification
quality scoring
provider ranking based on FHIR
```

The integration is focused on architecture and interoperability.

---

# PHI Boundary

Do not send:

```text
patient names
medical record numbers
patient identifiers
clinical notes
diagnoses tied to individuals
confidential health information
```

to the public HAPI test endpoint.

The public endpoint is not part of a production privacy architecture.

---

# Production FHIR Requirements

Before connecting production healthcare data, the architecture should be extended for:

```text
authentication
authorization
access scopes
secret management
audit logging
PHI controls
data minimization
provenance
publisher trust
terminology systems
coded specialties
rate limiting
timeouts
retries
error classification
observability
tool authorization
prompt-injection defenses
```

These are not part of the initial v0.7 milestone.

---

# Production Authority Model

A future trusted FHIR environment should distinguish source authority by publisher.

For example:

```text
FHIR Source
    |
    +--> public test server
    |        |
    |        v
    |    low evidence authority
    |
    +--> trusted health system
    |        |
    |        v
    |    organization-level authority
    |
    +--> government source
             |
             v
         potentially high authority
         for appropriate claim types
```

Authority must remain claim-specific.

A highly trusted organization still may not be authoritative for every type of claim.

---

# Future Terminology Improvements

The current public-server demonstration uses practical search parameters suitable for the v0.7 architecture milestone.

Future production integrations should prefer coded terminology when supported.

Examples may include:

```text
specialty coding
service coding
organization type coding
location relationships
identifier systems
```

This would reduce dependence on free-text specialty matching.

---

# Future Provenance

Production FHIR integration should consider:

```text
Provenance
meta.source
identifier systems
organization ownership
lastUpdated
publisher trust
resource lineage
```

Evidence scoring can then use actual provenance rather than assuming equal trust across FHIR servers.

---

# Future Authentication

Many production FHIR systems require authenticated access.

Possible production patterns may include:

```text
SMART on FHIR
OAuth 2.0
service-to-service credentials
scoped application access
```

Authentication is intentionally not required for the public HAPI v0.7 development server.

---

# Architectural Principle

FHIR extends the platform's interoperability capabilities.

It does not replace evidence validation.

The relationship is:

```text
FHIR
  |
  v
standardized healthcare data
  |
  v
normalized evidence
  |
  v
grounding rules
  |
  v
claim-safe answer
```

not:

```text
FHIR
  |
  v
automatically trusted answer
```

The core system rule remains:

> **No evidence → no claim.**
