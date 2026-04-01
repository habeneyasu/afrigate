"""
HS code classification — deterministic lookup against rules/hs_codes.json.

LangGraph: use as a graph node — ``hs_classifier_node(state) -> dict`` returns a
partial state update (``hs_result``, ``agent_log``) merged by the checkpointer.
"""

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

from utils.logger import get_logger

_RULES_PATH = Path(__file__).resolve().parent.parent / "rules" / "hs_codes.json"
_log = get_logger("agents.hs_classifier")


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


@lru_cache(maxsize=1)
def _load_entries() -> list[dict[str, Any]]:
    raw = _RULES_PATH.read_text(encoding="utf-8")
    data = json.loads(raw)
    entries = data.get("entries", [])
    return [e for e in entries if isinstance(e, dict)]


def _match_product(product: str) -> dict[str, Any] | None:
    normalized = _normalize(product)
    if not normalized:
        return None
    for entry in _load_entries():
        keywords = entry.get("keywords") or []
        for kw in keywords:
            if not isinstance(kw, str):
                continue
            kw_norm = _normalize(kw)
            if len(kw_norm) >= 2 and kw_norm in normalized:
                return {
                    "found": True,
                    "hs_code": str(entry["hs_code"]),
                    "description": str(entry.get("description", "")),
                    "tariff_rate": float(entry["tariff_rate"]),
                    "trade_agreement": str(entry.get("trade_agreement", "")),
                }
    return None


def run_hs_classifier(state: Mapping[str, Any]) -> dict[str, Any]:
    """
    Classify the shipment product into an HS code using local JSON rules.

    Expects ``state["extracted_fields"]["product"]``. Returns a partial state
    update suitable for ``StateGraph`` node return values.
    """
    fields = state.get("extracted_fields") or {}
    product = fields.get("product", "")
    product_str = product if isinstance(product, str) else str(product)

    match = _match_product(product_str)
    if match is None:
        hs_result: dict[str, Any] = {
            "found": False,
            "hs_code": None,
            "tariff_rate": None,
            "trade_agreement": None,
            "description": None,
        }
        log_line = f"hs_classifier: no HS match for product={product_str!r}"
    else:
        hs_result = match
        log_line = (
            f"hs_classifier: {hs_result['hs_code']} "
            f"({hs_result['trade_agreement']}, tariff {hs_result['tariff_rate']}%)"
        )

    _log.info(
        "hs_classification",
        extra={
            "agent": "hs_classifier",
            "event": "hs_classification",
            "product": product_str[:500],
            "found": bool(match),
            "hs_code": hs_result.get("hs_code"),
            "trade_agreement": hs_result.get("trade_agreement"),
            "tariff_rate": hs_result.get("tariff_rate"),
        },
    )

    return {
        "hs_result": hs_result,
        "agent_log": [log_line],
    }


def hs_classifier_node(state: Mapping[str, Any]) -> dict[str, Any]:
    """LangGraph node alias — same contract as ``run_hs_classifier``."""
    return run_hs_classifier(state)
