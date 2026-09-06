# v1.1 Evaluation Benchmark

## Goal

The v1.1 benchmark evaluates whether the healthcare agent platform behaves correctly across multiple supported and unsupported healthcare workflows.

The benchmark separates:

```text
APPLICATION CORRECTNESS
!=
MODEL PERFORMANCE
```

Deterministic expectations can be pass/fail. Runtime observations such as latency or wording variation are recorded as diagnostics unless a future benchmark explicitly defines a justified threshold.

## Initial Benchmark Coverage

The initial dataset covers:

- provider discovery across multiple cities and specialties
- biomedical research
- general health information
- FHIR interoperability
- explicitly unsupported care-program discovery
- explicitly unsupported clinical-trials retrieval

The original Houston pediatric-dentist query remains a regression case, not application configuration.

## Evaluation Categories

Planned deterministic metrics:

- retrieval relevance
- source authority
- citation support
- groundedness
- answer completeness
- healthcare safety / evidence-boundary adherence

Observed diagnostics:

- latency
- model provider
- model name
- result counts
- model/runtime variation

## Dataset

```text
evaluation/datasets/healthcare_benchmark.jsonl
```

Each line is one `EvaluationCase`.

## Important Boundary

The benchmark must not silently turn observed behavior into claims of model superiority.
