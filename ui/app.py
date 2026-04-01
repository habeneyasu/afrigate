"""
Afrigate – ui/app.py
=====================
Phase 1 UI: wired to the agent swarm via run_graph().

To switch
    Change:
        from core.mock_graph import run_graph
    To:
        from core.graph import run_graph
   

"""

from __future__ import annotations

import sys
import json
import time
from pathlib import Path

#Path setup
_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "agents"))

#Graph import  (swap this one line when real graph is ready) 
from core.mock_graph import run_graph   #replace with: from core.graph import run_graph
from core.state import AgentStep, FinalResult

import gradio as gr



FIELD_GROUPS = {
    "🏢 Parties": [
        ("Exporter Name",        "exporter_name"),
        ("Exporter Country",     "exporter_country"),
        ("Exporter Address",     "exporter_address"),
        ("Exporter Tax ID",      "exporter_tax_id"),
        ("Exporter Email",       "exporter_email"),
        ("Importer Name",        "importer_name"),
        ("Importer Country",     "importer_country"),
        ("Importer Address",     "importer_address"),
        ("Consignee",            "consignee_name"),
        ("Notify Party",         "notify_party"),
        ("Manufacturer",         "manufacturer_name"),
        ("Freight Forwarder",    "freight_forwarder"),
        ("Customs Broker",       "customs_broker"),
    ],
    "📦 Product & Goods": [
        ("Product Name",         "product_name"),
        ("Description",          "product_description"),
        ("HS Code",              "hs_code"),
        ("Commodity Code",       "commodity_code"),
        ("ECCN",                 "eccn"),
        ("Brand",                "brand"),
        ("Batch / Lot",          "batch_lot_number"),
        ("Quantity",             "quantity"),
        ("Quantity Unit",        "quantity_unit"),
        ("Net Weight",           "net_weight"),
        ("Gross Weight",         "gross_weight"),
        ("Weight Unit",          "weight_unit"),
        ("Volume",               "volume"),
        ("No. of Packages",      "number_of_packages"),
        ("Package Type",         "package_type"),
        ("Country of Origin",    "country_of_origin"),
    ],
    "💰 Financial": [
        ("Invoice Value",        "invoice_value"),
        ("Currency",             "currency"),
        ("Unit Price",           "unit_price"),
        ("Total Value",          "total_value"),
        ("FOB Value",            "fob_value"),
        ("CIF Value",            "cif_value"),
        ("Freight",              "freight_value"),
        ("Insurance",            "insurance_value"),
        ("Duty Amount",          "duty_amount"),
        ("VAT",                  "vat_amount"),
        ("Incoterms",            "incoterms"),
        ("Payment Terms",        "payment_terms"),
        ("Letter of Credit",     "letter_of_credit_number"),
    ],
    "🚢 Shipment": [
        ("Trade Type",           "trade_type"),
        ("Mode of Transport",    "mode_of_transport"),
        ("Origin Country",       "origin_country"),
        ("Destination Country",  "destination_country"),
        ("Port of Loading",      "port_of_loading"),
        ("Port of Discharge",    "port_of_discharge"),
        ("Vessel Name",          "vessel_name"),
        ("Voyage No.",           "voyage_number"),
        ("Flight No.",           "flight_number"),
        ("Container No.",        "container_number"),
        ("Seal No.",             "seal_number"),
        ("Bill of Lading",       "bill_of_lading_number"),
        ("Airway Bill",          "airway_bill_number"),
        ("Booking No.",          "booking_number"),
        ("Shipment Date",        "shipment_date"),
        ("Arrival Date",         "arrival_date"),
    ],
    "📄 Documents": [
        ("Invoice Number",           "invoice_number"),
        ("Invoice Date",             "invoice_date"),
        ("Purchase Order",           "purchase_order_number"),
        ("Cert. of Origin",          "certificate_of_origin_number"),
        ("Phytosanitary Cert.",      "phytosanitary_certificate_number"),
        ("Health Certificate",       "health_certificate_number"),
        ("Fumigation Cert.",         "fumigation_certificate_number"),
        ("Inspection Cert.",         "inspection_certificate_number"),
        ("Conformity Cert.",         "conformity_certificate_number"),
        ("Packing List",             "packing_list_number"),
        ("Halal Cert.",              "halal_certificate_number"),
        ("Organic Cert.",            "organic_certificate_number"),
        ("ISO Cert.",                "iso_certificate_number"),
        ("CITES Permit",             "cites_permit_number"),
        ("GSP Form",                 "gsp_form_number"),
        ("Export License",           "export_license_number"),
        ("Import License",           "import_license_number"),
    ],
    "⚖️ Compliance": [
        ("Free Trade Agreement",     "free_trade_agreement"),
        ("Import Regime",            "import_regime"),
        ("Export Regime",            "export_regime"),
        ("Customs Procedure",        "customs_procedure_code"),
        ("Preference Code",          "preference_code"),
        ("Quota Number",             "quota_number"),
        ("End Use",                  "end_use"),
        ("Transaction Type",         "transaction_type"),
        ("Reason for Export",        "reason_for_export"),
        ("Expiry Date",              "expiry_date"),
    ],
}


#AGENT DISPLAY CONFIG

AGENT_META = {
    "doc_intel":     {"icon": "📄", "label": "Document Intelligence"},
    "hs_classifier": {"icon": "🔢", "label": "HS Code Classifier"},
    "compliance":    {"icon": "⚖️",  "label": "Compliance Checker"},
    "evaluator":     {"icon": "🧠", "label": "Evaluator"},
}

STATUS_STYLE = {
    "running":  ("ag-log-running",  "●"),
    "done":     ("ag-log-done",     "✓"),
    "failed":   ("ag-log-failed",   "✗"),
    "retrying": ("ag-log-retrying", "↺"),
    "waiting":  ("ag-log-waiting",  "⏸"),
}

DECISION_STYLE = {
    "accepted": ("ag-verdict-accepted", "✓ ACCEPTED",     "All compliance requirements met."),
    "rejected": ("ag-verdict-rejected", "✗ REJECTED",     "Maximum retries reached. Manual review required."),
    "ask_user": ("ag-verdict-askuser",  "⏸ INPUT NEEDED", "Evaluator needs clarification from you."),
}


#builders

def _step_html(step: AgentStep, elapsed: float) -> str:
    agent   = step["agent"]
    status  = step["status"]
    message = step["message"]
    itr     = step["iteration"]

    meta          = AGENT_META.get(agent, {"icon": "?", "label": agent})
    css_cls, icon = STATUS_STYLE.get(status, ("", "?"))
    iter_badge    = f'<span class="ag-iter-badge">iter {itr}</span>' if itr > 1 else ""

    return f"""
<div class="ag-log-row {css_cls}">
  <span class="ag-log-icon">{icon}</span>
  <span class="ag-log-agent">{meta['icon']} {meta['label']}</span>
  {iter_badge}
  <span class="ag-log-msg">{message}</span>
  <span class="ag-elapsed">{elapsed:.1f}s</span>
</div>"""


def _verdict_html(final: FinalResult) -> str:
    decision = final["decision"]
    css, label, subtitle = DECISION_STYLE.get(
        decision, ("ag-verdict-rejected", "? UNKNOWN", "")
    )

    hs_line = ""
    if final.get("hs_code"):
        hs_line = f"""
      <div class="ag-verdict-detail">
        <span class="ag-vd-label">HS Code</span>
        <span class="ag-vd-val">{final['hs_code']} — {final.get('hs_description','')}</span>
      </div>
      <div class="ag-verdict-detail">
        <span class="ag-vd-label">Tariff Rate</span>
        <span class="ag-vd-val">{final.get('tariff_rate','—')}</span>
      </div>"""

    missing_line = ""
    if final.get("missing_documents"):
        items = "".join(f'<li>{d}</li>' for d in final["missing_documents"])
        missing_line = f'<div class="ag-verdict-missing"><strong>Still missing:</strong><ul>{items}</ul></div>'

    feedback_line = ""
    if final.get("feedback_history"):
        fb_items = "".join(
            f'<li class="ag-fb-item">Retry {i+1}: {fb}</li>'
            for i, fb in enumerate(final["feedback_history"])
        )
        feedback_line = f'<ul class="ag-feedback-list">{fb_items}</ul>'

    return f"""
<div class="ag-verdict {css}">
  <div class="ag-verdict-header">
    <span class="ag-verdict-label">{label}</span>
    <span class="ag-verdict-sub">{subtitle}</span>
  </div>
  {hs_line}
  <div class="ag-verdict-detail">
    <span class="ag-vd-label">Iterations</span>
    <span class="ag-vd-val">{final['total_iterations']} / 3</span>
  </div>
  <div class="ag-verdict-detail">
    <span class="ag-vd-label">Total time</span>
    <span class="ag-vd-val">{final['total_time_seconds']}s</span>
  </div>
  {missing_line}
  {feedback_line}
</div>"""


def _fields_html(fields: dict) -> str:
    if not fields:
        return '<div class="ag-empty">No fields extracted.</div>'

    total = len(fields)
    parts = [f"""
<div class="ag-results-wrap">
  <div class="ag-stats-bar">
    <span class="ag-stat">
      <span class="ag-stat-num">{total}</span>
      <span class="ag-stat-label">fields extracted</span>
    </span>
  </div>"""]

    for section_title, field_list in FIELD_GROUPS.items():
        rows = [(label, fields[key]) for label, key in field_list if fields.get(key)]
        if not rows:
            continue
        rows_html = "".join(
            f'<tr><td class="ag-field-name">{lbl}</td>'
            f'<td class="ag-field-value">{val}</td></tr>'
            for lbl, val in rows
        )
        parts.append(f"""
  <div class="ag-section">
    <div class="ag-section-header">{section_title}
      <span class="ag-section-count">{len(rows)}</span>
    </div>
    <table class="ag-table">{rows_html}</table>
  </div>""")

    parts.append("</div>")
    return "".join(parts)


#main processing function

def process_and_stream(text_input: str, file_upload):
    """
    Gradio generator function — yields partial updates as each agent runs.
    Outputs: (log_html, verdict_html, fields_html, json_str)
    """
    has_text = bool(text_input and text_input.strip())
    has_file = file_upload is not None

    if not has_text and not has_file:
        empty = '<div class="ag-empty">Enter text or upload a document to begin.</div>'
        yield empty, "", "", ""
        return

    file_path  = str(file_upload) if has_file else None
    user_input = text_input.strip() if has_text else ""

    log_rows: list[str] = []
    start_time = time.time()

    def log_html() -> str:
        return f'<div class="ag-log-wrap">{"".join(log_rows)}</div>'

    graph_gen = run_graph(user_input, file_path)
    final: FinalResult | None = None

    try:
        while True:
            step: AgentStep = next(graph_gen)
            elapsed = time.time() - start_time
            log_rows.append(_step_html(step, elapsed))
            yield log_html(), "", "", ""

    except StopIteration as e:
        final = e.value
    except Exception as ex:
        err = f'<div class="ag-error">❌ Graph error: {ex}</div>'
        yield err, "", "", ""
        return

    if final is None:
        yield log_html(), '<div class="ag-error">Graph returned no result.</div>', "", ""
        return

    verdict  = _verdict_html(final)
    fields   = _fields_html(final.get("extracted_fields", {}))
    json_str = json.dumps(final, indent=2, ensure_ascii=False)

    yield log_html(), verdict, fields, json_str


def clear_all():
    return "", None, EMPTY_LOG, "", EMPTY_RES, ""


# examples

EXAMPLES = [
    ["Export 500kg roasted coffee from Ethiopia to Kenya, value USD 8,000."],
    ["""Invoice Number: INV-2024-00712
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
Incoterms: FOB
Port of Loading: Djibouti Port
Port of Discharge: Mombasa Port
Mode of Transport: Sea
Certificate of Origin: CO-2024-ET-00712
Phytosanitary Certificate: PHY-2024-00123
Free Trade Agreement: COMESA
Payment Terms: 30 days LC"""],
    ["""Shipper: Lagos Textile Exports Ltd, Nigeria
Consignee: Cairo Fashion House, Egypt
Vessel: MV Atlantic Star  Voyage: AT-2024-041
B/L No: APLU123456789
Container: MSCU1234567
Port of Loading: Apapa Port, Lagos
Port of Discharge: Alexandria Port
Commodity: Cotton Fabrics
Gross Weight: 12,500 KGS
Invoice Ref: LTE-INV-2024-0312
FOB Value: USD 45,000
CIF Total: USD 47,700
Health Certificate: HC-NG-2024-0456"""],
]


# css

CSS = """
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Sora:wght@300;400;500;600;700&family=Playfair+Display:wght@700&display=swap');

:root {
  --ag-bg:      #0b0f1a; --ag-surface: #111827; --ag-surface2: #1a2235;
  --ag-border:  #1f2d45; --ag-accent:  #f59e0b; --ag-green: #10b981;
  --ag-red:     #ef4444; --ag-yellow:  #f59e0b; --ag-blue: #3b82f6;
  --ag-text:    #e2e8f0; --ag-muted:   #64748b; --ag-dim: #94a3b8;
  --ag-radius:  10px;
  --ag-mono:    'DM Mono', monospace;
  --ag-body:    'Sora', sans-serif;
  --ag-title:   'Playfair Display', serif;
}
.gradio-container { background:var(--ag-bg) !important; font-family:var(--ag-body) !important; max-width:1280px !important; margin:0 auto !important; }
footer { display:none !important; }
.ag-header { padding:36px 0 24px; border-bottom:1px solid var(--ag-border); margin-bottom:28px; }
.ag-logo-row { display:flex; align-items:center; gap:14px; margin-bottom:6px; }
.ag-logo-badge { width:44px; height:44px; background:var(--ag-accent); border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:22px; flex-shrink:0; }
.ag-title { font-family:var(--ag-title) !important; font-size:2rem !important; font-weight:700 !important; color:var(--ag-text) !important; letter-spacing:-0.02em; margin:0 !important; }
.ag-title span { color:var(--ag-accent); }
.ag-subtitle { color:var(--ag-muted); font-size:0.8rem; letter-spacing:0.1em; text-transform:uppercase; font-weight:600; padding-left:58px; }
.ag-tagline { color:var(--ag-dim); font-size:0.88rem; margin-top:12px; max-width:580px; line-height:1.65; }
.ag-tagline strong { color:var(--ag-accent); }
.ag-panel-label { font-size:0.68rem; font-weight:700; letter-spacing:0.14em; text-transform:uppercase; color:var(--ag-muted); margin-bottom:10px; display:flex; align-items:center; gap:8px; }
.ag-panel-label::after { content:''; flex:1; height:1px; background:var(--ag-border); }
.gr-box, .gr-form, .gr-panel, .gr-padded, textarea, .gr-file-drop { background:var(--ag-surface) !important; border:1px solid var(--ag-border) !important; border-radius:var(--ag-radius) !important; color:var(--ag-text) !important; font-family:var(--ag-body) !important; }
textarea { font-family:var(--ag-mono) !important; font-size:0.81rem !important; line-height:1.7 !important; resize:vertical !important; }
textarea::placeholder { color:var(--ag-muted) !important; }
textarea:focus { border-color:var(--ag-accent) !important; box-shadow:0 0 0 3px rgba(245,158,11,0.1) !important; outline:none !important; }
.gr-file-drop { border-style:dashed !important; }
button.primary, .gr-button-primary { background:var(--ag-accent) !important; color:#000 !important; font-weight:600 !important; font-family:var(--ag-body) !important; font-size:0.85rem !important; border:none !important; border-radius:8px !important; }
button.primary:hover { opacity:0.85 !important; }
button.secondary, .gr-button-secondary { background:var(--ag-surface2) !important; color:var(--ag-dim) !important; font-family:var(--ag-body) !important; border:1px solid var(--ag-border) !important; border-radius:8px !important; font-size:0.85rem !important; }
.tab-nav button { font-family:var(--ag-body) !important; font-size:0.78rem !important; font-weight:500 !important; color:var(--ag-muted) !important; border-bottom:2px solid transparent !important; background:transparent !important; }
.tab-nav button.selected { color:var(--ag-accent) !important; border-bottom-color:var(--ag-accent) !important; }
label > span { font-size:0.7rem !important; font-weight:600 !important; letter-spacing:0.1em !important; text-transform:uppercase !important; color:var(--ag-muted) !important; }

/* Agent Log */
.ag-log-wrap { font-family:var(--ag-mono); font-size:0.8rem; background:#070d18; border:1px solid var(--ag-border); border-radius:var(--ag-radius); padding:14px; min-height:120px; max-height:340px; overflow-y:auto; }
.ag-log-row { display:flex; align-items:baseline; gap:10px; padding:5px 0; border-bottom:1px solid rgba(31,45,69,0.5); animation:ag-fadein 0.25s ease; }
.ag-log-row:last-child { border-bottom:none; }
.ag-log-icon { font-size:0.75rem; flex-shrink:0; width:14px; text-align:center; }
.ag-log-agent { color:var(--ag-dim); font-weight:500; flex-shrink:0; min-width:185px; }
.ag-log-msg { color:var(--ag-text); flex:1; }
.ag-elapsed { color:var(--ag-muted); font-size:0.7rem; flex-shrink:0; }
.ag-iter-badge { background:var(--ag-surface2); color:var(--ag-accent); font-size:0.65rem; padding:1px 6px; border-radius:20px; border:1px solid var(--ag-border); flex-shrink:0; }
.ag-log-running .ag-log-icon, .ag-log-running .ag-log-agent { color:var(--ag-blue); }
.ag-log-done .ag-log-icon, .ag-log-done .ag-log-agent { color:var(--ag-green); }
.ag-log-failed .ag-log-icon, .ag-log-failed .ag-log-agent { color:var(--ag-red); }
.ag-log-retrying .ag-log-icon, .ag-log-retrying .ag-log-agent { color:var(--ag-yellow); }

/* Verdict */
.ag-verdict { border-radius:var(--ag-radius); padding:18px 20px; margin-bottom:20px; border:1px solid; animation:ag-fadein 0.4s ease; }
.ag-verdict-accepted { background:rgba(16,185,129,0.08); border-color:rgba(16,185,129,0.35); }
.ag-verdict-rejected { background:rgba(239,68,68,0.08); border-color:rgba(239,68,68,0.35); }
.ag-verdict-askuser  { background:rgba(245,158,11,0.08); border-color:rgba(245,158,11,0.35); }
.ag-verdict-header { display:flex; align-items:baseline; gap:14px; margin-bottom:14px; }
.ag-verdict-label { font-family:var(--ag-title); font-size:1.25rem; font-weight:700; }
.ag-verdict-accepted .ag-verdict-label { color:var(--ag-green); }
.ag-verdict-rejected .ag-verdict-label { color:var(--ag-red); }
.ag-verdict-askuser  .ag-verdict-label { color:var(--ag-yellow); }
.ag-verdict-sub { font-size:0.8rem; color:var(--ag-muted); }
.ag-verdict-detail { display:flex; gap:12px; align-items:baseline; padding:6px 0; border-bottom:1px solid rgba(255,255,255,0.04); font-size:0.82rem; }
.ag-verdict-detail:last-of-type { border-bottom:none; }
.ag-vd-label { color:var(--ag-muted); font-weight:500; min-width:120px; flex-shrink:0; }
.ag-vd-val { color:var(--ag-text); font-family:var(--ag-mono); }
.ag-verdict-missing { margin-top:12px; font-size:0.8rem; color:var(--ag-red); }
.ag-verdict-missing ul { margin:4px 0 0 16px; }
.ag-feedback-list { margin:10px 0 0; padding:0; list-style:none; }
.ag-fb-item { font-size:0.75rem; color:var(--ag-muted); font-family:var(--ag-mono); padding:3px 0; border-bottom:1px solid var(--ag-border); }

/* Fields */
.ag-results-wrap { font-family:var(--ag-body); animation:ag-fadein 0.35s ease; }
.ag-stats-bar { display:flex; gap:20px; margin-bottom:18px; padding-bottom:14px; border-bottom:1px solid var(--ag-border); }
.ag-stat { display:flex; align-items:center; gap:8px; }
.ag-stat-num { font-family:var(--ag-title); font-size:1.8rem; color:var(--ag-accent); line-height:1; }
.ag-stat-label { font-size:0.73rem; color:var(--ag-muted); text-transform:uppercase; letter-spacing:0.06em; font-weight:500; }
.ag-section { margin-bottom:16px; background:var(--ag-surface); border:1px solid var(--ag-border); border-radius:var(--ag-radius); overflow:hidden; }
.ag-section-header { display:flex; align-items:center; justify-content:space-between; padding:10px 16px; background:var(--ag-surface2); font-size:0.76rem; font-weight:600; color:var(--ag-dim); letter-spacing:0.05em; border-bottom:1px solid var(--ag-border); }
.ag-section-count { background:var(--ag-accent); color:#000; font-size:0.64rem; font-weight:700; padding:2px 7px; border-radius:20px; }
.ag-table { width:100%; border-collapse:collapse; }
.ag-table tr { border-bottom:1px solid var(--ag-border); }
.ag-table tr:last-child { border-bottom:none; }
.ag-table tr:hover { background:rgba(255,255,255,0.02); }
.ag-field-name { padding:8px 16px; font-size:0.74rem; color:var(--ag-muted); font-weight:500; width:38%; white-space:nowrap; }
.ag-field-value { padding:8px 16px; font-size:0.8rem; color:var(--ag-text); font-family:var(--ag-mono); word-break:break-word; }
.ag-json-wrap textarea { font-family:var(--ag-mono) !important; font-size:0.76rem !important; color:#7dd3fc !important; background:#060c18 !important; }
.ag-empty { color:var(--ag-muted); font-size:0.85rem; padding:12px 0; }
.ag-error { background:rgba(239,68,68,0.09); border:1px solid rgba(239,68,68,0.3); color:#fca5a5; padding:12px 16px; border-radius:8px; font-size:0.84rem; }
.ag-divider { height:1px; background:var(--ag-border); margin:8px 0 20px; }
@keyframes ag-fadein { from { opacity:0; transform:translateY(5px); } to { opacity:1; transform:translateY(0); } }
::-webkit-scrollbar { width:5px; } ::-webkit-scrollbar-track { background:var(--ag-surface); } ::-webkit-scrollbar-thumb { background:var(--ag-border); border-radius:3px; }
"""

HEADER_HTML = """
<div class="ag-header">
  <div class="ag-logo-row">
    <div class="ag-logo-badge">🌍</div>
    <h1 class="ag-title">Afri<span>gate</span></h1>
  </div>
  <div class="ag-subtitle">Autonomous Trade Compliance · Phase 1 Demo</div>
  <p class="ag-tagline">
    A <strong>self-correcting agent swarm</strong> that extracts trade fields,
    classifies HS codes, checks compliance rules, and retries automatically
    when documents are missing — until all requirements are met.
  </p>
</div>
"""

EMPTY_LOG = '<div class="ag-empty">Agent logs will appear here during processing.</div>'
EMPTY_RES = '<div class="ag-empty">Results will appear here after processing.</div>'

#build ui

with gr.Blocks(title="Afrigate – Trade Compliance") as demo:

    gr.HTML(HEADER_HTML)

    with gr.Row(equal_height=False):

        #LEFT: Input
        with gr.Column(scale=4):
            gr.HTML('<div class="ag-panel-label">📥 Trade Request</div>')

            text_input = gr.Textbox(
                label="Document Text or Trade Request",
                placeholder=(
                    "Type a trade request or paste document text.\n\n"
                    "Example: Export 500kg roasted coffee from Ethiopia to Kenya, value USD 8,000."
                ),
                lines=10,
                max_lines=28,
            )

            file_upload = gr.File(
                label="Upload Document  (PDF · DOCX · TXT)",
                file_types=[".pdf", ".docx", ".doc", ".txt"],
                file_count="single",
            )

            with gr.Row():
                run_btn   = gr.Button("▶  Run Compliance Check", variant="primary",   size="lg")
                clear_btn = gr.Button("✕  Clear",                variant="secondary", size="lg")

            gr.HTML('<div class="ag-divider"></div>')
            gr.HTML('<div class="ag-panel-label">💡 Examples</div>')
            gr.Examples(examples=EXAMPLES, inputs=[text_input], label=None, examples_per_page=3)

        #RIGHT: Output 
        with gr.Column(scale=8):

            gr.HTML('<div class="ag-panel-label">🤖 Agent Activity Log</div>')
            log_out = gr.HTML(value=EMPTY_LOG)

            gr.HTML('<div class="ag-divider"></div>')
            gr.HTML('<div class="ag-panel-label">📊 Compliance Result</div>')
            verdict_out = gr.HTML(value=EMPTY_RES)

            with gr.Tabs():
                with gr.Tab("Extracted Fields"):
                    fields_out = gr.HTML(value="")
                with gr.Tab("Full JSON"):
                    json_out = gr.Textbox(
                        label="", lines=24, max_lines=50,
                        buttons=["copy"],
                        elem_classes=["ag-json-wrap"],
                        interactive=False,
                    )

    #Events
    run_btn.click(
        fn=process_and_stream,
        inputs=[text_input, file_upload],
        outputs=[log_out, verdict_out, fields_out, json_out],
    )
    text_input.submit(
        fn=process_and_stream,
        inputs=[text_input, file_upload],
        outputs=[log_out, verdict_out, fields_out, json_out],
    )
    file_upload.change(
        fn=process_and_stream,
        inputs=[text_input, file_upload],
        outputs=[log_out, verdict_out, fields_out, json_out],
    )
    clear_btn.click(
        fn=clear_all,
        inputs=[],
        outputs=[text_input, file_upload, log_out, verdict_out, fields_out, json_out],
    )


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        css=CSS,
    )