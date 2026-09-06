# Model Portability

## v0.8 — Gemini + Gemma / Ollama

v0.8 introduces model-runtime portability to the Google ADK healthcare multi-agent architecture.

The goal is not to decide which model is better.

The goal is to demonstrate that the same application architecture can use either hosted Gemini or locally operated Gemma without duplicating healthcare retrieval, evidence ranking, citations, or safety logic.

## Architecture

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
                 EXACT SAME 3 AGENTS
                              |
        +---------------------+---------------------+
        |                     |                     |
        v                     v                     v
 Search Planner Agent   Healthcare Research   Evidence &
                              Agent          Answer Agent
                                |
                                v
                            MCP Tools
                      +---------+---------+
                      |         |         |
                      v         v         v
                    NPPES     PubMed     FHIR
                      \         |         /
                       \        |        /
                        v       v       v
                        Evidence Ranking
                              |
                              v
                    Deterministic Citations
                              |
                              v
                     Grounding Policy
                              |
                              v
                    Grounded Answer
```

## Runtime Roles

### Gemini

Gemini is the hosted Google model path.

Google ADK receives the configured Gemini model directly.

### Gemma

Gemma provides the local/open-model path.

The v0.8 local development runtime is:

```text
Google ADK
   |
   v
LiteLLM
   |
   v
Ollama
   |
   v
Gemma
```

Ollama is the local model runtime.

LiteLLM acts as the adapter between Google ADK and the Ollama-hosted Gemma model.

Neither Ollama nor LiteLLM is application business logic.

## Model Factory

The three core agents use a shared model factory.

Conceptually:

```text
MODEL_PROVIDER=gemini
        |
        v
      Gemini

MODEL_PROVIDER=gemma
        |
        v
     LiteLLM
        |
        v
 Ollama / Gemma
```

## Why State-Based Handoffs Matter

Model portability is more than replacing a model name.

Different models may reconstruct large structured objects differently.

The Research and Evidence tool boundaries therefore read authoritative workflow data from Google ADK session state.

### Before

```text
Planner Output
      |
      v
Research LLM
      |
      v
reconstruct/copy large SearchPlan
      |
      v
Research Tool
```

### After

```text
Planner Output
      |
      v
ADK State
      |
      v
Research Agent
      |
      v
retrieve_healthcare_evidence()
      |
      v
Tool reads planner_output from state
```

The same principle is used for the Research → Evidence handoff.

This reduces unnecessary model-dependent structured-data transformation.

## Provider-Discovery Safety Boundary

The flagship provider-discovery workflow uses deterministic final grounding.

```text
Gemini OR Gemma
      |
      v
Agent Reasoning
      |
      v
Tool Invocation
      |
      v
MCP Retrieval
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
Deterministic Provider Claims
      |
      v
Grounded Answer
```

Models reason and invoke tools.

Deterministic code owns the safety-critical provider claim boundary.

This prevents unsupported claims about:

- active licensure
- good standing
- board certification
- clinical quality
- patient satisfaction
- anxiety-management expertise
- sedation availability
- other provider-specific services

unless the selected evidence explicitly supports them.

## Evidence Boundaries

### NPPES

May support:

- provider identity
- NPI
- reported location
- taxonomy
- NPPES-reported license metadata

NPPES alone does not establish active/current licensure, good standing, board certification, provider quality, or service availability.

### PubMed

Supports general biomedical and scientific context.

PubMed evidence is not converted into a claim about an individual provider unless the source explicitly supports that provider-level claim.

### FHIR

FHIR provides healthcare interoperability evidence.

The public HAPI FHIR R4 endpoint used for development contains test/development records.

Those records remain observable in retrieval and scoring but do not consume provider recommendation grounding slots.

## Configuration

Gemini:

```bash
MODEL_PROVIDER=gemini
GEMINI_API_KEY=...
GEMINI_MODEL=...
```

Gemma / Ollama:

```bash
MODEL_PROVIDER=gemma
OLLAMA_BASE_URL=http://localhost:11434
GEMMA_MODEL=...
```

## What v0.8 Does Not Claim

v0.8 does not claim:

- Gemini and Gemma have identical latency
- Gemini and Gemma have identical reasoning behavior
- one model is more accurate than the other
- local execution is automatically HIPAA compliant
- Ollama makes healthcare data automatically private or secure
- public HAPI FHIR records are production healthcare evidence

Formal model comparison belongs to the v1.0 evaluation benchmark.

## Acceptance

Both configured model paths completed the flagship Google ADK three-agent workflow during v0.8 acceptance testing.

The Gemma acceptance run was performed with Gemini API credentials unavailable, demonstrating that the Gemma path did not depend on hidden Gemini synthesis.

See:

```text
examples/v0.8-acceptance.md
```
