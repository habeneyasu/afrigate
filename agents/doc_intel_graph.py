"""
Document Intelligence — LangGraph Pipeline
============================================
Flow:
  1. parse_node  — uses doc_intel.py to extract raw fields from text/file
  2. llm_node    — sends raw text + pre-extracted fields to GPT for final
                   structured ExtractedFields output
  3. output_node — validates and returns the final ExtractedFields

Usage:
    from doc_intel_graph import run_pipeline

    result = run_pipeline(user_input="Export 500kg coffee from Ethiopia to Kenya, USD 8000")
    result = run_pipeline(file_path="invoice.pdf")
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END

# ── local import ────────────────────────────────────────────────────────────
from agents.doc_intel import (
    ExtractedFields,
    TradeDocument,
    extract_from_text,
    extract_from_file,
    _to_iso2,
    _to_float,
    _CERT_FIELDS,
)


#graph state

class DocIntelState(dict):
    """
    Shared state passed between LangGraph nodes.

    Keys
    ----
    user_input       : str   — raw typed text (may be empty if file_path given)
    file_path        : str | None
    raw_text         : str   — text extracted from the document
    pre_extracted    : dict  — fields found by the regex/KV parser
    llm_output       : dict  — raw JSON dict returned by the LLM
    final_result     : ExtractedFields — validated final output
    error            : str | None — any error message
    """


#prompts

SYSTEM_PROMPT = """\
You are a trade document intelligence specialist. Your job is to extract \
structured fields from trade documents (invoices, bills of lading, packing \
lists, certificates, or plain text trade requests).

You will receive:
1. The raw document text
2. Fields already pre-extracted by a rule-based parser (may be incomplete or wrong)

Your task: produce the most accurate extraction possible by combining both sources.

You MUST return ONLY a valid JSON object with exactly these keys \
(omit a key entirely if the value cannot be determined — do NOT use null):

{
  "exporter":            string,   // company or person name
  "importer":            string,   // company or person name
  "origin_country":      string,   // ISO 3166-1 alpha-2 code e.g. "ET"
  "destination_country": string,   // ISO 3166-1 alpha-2 code e.g. "KE"
  "product":             string,   // normalised lowercase product name
  "weight_kg":           number,   // numeric kg value only
  "value_usd":           number,   // numeric USD value only
  "documents_present":   [string]  // list of document names present
}

Rules:
- Countries MUST be ISO 3166-1 alpha-2 codes (2 uppercase letters)
- weight_kg and value_usd MUST be numbers, not strings
- documents_present should list document types found e.g. \
  ["Commercial Invoice", "Certificate of Origin", "Packing List"]
- product should be lowercase and concise e.g. "roasted arabica coffee"
- Correct any errors you spot in the pre-extracted fields
- Return ONLY the JSON object — no markdown, no explanation, no code fences
"""


def _build_user_prompt(raw_text: str, pre_extracted: dict, feedback: str | None = None) -> str:
    feedback_section = ""
    if feedback:
        feedback_section = f"""
=== EVALUATOR FEEDBACK FROM PREVIOUS ATTEMPT ===
{feedback}
The above documents were found to be missing. If any evidence of them exists
in the document text, extract them. Otherwise note they are absent.
"""
    return f"""\
=== RAW DOCUMENT TEXT ===
{raw_text[:6000]}

=== PRE-EXTRACTED FIELDS (rule-based parser) ===
{json.dumps(pre_extracted, indent=2, ensure_ascii=False)}
{feedback_section}
Now produce the final ExtractedFields JSON object.
"""


#nodes

def parse_node(state: DocIntelState) -> DocIntelState:
    """
    Node 1: Use doc_intel.py rule-based parser to extract raw fields
    and capture the raw document text.
    """
    try:
        file_path = state.get("file_path")
        user_input = state.get("user_input", "")

        if file_path:
            doc: TradeDocument = extract_from_file(file_path)
        else:
            doc: TradeDocument = extract_from_text(user_input)

        state["raw_text"]     = doc.raw_text or user_input
        state["pre_extracted"] = doc.to_dict()

    except Exception as e:
        state["error"]        = f"Parse error: {e}"
        state["raw_text"]     = state.get("user_input", "")
        state["pre_extracted"] = {}

    return state


def llm_node(state: DocIntelState) -> DocIntelState:
    """
    Node 2: Send raw text + pre-extracted fields to GPT.
    GPT returns a JSON object matching ExtractedFields.
    """
    if state.get("error"):
        return state

    try:
        llm = ChatOpenAI(
            model="gpt-4o-mini",       
            temperature=0,            
            response_format={"type": "json_object"},
        )

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=_build_user_prompt(
                state["raw_text"],
                state["pre_extracted"],
                state.get("feedback")
            )),
        ]

        response = llm.invoke(messages)
        raw_json = response.content.strip()

        state["llm_output"] = json.loads(raw_json)

    except json.JSONDecodeError as e:
        state["error"] = f"LLM returned invalid JSON: {e}"
    except Exception as e:
        state["error"] = f"LLM error: {e}"

    return state


def output_node(state: DocIntelState) -> DocIntelState:
    """
    Node 3: Validate and coerce the LLM output into ExtractedFields.
    Falls back to the pre-extracted fields if LLM failed.
    """
    if state.get("error") or not state.get("llm_output"):
        #graceful fallback
        pre = state.get("pre_extracted", {})
        raw = state.get("raw_text", "")

        fallback = ExtractedFields(
            exporter=            pre.get("exporter_name"),
            importer=            pre.get("importer_name"),
            origin_country=      _to_iso2(pre.get("origin_country") or pre.get("country_of_origin")),
            destination_country= _to_iso2(pre.get("destination_country") or pre.get("importer_country")),
            product=             (pre.get("product_name") or "").lower().strip() or None,
            weight_kg=           _to_float(pre.get("net_weight") or pre.get("gross_weight")),
            value_usd=           _to_float(pre.get("invoice_value") or pre.get("total_value")),
            documents_present=   [
                label for f, label in _CERT_FIELDS.items() if pre.get(f)
            ],
        )
        state["final_result"] = {k: v for k, v in fallback.items() if v is not None}
        return state

    raw = state["llm_output"]

    # Coerce and validate each field
    result: dict[str, Any] = {}

    if raw.get("exporter"):
        result["exporter"] = str(raw["exporter"])

    if raw.get("importer"):
        result["importer"] = str(raw["importer"])

    # Country codes: ensure 2-letter uppercase, fallback to _to_iso2
    for country_key in ("origin_country", "destination_country"):
        val = raw.get(country_key)
        if val:
            val = str(val).strip().upper()
            if len(val) == 2 and val.isalpha():
                result[country_key] = val
            else:
                # LLM returned full name instead of code — convert it
                iso = _to_iso2(val)
                if iso:
                    result[country_key] = iso

    if raw.get("product"):
        result["product"] = str(raw["product"]).lower().strip()

    # Numerics
    for num_key in ("weight_kg", "value_usd"):
        val = raw.get(num_key)
        if val is not None:
            coerced = _to_float(str(val))
            if coerced is not None:
                result[num_key] = coerced

    # Documents list
    docs = raw.get("documents_present")
    if docs and isinstance(docs, list):
        result["documents_present"] = [str(d) for d in docs if d]

    state["final_result"] = result
    return state


#build graph

def _build_graph() -> Any:
    graph = StateGraph(DocIntelState)

    graph.add_node("parse",  parse_node)
    graph.add_node("llm",    llm_node)
    graph.add_node("output", output_node)

    graph.set_entry_point("parse")
    graph.add_edge("parse",  "llm")
    graph.add_edge("llm",    "output")
    graph.add_edge("output", END)

    return graph.compile()


_graph = _build_graph()


#public api

def run_pipeline(
    user_input: str = "",
    file_path: str | None = None,
    openai_api_key: str | None = None,
    feedback: str | None = None,          # ← add this
) -> ExtractedFields:
    """
    Run the full Document Intelligence LangGraph pipeline.

    Parameters
    ----------
    user_input      : plain text (invoice text, trade sentence, etc.)
    file_path       : path to PDF / DOCX / TXT file (overrides user_input)
    openai_api_key  : optional — reads from OPENAI_API_KEY env var if not given

    Returns
    -------
    ExtractedFields TypedDict
    """
    if openai_api_key:
        os.environ["OPENAI_API_KEY"] = openai_api_key

    if not os.environ.get("OPENAI_API_KEY"):
        raise ValueError(
            "OpenAI API key not set. Pass openai_api_key=... or set "
            "the OPENAI_API_KEY environment variable."
        )

    
    initial_state = DocIntelState(
        user_input=user_input,
        file_path=file_path,
        feedback=feedback,
        raw_text="",
        pre_extracted={},
        llm_output={},
        final_result={},
        error=None,
    )

    final_state = _graph.invoke(initial_state)

    return final_state.get("final_result", {})


#quick testing

if __name__ == "__main__":
    import sys

    samples = [
        "Export 500kg roasted coffee from Ethiopia to Kenya, value USD 8,000.",
        """
        Invoice Number: INV-2024-00712
        Invoice Date: 15 March 2024
        Exporter: Addis Trading PLC
        Exporter Country: Ethiopia
        Importer: Nairobi Imports Ltd
        Importer Country: Kenya
        Product: Roasted Arabica Coffee
        HS Code: 0901.21.00
        Quantity: 500 kg
        Net Weight: 500 kg
        Gross Weight: 540 kg
        Unit Price: USD 16.00
        Total Value: USD 8,000
        Currency: USD
        Incoterms: FOB
        Port of Loading: Djibouti Port
        Port of Discharge: Mombasa Port
        Mode of Transport: Sea
        Certificate of Origin: CO-2024-ET-00712
        Phytosanitary Certificate: PHY-2024-00123
        Free Trade Agreement: COMESA
        Payment Terms: 30 days LC
        """,
    ]

    for i, sample in enumerate(samples, 1):
        print(f"\n{'='*60}")
        print(f"SAMPLE {i}")
        print(f"{'='*60}")
        try:
            result = run_pipeline(user_input=sample)
            for k, v in result.items():
                print(f"  {k:<25} {v}")
        except ValueError as e:
            print(f"  ERROR: {e}")

    if len(sys.argv) > 1:
        fp = sys.argv[1]
        print(f"\n{'='*60}")
        print(f"FILE: {fp}")
        print(f"{'='*60}")
        result = run_pipeline(file_path=fp)
        for k, v in result.items():
            print(f"  {k:<25} {v}")
