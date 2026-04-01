# Afrigate

Autonomous multi-agent swarm for African cross-border trade compliance, built with LangGraph.

Phase 1 uses fully deterministic (mocked) agents — no API keys required. The orchestration graph, self-correction loop, and Gradio UI all work out of the box.

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
  ├─► accept    ──► END  (final report produced)
  ├─► retry     ──► back to doc_intel with feedback  (max 3 iterations)
  └─► ask_user  ──► END  (manual intervention required)
```

The self-correction loop is the core feature: on a failed compliance check, the evaluator generates feedback, doc_intel applies it (e.g. adds the missing certificate), and the pipeline reruns automatically.

---

## Project Structure

```
afrigate/
├── agents/
│   ├── doc_intel.py        # @naheem      — extraction & parsing
│   ├── hs_classifier.py    # @Matrix      — HS code classification
│   ├── compliance.py       # Auditor      — compliance validation
│   └── evaluator.py        # @iyanuashiri — reasoning & retry logic
├── core/
│   ├── state.py            # AfrigateState (shared TypedDict)
│   ├── graph.py            # LangGraph state machine & routing
│   └── config.py           # Pydantic settings (keys, max_iterations, etc.)
├── rules/
│   ├── regulations.json    # Country-specific required documents (KE, NG, GH, ET)
│   └── hs_codes.json       # Product → HS code + tariff mapping
├── rag/                    # Phase 2 — RAG knowledge base (stubs only)
├── ui/
│   └── app.py              # Gradio web interface
├── utils/
│   ├── logger.py           # Structured logging
│   └── langsmith.py        # LangSmith tracing setup
└── tests/
    ├── conftest.py         # Shared fixtures (Addis-to-Nairobi scenario)
    ├── unit/               # Per-agent unit tests (skipped until implemented)
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

## Team — Module Ownership

| Module | Owner | Status |
|---|---|---|
| `agents/doc_intel.py` | @naheem | TODO |
| `agents/hs_classifier.py` | @Matrix | TODO |
| `agents/compliance.py` | Auditor | TODO |
| `agents/evaluator.py` | @iyanuashiri | TODO |
| `core/graph.py` + `core/state.py` | Haben E. Akelom | Done |

Each agent has a clear function signature, docstring, and matching unit tests in `tests/unit/`. Implement the body, remove the `raise NotImplementedError`, and the tests will automatically unskip.

---

## State Schema

All agents read from and write to `AfrigateState` (defined in `core/state.py`):

| Field | Type | Set by |
|---|---|---|
| `document_raw` | `str` | UI input |
| `extracted_fields` | `dict` | doc_intel |
| `hs_result` | `dict` | hs_classifier |
| `compliance_result` | `dict` | compliance |
| `evaluator_decision` | `accept / retry / ask_user` | evaluator |
| `evaluator_feedback` | `str` | evaluator |
| `iteration` | `int` | evaluator (incremented on retry) |
| `agent_log` | `list[str]` | all agents (appended) |
| `final_report` | `dict` | evaluator (on accept/ask_user) |

---

## Rules Data

- `rules/regulations.json` — required documents per destination country (KE, NG, GH, ET)
- `rules/hs_codes.json` — product keyword → HS code + tariff + trade agreement

Add new countries or products by editing these files — no code changes needed.

---

See `SPEC.md` for the full RFC.
