"""
LangSmith / LangChain tracing — optional setup stub.

Enables tracing only when ``settings.langchain_tracing_v2`` is true and an API
key is configured. Safe no-op when disabled (Phase 1 default).
"""

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.config import Settings


def configure_langsmith(settings: "Settings | None" = None) -> bool:
    """
    Apply LangSmith environment variables from settings.

    Returns True if tracing env vars were set; False if tracing stays off.
    Does not unset existing ``LANGCHAIN_*`` variables when tracing is disabled.
    """
    if settings is None:
        from core.config import settings as default_settings

        settings = default_settings

    if not settings.langchain_tracing_v2:
        return False

    if not (settings.langchain_api_key or "").strip():
        return False

    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key.strip()
    os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project or "afrigate"
    return True


def tracing_enabled() -> bool:
    """Whether LangChain clients are likely to emit traces (best-effort)."""
    return os.environ.get("LANGCHAIN_TRACING_V2", "").lower() in ("1", "true", "yes")
