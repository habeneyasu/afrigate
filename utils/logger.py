"""
Structured logging for Afrigate (JSON lines on stderr by default).

Uses the stdlib only. Call ``setup_logging()`` once at process entry
(e.g. ``ui.app`` or a CLI), then use ``get_logger(__name__)``.
"""

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

_LOG_RECORD_SKIP = frozenset(
    {
        "name",
        "msg",
        "args",
        "created",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "exc_info",
        "exc_text",
        "thread",
        "threadName",
        "taskName",
        "message",
    }
)


class JsonLineFormatter(logging.Formatter):
    """One JSON object per line; merges ``extra=`` keys into the payload."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        for key, value in record.__dict__.items():
            if key in _LOG_RECORD_SKIP or key.startswith("_"):
                continue
            payload[key] = value

        return json.dumps(payload, default=str)


def setup_logging(
    level: str = "INFO",
    *,
    stream: Any | None = None,
    force: bool = True,
) -> None:
    """
    Configure the ``afrigate`` logger tree with a single JSON handler.

    ``level``: e.g. DEBUG, INFO, WARNING (or from ``core.config.settings.log_level``).
    """
    root = logging.getLogger("afrigate")
    root.setLevel(level.upper())
    handler = logging.StreamHandler(stream or sys.stderr)
    handler.setLevel(level.upper())
    handler.setFormatter(JsonLineFormatter())
    root.handlers.clear()
    root.addHandler(handler)
    root.propagate = False


def get_logger(name: str) -> logging.Logger:
    """Child loggers under ``afrigate.*`` inherit JSON formatting."""
    if name == "afrigate" or name.startswith("afrigate."):
        return logging.getLogger(name)
    return logging.getLogger(f"afrigate.{name}")
