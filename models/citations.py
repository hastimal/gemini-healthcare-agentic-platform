from pydantic import BaseModel, HttpUrl


class Citation(BaseModel):
    citation_id: str
    title: str
    url: HttpUrl | None = None
    source_name: str | None = None
    claim_supported: str | None = None
