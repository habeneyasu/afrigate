"""End-to-end LangGraph test — RFC §2 Addis-to-Nairobi coffee scenario."""

from core.graph import build_graph
from core.state import initial_state


def test_coffee_export_retry_then_compliant():
    """
    First pass: no certificates in free text → compliance fails → evaluator retries.
    Second pass: doc_intel attaches required KE documents → compliant accept.
    """
    graph = build_graph()
    doc = (
        "Export 500kg roasted coffee from Ethiopia to Kenya, value USD 8,000."
    )
    result = graph.invoke(initial_state(doc))

    assert result.get("final_report") is not None
    assert result["final_report"]["status"] == "compliant"
    assert result["final_report"]["hs_code"] == "0901.21"
    assert result["final_report"]["iterations_taken"] == 1

    log = result.get("agent_log") or []
    assert any("FAILED" in line for line in log)
    assert any("retry" in line.lower() for line in log)
    assert any("PASSED" in line for line in log)
    assert any("accept" in line.lower() for line in log)


def test_structured_input_compliant_without_retry():
    """When all certificates are present in the text, one pass should succeed."""
    graph = build_graph()
    doc = """
    Exporter: Addis Trading PLC
    Exporter Country: Ethiopia
    Importer: Nairobi Imports Ltd
    Importer Country: Kenya
    Product: Roasted Arabica Coffee
    Quantity: 500 kg
    Total Value: USD 8,000
    Certificate of Origin: CO-2024-ET-00712
    Phytosanitary Certificate: PHY-2024-00123
    Commercial Invoice: INV-2024-00712
    Packing List: PL-2024-00712
    """
    result = graph.invoke(initial_state(doc))

    assert result.get("final_report") is not None
    assert result["final_report"]["status"] == "compliant"
    assert result["final_report"]["iterations_taken"] == 0
