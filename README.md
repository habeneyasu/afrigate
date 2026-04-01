# Afrigate

Autonomous multi-agent swarm for African cross-border trade compliance, built with LangGraph.

Phase 1 uses a zero-API, deterministic architecture — no API keys required to run the demo.

---

## The Problem

African exporters face a high-friction compliance process: wrong HS codes, missing certificates, and country-specific rules that change frequently. Afrigate automates this end-to-end.

**Reference scenario (RFC §2):** An Ethiopian exporter ships 500 kg of roasted coffee to Kenya. Kenyan rules require a Certificate of Origin and a Phytosanitary Certificate. Afrigate detects the missing documents, self-corrects, and produces a compliant report — without human intervention.

---

## How It Works

Five agents collaborate under a LangGraph state machine, sharing a single `AfrigateState` object:

```
START
  │
  ▼
doc_intel        — extracts product, countries, value, documents from user input
  │
  ▼
hs_classifier    — looks up HS code + tariff rate from rules/hs_codes.json
  │
  ▼
compliance       — validates required documents against rules/regulations.json
  │
  ▼
evaluator        — decides: accept / retry (with feedback) / ask_user
  │
  ├─► accept    ──► END  (final_report produced)
  ├─► retry     ──► back to doc_intel with feedback  (max MAX_ITERATIONS, default 3)
  └─► ask_user  ──► END  (manual intervention required)
```

---

## Project Structure

```
afrigate/
├── agents/
│   ├── doc_intel.py        # @naheem      — extraction & parsing
│   ├── hs_classifier.py    # @Matrix      — HS code classification  ✓
│   ├── compliance.py       # Auditor      — compliance validation
│   └── evaluator.py        # @iyanuashiri — reasoning & retry logic
├── core/
│   ├── state.py            # AfrigateState + sub-schemas + initial_state()  ✓
│   ├── graph.py            # LangGraph nodes, edges, retry routing  ✓
│   └── config.py           # Pydantic settings (API keys, MAX_ITERATIONS)  ✓
├── rules/
│   ├── regulations.json    # Required documents per country (KE, NG, GH, ET)
│   └── hs_codes.json       # Product → HS code + tariff + trade agreement  ✓
├── rag/                    # Phase 2 — RAG knowledge base (stubs)
├── ui/
│   └── app.py              # Gradio web interface
├── utils/
│   ├── logger.py           # Structured logging
│   └── langsmith.py        # LangSmith tracing setup
└── tests/
    ├── conftest.py         # Shared fixtures (Addis-to-Nairobi scenario)
    ├── unit/               # Per-agent unit tests
    └── integration/        # Full graph end-to-end test
```

---

## Getting Started

**Requirements:** Python 3.11+

```bash
# 1. Install dependencies
pip install -e ".[dev]"

# 2. Set up environment
cp .env.example .env
# Phase 1 needs no API keys — leave them blank

# 3. Run the UI
python -m ui.app

# 4. Run tests
pytest -q
```

---

## State Schema

Defined in `core/state.py` as typed sub-schemas. All agents return partial update dicts; LangGraph merges them automatically.

| Field | Type | Set by |
|---|---|---|
| `document_raw` | `str` | UI / caller |
| `extracted_fields` | `ExtractedFields` | doc_intel |
| `hs_result` | `HSResult` | hs_classifier |
| `compliance_result` | `ComplianceResult` | compliance |
| `evaluator_decision` | `accept \| retry \| ask_user` | evaluator |
| `evaluator_feedback` | `str` | evaluator |
| `iteration` | `int` | evaluator (incremented on retry) |
| `agent_log` | `list[str]` | all agents (append-merged) |
| `final_report` | `FinalReport \| None` | evaluator (on accept/ask_user) |
| `errors` | `list[str]` | any agent (append-merged) |

To start a new request:

```python
from core.state import initial_state
from core.graph import build_graph

result = build_graph().invoke(initial_state(
    "Export 500kg roasted coffee from Ethiopia to Kenya, value USD 8,000."
))
```

---

## Configuration

All settings are in `core/config.py` (Pydantic, reads from `.env`):

| Variable | Default | Description |
|---|---|---|
| `MAX_ITERATIONS` | `3` | Self-correction loop cap |
| `DEFAULT_MODEL` | `gpt-4o-mini` | LLM model (Phase 2) |
| `LANGCHAIN_TRACING_V2` | `false` | Enable LangSmith tracing |
| `OPENAI_API_KEY` | — | Required only when LLM layer is enabled |
| `GOOGLE_API_KEY` | — | Required only when LLM layer is enabled |

---

## Rules Data

Edit these files to extend coverage — no code changes needed:

- `rules/hs_codes.json` — product keywords → HS code, tariff rate, trade agreement
- `rules/regulations.json` — destination country → required document keys

---

See `SPEC.md` for the full RFC.
