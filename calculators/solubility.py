"""Solubility calculator wrapper for UI use."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from core.solubility import evaluate_salt_solubility


def analyze_salt_solubility_with_steps(
    salt_formula: str,
) -> Tuple[Dict[str, Any], List[str], Dict[str, Any]]:
    """Analyze salt solubility and provide user-facing explanation steps."""
    try:
        result = evaluate_salt_solubility(salt_formula)
    except ValueError as exc:
        msg = str(exc)
        salt_display = "".join(str(salt_formula).split()) if salt_formula is not None else ""
        result = {
            "salt": salt_display,
            "cation": {"symbol": "ukendt", "formula": "?", "charge": 0, "units": 0},
            "anion": {"symbol": "ukendt", "formula": "?", "charge": 0, "units": 0},
            "status": "unknown",
            "classification_da": "ukendt / kan ikke afgøres sikkert",
            "classification_en": "unknown / cannot determine",
            "rule_id": "R0_UNKNOWN",
            "rule": "Ingen implementeret regel matcher sikkert denne kombination.",
            "reason": msg,
            "error_message": msg,
        }

    steps: List[str] = [
        f"Input salt: {result['salt']}",
        f"Parsed cation: {result['cation']['symbol']}",
        f"Parsed anion: {result['anion']['symbol']}",
        f"Matched rule ({result['rule_id']}): {result['rule']}",
        f"Conclusion: {result['classification_da']} / {result['classification_en']}",
    ]
    metadata = {
        "matched_rule": result["rule_id"],
    }
    return result, steps, metadata
