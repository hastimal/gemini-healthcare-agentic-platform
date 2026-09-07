# v1.1 Evaluation Benchmark Results

> Generated from stored benchmark results. Do not edit measured values manually.

## Model Summary

| Provider | Model | Cases | Passed | Pass Rate | Median Latency (s) |
| --- | --- | --- | --- | --- | --- |
| gemini | gemini-3.7-flash | 11 | 11 | 1.000 | 10.602 |

## Workflow / Intent Summary

| Intent | Provider | Cases | Passed | Pass Rate | Avg Retrieved | Avg Citations | Median Latency (s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BIOMEDICAL_RESEARCH | gemini | 2 | 2 | 1.000 | 9.500 | 5.000 | 12.748 |
| CARE_PROGRAM_DISCOVERY | gemini | 1 | 1 | 1.000 | 0.000 | 0.000 | 3.491 |
| CLINICAL_TRIALS | gemini | 1 | 1 | 1.000 | 0.000 | 0.000 | 3.370 |
| FHIR_INTEROPERABILITY | gemini | 2 | 2 | 1.000 | 6.500 | 4.000 | 10.853 |
| HEALTH_INFORMATION | gemini | 1 | 1 | 1.000 | 7.000 | 5.000 | 11.366 |
| PROVIDER_DISCOVERY | gemini | 4 | 4 | 1.000 | 17.750 | 5.000 | 9.554 |

## Metric Summary

| Provider | Metric | Evaluated | Passed | Failed | Pass Rate | Mean Score |
| --- | --- | --- | --- | --- | --- | --- |
| gemini | candidate_count | 4 | 4 | 0 | 1.000 | 1.000 |
| gemini | citation_presence | 9 | 9 | 0 | 1.000 | 1.000 |
| gemini | citation_reference_integrity | 9 | 9 | 0 | 1.000 | 1.000 |
| gemini | claim_support | 4 | 4 | 0 | 1.000 | 1.000 |
| gemini | explicit_unsupported_status | 2 | 2 | 0 | 1.000 | 1.000 |
| gemini | fhir_provider_recommendation_boundary | 6 | 6 | 0 | 1.000 | 1.000 |
| gemini | forbidden_claim_flags | 4 | 4 | 0 | 1.000 | 1.000 |
| gemini | provider_evidence_authority | 4 | 4 | 0 | 1.000 | 1.000 |
| gemini | required_source_types | 8 | 8 | 0 | 1.000 | 1.000 |
| gemini | retrieval_presence | 9 | 9 | 0 | 1.000 | 1.000 |

## Case Results

| Case | Intent | Provider | Status | Passed | Retrieved | Selected | Citations | Latency (s) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| provider_houston_pediatric_dentistry | PROVIDER_DISCOVERY | gemini | success | True | 20 | 5 | 5 | 10.602 |
| provider_dallas_cardiology | PROVIDER_DISCOVERY | gemini | success | True | 23 | 5 | 5 | 11.554 |
| provider_austin_neurology | PROVIDER_DISCOVERY | gemini | success | True | 15 | 5 | 5 | 8.505 |
| provider_chicago_dermatology | PROVIDER_DISCOVERY | gemini | success | True | 13 | 5 | 5 | 7.774 |
| research_childhood_dental_anxiety | BIOMEDICAL_RESEARCH | gemini | success | True | 7 | 5 | 5 | 11.945 |
| research_pediatric_procedural_anxiety | BIOMEDICAL_RESEARCH | gemini | success | True | 12 | 5 | 5 | 13.551 |
| health_general_patient_fear | HEALTH_INFORMATION | gemini | success | True | 7 | 5 | 5 | 11.366 |
| fhir_practitioner_role | FHIR_INTEROPERABILITY | gemini | success | True | 10 | 5 | 5 | 11.964 |
| fhir_healthcare_service | FHIR_INTEROPERABILITY | gemini | success | True | 3 | 3 | 3 | 9.741 |
| unsupported_care_program_discovery | CARE_PROGRAM_DISCOVERY | gemini | unsupported | True | 0 | 0 | 0 | 3.491 |
| unsupported_clinical_trials | CLINICAL_TRIALS | gemini | unsupported | True | 0 | 0 | 0 | 3.370 |

Latency is reported as a diagnostic measurement, not as a model-superiority claim.
