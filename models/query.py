from enum import Enum

from pydantic import BaseModel, Field


class SearchIntent(str, Enum):
    PROVIDER_DISCOVERY = "provider_discovery"
    CARE_PROGRAM_DISCOVERY = "care_program_discovery"
    HEALTH_INFORMATION = "health_information"
    BIOMEDICAL_RESEARCH = "biomedical_research"
    CLINICAL_TRIALS = "clinical_trials"


class UserQuery(BaseModel):
    text: str = Field(min_length=3)
    location: str | None = None
    specialty: str | None = None
    intent: SearchIntent | None = None


class SearchQuery(BaseModel):
    query: str = Field(min_length=3)
    purpose: str
    priority: int = Field(default=1, ge=1, le=5)


class SearchPlan(BaseModel):
    original_query: UserQuery
    intent: SearchIntent
    generated_queries: list[SearchQuery]
    notes: str | None = None
