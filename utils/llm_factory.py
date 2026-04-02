"""LLM provider factory for Afrigate.

Two agent-specific constructors reflecting the LLM strategy (IMPLEMENTATION.md):

    get_worker_llm()    — doc_intel: fast structured extraction
                          Cerebras (CEREBRAS_MODEL_WORKER) → OpenAI → Gemini (GEMINI_MODEL_WORKER)

    get_evaluator_llm() — evaluator: reasoning & feedback generation
                          Gemini (GEMINI_MODEL_EVALUATOR) → OpenAI → Cerebras (CEREBRAS_MODEL_EVALUATOR)

Both return a zero-temperature LangChain BaseChatModel.
Guard with settings.is_llm_enabled before calling in Phase 1 contexts.
"""

from __future__ import annotations

from langchain_core.language_models import BaseChatModel

from core.config import settings


def get_worker_llm() -> BaseChatModel:
    """LLM for doc_intel — optimised for speed and structured extraction.

    Resolution: Cerebras → OpenAI → Google Gemini.
    Model controlled by CEREBRAS_MODEL_WORKER / GEMINI_MODEL_WORKER in .env.
    """
    if settings.cerebras_api_key:
        return _cerebras(settings.cerebras_model_worker)
    if settings.openai_api_key:
        return _openai("gpt-4o-mini")
    if settings.google_api_key:
        return _google(settings.gemini_model_worker)
    raise RuntimeError(
        "No LLM API key configured. Set CEREBRAS_API_KEY, OPENAI_API_KEY, "
        "or GOOGLE_API_KEY in .env."
    )


def get_evaluator_llm() -> BaseChatModel:
    """LLM for evaluator — optimised for reasoning and natural-language output.

    Resolution: Google Gemini → OpenAI → Cerebras.
    Model controlled by GEMINI_MODEL_EVALUATOR / CEREBRAS_MODEL_EVALUATOR in .env.
    """
    if settings.google_api_key:
        return _google(settings.gemini_model_evaluator)
    if settings.openai_api_key:
        return _openai("gpt-4o-mini")
    if settings.cerebras_api_key:
        return _cerebras(settings.cerebras_model_evaluator)
    raise RuntimeError(
        "No LLM API key configured. Set GOOGLE_API_KEY, OPENAI_API_KEY, "
        "or CEREBRAS_API_KEY in .env."
    )


# ---------------------------------------------------------------------------
# Provider constructors — lazy imports keep Phase 1 startup clean
# ---------------------------------------------------------------------------


def _cerebras(model: str) -> BaseChatModel:
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model=model,
        api_key=settings.cerebras_api_key,
        base_url=settings.cerebras_base_url,
        temperature=0,
    )


def _openai(model: str) -> BaseChatModel:
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model=model,
        api_key=settings.openai_api_key,
        temperature=0,
    )


def _google(model: str) -> BaseChatModel:
    from langchain_google_genai import ChatGoogleGenerativeAI
    return ChatGoogleGenerativeAI(
        model=model,
        google_api_key=settings.google_api_key,
        temperature=0,
    )
