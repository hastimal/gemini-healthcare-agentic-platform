from enum import Enum

from pydantic import BaseModel, Field, HttpUrl


class SourceType(str, Enum):
    WEB = "web"
    PROVIDER = "provider"
    PUBMED = "pubmed"
    CLINICAL_TRIAL = "clinical_trial"
    CMS = "cms"
    FHIR = "fhir"


class SearchResult(BaseModel):
    source_type: SourceType
    title: str
    url: HttpUrl | None = None
    snippet: str | None = None
    content: str | None = None

    provider_name: str | None = None
    location: str | None = None

    retrieved_by: str | None = None
    query_used: str | None = None

    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)
