"""Shared fixtures (mocks, LangSmith)"""

import pytest


@pytest.fixture
def state_after_doc_intel():
    """Minimal post–doc_intel state for unit tests (Addis-to-Nairobi coffee)."""
    return {
        "document_raw": "Export 500kg roasted coffee from Ethiopia to Kenya, value USD 8,000.",
        "extracted_fields": {
            "product": "roasted coffee",
            "origin": "Ethiopia",
            "destination": "Kenya",
            "value_usd": 8000,
        },
        "hs_result": {},
        "compliance_result": {},
        "evaluator_decision": "",
        "evaluator_feedback": "",
        "iteration": 0,
        "agent_log": [],
        "final_report": {},
    }
