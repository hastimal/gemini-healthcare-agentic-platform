from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class EvaluationIntent(str, Enum):
    PROVIDER_DISCOVERY = "PROVIDER_DISCOVERY"
    HEALTH_INFORMATION = "HEALTH_INFORMATION"
    BIOMEDICAL_RESEARCH = "BIOMEDICAL_RESEARCH"
    FHIR_INTEROPERABILITY = "FHIR_INTEROPERABILITY"
    CARE_PROGRAM_DISCOVERY = "CARE_PROGRAM_DISCOVERY"
    CLINICAL_TRIALS = "CLINICAL_TRIALS"


class ExpectationType(str, Enum):
    REQUIRED = "required"
    FORBIDDEN = "forbidden"
    OBSERVE = "observe"


class EvaluationExpectation(BaseModel):
    name: str = Field(min_length=3)
    expectation_type: ExpectationType
    description: str = Field(min_length=3)
    value: Any | None = None


class EvaluationCase(BaseModel):
    case_id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]+$")
    title: str = Field(min_length=3)
    query: str = Field(min_length=3)
    intent: EvaluationIntent
    location: str | None = None
    specialty: str | None = None
    tags: list[str] = Field(default_factory=list)
    expectations: list[EvaluationExpectation] = Field(min_length=1)
    notes: str | None = None

    @model_validator(mode="after")
    def validate_provider_case(self) -> "EvaluationCase":
        if self.intent == EvaluationIntent.PROVIDER_DISCOVERY:
            if not self.location:
                raise ValueError("provider-discovery benchmark cases require location")
            if not self.specialty:
                raise ValueError("provider-discovery benchmark cases require specialty")
        return self


class EvaluationMetricResult(BaseModel):
    metric: str = Field(min_length=2)
    passed: bool | None = None
    score: float | None = Field(default=None, ge=0.0, le=1.0)
    details: str | None = None


class EvaluationRunResult(BaseModel):
    case_id: str
    model_provider: str
    model_name: str | None = None
    metrics: list[EvaluationMetricResult] = Field(default_factory=list)
    latency_seconds: float | None = Field(default=None, ge=0.0)
    diagnostics: dict[str, Any] = Field(default_factory=dict)


class BenchmarkExecutionResult(BaseModel):
    case_id: str
    query: str
    model_provider: str
    model_name: str | None = None
    status: str
    planner_output: dict[str, Any] | None = None
    research_output: dict[str, Any] | None = None
    answer_output: dict[str, Any] | None = None
    event_log: list[dict[str, Any]] = Field(default_factory=list)
    latency_seconds: float | None = Field(default=None, ge=0.0)
    error_type: str | None = None
    error_message: str | None = None


class ResearchBenchmarkCaseResult(BaseModel):
    benchmark_version: str = "v1.1-core"
    case_id: str
    title: str
    query: str
    benchmark_intent: EvaluationIntent
    tags: list[str] = Field(default_factory=list)

    model_provider: str
    model_name: str | None = None
    execution_status: str
    latency_seconds: float | None = Field(default=None, ge=0.0)

    retrieved_sources: int = 0
    deduplicated_sources: int = 0
    selected_evidence_count: int = 0
    recommendation_count: int = 0
    citation_count: int = 0

    metrics: list[EvaluationMetricResult] = Field(default_factory=list)
    overall_passed: bool | None = None

    error_type: str | None = None
    error_message: str | None = None
    diagnostics: dict[str, Any] = Field(default_factory=dict)

