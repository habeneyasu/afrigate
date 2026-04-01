"""Shared pytest fixtures — RFC §2 Addis-to-Nairobi reference scenario."""

import pytest


@pytest.fixture
def sample_input() -> dict:
    """Raw initial state as the UI would pass to the graph."""
    return {
        "document_raw": "Export 500kg roasted coffee from Ethiopia to Kenya, value USD 8,000.",
        "iteration": 0,
        "agent_log": [],
        "errors": [],
    }


@pytest.fixture
def state_after_doc_intel() -> dict:
    """State after doc_intel runs — first pass, no documents present yet."""
    return {
        "document_raw": "Export 500kg roasted coffee from Ethiopia to Kenya, value USD 8,000.",
        "extracted_fields": {
            "exporter": None,
            "importer": None,
            "origin_country": "ET",
            "destination_country": "KE",
            "product": "roasted coffee",
            "weight_kg": 500.0,
            "value_usd": 8000.0,
            "documents_present": [],
        },
        "iteration": 0,
        "agent_log": ["doc_intel: extracted product='roasted coffee', destination='KE'"],
        "errors": [],
    }


@pytest.fixture
def state_after_hs(state_after_doc_intel) -> dict:
    """State after hs_classifier runs — coffee matched to 0901.21 COMESA."""
    return {
        **state_after_doc_intel,
        "hs_result": {
            "found": True,
            "hs_code": "0901.21",
            "description": "Coffee, roasted",
            "tariff_rate": 0.0,
            "trade_agreement": "COMESA",
        },
        "agent_log": [
            *state_after_doc_intel["agent_log"],
            "hs_classifier: 0901.21 (COMESA, tariff 0.0%)",
        ],
    }


@pytest.fixture
def state_compliance_failed(state_after_hs) -> dict:
    """State after compliance fails — missing docs on first pass."""
    return {
        **state_after_hs,
        "compliance_result": {
            "passed": False,
            "missing_fields": [
                "certificate_of_origin",
                "phytosanitary_certificate",
                "commercial_invoice",
                "packing_list",
            ],
            "suggestion": "Missing 4 required document(s) for Kenya.",
        },
        "agent_log": [
            *state_after_hs["agent_log"],
            "compliance: FAILED — missing ['certificate_of_origin', 'phytosanitary_certificate', 'commercial_invoice', 'packing_list']",
        ],
    }


@pytest.fixture
def state_compliance_passed(state_after_hs) -> dict:
    """State after compliance passes — all documents present (second pass)."""
    state = dict(state_after_hs)
    state["extracted_fields"] = {
        **state_after_hs["extracted_fields"],
        "documents_present": [
            "certificate_of_origin",
            "phytosanitary_certificate",
            "commercial_invoice",
            "packing_list",
        ],
    }
    state["compliance_result"] = {
        "passed": True,
        "missing_fields": [],
        "suggestion": "All required documents present. Shipment is compliant.",
    }
    state["agent_log"] = [
        *state_after_hs["agent_log"],
        "compliance: PASSED",
    ]
    return state
