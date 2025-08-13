"""
Electrochemistry calculators wrapping core helpers.
"""

from typing import Dict, List, Tuple
from core.electrochem import (
    load_reduction_potentials,
    standard_cell_potential,
    nernst_potential,
    daniell_Q,
    deltaG_from_E,
    K_from_E0,
)


def calculate_standard_cell_with_steps(cathode_half: str, anode_half: str):
    return standard_cell_potential(cathode_half, anode_half)


def calculate_nernst_with_steps(E0_cell_V: float, n: int, T_K: float, Q: float):
    return nernst_potential(E0_cell_V, n, T_K, Q)


def calculate_daniell_Q(Zn2_M: float, Cu2_M: float) -> float:
    return daniell_Q(Zn2_M, Cu2_M)


def calculate_deltaG_from_E_with_steps(n: int, E_V: float):
    return deltaG_from_E(n, E_V)


def calculate_K_from_E0_with_steps(n: int, E0_V: float, T_K: float):
    return K_from_E0(n, E0_V, T_K)


