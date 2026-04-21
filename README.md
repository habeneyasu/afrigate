---
title: Afrigate
emoji: 🌍
colorFrom: gray
colorTo: blue
sdk: gradio
app_file: app.py
pinned: false
---

# Afrigate

**Autonomous trade compliance for African cross-border corridors** — a LangGraph multi-agent system we built to turn natural-language export intent into validated, rule-checked outcomes. Phase 1 runs a **zero-API, deterministic middle layer** so you can explore the graph and UI without external keys.

[Repository](https://github.com/habeneyasu/afrigate) · Built at the **Andela AI Engineering Bootcamp** (AfCFTA-focused prototype; initial corridor: **Ethiopia → Kenya**, coffee).

---

## Why we built this

Cross-border African trade fails in expensive, mundane ways: a missing certificate, a miscoded product line, or paperwork that does not match the destination regime can delay shipments, burn margin, and shut markets.

We built Afrigate to automate a slice of that workflow — **extract → classify → validate → decide** — and to make the **failure → recovery → success** loop visible when the first pass is incomplete.

## What you can do with Afrigate (today)

- **Run a cross-border compliance check** from a single natural-language request via the Gradio UI (`ui/app.py`).
- **Watch the system self-correct**: the evaluator writes feedback into shared state and the graph reruns extraction (bounded by `MAX_ITERATIONS`).
- **Extend coverage without code changes** by editing JSON rules in `rules/` (HS mappings and destination requirements).
- **Test each step in isolation** (unit tests) or run the full graph end-to-end (integration tests).

---

## Architecture in one minute

### Orchestration: shared state, not “agent chat”

In LangGraph, **agents do not call one another**. There are no hand-offs or peer messages between nodes. Each step **reads** a shared `TypedDict` state, **writes** partial updates, and returns control to the **graph**, which chooses what runs next.

That separation keeps steps **stateless, narrow, and testable**, and it concentrates orchestration intelligence in **edges and conditional routing** — where audits and changes belong in production systems.

### Design choice: LLM at the edges, deterministic in the middle

| Layer | Role | Why |
|--------|------|-----|
| **Edges (LLM-capable)** | Natural-language understanding (document intelligence) and qualitative decisions (evaluator feedback) | Human input and “what went wrong?” explanations are not safely reduced to regex alone. |
| **Middle (deterministic)** | HS lookup and compliance rules | **Correctness and repeatability** are non-negotiable; rules live in **Python + JSON**, not in model weights. |

### What actually makes the demo work

1. **Agree the state schema before implementing nodes** — every agent assumes the same fields and merge semantics.
2. **Treat the graph as the product** — nodes are replaceable; routing, caps, and termination policy are the design.
3. **Show failure → recovery → success** — audiences understand multi-agent orchestration faster when the loop is visible end-to-end.

---

## Pipeline

Four graph nodes, one shared `AfrigateState`:

```
START
  │
  ▼
doc_intel        — structured extraction from natural-language input (LLM when enabled)
  │
  ▼
hs_classifier    — product → 6-digit HS-style code via deterministic lookup
  │
  ▼
compliance       — validates extracted data vs destination rules (JSON-backed)
  │
  ▼
evaluator        — accept | retry (with NL feedback) | ask_user
  │
  ├─► accept    ──► END  (final_report)
  ├─► retry     ──► doc_intel (feedback merged into state; bounded by MAX_ITERATIONS, default 3)
  └─► ask_user  ──► END  (human follow-up)
```

**Reference scenario:** an Ethiopian exporter ships **500 kg roasted coffee** to Kenya. Kenyan rules may require documents such as a **Certificate of Origin** and **Phytosanitary certificate**. If the first extraction omits a requirement, the evaluator records **actionable feedback** in state; document intelligence runs again with that context until compliance passes or the loop cap is reached.

---

## Stack

**LangGraph** · **GPT-4o-mini** (when LLM features are on) · **Gradio** · **LangSmith** (optional tracing)

---

## Authors

Built by **Haben E. Akelom**, **Naheem Quadri**, **Iyanuoluwa Ajao**, and **Mubaraq Sanusi** at the Andela AI Engineering Bootcamp.

---

## Project structure

```
afrigate/
├── agents/
│   ├── doc_intel.py        — extraction & parsing
│   ├── hs_classifier.py    — HS code classification
│   ├── compliance.py       — compliance validation
│   └── evaluator.py        — decisioning & retry feedback
├── core/
│   ├── state.py            — AfrigateState + sub-schemas + initial_state()
│   ├── graph.py            — LangGraph nodes, edges, retry routing
│   └── config.py           — Pydantic settings (API keys, MAX_ITERATIONS)
├── rules/
│   ├── regulations.json    # Required documents per country (KE, NG, GH, ET)
│   └── hs_codes.json       # Product → HS code + tariff + trade agreement  ✓
├── rag/                    # Phase 2 — RAG knowledge base (stubs)
├── app.py                  # Hugging Face Spaces entry (Gradio)
├── requirements.txt        # pip / Spaces dependencies
├── ui/
│   ├── demo.py             # Gradio demo (shared with app.py)
│   └── app.py              # Full Gradio UI (streaming mock_graph)
├── utils/
│   ├── logger.py           — structured logging
│   └── langsmith.py        — LangSmith tracing setup
└── tests/
    ├── conftest.py         — shared fixtures (Addis–Nairobi scenario)
    ├── unit/               — per-agent unit tests
    └── integration/        — full graph end-to-end test
```

---

## Getting started

**Requirements:** Python 3.11+

```bash
# 1. Install dependencies
pip install -e ".[dev]"

# 2. Set up environment
cp .env.example .env
# Phase 1: you can leave API keys blank for the deterministic demo path

# 3. Run the UI
python app.py              # demo (same as Spaces)
# or: python -m ui.app    # full streaming UI

# 4. Run tests
pytest -q
```

### Hugging Face Spaces

1. Create a **Gradio** Space and connect this repository (or push a copy).
2. Leave **App file** as **`app.py`** (declared in the YAML header above).
3. Dependencies install from **`requirements.txt`**. Phase 1 needs **no secrets**; optional API keys later go in **Space secrets** (e.g. `OPENAI_API_KEY`), read by `core/config.py`.
4. Use a **CPU basic** tier to start; **chromadb** and LangChain pull a sizeable stack — first boot can take a few minutes.

---

## State schema

Defined in `core/state.py` as typed sub-schemas. Agents return **partial update** dicts; LangGraph merges them into `AfrigateState`.

| Field | Type | Set by |
|------|------|--------|
| `document_raw` | `str` | UI / caller |
| `extracted_fields` | `ExtractedFields` | doc_intel |
| `hs_result` | `HSResult` | hs_classifier |
| `compliance_result` | `ComplianceResult` | compliance |
| `evaluator_decision` | `accept \| retry \| ask_user` | evaluator |
| `evaluator_feedback` | `str` | evaluator |
| `iteration` | `int` | evaluator (incremented on retry) |
| `agent_log` | `list[str]` | all agents (append-merged) |
| `final_report` | `FinalReport \| None` | evaluator (on accept / ask_user) |
| `errors` | `list[str]` | any agent (append-merged) |

Minimal invoke:

```python
from core.state import initial_state
from core.graph import build_graph

result = build_graph().invoke(initial_state(
    "Export 500kg roasted coffee from Ethiopia to Kenya, value USD 8,000."
))
```

---

## Configuration

Settings live in `core/config.py` (Pydantic, loaded from `.env`):

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_ITERATIONS` | `3` | Upper bound on self-correction loops |
| `DEFAULT_MODEL` | `gpt-4o-mini` | LLM model when the LLM layer is enabled |
| `LANGCHAIN_TRACING_V2` | `false` | Enable LangSmith tracing |
| `OPENAI_API_KEY` | — | Required only when the LLM layer is enabled |
| `GOOGLE_API_KEY` | — | Required only for optional Google-backed paths |

---

## Rules data

Extend coverage by editing JSON — no code changes required for many rule updates:

- `rules/hs_codes.json` — product keywords → HS code, tariff rate, trade agreement
- `rules/regulations.json` — destination country → required document keys

---

## Specification

See `SPEC.md` for the full project RFC and design notes.
