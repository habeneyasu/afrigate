"""
Evaluator agent — reasoning & retry logic.

Reads compliance_result and decides one of three outcomes (RFC §4):
  accept   — compliance passed; build final_report and end.
  retry    — compliance failed and iteration < max_iterations;
             write evaluator_feedback and increment iteration.
  ask_user — compliance failed and iteration >= max_iterations;
             build final_report with pending_user_input status and end.
"""

from typing import Any, Mapping

from core.config import settings
from utils.logger import get_logger

_log = get_logger("agents.evaluator")


def run_evaluator(state: Mapping[str, Any]) -> dict[str, Any]:
    """Decide accept / retry / ask_user based on compliance_result.

    Returns a partial state update with evaluator_decision,
    evaluator_feedback, iteration, final_report, and agent_log.
    """
    compliance: dict[str, Any] = state.get("compliance_result") or {}
    hs: dict[str, Any] = state.get("hs_result") or {}
    iteration: int = state.get("iteration", 0)

    passed: bool = compliance.get("passed", False)
    missing: list[str] = compliance.get("missing_fields", [])
    suggestion: str = compliance.get("suggestion", "")

    if passed:
        decision = "accept"
        feedback = ""
        final_report: dict[str, Any] = {
            "status": "compliant",
            "hs_code": hs.get("hs_code"),
            "tariff_rate": hs.get("tariff_rate"),
            "trade_agreement": hs.get("trade_agreement"),
            "missing_documents": [],
            "suggestion": suggestion,
            "iterations_taken": iteration,
        }
        log_line = f"evaluator: accept — compliant after {iteration} iteration(s)"

    elif iteration < settings.max_iterations:
        decision = "retry"
        readable = ", ".join(d.replace("_", " ").title() for d in missing)
        feedback = f"Missing document(s): {readable}. Please provide these to proceed."
        final_report = None
        log_line = f"evaluator: retry (iteration={iteration + 1}) — {feedback}"

    else:
        decision = "ask_user"
        feedback = ""
        final_report = {
            "status": "pending_user_input",
            "hs_code": hs.get("hs_code"),
            "tariff_rate": hs.get("tariff_rate"),
            "trade_agreement": hs.get("trade_agreement"),
            "missing_documents": missing,
            "suggestion": suggestion,
            "iterations_taken": iteration,
        }
        log_line = f"evaluator: ask_user — max iterations reached, missing {missing}"

    _log.info(
        "evaluation",
        extra={
            "decision": decision,
            "iteration": iteration,
            "missing": missing,
        },
    )

    update: dict[str, Any] = {
        "evaluator_decision": decision,
        "evaluator_feedback": feedback,
        "agent_log": [log_line],
    }
    if decision == "retry":
        update["iteration"] = iteration + 1
    if final_report is not None:
        update["final_report"] = final_report

    return update
