# Learning Guide

This guide is for programmers who want to reproduce, run, test, evaluate, and extend the platform from the command line. It is intentionally a **how-to guide**, not a release summary.

## 1. Clone and set up the project

```bash
git clone https://github.com/hastimal/gemini-healthcare-agentic-platform.git
cd gemini-healthcare-agentic-platform
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Configure a model path

### Gemini

Keep the Gemini API key in your local `.env`. Never commit `.env` or paste the key into terminal output, screenshots, issues, or documentation.

```bash
export MODEL_PROVIDER=gemini
```

### Gemma + Ollama

Confirm Ollama and the configured Gemma model are available:

```bash
ollama list
export MODEL_PROVIDER=gemma
```

The Gemma path uses LiteLLM as the Google ADK model adapter and Ollama as the local runtime.

## 3. Understand the application flow

```text
User Question
  -> Search Planner Agent
  -> SearchPlan
  -> Healthcare Research Agent
  -> MCP retrieval
      -> NPPES
      -> PubMed
      -> FHIR
  -> SearchResult[]
  -> Evidence & Answer Agent
  -> grounded answer + citations + limitations
```

There are exactly three core agents. NPPES, PubMed, FHIR, and MCP services are tools/data capabilities, not agents.

Two rules should remain visible while extending the platform:

> **The flagship query is a test case, not application configuration.**

> **No evidence → no claim.**

## 4. Validate the repository before changing code

```bash
ruff check .
pytest -q
git diff --check
```

Use focused tests during development, then run the full suite before committing.

Avoid repository-wide formatting unless the formatting change itself is intentional. Keep feature commits focused.

## 5. Run the local application

Gemini:

```bash
./scripts/demo-local.sh gemini
```

Gemma:

```bash
./scripts/demo-local.sh gemma
```

Stop:

```bash
./scripts/demo-stop.sh
```

Open:

```text
http://localhost:8501
```

## 6. Run the Docker application

Gemini:

```bash
./scripts/demo-docker.sh gemini
```

Gemma on macOS:

```bash
./scripts/demo-docker.sh gemma
```

Stop:

```bash
./scripts/demo-docker-stop.sh
```

On macOS, the healthcare application is containerized while Ollama remains native on the host. Docker reaches it through `host.docker.internal:11434`.

This topology does not automatically make the application HIPAA compliant, PHI-safe, secure, private, or production-ready.

## 7. Deploy and run on Google Kubernetes Engine

v1.2 adds a cloud-native runtime around the same Gemini + Google ADK three-agent application.

The important separation is:

    AGENT INTELLIGENCE
    Gemini + Google ADK + MCP
              |
              v
    APPLICATION
    Python + Streamlit
              |
              v
    CONTAINER
    Docker
              |
              v
    ORCHESTRATION
    Kubernetes
              |
              v
    GOOGLE CLOUD
    Google Kubernetes Engine (GKE)

The Kubernetes resources live under:

    deployment/kubernetes/

They include:

    namespace.yaml
    configmap.yaml
    secret.example.yaml
    deployment.yaml
    service.yaml

The GKE deployment includes:

- CPU and memory requests/limits
- readiness probe
- liveness probe
- Streamlit port `8501`
- ConfigMap-based runtime configuration
- Secret injection
- Kubernetes Service routing

The health endpoint is:

    /_stcore/health

A healthy runtime should show approximately:

    Pod:         1/1 Running
    Restarts:    0
    Deployment:  1/1 Available

The deployment layer does not create another AI agent. The platform still has exactly three core Google ADK agents.

## 8. Run an on-demand public GKE demo

The application does not need a permanent public IP.

For normal private cluster access, the Service can use:

    ClusterIP

When a public demo is needed, use:

    ./scripts/demo-up.sh

The script changes the Service to `LoadBalancer`, waits for GKE to assign an external IP, discovers that IP automatically, and prints the current demo URL.

The flow is:

    Need Demo
       |
       v
    ClusterIP
       |
       v
    LoadBalancer
       |
       v
    GKE assigns external IP
       |
       v
    Script discovers IP
       |
       v
    Streamlit UI
       |
       v
    Google ADK + Gemini Demo

After the demo, run:

    ./scripts/demo-down.sh

This returns the Service to `ClusterIP`.

The external IP is intentionally not hard-coded because a newly created GKE environment can receive a different address.

Useful Kubernetes demo helpers include:

    ./scripts/demo-k8s.sh
    ./scripts/demo-k8s-status.sh
    ./scripts/demo-k8s-stop.sh
    ./scripts/demo-up.sh
    ./scripts/demo-down.sh

This v1.2 milestone demonstrates the progression:

    Local Python
        |
        v
    Docker
        |
        v
    Kubernetes
        |
        v
    Google Kubernetes Engine
        |
        v
    On-Demand Public Demo

## 9. Understand query planning

The configured model infers the query intent plus optional location, optional specialty, and generated queries. Deterministic code then normalizes, deduplicates, and caps the plan.

Provider discovery currently requires a U.S. city/state and specialty before NPPES retrieval. A conservative specialty resolver maps common language such as:

```text
cardiologist -> Cardiovascular Disease
neurologist -> Neurology
dermatologist -> Dermatology
pediatric dentist -> Pediatric Dentistry
```

Unknown specialties pass through rather than being silently rewritten into unrelated specialties.

## 10. Understand retrieval routing

```text
PROVIDER_DISCOVERY
  -> NPPES
  -> PubMed only for evidence-oriented research context

BIOMEDICAL_RESEARCH
  -> PubMed

HEALTH_INFORMATION
  -> PubMed

explicit FHIR/interoperability query
  -> FHIR

CARE_PROGRAM_DISCOVERY
  -> explicit NotImplementedError

CLINICAL_TRIALS
  -> explicit NotImplementedError
```

An unsupported workflow should fail explicitly instead of being silently routed into an unrelated connector.

## 11. Understand evidence authority

### NPPES

NPPES can support provider identity, NPI, taxonomy, and reported location.

NPPES alone does not establish that a provider is best, board certified, actively licensed, in good standing, clinically high quality, or offers a requested service.

### PubMed

PubMed supports general biomedical/scientific context. A paper about childhood dental anxiety does not establish that a particular dentist is good at treating anxious children.

### FHIR

Public HAPI FHIR data demonstrates interoperability and resource structure. It is not authoritative provider-quality evidence and must not be promoted into provider recommendations.

## 12. Understand the v1.1 evaluation dataset

The benchmark dataset is:

```text
evaluation/datasets/healthcare_benchmark.jsonl
```

It contains:

```text
4 provider-discovery cases
2 biomedical-research cases
1 health-information case
2 FHIR-interoperability cases
2 expected-unsupported cases
--------------------------------
11 total cases
```

The runner sends only the case query to production. Expected location/specialty values are not injected because doing so would hide planner failures.

## 13. Run one smoke benchmark

Gemini:

```bash
python -m evaluation.benchmark \
  --provider gemini \
  --case provider_houston_pediatric_dentistry
```

Gemma:

```bash
python -m evaluation.benchmark \
  --provider gemma \
  --case provider_houston_pediatric_dentistry
```

Smoke runs are for debugging. Keep them separate from preserved full benchmark evidence.

## 14. Run the full Gemini benchmark

```bash
python -m evaluation.benchmark --provider gemini
```

Results are written to:

```text
evaluation/results/gemini/
```

Key files:

```text
raw/benchmark-gemini.json
research-results.json
case-results.csv
metric-results.csv
summary.csv
intent-summary.csv
metric-summary.csv
results.md
```

## 15. Run the full Gemma benchmark

Confirm Ollama first:

```bash
ollama list
```

Then run:

```bash
python -m evaluation.benchmark --provider gemma
```

Results are written to:

```text
evaluation/results/gemma/
```

For a long local run on macOS, prevent sleep if necessary:

```bash
caffeinate -dimsu
```

Do not overwrite a measured first-run failure with a later successful retry. A retry should be stored as a separate recovery experiment.

## 16. Generate Gemini/Gemma comparison tables

After both full result directories exist:

```bash
python -m evaluation.comparison
```

Generated comparison files:

```text
evaluation/results/comparison/model-comparison.csv
evaluation/results/comparison/workflow-comparison.csv
evaluation/results/comparison/metric-comparison.csv
evaluation/results/comparison/case-comparison.csv
evaluation/results/comparison/model-comparison.md
```

These files are generated from stored benchmark results. Do not manually rewrite measured values.

## 17. Understand the provider metrics

Provider discovery currently evaluates:

```text
retrieval_presence
required_source_types
citation_presence
citation_reference_integrity
claim_support
provider_evidence_authority
fhir_provider_recommendation_boundary
candidate_count
forbidden_claim_flags
```

Other workflows receive only metrics applicable to their contracts.

A blank metric in a cross-model comparison can mean **not applicable**, not zero.

## 18. Read unsupported passes correctly

The expected unsupported workflows are:

```text
CARE_PROGRAM_DISCOVERY
CLINICAL_TRIALS
```

A pass means the system rejected the unsupported retrieval path explicitly.

Therefore Gemini's measured `11 / 11` does **not** mean 11 successful healthcare answers. It means:

```text
9 supported workflows completed
2 unsupported workflows rejected correctly
```

## 19. Read the preserved v1.1 results correctly

```text
Gemini 3.7 Flash
  Core acceptance:          11 / 11
  Supported completions:     9 / 9
  Unsupported boundaries:    2 / 2
  Provider discovery:        4 / 4
  FHIR:                      2 / 2
  Median latency:           10.602 s

Gemma 4 12B + local Ollama
  Core acceptance:          10 / 11
  Supported completions:     8 / 9
  Unsupported boundaries:    2 / 2
  Provider discovery:        4 / 4
  FHIR:                      1 / 2
  Median latency:          167.415 s
```

Gemma's single failed supported case was FHIR PractitionerRole. The local LiteLLM/Ollama request exceeded the configured 600-second timeout.

Do not write:

```text
Gemini healthcare accuracy = 100%
Gemma healthcare accuracy = 90.9%
```

Use:

```text
Gemini passed 11/11 cases on the frozen v1.1 Core Acceptance Benchmark.
Gemma passed 10/11 cases on the same benchmark.
```

## 20. Treat latency as diagnostic data

The runtime paths are different:

```text
Gemini -> hosted API
Gemma -> local Ollama on Apple M3 Pro
```

Gemma's mean also includes a timeout.

The measured latency is useful operational evidence, not a controlled model-superiority benchmark.

## 21. Debug a failed benchmark case

The runner preserves:

```text
planner_output
research_output
answer_output
```

Inspect failures in this order:

```text
1. planner_output
2. generated queries
3. research_output
4. source mix
5. selected evidence / citations
6. grounded answer
7. metric results
8. event/error log
```

This helps separate planning, retrieval, grounding, citation, and runtime failures.

## 22. Add a benchmark case

Edit:

```text
evaluation/datasets/healthcare_benchmark.jsonl
```

Define expectations around observable workflow behavior rather than unstable live counts.

Good examples:

```text
provider discovery requires PROVIDER evidence
FHIR interoperability requires FHIR evidence
provider recommendations cannot use public HAPI FHIR test data as quality evidence
unsupported workflows reject explicitly
```

Avoid requiring an exact live NPPES/PubMed result count.

## 23. Add a metric

Implement metrics under:

```text
evaluation/metrics/
```

Wire them into:

```text
evaluation/orchestrator.py
```

A metric should inspect normalized production outputs rather than duplicate the production business logic it is evaluating.

## 24. Validate evaluation changes

Run focused tests:

```bash
pytest -q tests/unit/test_evaluation_models.py
pytest -q tests/unit/test_evaluation_metrics.py
pytest -q tests/unit/test_evaluation_runner.py
pytest -q tests/unit/test_evaluation_production_adapter.py
pytest -q tests/unit/test_evaluation_orchestrator.py
pytest -q tests/unit/test_evaluation_reporting.py
pytest -q tests/unit/test_evaluation_comparison.py
```

Then:

```bash
ruff check .
pytest -q
git diff --check
```

Do not rerun expensive live Gemini/Gemma benchmarks unless the production or evaluation behavior being measured changed.

## 25. Preserve research evidence

Keep these concepts separate in Git history:

```text
benchmark implementation
measured raw results
generated comparison
documentation
```

A first-run failure is evidence. Do not silently replace it.

## 26. Extend beyond the v1.1 acceptance set

The 11-case benchmark is a software acceptance set, not a statistically comprehensive healthcare-AI study.

A larger research study should use a separate frozen dataset with:

```text
50-100+ stratified queries
multiple repeated runs
runtime/version metadata
failure taxonomy
controlled retry/recovery experiments
median + IQR
mean + standard deviation where appropriate
larger workflow coverage
appropriate statistical analysis
```

Keep that research dataset separate from the v1.1 Core Acceptance Benchmark so the original release evidence remains reproducible.

## 27. Safe extension order

When adding a source or workflow:

```text
1. define the use case
2. define source authority
3. build connector/tool path
4. normalize results
5. define retrieval routing
6. define grounding boundary
7. define explicit failure behavior
8. add deterministic tests
9. add benchmark expectations
10. run live acceptance
```

This keeps architecture, tests, and evaluation aligned.
