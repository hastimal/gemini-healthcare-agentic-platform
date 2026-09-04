from pydantic import BaseModel, Field

from models.search import SearchResult


class EvidenceScore(BaseModel):
    relevance: float = Field(ge=0.0, le=1.0)
    authority: float = Field(ge=0.0, le=1.0)
    freshness: float = Field(ge=0.0, le=1.0)
    specificity: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)


class Evidence(BaseModel):
    result: SearchResult
    summary: str
    claims: list[str] = Field(default_factory=list)
    score: EvidenceScore
    selected: bool = False
