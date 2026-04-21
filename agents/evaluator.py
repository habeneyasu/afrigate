"""
Evaluator agent — reasoning & retry logic.

Reads compliance_result and decides one of three outcomes (RFC §4):
  accept   — compliance passed; build final_report and end.
  retry    — compliance failed and iteration < max_iterations;
             write evaluator_feedback and increment iteration.
  ask_user — compliance failed and iteration >= max_iterations;
             build final_report with pending_user_input status and end.

LLM layer (optional, RFC §10):
  When settings.is_llm_enabled is True, uses get_evaluator_llm() to generate
  richer, context-aware feedback on retry. Falls back to a deterministic
  template if the LLM call fails. Decision logic stays deterministic.
"""

from typing import Any, Mapping

from core.config import settings
from utils.logger import get_logger

_log = get_logger("agents.evaluator")

# ---------------------------------------------------------------------------
# LLM feedback — used on retry when settings.is_llm_enabled is True
# ---------------------------------------------------------------------------

_FEEDBACK_PROMPT = """\
You are a trade compliance assistant. A shipment has failed its compliance check.

Product: {product}
Destination: {destination}
Missing documents: {missing}

Write a clear, concise message (2-3 sentences) telling the exporter exactly which
documents are missing and why they are required. Be specific and professional.
Do not use bullet points. Respond with the message only."""


def _llm_feedback(product: str, destination: str, missing: list[str]) -> str:
    """Generate natural-language retry feedback using get_evaluator_llm()."""
    from utils.llm_factory import get_evaluator_llm

    readable = ", ".join(d.replace("_", " ").title() for d in missing)
    prompt = _FEEDBACK_PROMPT.format(
        product=product, destination=destination, missing=readable
    )
    try:
        response = get_evaluator_llm().invoke(prompt)
        return response.content.strip()
    except Exception as exc:
        _log.warning("llm_feedback_failed", extra={"error": str(exc)})
        return f"Missing document(s): {readable}. Please provide these to proceed."


def run_evaluator(state: Mapping[str, Any]) -> dict[str, Any]:
    """Decide accept / retry / ask_user based on compliance_result.

    Returns a partial state update with evaluator_decision,
    evaluator_feedback, iteration, final_report, and agent_log.
    """
    compliance: dict[str, Any] = state.get("compliance_result") or {}
    hs: dict[str, Any] = state.get("hs_result") or {}
    fields: dict[str, Any] = state.get("extracted_fields") or {}
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

        if settings.is_llm_enabled:
            feedback = _llm_feedback(
                product=fields.get("product", "unknown product"),
                destination=fields.get("destination_country", "unknown destination"),
                missing=missing,
            )
        else:
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
            "llm_enabled": settings.is_llm_enabled,
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
