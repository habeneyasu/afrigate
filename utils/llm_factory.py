"""LLM provider wrappers — returns a LangChain chat model for the active provider.

Check settings.is_llm_enabled before calling. Phase 1 runs without an LLM.
"""

from __future__ import annotations

from typing import Optional

from langchain_core.language_models import BaseChatModel

from core.config import settings


def get_llm(model: Optional[str] = None) -> BaseChatModel:
    """Return a zero-temperature chat model for the configured provider.

    Provider is inferred from the available API key (OpenAI takes precedence).
    Raises RuntimeError if no key is set.
    """
    model_name = model or settings.default_model

    if settings.openai_api_key:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model_name, api_key=settings.openai_api_key, temperature=0)

    if settings.google_api_key:
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model=model_name, google_api_key=settings.google_api_key, temperature=0)

    raise RuntimeError(
        "No LLM API key configured. Set OPENAI_API_KEY or GOOGLE_API_KEY in .env."
    )
