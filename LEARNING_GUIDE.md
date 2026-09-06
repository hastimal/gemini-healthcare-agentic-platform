# Learning Guide

This guide is for programmers who want to understand, run, test, and extend the platform.

## End-to-end flow

```text
User Question
  -> Search Planner Agent
  -> SearchPlan
  -> Healthcare Research Agent
  -> MCP tools
  -> NPPES / PubMed / FHIR
  -> SearchResult[]
  -> Evidence & Answer Agent
  -> grounded answer + citations + limitations
```

Exactly three agents are used. NPPES, PubMed, and FHIR are tools/data capabilities, not agents.

## Build evolution

- **v0.1:** Gemini query planning and fan-out.
- **v0.2:** real NPPES and PubMed retrieval normalized into shared results.
- **v0.3:** evidence scoring/ranking.
- **v0.4:** grounded answers and deterministic citations; `No evidence -> no claim`.
- **v0.5:** Google ADK three-agent orchestration.
- **v0.6:** MCP tool layer wrapping/reusing existing NPPES/PubMed connectors.
- **v0.7:** FHIR R4 interoperability for Practitioner, PractitionerRole, Organization, Location, and HealthcareService.
- **v0.8:** Gemini plus Gemma/Ollama model portability through the same ADK architecture.
- **v0.9:** generalized planning/retrieval plus one Streamlit UI.

## v0.6 architecture change

```text
BEFORE v0.6
Healthcare Research Agent -> Python NPPES/PubMed connectors

AFTER v0.6
Healthcare Research Agent -> MCP tools (find_providers/search_pubmed)
                          -> existing NPPES/PubMed connectors
```

## v0.9 generalization

GUI testing exposed Houston/Pediatric Dentistry assumptions. The rule became: **the flagship query is a test case, not application configuration.**

The configured model now infers intent, optional location, optional specialty, and generated queries. Deterministic `QueryFanoutPlanner` normalizes/deduplicates/caps the plan without a hidden direct Gemini call. Retrieval follows planner state. Provider discovery derives city/state/specialty from the current query; a conservative NPPES specialty resolver bridges common wording differences. Biomedical research routes to PubMed; explicit interoperability routes to FHIR.

The same `ui/streamlit_app.py` runs Gemini or Gemma/Ollama. Models may infer optional metadata differently; acceptance tests behavioral routing and evidence boundaries rather than requiring identical metadata.

## Run and test

```bash
pytest -q
ruff check .
git diff --check
./scripts/test-ui.sh gemini
./scripts/test-ui.sh gemma
./scripts/demo-local.sh gemini
./scripts/demo-stop.sh
./scripts/demo-local.sh gemma
```

The interactive GUI is `http://localhost:8501`. `test-ui.sh` is an automated acceptance runner and is not the interactive demo launcher.

## v0.9 acceptance queries

```text
Find cardiologists in Dallas, TX
Find neurologists in Austin, TX
What does research say about childhood dental anxiety?
Explain FHIR PractitionerRole and how it represents provider relationships.
Find three pediatric dentists in Houston for a child who is scared of going to the dentist. Compare them using trustworthy sources, provider credentials, services, and location, and explain why you selected each one.
```

## Extension rule

When adding a source or intent: define the connector/tool path, normalization, source authority, grounding boundary, deterministic tests, explicit failure behavior, and only then live acceptance. Do not add an enum value and silently route it through an unrelated connector.

## Next

v1.0 packages accepted v0.9 behavior into a reproducible Docker runtime. Packaging should not change healthcare evidence semantics.
