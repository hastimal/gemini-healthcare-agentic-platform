# v0.9 End-to-End UI Acceptance

This harness validates the real Streamlit entrypoint and the generalized
healthcare workflow introduced in v0.9.

## What it tests

1. The real Streamlit server boots and its health endpoint responds.
2. Streamlit's official `AppTest` API executes `ui/streamlit_app.py`.
3. The UI submits real healthcare questions through the production workflow.
4. Planner JSON, research JSON, and grounded-answer JSON are inspected.
5. Regression guards ensure Houston/Pediatric Dentistry do not leak into
   unrelated queries.

Acceptance queries include:

- Dallas cardiology
- Austin neurology
- childhood dental-anxiety research
- FHIR PractitionerRole
- the original Houston pediatric-dentist flagship regression query

The flagship query remains a test case, not application configuration.

## Run with Gemini

```bash
./scripts/test-ui.sh gemini
```

## Run with local Gemma / Ollama

```bash
./scripts/test-ui.sh gemma
```

Gemma receives a longer default timeout because local inference can be
materially slower than hosted Gemini. Passing Gemini acceptance does not imply
that every non-provider synthesis path has already been performance-validated
with Gemma.

## Important

These are live acceptance tests. NPPES, PubMed, FHIR, model APIs, and Ollama
are external/runtime dependencies and can fail independently of deterministic
unit tests.

For fast deterministic regression testing, continue using:

```bash
pytest -q
```

## Accepted v0.9 matrix

```text
Scenario                         Gemini   Gemma
Dallas Cardiology                PASS     PASS
Austin Neurology                 PASS     PASS
Biomedical research              PASS     PASS
FHIR PractitionerRole            PASS     PASS
Houston pediatric dentistry      PASS     PASS
                                 5/5      5/5
```

Deterministic checkpoint: `85 passed, 5 skipped`. Optional semantic metadata may differ by model while still satisfying the same behavioral routing and evidence contract.
