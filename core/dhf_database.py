"""
Local ΔHf° JSON database utilities.
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, Optional

DHF_USER_PATH = Path(__file__).parent.parent / "data" / "dhf.json"
DHF_EXAM_PATH = Path(__file__).parent.parent / "data" / "dhf.exampack.json"
DHF_OPENSTAX_PATH = Path(__file__).parent.parent / "data" / "dhf.openstax.tableG1.json"
DHF_EXTENDED_PATH = Path(__file__).parent.parent / "data" / "dhf.extended.json"

_PHASE_RE = re.compile(r"\((s|l|g|aq)\)$", re.IGNORECASE)
_SUBSCRIPT_TRANS = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")
_SUPERSCRIPT_TRANS = str.maketrans({
    "⁰": "0",
    "¹": "1",
    "²": "2",
    "³": "3",
    "⁴": "4",
    "⁵": "5",
    "⁶": "6",
    "⁷": "7",
    "⁸": "8",
    "⁹": "9",
    "⁺": "+",
    "⁻": "-",
})


def _split_phase(species_key: str) -> tuple[str, Optional[str]]:
    match = _PHASE_RE.search(species_key)
    if not match:
        return species_key, None
    return species_key[:match.start()], match.group(1).lower()


def normalizeSpeciesKey(raw: str) -> str:
    """
    Normalize species key to canonical format:
    - Remove extra whitespace
    - Canonicalize phase to lowercase
    - Canonicalize spaced charge notation, e.g. "SO4 2-(aq)" -> "SO4^2-(aq)"
    """
    if raw is None:
        raise ValueError("Species key cannot be None")

    text = unicodedata.normalize("NFKC", str(raw)).strip()
    if not text:
        raise ValueError("Species key cannot be empty")

    text = text.translate(_SUBSCRIPT_TRANS).translate(_SUPERSCRIPT_TRANS)
    text = text.replace("−", "-").replace("–", "-").replace("—", "-")

    # Convert spaced charge notation near the end to caret form.
    # Example: "SO4 2-(aq)" -> "SO4^2-(aq)"
    text = re.sub(r"\s+(\d+)\s*([+-])(?=\s*(?:\([A-Za-z]+\))?\s*$)", r"^\1\2", text)

    # Remove all remaining whitespace
    text = re.sub(r"\s+", "", text)

    base, phase = _split_phase(text)
    if phase is not None:
        return f"{base}({phase})"
    return base


def _load_json_file(path: Path) -> Dict[str, Dict[str, Any]]:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Invalid JSON format in {path.name}: expected object at top-level")

    normalized: Dict[str, Dict[str, Any]] = {}
    for key, value in data.items():
        norm_key = normalizeSpeciesKey(key)
        if isinstance(value, dict):
            normalized[norm_key] = value
    return normalized


def load_dhf_database() -> Dict[str, Dict[str, Any]]:
    """
    Load merged database:
    1) OpenStax base table (generated)
    2) extension layer (NIST + ion PDF)
    3) exam pack overrides
    4) user db overrides/additions (dhf.json)
    """
    openstax_db = _load_json_file(DHF_OPENSTAX_PATH)
    extended_db = _load_json_file(DHF_EXTENDED_PATH)
    exam_db = _load_json_file(DHF_EXAM_PATH)
    user_db = _load_json_file(DHF_USER_PATH)

    merged = dict(openstax_db)
    merged.update(extended_db)
    merged.update(exam_db)
    merged.update(user_db)
    return merged


def getDhf(
    speciesKey: str,
    overrides: Optional[Dict[str, float]] = None,
    db: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Lookup ΔHf° by canonicalized key.

    Rules:
    - Canonical key lookup first.
    - If not found and phase is missing, attempt unique phase match in overrides/db.
    """
    overrides = overrides or {}
    db = db or {}

    canonical_input = normalizeSpeciesKey(speciesKey)
    input_base, input_phase = _split_phase(canonical_input)

    normalized_overrides = {normalizeSpeciesKey(k): float(v) for k, v in overrides.items()}

    if canonical_input in normalized_overrides:
        return {
            "found": True,
            "value": normalized_overrides[canonical_input],
            "source": "override",
            "key": canonical_input,
        }

    if canonical_input in db:
        row = db[canonical_input]
        return {
            "found": True,
            "value": float(row["dhf_kj_per_mol"]),
            "source": row.get("source", "database"),
            "key": canonical_input,
        }

    if input_phase is None:
        override_candidates = [
            key for key in normalized_overrides.keys()
            if _split_phase(key)[0] == input_base
        ]
        if len(override_candidates) == 1:
            key = override_candidates[0]
            return {
                "found": True,
                "value": normalized_overrides[key],
                "source": "override",
                "key": key,
            }

        db_candidates = [
            key for key in db.keys()
            if _split_phase(key)[0] == input_base
        ]
        if len(db_candidates) == 1:
            key = db_candidates[0]
            row = db[key]
            return {
                "found": True,
                "value": float(row["dhf_kj_per_mol"]),
                "source": row.get("source", "database"),
                "key": key,
            }

    return {
        "found": False,
        "value": None,
        "source": None,
        "key": canonical_input,
    }


def save_dhf_database(database: Dict[str, Dict[str, Any]]) -> None:
    ordered_keys = sorted(database.keys())
    ordered = {k: database[k] for k in ordered_keys}
    with open(DHF_USER_PATH, "w", encoding="utf-8") as handle:
        json.dump(ordered, handle, indent=2, ensure_ascii=False)


def add_to_dhf_database(entries: Dict[str, float], source: str) -> Dict[str, Dict[str, Any]]:
    database = _load_json_file(DHF_USER_PATH)
    for species_key, value in entries.items():
        normalized_key = normalizeSpeciesKey(species_key)
        if _split_phase(normalized_key)[1] is None:
            raise ValueError(f"Species key must include phase (s/l/g/aq): {species_key}")
        database[normalized_key] = {
            "dhf_kj_per_mol": float(value),
            "source": source,
        }
    save_dhf_database(database)
    return load_dhf_database()
