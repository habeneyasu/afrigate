"""
ui/demo.py — Afrigate end-to-end compliance demo.

Run:
    uv run python3 -m ui.demo
    Open http://127.0.0.1:7860
"""

from __future__ import annotations

import json
from typing import Any

import gradio as gr

from core.graph import build_graph
from core.state import initial_state
from utils.langsmith import configure_langsmith
from utils.logger import setup_logging

setup_logging()
configure_langsmith()

_graph = build_graph()

# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def run_pipeline(trade_request: str) -> tuple[str, str]:
    if not trade_request.strip():
        return _empty_log(), _empty_verdict()

    result: dict[str, Any] = _graph.invoke(dict(initial_state(trade_request)))
    log_html = _render_log(result.get("agent_log") or [])
    verdict_html = _render_verdict(result)
    return log_html, verdict_html


# ---------------------------------------------------------------------------
# Renderers — only what matters during a demo
# ---------------------------------------------------------------------------

_AGENT_META = {
    "doc_intel":     ("📄", "Document Intelligence"),
    "hs_classifier": ("🔢", "HS Classifier"),
    "compliance":    ("⚖️",  "Compliance Checker"),
    "evaluator":     ("🧠", "Evaluator"),
}


def _agent_tag(line: str) -> tuple[str, str]:
    for key, (icon, label) in _AGENT_META.items():
        if line.startswith(key + ":"):
            body = line[len(key) + 1:].strip()
            return f"{icon} {label}", body
    return "⚙️ System", line


def _line_accent(line: str) -> str:
    if "PASSED" in line or "accept" in line:
        return "#22c55e"
    if "retry" in line or "FAILED" in line:
        return "#f59e0b"
    if "ask_user" in line or "UNKNOWN" in line:
        return "#ef4444"
    return "#94a3b8"


def _empty_log() -> str:
    return (
        '<div style="height:100%;display:flex;align-items:center;justify-content:center;">'
        '<p style="color:#94a3b8;font-size:0.9rem;letter-spacing:0.05em;">Awaiting input…</p>'
        '</div>'
    )


def _empty_verdict() -> str:
    return (
        '<div style="height:100%;display:flex;align-items:center;justify-content:center;">'
        '<p style="color:#94a3b8;font-size:0.9rem;letter-spacing:0.05em;">No result yet.</p>'
        '</div>'
    )


def _render_log(lines: list[str]) -> str:
    rows = []
    for i, line in enumerate(lines):
        agent_label, body = _agent_tag(line)
        accent = _line_accent(line)
        border = "border-bottom:1px solid #e2e8f0;" if i < len(lines) - 1 else ""
        rows.append(f"""
        <div style="display:flex;gap:16px;align-items:flex-start;
                    padding:12px 20px;{border}">
          <span style="font-size:0.68rem;font-weight:700;letter-spacing:0.08em;
                       text-transform:uppercase;color:#64748b;min-width:180px;
                       flex-shrink:0;padding-top:2px;">{agent_label}</span>
          <span style="font-size:0.84rem;color:{accent};font-family:'JetBrains Mono',monospace;
                       line-height:1.6;word-break:break-word;">{body}</span>
        </div>""")

    return f"""
    <div style="height:100%;background:#ffffff;border-right:1px solid #e2e8f0;overflow-y:auto;">
      <div style="padding:12px 20px;background:#f8fafc;border-bottom:1px solid #e2e8f0;
                  display:flex;align-items:center;justify-content:space-between;">
        <span style="font-size:0.65rem;font-weight:700;letter-spacing:0.12em;
                     text-transform:uppercase;color:#2563eb;">Agent Activity</span>
        <span style="font-size:0.65rem;color:#94a3b8;">{len(lines)} steps</span>
      </div>
      {"".join(rows)}
    </div>"""


def _render_verdict(result: dict) -> str:
    report = result.get("final_report") or {}
    fields = result.get("extracted_fields") or {}
    hs = result.get("hs_result") or {}

    if not report:
        return _empty_verdict()

    status = report.get("status", "unknown")
    is_compliant = status == "compliant"
    is_pending = status == "pending_user_input"

    accent = "#22c55e" if is_compliant else ("#f59e0b" if is_pending else "#ef4444")
    icon = "✓" if is_compliant else ("!" if is_pending else "✗")
    label = "COMPLIANT" if is_compliant else ("PENDING INPUT" if is_pending else "NON-COMPLIANT")

    product = (fields.get("product") or "").title() or "—"
    origin = fields.get("origin_country") or "—"
    destination = fields.get("destination_country") or "—"
    hs_code = report.get("hs_code") or "—"
    tariff = report.get("tariff_rate")
    tariff_str = f"{tariff * 100:.0f}%" if tariff is not None else "—"
    agreement = report.get("trade_agreement") or "—"
    iterations = report.get("iterations_taken", 0)

    def kv(label: str, value: str, mono: bool = False) -> str:
        font = "'JetBrains Mono',monospace" if mono else "'Inter',sans-serif"
        return f"""
        <div style="display:flex;justify-content:space-between;align-items:baseline;
                    padding:10px 0;border-bottom:1px solid #f1f5f9;">
          <span style="font-size:0.72rem;font-weight:600;letter-spacing:0.06em;
                       text-transform:uppercase;color:#94a3b8;">{label}</span>
          <span style="font-size:0.85rem;color:#0f172a;font-family:{font};">{value}</span>
        </div>"""

    missing = report.get("missing_documents") or []
    missing_block = ""
    if missing:
        items = "".join(
            f'<div style="padding:6px 0;font-size:0.82rem;color:#dc2626;'
            f'border-bottom:1px solid #fee2e2;">'
            f'— {d.replace("_"," ").title()}</div>'
            for d in missing
        )
        missing_block = f"""
        <div style="margin-top:20px;padding:14px 16px;background:#fef2f2;
                    border:1px solid #fecaca;border-radius:8px;">
          <p style="font-size:0.65rem;font-weight:700;letter-spacing:0.12em;
                    text-transform:uppercase;color:#dc2626;margin:0 0 10px;">
            Missing Documents
          </p>
          {items}
        </div>"""

    return f"""
    <div style="height:100%;background:#ffffff;overflow-y:auto;font-family:'Inter',sans-serif;">

      <!-- Verdict banner -->
      <div style="padding:24px 28px 20px;background:#f8fafc;
                  border-bottom:1px solid #e2e8f0;">
        <div style="display:flex;align-items:center;gap:16px;">
          <div style="width:48px;height:48px;border-radius:50%;
                      background:{accent}18;border:2px solid {accent};
                      display:flex;align-items:center;justify-content:center;
                      font-size:1.3rem;font-weight:700;color:{accent};flex-shrink:0;">
            {icon}
          </div>
          <div>
            <p style="margin:0;font-size:1.2rem;font-weight:700;
                      color:{accent};letter-spacing:0.02em;">{label}</p>
            <p style="margin:4px 0 0;font-size:0.75rem;color:#94a3b8;">
              Resolved in {iterations} iteration(s)
            </p>
          </div>
        </div>
      </div>

      <!-- Key fields -->
      <div style="padding:20px 28px;">
        {kv("Product", product)}
        {kv("Route", f"{origin} → {destination}")}
        {kv("HS Code", hs_code, mono=True)}
        {kv("Tariff Rate", tariff_str)}
        {kv("Trade Agreement", agreement)}
        {missing_block}
      </div>

    </div>"""


# ---------------------------------------------------------------------------
# CSS — full-screen, no chrome
# ---------------------------------------------------------------------------

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body {
    margin: 0 !important;
    padding: 0 !important;
    background: #f8fafc !important;
    height: 100% !important;
}

.gradio-container {
    max-width: 100% !important;
    width: 100% !important;
    min-height: 100vh !important;
    margin: 0 !important;
    padding: 0 !important;
    background: #f8fafc !important;
    font-family: 'Inter', sans-serif !important;
}

footer, .footer { display: none !important; }
.contain { padding: 0 !important; }

/* Input panel */
textarea {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 6px !important;
    color: #0f172a !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.875rem !important;
    line-height: 1.65 !important;
    resize: none !important;
}
textarea:focus {
    border-color: #2563eb !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.12) !important;
    outline: none !important;
}
textarea::placeholder { color: #cbd5e1 !important; }

/* Run button */
button.primary, .gr-button-primary {
    background: #2563eb !important;
    color: #fff !important;
    font-weight: 600 !important;
    font-size: 0.8rem !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 12px 24px !important;
    width: 100% !important;
    transition: background 0.15s !important;
}
button.primary:hover { background: #1d4ed8 !important; }

/* Examples */
.gr-examples button {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    color: #64748b !important;
    font-size: 0.75rem !important;
    border-radius: 4px !important;
    padding: 6px 10px !important;
}
.gr-examples button:hover {
    border-color: #2563eb !important;
    color: #2563eb !important;
}

/* Labels */
label > span {
    font-size: 0.65rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    color: #94a3b8 !important;
}

/* Output panels */
.output-html {
    height: calc(100vh - 80px) !important;
    overflow: hidden !important;
    border-radius: 0 !important;
    border: none !important;
    padding: 0 !important;
    background: #ffffff !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 3px; }
::-webkit-scrollbar-track { background: #f1f5f9; }
::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 3px; }
"""

HEADER = """
<div style="padding:16px 28px;background:#ffffff;
            border-bottom:1px solid #e2e8f0;
            display:flex;align-items:center;justify-content:space-between;
            font-family:'Inter',sans-serif;">
  <div style="display:flex;align-items:center;gap:12px;">
    <span style="font-size:1.1rem;">🌍</span>
    <div>
      <span style="font-size:1rem;font-weight:700;color:#0f172a;
                   letter-spacing:-0.01em;">Afrigate</span>
      <span style="font-size:0.7rem;color:#94a3b8;margin-left:10px;
                   letter-spacing:0.08em;text-transform:uppercase;">
        Trade Compliance · Phase 1
      </span>
    </div>
  </div>
  <span style="font-size:0.65rem;color:#2563eb;font-weight:700;
               letter-spacing:0.12em;text-transform:uppercase;">
    Addis → Nairobi · RFC §2
  </span>
</div>
"""

EXAMPLES = [
    ["Export 500kg roasted coffee from Ethiopia to Kenya, value USD 8,000."],
    ["Ship 1000kg cocoa beans from Ghana to South Africa, value USD 15,000."],
    [
        "Exporter: Addis Trading PLC, Ethiopia\n"
        "Importer: Nairobi Imports Ltd, Kenya\n"
        "Product: Roasted Arabica Coffee — 500 kg — USD 8,000\n"
        "Certificate of Origin: CO-2024-ET-00712\n"
        "Phytosanitary Certificate: PHY-2024-00123\n"
        "Commercial Invoice: INV-2024-00712\n"
        "Packing List: PL-2024-00712"
    ],
]

# ---------------------------------------------------------------------------
# Layout — full-screen three-panel
# ---------------------------------------------------------------------------

with gr.Blocks(title="Afrigate", css=CSS) as demo:

    gr.HTML(HEADER)

    with gr.Row(equal_height=True):

        # Left — input
        with gr.Column(scale=3, min_width=280):
            gr.HTML(
                '<div style="padding:16px 20px 8px;font-size:0.65rem;font-weight:700;'
                'letter-spacing:0.12em;text-transform:uppercase;color:#334155;">'
                'Trade Request</div>'
            )
            trade_input = gr.Textbox(
                label="",
                placeholder=(
                    "Export 500kg roasted coffee\n"
                    "from Ethiopia to Kenya,\n"
                    "value USD 8,000."
                ),
                lines=12,
                max_lines=20,
                container=False,
            )
            gr.HTML('<div style="padding:0 20px 8px;">')
            run_btn = gr.Button("▶  Run Check", variant="primary")
            gr.HTML('</div>')
            gr.Examples(
                examples=EXAMPLES,
                inputs=trade_input,
                label="Examples",
                examples_per_page=3,
            )

        # Centre — agent log
        with gr.Column(scale=5, min_width=400):
            log_out = gr.HTML(
                value=_empty_log(),
                elem_classes=["output-html"],
            )

        # Right — verdict
        with gr.Column(scale=4, min_width=320):
            verdict_out = gr.HTML(
                value=_empty_verdict(),
                elem_classes=["output-html"],
            )

    run_btn.click(
        fn=run_pipeline,
        inputs=trade_input,
        outputs=[log_out, verdict_out],
    )
    trade_input.submit(
        fn=run_pipeline,
        inputs=trade_input,
        outputs=[log_out, verdict_out],
    )


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
    )
