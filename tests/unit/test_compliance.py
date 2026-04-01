"""Tests for agents/compliance.py."""

from agents.compliance import run_compliance


class TestComplianceFailed:
    def test_fails_when_no_documents_present(self, state_after_hs):
        result = run_compliance(state_after_hs)
        assert result["compliance_result"]["passed"] is False

    def test_returns_all_missing_fields_for_kenya(self, state_after_hs):
        result = run_compliance(state_after_hs)
        missing = result["compliance_result"]["missing_fields"]
        assert "certificate_of_origin" in missing
        assert "phytosanitary_certificate" in missing
        assert "commercial_invoice" in missing
        assert "packing_list" in missing

    def test_suggestion_names_country(self, state_after_hs):
        result = run_compliance(state_after_hs)
        assert "Kenya" in result["compliance_result"]["suggestion"]

    def test_log_line_emitted(self, state_after_hs):
        result = run_compliance(state_after_hs)
        assert any("FAILED" in line for line in result["agent_log"])


class TestCompliancePassed:
    def test_passes_when_all_documents_present(self, state_compliance_passed):
        result = run_compliance(state_compliance_passed)
        assert result["compliance_result"]["passed"] is True

    def test_no_missing_fields_on_pass(self, state_compliance_passed):
        result = run_compliance(state_compliance_passed)
        assert result["compliance_result"]["missing_fields"] == []

    def test_log_line_emitted(self, state_compliance_passed):
        result = run_compliance(state_compliance_passed)
        assert any("PASSED" in line for line in result["agent_log"])


class TestComplianceEdgeCases:
    def test_unknown_destination_fails_gracefully(self, state_after_hs):
        state = {
            **state_after_hs,
            "extracted_fields": {
                **state_after_hs["extracted_fields"],
                "destination_country": "XX",
            },
        }
        result = run_compliance(state)
        assert result["compliance_result"]["passed"] is False
        assert "XX" in result["compliance_result"]["suggestion"]

    def test_empty_required_docs_passes(self, state_after_hs):
        # Ethiopia (ET) has no required documents — origin country
        state = {
            **state_after_hs,
            "extracted_fields": {
                **state_after_hs["extracted_fields"],
                "destination_country": "ET",
                "documents_present": [],
            },
        }
        result = run_compliance(state)
        assert result["compliance_result"]["passed"] is True
