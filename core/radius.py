"""
Radius lookup utilities.

Note:
- Radius is data-driven and cannot be derived numerically from electron configuration alone.
- Neutral atoms use a configurable definition.
- Ions use ionic radius table lookup.
"""

from __future__ import annotations

from enum import Enum
import json
from pathlib import Path
from typing import Dict, Optional

import periodictable


class NeutralRadiusDefinition(str, Enum):
    EMPIRICAL_ATOMIC = "empirical_atomic_radius"
    COVALENT = "covalent_radius"


DEFAULT_NEUTRAL_RADIUS_DEFINITION = NeutralRadiusDefinition.COVALENT

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ATOMIC_RADII_PATH = DATA_DIR / "radii.atomic.json"
IONIC_RADII_PATH = DATA_DIR / "radii.ionic.json"


_ATOMIC_CACHE: Optional[Dict] = None
_IONIC_CACHE: Optional[Dict] = None


def resolve_radius(
    Z: int,
    charge: int,
    unit: str = "pm",
    neutral_definition: NeutralRadiusDefinition = DEFAULT_NEUTRAL_RADIUS_DEFINITION,
) -> Dict[str, object]:
    """
    Resolve atomic/ionic radius from local datasets.

    Returns:
      {
        value: float | None,
        unit: "pm" | "Å",
        kind: "atomic" | "ionic",
        note?: str,
        source?: str,
      }
    """
    if Z < 1 or Z > 118:
        raise ValueError("Z skal være i intervallet 1..118.")
    if unit not in {"pm", "Å"}:
        raise ValueError("Enhed skal være 'pm' eller 'Å'.")

    symbol = periodictable.elements[Z].symbol

    if charge == 0:
        return _resolve_neutral_radius(
            Z=Z,
            unit=unit,
            neutral_definition=neutral_definition,
        )

    return _resolve_ionic_radius(symbol=symbol, charge=charge, unit=unit)


def resolveRadius(
    Z: int,
    charge: int,
    unit: str = "pm",
    neutral_definition: NeutralRadiusDefinition = DEFAULT_NEUTRAL_RADIUS_DEFINITION,
) -> Dict[str, object]:
    """CamelCase alias for resolve_radius."""
    return resolve_radius(
        Z=Z,
        charge=charge,
        unit=unit,
        neutral_definition=neutral_definition,
    )


def _resolve_neutral_radius(
    Z: int,
    unit: str,
    neutral_definition: NeutralRadiusDefinition,
) -> Dict[str, object]:
    data = _load_atomic_data()
    symbol = periodictable.elements[Z].symbol
    radius_pm = _lookup_neutral_radius_pm(data=data, Z=Z, symbol=symbol)
    source = data.get("meta", {}).get("source", "lokal radius-tabel")
    radius_type = data.get("meta", {}).get("radius_type", "neutral_radius")

    note_parts = []
    if neutral_definition.value not in radius_type:
        note_parts.append(
            f"anmodet definition '{neutral_definition.value}', men data bruger '{radius_type}'"
        )

    if radius_pm is None:
        note_parts.append(f"ingen neutral radius-data for Z={Z} ({symbol})")
        return {
            "value": None,
            "unit": unit,
            "kind": "atomic",
            "note": "; ".join(note_parts),
            "source": source,
            "radius_type": radius_type,
        }

    value = _convert_pm(float(radius_pm), unit)
    payload = {
        "value": value,
        "unit": unit,
        "kind": "atomic",
        "source": source,
        "radius_type": radius_type,
    }
    if note_parts:
        payload["note"] = "; ".join(note_parts)
    return payload


def _lookup_neutral_radius_pm(data: Dict, Z: int, symbol: str) -> Optional[float]:
    z_keys = [str(Z), Z]

    for container_key in ("data", "radii_by_z"):
        container = data.get(container_key)
        if isinstance(container, dict):
            for key in z_keys:
                value = container.get(key)
                if value is not None:
                    return float(value)

    symbol_container = data.get("by_symbol")
    if isinstance(symbol_container, dict):
        value = symbol_container.get(symbol)
        if value is not None:
            return float(value)

    return None


def _resolve_ionic_radius(symbol: str, charge: int, unit: str) -> Dict[str, object]:
    data = _load_ionic_data()
    source = data.get("meta", {}).get("source", "lokal ionradius-tabel")

    ion_key = f"{symbol}{charge:+d}"
    radius_pm = data.get("radii_by_ion", {}).get(ion_key)
    if radius_pm is None:
        return {
            "value": None,
            "unit": unit,
            "kind": "ionic",
            "note": f"ingen ionradius-data for {ion_key}",
            "source": source,
        }

    value = _convert_pm(float(radius_pm), unit)
    return {
        "value": value,
        "unit": unit,
        "kind": "ionic",
        "source": source,
    }


def _convert_pm(value_pm: float, unit: str) -> float:
    if unit == "pm":
        return value_pm
    return value_pm / 100.0


def _load_atomic_data() -> Dict:
    global _ATOMIC_CACHE
    if _ATOMIC_CACHE is None:
        _ATOMIC_CACHE = json.loads(ATOMIC_RADII_PATH.read_text(encoding="utf-8"))
    return _ATOMIC_CACHE


def _load_ionic_data() -> Dict:
    global _IONIC_CACHE
    if _IONIC_CACHE is None:
        _IONIC_CACHE = json.loads(IONIC_RADII_PATH.read_text(encoding="utf-8"))
    return _IONIC_CACHE
