"""
Tests for hs_classifier agent.
"""
import pytest
from agents.hs_classifier import run_hs_classifier


@pytest.mark.skip(reason="TODO @Matrix: implement run_hs_classifier")
def test_classifies_coffee(state_after_doc_intel):
    result = run_hs_classifier(state_after_doc_intel)
    assert result["hs_result"]["hs_code"] == "0901.21"
    assert result["hs_result"]["tariff_rate"] == 0.0
    assert result["hs_result"]["trade_agreement"] == "COMESA"


@pytest.mark.skip(reason="TODO @Matrix: implement run_hs_classifier")
def test_unknown_product_returns_not_found(state_after_doc_intel):
    state = {
        **state_after_doc_intel,
        "extracted_fields": {**state_after_doc_intel["extracted_fields"], "product": "unknown widget"},
    }
    result = run_hs_classifier(state)
    assert result["hs_result"]["found"] is False
