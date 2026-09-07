# v1.1 Gemini ↔ Gemma Benchmark Comparison

> Generated from stored benchmark results. Do not edit measured values manually.

## Model Summary

| Provider | Model | Core | Supported Success | Expected Unsupported | Passed | Pass Rate | Median Latency (s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| gemini | gemini-3.7-flash | 11 | 9/9 | 2/2 | 11/11 | 1.000 | 10.602 |
| gemma | gemma4:12b | 11 | 8/9 | 2/2 | 10/11 | 0.909 | 167.415 |

## Workflow / Intent Comparison

| Intent | gemini Passed | gemini Pass Rate | gemini Median Latency (s) | gemma Passed | gemma Pass Rate | gemma Median Latency (s) |
| --- | --- | --- | --- | --- | --- | --- |
| BIOMEDICAL_RESEARCH | 2/2 | 1.000 | 12.748 | 2/2 | 1.000 | 337.654 |
| CARE_PROGRAM_DISCOVERY | 1/1 | 1.000 | 3.491 | 1/1 | 1.000 | 98.579 |
| CLINICAL_TRIALS | 1/1 | 1.000 | 3.370 | 1/1 | 1.000 | 71.848 |
| FHIR_INTEROPERABILITY | 2/2 | 1.000 | 10.853 | 1/2 | 0.500 | 457.322 |
| HEALTH_INFORMATION | 1/1 | 1.000 | 11.366 | 1/1 | 1.000 | 216.701 |
| PROVIDER_DISCOVERY | 4/4 | 1.000 | 9.554 | 4/4 | 1.000 | 129.158 |

## Metric Comparison

| Metric | gemini Passed | gemini Pass Rate | gemma Passed | gemma Pass Rate |
| --- | --- | --- | --- | --- |
| candidate_count | 4/4 | 1.000 | 4/4 | 1.000 |
| citation_presence | 9/9 | 1.000 | 8/8 | 1.000 |
| citation_reference_integrity | 9/9 | 1.000 | 8/8 | 1.000 |
| claim_support | 4/4 | 1.000 | 4/4 | 1.000 |
| execution_success |  |  | 0/1 | 0.000 |
| explicit_unsupported_status | 2/2 | 1.000 | 2/2 | 1.000 |
| fhir_provider_recommendation_boundary | 6/6 | 1.000 | 5/5 | 1.000 |
| forbidden_claim_flags | 4/4 | 1.000 | 4/4 | 1.000 |
| provider_evidence_authority | 4/4 | 1.000 | 4/4 | 1.000 |
| required_source_types | 8/8 | 1.000 | 7/7 | 1.000 |
| retrieval_presence | 9/9 | 1.000 | 8/8 | 1.000 |

## Case Comparison

| Case | Intent | gemini Status | gemini Passed | gemini Retrieved | gemini Citations | gemini Latency (s) | gemma Status | gemma Passed | gemma Retrieved | gemma Citations | gemma Latency (s) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| provider_houston_pediatric_dentistry | PROVIDER_DISCOVERY | success | True | 20 | 5 | 10.602 | success | True | 19 | 5 | 167.415 |
| provider_dallas_cardiology | PROVIDER_DISCOVERY | success | True | 23 | 5 | 11.554 | success | True | 16 | 5 | 126.701 |
| provider_austin_neurology | PROVIDER_DISCOVERY | success | True | 15 | 5 | 8.505 | success | True | 13 | 5 | 131.616 |
| provider_chicago_dermatology | PROVIDER_DISCOVERY | success | True | 13 | 5 | 7.774 | success | True | 17 | 5 | 118.844 |
| research_childhood_dental_anxiety | BIOMEDICAL_RESEARCH | success | True | 7 | 5 | 11.945 | success | True | 11 | 5 | 383.441 |
| research_pediatric_procedural_anxiety | BIOMEDICAL_RESEARCH | success | True | 12 | 5 | 13.551 | success | True | 7 | 5 | 291.866 |
| health_general_patient_fear | HEALTH_INFORMATION | success | True | 7 | 5 | 11.366 | success | True | 12 | 5 | 216.701 |
| fhir_practitioner_role | FHIR_INTEROPERABILITY | success | True | 10 | 5 | 11.964 | error | False | 0 | 0 | 707.760 |
| fhir_healthcare_service | FHIR_INTEROPERABILITY | success | True | 3 | 3 | 9.741 | success | True | 3 | 3 | 206.884 |
| unsupported_care_program_discovery | CARE_PROGRAM_DISCOVERY | unsupported | True | 0 | 0 | 3.491 | unsupported | True | 0 | 0 | 98.579 |
| unsupported_clinical_trials | CLINICAL_TRIALS | unsupported | True | 0 | 0 | 3.370 | unsupported | True | 0 | 0 | 71.848 |

## Interpretation Notes

- Acceptance pass rates are deterministic benchmark outcomes for this frozen v1.1 Core Acceptance Set; they are not claims of general healthcare-AI accuracy.
- Expected unsupported workflows pass only when the system rejects them explicitly rather than silently routing them to an unrelated retrieval source.
- Citation, authority, grounding, and safety metrics are evaluated only where their workflow contracts apply.
- Latency is a runtime diagnostic. Hosted Gemini API execution and local Gemma/Ollama execution are different runtime environments, so latency values are not model-superiority claims.
- Execution errors remain visible in the comparison. They are not replaced by retry results.
