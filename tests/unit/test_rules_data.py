"""Sanity checks for bundled JSON rule files."""

import json
from pathlib import Path

_RULES = Path(__file__).resolve().parent.parent.parent / "rules"


def test_hs_codes_json_loads():
    data = json.loads((_RULES / "hs_codes.json").read_text(encoding="utf-8"))
    assert "entries" in data
    assert len(data["entries"]) >= 1
    coffee = next(e for e in data["entries"] if e.get("hs_code") == "0901.21")
    assert coffee["trade_agreement"] == "COMESA"


def test_regulations_et_ke_corridor():
    data = json.loads((_RULES / "regulations.json").read_text(encoding="utf-8"))
    corridors = data.get("corridors", [])
    et_ke = next(c for c in corridors if c.get("id") == "ET_to_KE")
    assert et_ke["origin_iso"] == "ET"
    assert et_ke["destination_iso"] == "KE"
    ids = {d["id"] for d in et_ke["required_documents"]}
    assert "certificate_of_origin" in ids
    assert "phytosanitary_certificate" in ids
