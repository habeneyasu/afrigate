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


def test_regulations_ke_required_documents():
    data = json.loads((_RULES / "regulations.json").read_text(encoding="utf-8"))
    assert "KE" in data
    ke = data["KE"]
    assert ke["country"] == "Kenya"
    required = ke["required_documents"]
    assert "certificate_of_origin" in required
    assert "phytosanitary_certificate" in required
