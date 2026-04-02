"""Afrigate application settings — loaded once at import time."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # Cerebras — active provider
    # ------------------------------------------------------------------
    cerebras_api_key: str = Field(default="", alias="CEREBRAS_API_KEY")
    cerebras_base_url: str = Field(
        default="https://api.cerebras.ai/v1", alias="CEREBRAS_BASE_URL"
    )
    cerebras_model_worker: str = Field(default="llama3.1-8b", alias="CEREBRAS_MODEL_WORKER")
    cerebras_model_evaluator: str = Field(default="llama3.1-8b", alias="CEREBRAS_MODEL_EVALUATOR")

    # ------------------------------------------------------------------
    # Google Gemini — preferred evaluator provider
    # ------------------------------------------------------------------
    google_api_key: str = Field(default="", alias="GOOGLE_API_KEY")
    gemini_model_worker: str = Field(default="gemini-2.5-flash", alias="GEMINI_MODEL_WORKER")
    gemini_model_evaluator: str = Field(default="gemini-1.5-flash", alias="GEMINI_MODEL_EVALUATOR")

    # ------------------------------------------------------------------
    # OpenAI — fallback
    # ------------------------------------------------------------------
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")

    # ------------------------------------------------------------------
    # LangSmith tracing
    # ------------------------------------------------------------------
    langchain_tracing_v2: bool = Field(default=False, alias="LANGCHAIN_TRACING_V2")
    langchain_api_key: str = Field(default="", alias="LANGCHAIN_API_KEY")
    langchain_project: str = Field(default="afrigate", alias="LANGCHAIN_PROJECT")

    # ------------------------------------------------------------------
    # Orchestration
    # ------------------------------------------------------------------
    max_iterations: int = Field(default=3, ge=1, alias="MAX_ITERATIONS")

    # ------------------------------------------------------------------
    # App
    # ------------------------------------------------------------------
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    environment: str = Field(default="development", alias="ENVIRONMENT")

    @property
    def is_llm_enabled(self) -> bool:
        """True when at least one LLM API key is configured."""
        return bool(self.cerebras_api_key or self.openai_api_key or self.google_api_key)

    @property
    def is_tracing_enabled(self) -> bool:
        """True when LangSmith tracing is active."""
        return self.langchain_tracing_v2 and bool(self.langchain_api_key)


settings = Settings()
