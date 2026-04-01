# 🌍 Project RFC: Afrigate (Phase 1)

Autonomous Multi-Agent Swarm for Cross-Border Trade Compliance  
Phase 1 – Technical Specification (RFC)  
Version 1.0 | April 2026  
Prepared by: squad-3

---

## 1. Executive Summary

Afrigate is an intelligent orchestration system designed to automate the high-friction world of African trade compliance (AfCFTA). Instead of a simple chatbot, we are building a Self-Correcting Swarm of 5 Specialized Agents that handle data extraction, customs classification, and regulatory auditing.

Why this project stands out:
- Uniqueness – Moves beyond generic chatbots into a $50B African trade compliance gap.
- Complexity – Showcases Hierarchical Orchestration, Stateful Execution, and a Self-Correction Loop.
- Scalability – Modular "Plug-and-Play" architecture; mocks can be upgraded to LLMs/Vision APIs in Phase 2 without changing the graph.
- Real‑world impact – Solves a tangible problem: enabling an African exporter to reach the Kenyan market seamlessly.
- Defined scope – Phase 1 uses deterministic (mocked) agents, delivering a working demo within 2-3 days.

---

## 2. The Scenario: "Addis-to-Nairobi" Coffee Route

Business Situation: An Ethiopian exporter wants to ship 500kg of roasted coffee to Kenya.  
The Constraint: Kenyan rules require a Certificate of Origin and a Phytosanitary Certificate.

The Demo Flow (Self-Correction in Action):
1. User Input: "Export 500kg roasted coffee from Ethiopia to Kenya, value USD 8,000."
2. First Pass (Failure): The system identifies the product but flags missing certificates.
3. Self-Correction: The Evaluator provides feedback; the Document Agent retries and "attaches" the missing docs.
4. Success: The second pass meets all criteria and is Accepted.

Behind the scenes, five AI agents collaborate to process this request.

---

## 3. The Agent Team – Roles & Responsibilities

| Agent | Role | Real‑world Equivalent | Responsibility |
|---|---|---|---|
| Document Intelligence | The Clerk | Extracts key trade fields (exporter, product, value) from input. | doc_intel |
| HS Code Classifier | The Specialist | Assigns the correct 6-digit customs code (e.g., Coffee → 0901). | hs_classifier |
| Compliance Checker | The Auditor | Validates data against destination country rules (Kenya). | compliance |
| Evaluator | The QA Lead | Decides: Accept, Retry (Loop), or Ask User. | evaluator |
| Supervisor (LangGraph) | The Brain | LangGraph logic manages the sequence and conditional routing. | core/graph.py |

---

## 4. Orchestration Flow – Step by Step

The system operates on a shared global state (`AfrigateState`) that holds user input, extracted data, HS code, compliance result, evaluator decision, and iteration count.

The flow is fully deterministic and repeatable:
1. Document Intelligence reads the user input and extracts basic data (exporter, product, value).  
   First pass: the required certificates are missing.
2. HS Code Classifier looks up the product in a mock tariff database → returns HS code 0901 and tariff 0% (under COMESA).
3. Compliance Checker validates the extracted data against Kenyan rules:  
   Detects missing `certificate_of_origin` → returns `passed=False`, `missing_fields=["certificate_of_origin"]`, and a suggestion.
4. Evaluator receives the compliance result:  
   Because it failed and `iteration < max_iterations` (default 3), the evaluator decides `retry`.  
   It stores feedback: “Missing Certificate of Origin – please upload.”
5. The Supervisor (LangGraph) routes the flow back to Document Intelligence, passing the evaluator’s feedback.
6. Document Intelligence, now armed with feedback, “adds” the missing certificate (mocked) to its extracted data.
7. Compliance Checker runs again; now all required documents are present → `passed=True`.
8. Evaluator sees `passed=True` → decides `accept` → workflow ends.

Throughout the process, the user sees a step‑by‑step log in the UI, showing the failure, feedback, retry, and final success.

---

## 5. Visual Representation of the Swarm

```
START
  │
  ▼
Document Intelligence  ───► (Extracts data)
  │
  ▼
HS Code Classifier     ───► (Assigns HS code & tariff)
  │
  ▼
Compliance Checker     ───► (Validates against rules)
  │
  ▼
Evaluator              ───► (Decision Node)
  │
  ├─► [Decision: accept] ────► END
  │
  ├─► [Decision: retry]  ────► Back to Document Intelligence (w/ feedback)
  │
  └─► [Decision: ask_user] ──► END (Manual Intervention)
```

Safety: An iteration cap (default 3) prevents infinite loops. The evaluator increments the counter each time it runs, and the router only allows a retry if `iteration < max_iterations`.

---

## 6. Phase 1 Engineering Standards

-Structured LLM Extraction: We use Lite LLMs (GPT-4o-mini / Gemini Flash) for Document Intelligence and the Evaluator. These are strictly constrained to return structured JSON, ensuring they act as reliable data parsers rather than creative writers.

-Deterministic Guardrails: The HS Classifier and Compliance Checker run on local, mocked JSON rules (/rules). This prevents "hallucinated compliance" and ensures that if a document is missing, the system detects it with 100% mathematical certainty.

-Orchestration over Prompting: We prioritize LangGraph's state machine logic over long-form prompting. The "intelligence" of the system is in the Self-Correction Loop, not just the individual LLM calls.

-Zero-Failure Demo Mode: Phase 1 includes a "Safety Buffer" where critical regulatory checks are pre-validated against our local knowledge base to ensure the demo is repeatable and robust.

---

## 7. RAG as a Knowledge Base (Planned Enhancement)

While Phase 1 uses deterministic mocks, the architecture is designed to seamlessly integrate a Retrieval‑Augmented Generation (RAG) layer in later phases. This will allow the agents to access and reason over external knowledge sources, such as:
- Country‑specific trade regulations – dynamically retrieved from official customs databases.
- Document templates – standard forms (e.g., Certificate of Origin, Phytosanitary Certificate) for the Document Intelligence agent.
- HS code descriptions – to improve classification accuracy.

How RAG would be integrated:
- A vector store (e.g., ChromaDB) will hold chunked versions of trade rules, HS code tables, and sample documents.
- When an agent needs context (e.g., the Compliance Checker validating a document), it will perform a semantic search over the knowledge base and inject relevant passages into its prompt.
- The Evaluator could also retrieve historical compliance decisions to provide richer feedback.

This approach makes the system knowledge‑driven and adaptable – new rules can be added simply by updating the knowledge base without changing agent code.

---

## 8. What the Demo Shows

The live Gradio demo will:
1. Accept a trade request from the user.
2. Display the progress of each agent step by step.
3. Show the self‑correction loop in action: first attempt fails → feedback is given → second attempt succeeds.
4. Make the orchestration logic transparent – viewers can see the conditional routing and iteration cap.

---

## 9. Business Value – Why This Matters

| Problem | How Afrigate Solves It |
|---|---|
| Manual data extraction is slow and error‑prone. | Automates the extraction and structuring of trade information. |
| Customs rules are complex and change frequently. | Compliance Checker applies consistent, up‑to‑date rules. |
| Missing documents cause delays and penalties. | Evaluator detects gaps and triggers self‑correction. |
| Business processes involve multiple handoffs. | Supervisor orchestrates a seamless, auditable workflow. |
| Multi‑agent orchestration is the core requirement. | Built as a LangGraph swarm: hierarchical control, stateful collaboration, self‑correcting loop. |

The result is a reliable, scalable, and self‑improving system that can handle high volumes of trade requests with minimal human oversight.



---

## 10. LLM Feature

To demonstrate AI-powered interfaces while preserving deterministic core logic, we will introduce a minimal LLM layer:

- Structured Extraction — Use a lightweight LLM (e.g., GPT‑4o‑mini or Gemini Flash) in the Document Intelligence node to parse the user’s request into our orchestration schema.
- Reasoning Evaluator — Replace the mock evaluator with an LLM that analyses why a document is missing and generates natural‑language feedback to drive the retry loop.
- The ‘Mock’ Guardrail — Keep the compliance rules as a local JSON/dictionary. This ensures the core logic remains deterministic and demo‑ready, while the interface and reasoning are AI‑powered.

Scope notes:
- No external API keys are required for Phase 1; this section is optional and can be toggled via config.
- When enabled, the LLM components only enrich input/output surfaces; compliance decisions continue to rely on local rules.

---

---

## 11. Module Ownership

| File | Owner |
|---|---|
| `agents/doc_intel.py` | @naheem |
| `agents/hs_classifier.py` | @Matrix |
| `agents/compliance.py` | Auditor |
| `agents/evaluator.py` | @iyanuashiri |
| `core/graph.py` | Haben E. Akelom |
| `core/state.py` | Haben E. Akelom |
