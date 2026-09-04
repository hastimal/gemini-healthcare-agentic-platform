from fastapi import FastAPI

from app.api.health import router as health_router
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Beyond RAG",
    description="Gemini-powered agentic healthcare information platform.",
    version="0.1.0",
)

app.include_router(health_router)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "project": "Beyond RAG",
        "repository": settings.app_name,
        "status": "development",
    }
