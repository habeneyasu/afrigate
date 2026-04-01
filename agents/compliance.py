"""
Compliance validation agent.

Loads rules/regulations.json and validates that every document required
by the destination country is present in extracted_fields.documents_present.
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

from utils.logger import get_logger

_RULES_PATH = Path(__file__).resolve().parent.parent / "rules" / "regulations.json"
_log = get_logger("agents.compliance")


@lru_cache(maxsize=1)
def _load_regulations() -> dict[str, Any]:
    return json.loads(_RULES_PATH.read_text(encoding="utf-8"))


def run_compliance(state: Mapping[str, Any]) -> dict[str, Any]:
    """Validate shipment documents against destination-country rules.

    Reads extracted_fields.destination_country and documents_present.
    Returns a partial state update with compliance_result and agent_log.
    """
    fields = state.get("extracted_fields") or {}
    destination: str = fields.get("destination_country", "")
    documents_present: list[str] = fields.get("documents_present") or []

    regs = _load_regulations()
    country_rules = regs.get(destination)

    if not country_rules:
        result = {
            "passed": False,
            "missing_fields": [],
            "suggestion": f"No regulations found for destination country '{destination}'.",
        }
        log_line = f"compliance: UNKNOWN destination='{destination}'"
    else:
        required: list[str] = country_rules.get("required_documents", [])
        missing = [doc for doc in required if doc not in documents_present]

        if missing:
            country_name = country_rules.get("country", destination)
            readable = ", ".join(d.replace("_", " ").title() for d in missing)
            result = {
                "passed": False,
                "missing_fields": missing,
                "suggestion": f"Missing {len(missing)} required document(s) for {country_name}: {readable}.",
            }
            log_line = f"compliance: FAILED — missing {missing}"
        else:
            result = {
                "passed": True,
                "missing_fields": [],
                "suggestion": "All required documents present. Shipment is compliant.",
            }
            log_line = "compliance: PASSED"

    _log.info(
        "compliance_check",
        extra={
            "destination": destination,
            "passed": result["passed"],
            "missing": result["missing_fields"],
        },
    )

    return {"compliance_result": result, "agent_log": [log_line]}
