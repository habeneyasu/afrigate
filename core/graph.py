"""
LangGraph state machine for the Afrigate swarm.

RFC §4/§5 routing:
    doc_intel → hs_classifier → compliance → evaluator
                    ↑_____________(retry)_____________|
"""

from langgraph.graph import END, StateGraph

from agents.compliance import run_compliance
from agents.doc_intel_graph import run_pipeline
from agents.evaluator import run_evaluator
from agents.hs_classifier import run_hs_classifier
from core.config import settings
from core.state import AfrigateState


# ---------------------------------------------------------------------------
# Doc Intel Node wrapper
# ---------------------------------------------------------------------------


def run_doc_intel_node(state: AfrigateState) -> AfrigateState:
    result = run_pipeline(
        user_input=state.get("user_input", ""),
        file_path=state.get("file_path"),
        feedback=state.get("evaluator_feedback"), 
    )
    return {
        **state,
        "extracted_fields": dict(result),
        "iteration": state.get("iteration", 0) + 1,
    }


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------


def _route(state: AfrigateState) -> str:
    """
    Called after the evaluator node.

    Returns the next node name or END based on the evaluator's decision
    and the current iteration count.
    """
    decision = state.get("evaluator_decision")
    iteration = state.get("iteration", 0)

    if decision == "retry" and iteration < settings.max_iterations:
        return "doc_intel"

    return END


# ---------------------------------------------------------------------------
# Graph factory
# ---------------------------------------------------------------------------


def build_graph() -> StateGraph:
    """Compile and return the Afrigate LangGraph."""
    graph = StateGraph(AfrigateState)

    graph.add_node("doc_intel",     run_doc_intel_node)
    graph.add_node("hs_classifier", run_hs_classifier)
    graph.add_node("compliance",    run_compliance)
    graph.add_node("evaluator",     run_evaluator)

    graph.set_entry_point("doc_intel")
    graph.add_edge("doc_intel",     "hs_classifier")
    graph.add_edge("hs_classifier", "compliance")
    graph.add_edge("compliance",    "evaluator")
    graph.add_conditional_edges(
        "evaluator",
        _route,
        {
            "doc_intel": "doc_intel",
            END:         END,
        },
    )

    return graph.compile()