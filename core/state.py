"""
Shared state contract for the Afrigate LangGraph swarm.

RFC §4 data flow:
    document_raw → doc_intel → hs_classifier → compliance → evaluator
                       ↑_____________(retry with feedback)_____________|
"""

from __future__ import annotations

import operator
from typing import Annotated, Literal, Optional
from typing_extensions import TypedDict


__all__ = [
    "EvaluatorDecision",
    "ComplianceStatus",
    "ExtractedFields",
    "HSResult",
    "ComplianceResult",
    "FinalReport",
    "AfrigateState",
    "initial_state",
]

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

EvaluatorDecision = Literal["accept", "retry", "ask_user"]
ComplianceStatus = Literal["compliant", "non_compliant", "pending_user_input"]


# ---------------------------------------------------------------------------
# Sub-schemas — one per agent output
# ---------------------------------------------------------------------------


class ExtractedFields(TypedDict, total=False):
    """Output of doc_intel. Countries use ISO 3166-1 alpha-2 codes."""

    exporter: Optional[str]
    importer: Optional[str]
    origin_country: str           # e.g. "ET"
    destination_country: str      # e.g. "KE"
    product: str                  # normalised, e.g. "roasted coffee"
    weight_kg: Optional[float]
    value_usd: Optional[float]
    documents_present: list[str]  # empty on first pass; populated on retry


class HSResult(TypedDict, total=False):
    """Output of hs_classifier. Mirrors agents/hs_classifier.py return shape."""

    found: bool
    hs_code: Optional[str]        # e.g. "0901.21"
    description: Optional[str]
    tariff_rate: Optional[float]  # decimal, e.g. 0.0 = duty-free
    trade_agreement: Optional[str]  # e.g. "COMESA", "AfCFTA"


class ComplianceResult(TypedDict, total=False):
    """Output of compliance. passed=False triggers evaluator retry logic."""

    passed: bool
    missing_fields: list[str]  # e.g. ["certificate_of_origin"]
    suggestion: str


class FinalReport(TypedDict, total=False):
    """Terminal output produced by evaluator on accept or ask_user."""

    status: ComplianceStatus
    hs_code: Optional[str]
    tariff_rate: Optional[float]
    trade_agreement: Optional[str]
    missing_documents: list[str]
    suggestion: str
    iterations_taken: int


# ---------------------------------------------------------------------------
# AfrigateState
# ---------------------------------------------------------------------------


class AfrigateState(TypedDict, total=False):
    """
    Single source of truth shared across all graph nodes.

    total=False: graph starts with only document_raw set; fields populate
    incrementally as each node runs.

    agent_log and errors use Annotated[list, operator.add] so LangGraph
    appends each node's entries rather than overwriting them.
    """

    # Input
    document_raw: str

    # Agent outputs
    extracted_fields: ExtractedFields
    hs_result: HSResult
    compliance_result: ComplianceResult

    # Evaluator
    evaluator_decision: EvaluatorDecision
    evaluator_feedback: str  # passed back to doc_intel on retry

    # Orchestration
    iteration: int  # incremented by evaluator on every retry; capped at max_iterations
    agent_log: Annotated[list[str], operator.add]  # step-by-step UI log (RFC §8)

    # Output
    final_report: Optional[FinalReport]  # None until evaluator reaches a verdict
    errors: Annotated[list[str], operator.add]


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def initial_state(document_raw: str) -> AfrigateState:
    """Return a zero-value AfrigateState for a new request.

    Usage::

        result = graph.invoke(initial_state(
            "Export 500kg roasted coffee from Ethiopia to Kenya, value USD 8,000."
        ))
    """
    return AfrigateState(
        document_raw=document_raw,
        iteration=0,
        agent_log=[],
        errors=[],
    )
