"""
Streamlit UI wrapper helpers for Solutions calculators.
"""

from typing import List, Tuple
from core.solutions import (
    solve_molarity,
    grams_for_solution,
    volume_stock_for_dilution,
    solve_molality,
    percent_w_w,
    percent_v_v,
    percent_w_v,
    ppm_general,
    ppm_aqueous_from_mg_per_L,
    mix_solutions,
    mole_fraction_from_masses,
    mole_fraction_from_moles,
    ionic_strength,
)


__all__ = [
    "solve_molarity",
    "grams_for_solution",
    "volume_stock_for_dilution",
    "solve_molality",
    "percent_w_w",
    "percent_v_v",
    "percent_w_v",
    "ppm_general",
    "ppm_aqueous_from_mg_per_L",
    "mix_solutions",
    "mole_fraction_from_masses",
    "mole_fraction_from_moles",
    "ionic_strength",
]


