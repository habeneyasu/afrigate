"""Smoke tests for utils.logger and utils.langsmith."""

import json
import logging

from utils import langsmith
from utils.logger import JsonLineFormatter, get_logger, setup_logging


def test_json_log_formatter_outputs_json():
    record = logging.LogRecord(
        name="afrigate.test",
        level=logging.INFO,
        pathname="x.py",
        lineno=1,
        msg="hello",
        args=(),
        exc_info=None,
    )
    record.shipment_id = "abc-123"
    line = JsonLineFormatter().format(record)
    data = json.loads(line)
    assert data["level"] == "INFO"
    assert data["message"] == "hello"
    assert data["shipment_id"] == "abc-123"


def test_get_logger_namespaced():
    log = get_logger("compliance")
    assert log.name == "afrigate.compliance"


def test_configure_langsmith_noop_without_flag(monkeypatch):
    from core.config import Settings

    s = Settings(
        langchain_tracing_v2=False,
        langchain_api_key="",
        langchain_project="test",
    )
    assert langsmith.configure_langsmith(s) is False


def test_configure_langsmith_sets_env_when_enabled(monkeypatch):
    monkeypatch.setenv("LANGCHAIN_TRACING_V2", "true")
    monkeypatch.setenv("LANGCHAIN_API_KEY", "sk-test")
    monkeypatch.setenv("LANGCHAIN_PROJECT", "afrigate-ci")

    from core.config import Settings
    s = Settings()
    assert langsmith.configure_langsmith(s) is True

    import os
    assert os.environ.get("LANGCHAIN_TRACING_V2") == "true"
    assert os.environ.get("LANGCHAIN_API_KEY") == "sk-test"
    assert os.environ.get("LANGCHAIN_PROJECT") == "afrigate-ci"
