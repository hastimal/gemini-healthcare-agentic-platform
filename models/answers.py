from pydantic import BaseModel, Field

from models.citations import Citation


class ProviderRecommendation(BaseModel):
    name: str
    location: str | None = None
    credentials: list[str] = Field(default_factory=list)
    services: list[str] = Field(default_factory=list)
    reasons_selected: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


class SearchTransparency(BaseModel):
    generated_queries: int = 0
    retrieved_sources: int = 0
    deduplicated_sources: int = 0
    selected_sources: int = 0


class GroundedAnswer(BaseModel):
    answer: str
    recommendations: list[ProviderRecommendation] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    transparency: SearchTransparency
    limitations: list[str] = Field(default_factory=list)
