"""Tests for agents/evaluator.py."""

from agents.evaluator import run_evaluator


class TestAccept:
    def test_decision_is_accept_when_passed(self, state_compliance_passed):
        result = run_evaluator(state_compliance_passed)
        assert result["evaluator_decision"] == "accept"

    def test_final_report_status_is_compliant(self, state_compliance_passed):
        result = run_evaluator(state_compliance_passed)
        assert result["final_report"]["status"] == "compliant"

    def test_final_report_includes_hs_data(self, state_compliance_passed):
        result = run_evaluator(state_compliance_passed)
        assert result["final_report"]["hs_code"] == "0901.21"
        assert result["final_report"]["tariff_rate"] == 0.0
        assert result["final_report"]["trade_agreement"] == "COMESA"

    def test_no_missing_documents_in_report(self, state_compliance_passed):
        result = run_evaluator(state_compliance_passed)
        assert result["final_report"]["missing_documents"] == []

    def test_feedback_is_empty_on_accept(self, state_compliance_passed):
        result = run_evaluator(state_compliance_passed)
        assert result["evaluator_feedback"] == ""


class TestRetry:
    def test_decision_is_retry_on_first_failure(self, state_compliance_failed):
        result = run_evaluator(state_compliance_failed)
        assert result["evaluator_decision"] == "retry"

    def test_iteration_incremented_on_retry(self, state_compliance_failed):
        result = run_evaluator(state_compliance_failed)
        assert result["iteration"] == 1

    def test_feedback_names_missing_documents(self, state_compliance_failed):
        result = run_evaluator(state_compliance_failed)
        assert "Certificate Of Origin" in result["evaluator_feedback"]

    def test_no_final_report_on_retry(self, state_compliance_failed):
        result = run_evaluator(state_compliance_failed)
        assert "final_report" not in result

    def test_log_line_contains_retry(self, state_compliance_failed):
        result = run_evaluator(state_compliance_failed)
        assert any("retry" in line for line in result["agent_log"])


class TestAskUser:
    def test_decision_is_ask_user_at_max_iterations(self, state_compliance_failed):
        state = {**state_compliance_failed, "iteration": 3}
        result = run_evaluator(state)
        assert result["evaluator_decision"] == "ask_user"

    def test_final_report_status_is_pending(self, state_compliance_failed):
        state = {**state_compliance_failed, "iteration": 3}
        result = run_evaluator(state)
        assert result["final_report"]["status"] == "pending_user_input"

    def test_missing_documents_in_report(self, state_compliance_failed):
        state = {**state_compliance_failed, "iteration": 3}
        result = run_evaluator(state)
        assert len(result["final_report"]["missing_documents"]) > 0

    def test_iteration_not_incremented_on_ask_user(self, state_compliance_failed):
        state = {**state_compliance_failed, "iteration": 3}
        result = run_evaluator(state)
        assert "iteration" not in result
