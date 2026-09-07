# v1.1 Evaluation Benchmark Results

> Generated from stored benchmark results. Do not edit measured values manually.

## Model Summary

| Provider | Model | Cases | Passed | Pass Rate | Median Latency (s) |
| --- | --- | --- | --- | --- | --- |
| gemma | gemma4:12b | 11 | 10 | 0.909 | 167.415 |

## Workflow / Intent Summary

| Intent | Provider | Cases | Passed | Pass Rate | Avg Retrieved | Avg Citations | Median Latency (s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BIOMEDICAL_RESEARCH | gemma | 2 | 2 | 1.000 | 9.000 | 5.000 | 337.654 |
| CARE_PROGRAM_DISCOVERY | gemma | 1 | 1 | 1.000 | 0.000 | 0.000 | 98.579 |
| CLINICAL_TRIALS | gemma | 1 | 1 | 1.000 | 0.000 | 0.000 | 71.848 |
| FHIR_INTEROPERABILITY | gemma | 2 | 1 | 0.500 | 1.500 | 1.500 | 457.322 |
| HEALTH_INFORMATION | gemma | 1 | 1 | 1.000 | 12.000 | 5.000 | 216.701 |
| PROVIDER_DISCOVERY | gemma | 4 | 4 | 1.000 | 16.250 | 5.000 | 129.158 |

## Metric Summary

| Provider | Metric | Evaluated | Passed | Failed | Pass Rate | Mean Score |
| --- | --- | --- | --- | --- | --- | --- |
| gemma | candidate_count | 4 | 4 | 0 | 1.000 | 1.000 |
| gemma | citation_presence | 8 | 8 | 0 | 1.000 | 1.000 |
| gemma | citation_reference_integrity | 8 | 8 | 0 | 1.000 | 1.000 |
| gemma | claim_support | 4 | 4 | 0 | 1.000 | 1.000 |
| gemma | execution_success | 1 | 0 | 1 | 0.000 | 0.000 |
| gemma | explicit_unsupported_status | 2 | 2 | 0 | 1.000 | 1.000 |
| gemma | fhir_provider_recommendation_boundary | 5 | 5 | 0 | 1.000 | 1.000 |
| gemma | forbidden_claim_flags | 4 | 4 | 0 | 1.000 | 1.000 |
| gemma | provider_evidence_authority | 4 | 4 | 0 | 1.000 | 1.000 |
| gemma | required_source_types | 7 | 7 | 0 | 1.000 | 1.000 |
| gemma | retrieval_presence | 8 | 8 | 0 | 1.000 | 1.000 |

## Case Results

| Case | Intent | Provider | Status | Passed | Retrieved | Selected | Citations | Latency (s) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| provider_houston_pediatric_dentistry | PROVIDER_DISCOVERY | gemma | success | True | 19 | 5 | 5 | 167.415 |
| provider_dallas_cardiology | PROVIDER_DISCOVERY | gemma | success | True | 16 | 5 | 5 | 126.701 |
| provider_austin_neurology | PROVIDER_DISCOVERY | gemma | success | True | 13 | 5 | 5 | 131.616 |
| provider_chicago_dermatology | PROVIDER_DISCOVERY | gemma | success | True | 17 | 5 | 5 | 118.844 |
| research_childhood_dental_anxiety | BIOMEDICAL_RESEARCH | gemma | success | True | 11 | 5 | 5 | 383.441 |
| research_pediatric_procedural_anxiety | BIOMEDICAL_RESEARCH | gemma | success | True | 7 | 5 | 5 | 291.866 |
| health_general_patient_fear | HEALTH_INFORMATION | gemma | success | True | 12 | 5 | 5 | 216.701 |
| fhir_practitioner_role | FHIR_INTEROPERABILITY | gemma | error | False | 0 | 0 | 0 | 707.760 |
| fhir_healthcare_service | FHIR_INTEROPERABILITY | gemma | success | True | 3 | 3 | 3 | 206.884 |
| unsupported_care_program_discovery | CARE_PROGRAM_DISCOVERY | gemma | unsupported | True | 0 | 0 | 0 | 98.579 |
| unsupported_clinical_trials | CLINICAL_TRIALS | gemma | unsupported | True | 0 | 0 | 0 | 71.848 |

Latency is reported as a diagnostic measurement, not as a model-superiority claim.
