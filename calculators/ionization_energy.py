"""Ionization Energy lookup and UI for the Atoms & Molar Mass tab.

Provides lookup functions and a Streamlit renderer that integrates with the
existing periodic table dataset in `core.periodic_table`.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

import streamlit as st

from core.periodic_table import get_periodic_table_elements, get_element_by_symbol

DATA_DIR = Path(__file__).parent.parent / "data"
IONIZATION_DATA_PATH = DATA_DIR / "ionization_energies.json"


def _load_ionization_data() -> Dict[str, Dict[str, Any]]:
    if not IONIZATION_DATA_PATH.exists():
        return {}
    with open(IONIZATION_DATA_PATH, "r", encoding="utf-8") as fh:
        raw = json.load(fh)
    return {str(k): v for k, v in raw.items() if isinstance(v, dict)}


_IONIZATION_DATA = _load_ionization_data()


def normalize_element_query(query: str) -> Optional[str]:
    """
    Takes user input such as 'O', 'oxygen', or ' Oxygen '
    and returns the matching element symbol if found.
    """
    if not isinstance(query, str):
        return None
    q = query.strip()
    if not q:
        return None

    # Quick symbol match (case-insensitive)
    for el in get_periodic_table_elements():
        if el["symbol"].lower() == q.lower():
            return el["symbol"]

    # Match by English name (case-insensitive)
    q_low = q.lower()
    for el in get_periodic_table_elements():
        if el.get("name", "").lower() == q_low:
            return el["symbol"]

    return None


def get_ionization_energy(query: str, level: int) -> Optional[float]:
    """
    Looks up the selected ionization energy level for an element.
    Returns the value in kJ/mol, or None if the element or level is not available.
    """
    if level is None:
        return None
    try:
        level_int = int(level)
    except Exception:
        return None
    symbol = normalize_element_query(query)
    if not symbol:
        return None

    data = _IONIZATION_DATA.get(symbol, {})
    energies = data.get("energies_kj_mol") or {}
    # JSON keys are strings; coerce to int for lookup
    for k, v in energies.items():
        try:
            if int(k) == level_int:
                return float(v)
        except Exception:
            continue
    return None


def _ordinal(n: int) -> str:
    if 10 <= (n % 100) <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def format_ionization_energy_result(query: str, level: int) -> str:
    """
    Returns a user-friendly text result for the app interface.
    """
    symbol = normalize_element_query(query)
    if not symbol:
        return (
            "Element not found. Try a symbol such as O, Fe, or Na, "
            "or an English element name such as oxygen."
        )

    element = get_element_by_symbol(symbol)
    name = element.get("name", symbol) if element else symbol

    value = get_ionization_energy(symbol, level)
    if value is None:
        return f"No data available for the { _ordinal(level) } ionization energy of {name} ({symbol})."

    return f"**{name} ({symbol})**\n**{_ordinal(level)} ionization energy:** {value} kJ/mol"


def render_ionization_energy_tab():
    """Streamlit UI renderer for the Ionization Energy tab."""
    st.markdown(
        """
        **Ionization energy is the energy required to remove an electron from an atom or ion in the gas phase."
        """,
    )

    st.caption("Search by symbol (O, Fe) or English name (oxygen, iron). Results in kJ/mol.")

    col1, col2 = st.columns([3, 1])
    with col1:
        elements_input = st.text_input(
            "Element (symbol or name). For multiple elements, separate with commas:",
            placeholder="e.g., O, Fe, sodium",
            help="Examples: O, oxygen, Fe, Iron. For compare: O, Na, Fe",
            key="ionization_elements",
        )
    with col2:
        level = st.number_input(
            "Ionization level (1 = first)",
            min_value=1,
            max_value=20,
            value=1,
            step=1,
            key="ionization_level",
        )

    if st.button("Lookup", type="primary", key="ionization_lookup"):
        if not elements_input.strip():
            st.error("Please enter at least one element symbol or name.")
            return

        parts = [p.strip() for p in elements_input.split(",") if p.strip()]
        results = []

        for p in parts:
            symbol = normalize_element_query(p)
            if not symbol:
                results.append((p, None, "element_not_found"))
                continue

            element = get_element_by_symbol(symbol)
            name = element.get("name", symbol) if element else symbol
            value = get_ionization_energy(symbol, int(level))
            if value is None:
                results.append((symbol, name, "level_missing"))
            else:
                results.append((symbol, name, value))

        for item in results:
            if item[1] is None and item[2] == "element_not_found":
                st.error(
                    "Element not found. Try a symbol such as O, Fe, or Na, or an English element name such as oxygen."
                )
            elif item[2] == "level_missing":
                st.info(f"No data available for the { _ordinal(int(level)) } ionization energy of {item[1]} ({item[0]}).")
            else:
                # item = (symbol, name, value)
                st.markdown(f"**{item[1]} ({item[0]})**")
                st.markdown(f"**{_ordinal(int(level))} ionization energy:** {item[2]} kJ/mol")
