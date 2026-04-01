"""
config.py — Pydantic settings for Afrigate.
Reads from .env / environment variables.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM keys (optional in Phase 1 — zero-API)
    openai_api_key: str = ""
    google_api_key: str = ""

    # LangSmith tracing
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""
    langchain_project: str = "afrigate"

    # App
    log_level: str = "INFO"
    environment: str = "development"
    default_model: str = "gpt-4o-mini"   # used when LLM layer is enabled (RFC §10)
    max_iterations: int = 3              # self-correction loop cap (RFC §4/§5)


settings = Settings()
