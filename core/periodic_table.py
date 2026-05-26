"""Periodic table dataset and helpers for Streamlit UI."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

import periodictable

from core.electron_configuration import electron_configuration


DATA_DIR = Path(__file__).parent.parent / "data"
PERIODIC_OVERRIDES_PATH = DATA_DIR / "periodic_table_overrides.json"

DIATOMIC_SYMBOLS = {"H", "N", "O", "F", "Cl", "Br", "I"}
GAS_SYMBOLS = {"H", "He", "N", "O", "F", "Ne", "Cl", "Ar", "Kr", "Xe", "Rn"}
LIQUID_SYMBOLS = {"Br", "Hg"}
METALLOID_SYMBOLS = {"B", "Si", "Ge", "As", "Sb", "Te", "Po"}
NONMETAL_SYMBOLS = {"H", "C", "N", "O", "P", "S", "Se"}
POST_TRANSITION_SYMBOLS = {"Al", "Ga", "In", "Tl", "Sn", "Pb", "Bi", "Nh", "Fl", "Mc", "Lv"}

MAIN_TABLE_LAYOUT: Dict[int, Dict[int, str]] = {
    1: {1: "H", 18: "He"},
    2: {1: "Li", 2: "Be", 13: "B", 14: "C", 15: "N", 16: "O", 17: "F", 18: "Ne"},
    3: {1: "Na", 2: "Mg", 13: "Al", 14: "Si", 15: "P", 16: "S", 17: "Cl", 18: "Ar"},
    4: {
        1: "K", 2: "Ca", 3: "Sc", 4: "Ti", 5: "V", 6: "Cr", 7: "Mn", 8: "Fe", 9: "Co", 10: "Ni",
        11: "Cu", 12: "Zn", 13: "Ga", 14: "Ge", 15: "As", 16: "Se", 17: "Br", 18: "Kr",
    },
    5: {
        1: "Rb", 2: "Sr", 3: "Y", 4: "Zr", 5: "Nb", 6: "Mo", 7: "Tc", 8: "Ru", 9: "Rh", 10: "Pd",
        11: "Ag", 12: "Cd", 13: "In", 14: "Sn", 15: "Sb", 16: "Te", 17: "I", 18: "Xe",
    },
    6: {
        1: "Cs", 2: "Ba", 3: "La", 4: "Hf", 5: "Ta", 6: "W", 7: "Re", 8: "Os", 9: "Ir", 10: "Pt",
        11: "Au", 12: "Hg", 13: "Tl", 14: "Pb", 15: "Bi", 16: "Po", 17: "At", 18: "Rn",
    },
    7: {
        1: "Fr", 2: "Ra", 3: "Ac", 4: "Rf", 5: "Db", 6: "Sg", 7: "Bh", 8: "Hs", 9: "Mt", 10: "Ds",
        11: "Rg", 12: "Cn", 13: "Nh", 14: "Fl", 15: "Mc", 16: "Lv", 17: "Ts", 18: "Og",
    },
}

LANTHANIDE_SERIES = ["La", "Ce", "Pr", "Nd", "Pm", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu"]
ACTINIDE_SERIES = ["Ac", "Th", "Pa", "U", "Np", "Pu", "Am", "Cm", "Bk", "Cf", "Es", "Fm", "Md", "No", "Lr"]


def _safe_float(value: Any) -> Optional[float]:
    try:
        if value is None:
            return None
        out = float(value)
        if out != out:
            return None
        return out
    except (TypeError, ValueError):
        return None


def _default_category(symbol: str, atomic_number: int, group: Optional[int]) -> str:
    if 57 <= atomic_number <= 71:
        return "lanthanide"
    if 89 <= atomic_number <= 103:
        return "actinide"
    if group == 1 and symbol != "H":
        return "alkali metal"
    if group == 2:
        return "alkaline earth metal"
    if group == 17:
        return "halogen"
    if group == 18:
        return "noble gas"
    if group is not None and 3 <= group <= 12:
        return "transition metal"
    if symbol in METALLOID_SYMBOLS:
        return "metalloid"
    if symbol in NONMETAL_SYMBOLS:
        return "nonmetal"
    if symbol in POST_TRANSITION_SYMBOLS:
        return "post-transition metal"
    if atomic_number <= 112:
        return "metal"
    return "unknown"


def _default_block(symbol: str, atomic_number: int, group: Optional[int]) -> str:
    if 57 <= atomic_number <= 71 or 89 <= atomic_number <= 103:
        return "f"
    if symbol == "He":
        return "s"
    if group in {1, 2}:
        return "s"
    if group is not None and 13 <= group <= 18:
        return "p"
    return "d"


def _default_phase(symbol: str) -> str:
    if symbol in GAS_SYMBOLS:
        return "gas"
    if symbol in LIQUID_SYMBOLS:
        return "liquid"
    return "solid"


def _default_oxidation_states(symbol: str, group: Optional[int], category: str) -> List[int]:
    specific: Dict[str, List[int]] = {
        "H": [-1, 1],
        "O": [-2],
        "F": [-1],
        "Cl": [-1, 1, 3, 5, 7],
        "Br": [-1, 1, 3, 5],
        "I": [-1, 1, 3, 5, 7],
        "N": [-3, 3, 5],
        "P": [-3, 3, 5],
        "S": [-2, 4, 6],
        "C": [-4, 2, 4],
        "Fe": [2, 3],
        "Cu": [1, 2],
        "Mn": [2, 4, 7],
        "Cr": [2, 3, 6],
        "Zn": [2],
        "Ag": [1],
        "Al": [3],
        "Si": [-4, 4],
        "Sn": [2, 4],
        "Pb": [2, 4],
        "Hg": [1, 2],
    }
    if symbol in specific:
        return specific[symbol]

    if category == "alkali metal":
        return [1]
    if category == "alkaline earth metal":
        return [2]
    if category == "halogen":
        return [-1, 1, 3, 5, 7]
    if category == "noble gas":
        return [0]
    if category in {"lanthanide", "actinide"}:
        return [3]
    if category == "transition metal":
        return [2, 3]

    if group == 13:
        return [3]
    if group == 14:
        return [-4, 4]
    if group == 15:
        return [-3, 3, 5]
    if group == 16:
        return [-2, 4, 6]
    return []


def _build_layout_index() -> Dict[str, Dict[str, int]]:
    layout: Dict[str, Dict[str, int]] = {}
    for period, row in MAIN_TABLE_LAYOUT.items():
        for group, symbol in row.items():
            layout[symbol] = {
                "period": period,
                "group": group,
                "series_col": group,
                "series_row": 0,
            }

    for idx, symbol in enumerate(LANTHANIDE_SERIES):
        layout.setdefault(symbol, {})
        layout[symbol]["series_row"] = 1
        layout[symbol]["series_col"] = 3 + idx

    for idx, symbol in enumerate(ACTINIDE_SERIES):
        layout.setdefault(symbol, {})
        layout[symbol]["series_row"] = 2
        layout[symbol]["series_col"] = 3 + idx

    return layout


@lru_cache(maxsize=1)
def _load_overrides() -> Dict[str, Dict[str, Any]]:
    if not PERIODIC_OVERRIDES_PATH.exists():
        return {}
    with open(PERIODIC_OVERRIDES_PATH, "r", encoding="utf-8") as fh:
        raw = json.load(fh)
    return {str(key): value for key, value in raw.items() if isinstance(value, dict)}


@lru_cache(maxsize=1)
def get_periodic_table_elements() -> List[Dict[str, Any]]:
    """Build periodic table data with local override support."""
    layout_index = _build_layout_index()
    overrides = _load_overrides()

    elements: List[Dict[str, Any]] = []

    for atomic_number in range(1, 119):
        el = periodictable.elements[atomic_number]
        symbol = str(el.symbol)
        layout = layout_index.get(symbol, {})

        period = layout.get("period")
        group = layout.get("group")
        category = _default_category(symbol, atomic_number, group)
        block = _default_block(symbol, atomic_number, group)
        phase = _default_phase(symbol)

        config = electron_configuration(atomic_number, charge=0)
        shells: List[int] = []
        for orbital in config.get("orbitals", []):
            n_val = int(orbital.get("n", 0))
            e_val = int(orbital.get("electrons", 0))
            while len(shells) < n_val:
                shells.append(0)
            shells[n_val - 1] += e_val

        mass = _safe_float(getattr(el, "mass", None))
        density = _safe_float(getattr(el, "density", None))
        covalent_radius_angstrom = _safe_float(getattr(el, "covalent_radius", None))
        atomic_radius_pm = covalent_radius_angstrom * 100.0 if covalent_radius_angstrom is not None else None

        entry: Dict[str, Any] = {
            "atomicNumber": atomic_number,
            "symbol": symbol,
            "name": str(el.name).capitalize(),
            "atomicMass": mass,
            "group": group,
            "period": period,
            "block": block,
            "category": category,
            "phase": phase,
            "electronConfiguration": config.get("long"),
            "shells": shells,
            "oxidationStates": _default_oxidation_states(symbol, group, category),
            "electronegativity": None,
            "ionizationEnergy": None,
            "atomicRadius": atomic_radius_pm,
            "meltingPoint": None,
            "boilingPoint": None,
            "density": density,
            "isDiatomic": symbol in DIATOMIC_SYMBOLS,
            "examNotes": "",
            "seriesRow": layout.get("series_row", 0),
            "seriesCol": layout.get("series_col", group),
        }

        override = overrides.get(symbol, {})
        for key, value in override.items():
            entry[key] = value

        elements.append(entry)

    return elements


def get_element_by_symbol(symbol: str) -> Optional[Dict[str, Any]]:
    symbol = symbol.strip().capitalize()
    for element in get_periodic_table_elements():
        if element["symbol"] == symbol:
            return element
    return None


def format_value(value: Any, unit: str = "", digits: int = 3) -> str:
    """Format optional numeric values for details panel."""
    if value is None:
        return "Ikke angivet"
    if isinstance(value, (int, float)):
        text = f"{value:.{digits}g}"
        return f"{text} {unit}".strip()
    return str(value)
