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
    convert_gibbs_to_j,
    convert_temperature_to_k,
    validate_n,
    validate_k,
    validate_potential,
    e_cell_from_half_potentials,
    e_cell_from_gibbs,
    unknown_potential_from_e_cell,
    unknown_potential_from_gibbs,
    match_candidate_potential,
    gibbs_from_e_cell,
    gibbs_from_k,
    k_from_gibbs,
    k_from_e_cell,
    e_cell_from_k,
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


def calculate_e_cell_from_half_potentials_with_steps(
    cathode_E: float,
    cathode_type: str,
    anode_E: float,
    anode_type: str,
):
    return e_cell_from_half_potentials(cathode_E, cathode_type, anode_E, anode_type)


def calculate_e_cell_from_gibbs_with_steps(dG_value: float, dG_unit: str, n_value: float):
    return e_cell_from_gibbs(dG_value, dG_unit, n_value)


def calculate_unknown_potential_from_e_cell_with_steps(
    e_cell_V: float,
    known_E: float,
    known_side: str,
    known_type: str,
    unknown_side: str,
    unknown_type: str,
):
    return unknown_potential_from_e_cell(
        e_cell_V,
        known_E,
        known_side,
        known_type,
        unknown_side,
        unknown_type,
    )


def calculate_unknown_potential_from_gibbs_with_steps(
    dG_value: float,
    dG_unit: str,
    n_value: float,
    known_E: float,
    known_side: str,
    known_type: str,
    unknown_side: str,
    unknown_type: str,
):
    return unknown_potential_from_gibbs(
        dG_value,
        dG_unit,
        n_value,
        known_E,
        known_side,
        known_type,
        unknown_side,
        unknown_type,
    )


def calculate_gibbs_from_e_cell_with_steps(n_value: float, e_cell_V: float):
    return gibbs_from_e_cell(n_value, e_cell_V)


def calculate_gibbs_from_k_with_steps(k_value: float, t_value: float, t_unit: str):
    return gibbs_from_k(k_value, t_value, t_unit)


def calculate_k_from_gibbs_with_steps(dG_value: float, dG_unit: str, t_value: float, t_unit: str):
    return k_from_gibbs(dG_value, dG_unit, t_value, t_unit)


def calculate_k_from_e_cell_with_steps(n_value: float, e_cell_V: float, t_value: float, t_unit: str):
    return k_from_e_cell(n_value, e_cell_V, t_value, t_unit)


def calculate_e_cell_from_k_with_steps(n_value: float, k_value: float, t_value: float, t_unit: str):
    return e_cell_from_k(n_value, k_value, t_value, t_unit)


def convert_gibbs_to_j_units(value: float, unit: str) -> float:
    return convert_gibbs_to_j(value, unit)


def convert_temperature_to_k_units(value: float, unit: str) -> float:
    return convert_temperature_to_k(value, unit)


def validate_n_value(n_value: float) -> int:
    return validate_n(n_value)


def validate_k_value(k_value: float) -> None:
    return validate_k(k_value)


def validate_potential_value(e_value: float) -> None:
    return validate_potential(e_value)


def match_candidate_potential_value(target_value: float, target_type: str, candidates, tolerance: float = 0.005):
    return match_candidate_potential(target_value, target_type, candidates, tolerance)


