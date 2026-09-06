from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "gemini-healthcare-agentic-platform"
    app_env: str = "development"
    log_level: str = "INFO"

    model_provider: str = "gemini"

    gemini_api_key: str | None = None
    gemini_model: str | None = None

    ollama_base_url: str = "http://localhost:11434"
    gemma_model: str | None = None

    ncbi_email: str | None = None
    ncbi_api_key: str | None = None

    # Public/demo FHIR endpoint used for development and interoperability testing.
    #
    # The default HAPI endpoint is a public R4 test server. It must never be
    # used for PHI or confidential healthcare information.
    fhir_base_url: str = "https://hapi.fhir.org/baseR4"
    fhir_timeout_seconds: float = 20.0

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
