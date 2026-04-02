# Afrigate — End-to-End Implementation Guide

Version 1.0 | Phase 1 | April 2026

---

## Overview

Afrigate is an autonomous multi-agent swarm that automates African cross-border trade compliance. A user submits a trade request in plain text; five specialised agents process it through a LangGraph state machine, self-correct when documents are missing, and produce a structured compliance report.

**Reference scenario (RFC §2):** An Ethiopian exporter ships 500 kg of roasted coffee to Kenya. Kenyan regulations require four documents. The system detects the missing documents on the first pass, retries with feedback, and resolves to compliant on the second pass — without human intervention.

---

## Architecture

```
User Input (Gradio)
       │
       ▼
  doc_intel          Extract product, countries, value, documents
       │
       ▼
  hs_classifier      Look up HS code + tariff from rules/hs_codes.json
       │
       ▼
  compliance         Validate documents against rules/regulations.json
       │
       ▼
  evaluator          Decide: accept / retry / ask_user
       │
       ├── accept    ──► FinalReport (compliant) → END
       ├── retry     ──► feedback → doc_intel (max 3 iterations)
       └── ask_user  ──► FinalReport (pending_user_input) → END
```

All agents share a single `AfrigateState` object. Each agent returns a **partial update dict**; LangGraph merges it back into the state automatically. No agent holds private state.

---

## Shared State — `AfrigateState`

Defined in `core/state.py`. Every field is optional (`total=False`) because the graph starts with only `document_raw` set and populates fields incrementally.

| Field | Type | Set by |
|---|---|---|
| `document_raw` | `str` | UI / caller |
| `extracted_fields` | `ExtractedFields` | doc_intel |
| `hs_result` | `HSResult` | hs_classifier |
| `compliance_result` | `ComplianceResult` | compliance |
| `evaluator_decision` | `accept \| retry \| ask_user` | evaluator |
| `evaluator_feedback` | `str` | evaluator (on retry) |
| `iteration` | `int` | evaluator (incremented on retry) |
| `agent_log` | `list[str]` | all agents (append-merged) |
| `final_report` | `FinalReport \| None` | evaluator (on accept/ask_user) |
| `errors` | `list[str]` | any agent (append-merged) |

`agent_log` and `errors` use `Annotated[list, operator.add]` — LangGraph appends each node's entries rather than overwriting them. This is what produces the step-by-step log in the UI.

---

## Agent Implementations

### 1. doc_intel — `agents/doc_intel.py`

**Status:** stub (`NotImplementedError`) — pending implementation.

**Contract:**
- Input: `state["document_raw"]`, `state["evaluator_feedback"]` (on retry), `state["iteration"]`
- Output: `extracted_fields`, `agent_log`

**On first pass:** parse the raw text and populate `ExtractedFields`. `documents_present` starts as an empty list.

**On retry (`iteration > 0`):** read `evaluator_feedback`, identify the named missing documents, and add them to `documents_present`. This is the self-correction mechanism.

`ExtractedFields` schema:
```python
{
    "origin_country": "ET",       # ISO-2
    "destination_country": "KE",  # ISO-2
    "product": "roasted coffee",  # normalised string
    "weight_kg": 500.0,
    "value_usd": 8000.0,
    "documents_present": [],      # empty on first pass
}
```

---

### 2. hs_classifier — `agents/hs_classifier.py`

**Status:** fully implemented.

Performs a deterministic keyword lookup against `rules/hs_codes.json`. Normalises the product string (lowercase, collapsed whitespace) and checks each entry's `keywords` array for a substring match.

**Input:** `state["extracted_fields"]["product"]`

**Output:** `hs_result`, `agent_log`

```python
# hs_result shape
{
    "found": True,
    "hs_code": "0901.21",
    "description": "Coffee, roasted",
    "tariff_rate": 0.0,       # 0% under COMESA
    "trade_agreement": "COMESA",
}
```

The JSON table (`rules/hs_codes.json`) covers 10 African trade commodities: coffee, cocoa, cashew, tea, cotton, palm oil, shea, sesame, mango, cut flowers.

---

### 3. compliance — `agents/compliance.py`

**Status:** fully implemented.

Loads `rules/regulations.json` (cached with `@lru_cache`) and performs a set-difference between the destination country's `required_documents` and `extracted_fields.documents_present`.

**Input:** `state["extracted_fields"]["destination_country"]`, `state["extracted_fields"]["documents_present"]`

**Output:** `compliance_result`, `agent_log`

```python
# compliance_result — failed
{
    "passed": False,
    "missing_fields": ["certificate_of_origin", "phytosanitary_certificate"],
    "suggestion": "Missing 2 required document(s) for Kenya: Certificate Of Origin, Phytosanitary Certificate.",
}

# compliance_result — passed
{
    "passed": True,
    "missing_fields": [],
    "suggestion": "All required documents present. Shipment is compliant.",
}
```

Handles unknown destinations gracefully — returns `passed=False` with an informative suggestion rather than raising an exception.

---

### 4. evaluator — `agents/evaluator.py`

**Status:** fully implemented.

The decision node. Reads `compliance_result.passed` and `iteration` against `settings.max_iterations` (default 3) to determine the routing outcome.

**Input:** `state["compliance_result"]`, `state["hs_result"]`, `state["iteration"]`

**Output:** `evaluator_decision`, `evaluator_feedback`, `iteration` (on retry), `final_report` (on accept/ask_user), `agent_log`

**Decision logic:**

| Condition | Decision | Action |
|---|---|---|
| `passed=True` | `accept` | Build `FinalReport(status="compliant")`, end |
| `passed=False` and `iteration < max_iterations` | `retry` | Write `evaluator_feedback`, increment `iteration` |
| `passed=False` and `iteration >= max_iterations` | `ask_user` | Build `FinalReport(status="pending_user_input")`, end |

On `retry`, `evaluator_feedback` names the missing documents in human-readable form:
```
"Missing document(s): Certificate Of Origin, Phytosanitary Certificate. Please provide these to proceed."
```

`doc_intel` reads this feedback on the next iteration to know which documents to add.

---

### 5. Supervisor — `core/graph.py`

The LangGraph state machine. Wires the four nodes and implements the conditional routing function `_route()`.

```python
def _route(state: AfrigateState) -> str:
    decision = state.get("evaluator_decision")
    iteration = state.get("iteration", 0)
    if decision == "retry" and iteration < settings.max_iterations:
        return "doc_intel"
    return END
```

`accept` and `ask_user` both route to `END`. The iteration cap is enforced here — even if the evaluator emits `retry`, the router blocks it once the cap is reached.

---

## Rules Data

### `rules/hs_codes.json`

Array of entries, each with `keywords`, `hs_code`, `description`, `tariff_rate`, and `trade_agreement`. The classifier does substring matching on normalised product strings against the keywords list.

### `rules/regulations.json`

Flat dict keyed by ISO-2 country code. Each entry has `country` (display name) and `required_documents` (list of document ID strings).

```json
{
  "KE": {
    "country": "Kenya",
    "required_documents": [
      "certificate_of_origin",
      "phytosanitary_certificate",
      "commercial_invoice",
      "packing_list"
    ]
  }
}
```

To add a new country or document requirement, edit this file — no code changes needed.

---

## Configuration — `core/config.py`

Pydantic `Settings` loaded from `.env` at import time.

| Variable | Default | Description |
|---|---|---|
| `MAX_ITERATIONS` | `3` | Self-correction loop cap (must be ≥ 1) |
| `DEFAULT_MODEL` | `gpt-4o-mini` | LLM model for Phase 2 |
| `OPENAI_API_KEY` | — | Required only when LLM layer is enabled |
| `GOOGLE_API_KEY` | — | Required only when LLM layer is enabled |
| `LANGCHAIN_TRACING_V2` | `false` | Enable LangSmith tracing |
| `LANGCHAIN_API_KEY` | — | LangSmith API key |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

Phase 1 requires no API keys. All logic is deterministic.

---

## Gradio UI — `ui/app.py`

The web interface runs the pipeline and displays results in two panels.

**To launch:**
```bash
uv run python3 -m ui.app
# Open http://127.0.0.1:7860
```

**Layout:**
- Trade request input (text box)
- Agent Log panel — chronological step-by-step output from every agent
- Final Report panel — structured JSON output

**Phase 1 note:** `doc_intel` is currently mocked with a hardcoded extraction (Ethiopia → Kenya, roasted coffee, 500 kg, USD 8,000). The self-correction loop still fires — compliance fails on pass 1, evaluator retries, the mock adds the missing documents, compliance passes on pass 2. Replace `_mock_doc_intel` with `run_doc_intel` once implemented.

---

## Self-Correction Loop — Walkthrough

Using the reference scenario:

```
Input: "Export 500kg roasted coffee from Ethiopia to Kenya, value USD 8,000."
```

**Pass 1**
```
doc_intel:     extracted product='roasted coffee', destination='KE'
hs_classifier: 0901.21 (COMESA, tariff 0.0%)
compliance:    FAILED — missing ['certificate_of_origin', 'phytosanitary_certificate',
                                  'commercial_invoice', 'packing_list']
evaluator:     retry (iteration=1) — Missing document(s): Certificate Of Origin,
               Phytosanitary Certificate, Commercial Invoice, Packing List.
```

**Pass 2** (doc_intel applies feedback, adds all missing docs)
```
doc_intel:     added missing documents from feedback
hs_classifier: 0901.21 (COMESA, tariff 0.0%)
compliance:    PASSED
evaluator:     accept — compliant after 1 iteration(s)
```

**Final Report**
```json
{
  "status": "compliant",
  "hs_code": "0901.21",
  "tariff_rate": 0.0,
  "trade_agreement": "COMESA",
  "missing_documents": [],
  "suggestion": "All required documents present. Shipment is compliant.",
  "iterations_taken": 1
}
```

---

## Testing

```bash
# All unit tests
uv run --extra dev pytest tests/unit/ -v

# Specific modules
uv run --extra dev pytest tests/unit/test_compliance.py tests/unit/test_evaluator.py -v

# Quick check
uv run --extra dev pytest tests/unit/ -q
```

**Current coverage:** 39 unit tests, all passing.

| Test file | Tests | Covers |
|---|---|---|
| `test_graph.py` | 8 | Routing logic, graph compilation |
| `test_hs_classifier.py` | 2 | Coffee classification, unknown product |
| `test_compliance.py` | 9 | Failed/passed/edge cases |
| `test_evaluator.py` | 12 | accept/retry/ask_user decision paths |
| `test_rules_data.py` | 2 | JSON file integrity |
| `test_utils.py` | 4 | Logger, LangSmith setup |

---

## What's Pending

| File | Description |
|---|---|
| `agents/doc_intel.py` | Parse `document_raw` → `ExtractedFields`; apply `evaluator_feedback` on retry |
| `tests/unit/test_doc_intel.py` | Unit tests for doc_intel |
| `tests/integration/test_end_to_end.py` | Full graph invocation test |

Once `doc_intel` is implemented, remove `_mock_doc_intel` from `ui/app.py` and replace with `run_doc_intel`.

---

## Phase 2 Roadmap

- Replace `doc_intel` mock with LLM structured extraction (GPT-4o-mini / Gemini Flash)
- Replace evaluator mock with LLM reasoning for richer feedback
- Enable RAG: ChromaDB vector store over regulation PDFs (`rag/`)
- Activate LangSmith tracing for full observability

---

## LLM Strategy — Which Agents Use AI and Why

A deliberate design principle in Afrigate is that **not every agent needs an LLM**. Applying an LLM where deterministic logic suffices adds latency, cost, and — critically in a compliance context — hallucination risk. The table below documents the reasoning for each agent.

| Agent | LLM? | Model | Reasoning |
|---|---|---|---|
| `doc_intel` | Yes | `llama3.1-8b` (Cerebras) | Parsing unstructured free text into a typed schema is exactly the task LLMs excel at. Cerebras inference on Llama 3.1-8b is fast enough to run on every pass including retries without noticeable latency. |
| `hs_classifier` | No | — | Deterministic keyword lookup against a local JSON table. An LLM would introduce hallucination risk on HS codes — a wrong code means wrong tariff and potential customs rejection. Correctness is guaranteed by the rules file, not by model confidence. |
| `compliance` | No | — | Pure set-difference: `required_documents − documents_present = missing`. There is no ambiguity to reason over. An LLM adds latency and cost with zero benefit, and would make the compliance decision non-auditable. |
| `evaluator` | Yes | `gemini-1.5-flash` | Generating natural-language feedback that explains *why* documents are missing and what the exporter should do requires reasoning and fluent output. Gemini 1.5 Flash outperforms Llama 3.1-8b on instruction-following and explanation quality. `gemini-1.0-pro` is older and weaker — not recommended. |
| Supervisor (`graph.py`) | No | — | Pure Python routing: `if decision == "retry" and iteration < max_iterations`. No language understanding needed. |

**The "Mock Guardrail" principle (RFC §10):** compliance decisions must remain deterministic and traceable to a specific rule in `regulations.json`. A system that says "this shipment is *probably* fine" is a liability. The LLM layer enriches the *interface* (extraction, feedback) while the *decisions* stay rule-based.

**`.env` configuration:**
```
CEREBRAS_MODEL_WORKER=llama3.1-8b       # doc_intel — fast structured extraction
GEMINI_MODEL_EVALUATOR=gemini-1.5-flash  # evaluator — natural-language reasoning
```
