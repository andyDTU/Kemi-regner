"""
Thermochemistry calculators:
- Calorimetry (q = m c ΔT)
- Heating/Cooling curve for water
- Reaction enthalpy from formation enthalpies
- Clausius–Clapeyron (two-point form)

All functions return (result, steps, metadata) to align with app patterns.
"""

from typing import Dict, List, Tuple, Optional, Any
from core.thermo import (
    load_constants,
    get_gas_constant,
    get_water_constants,
    q_mc_deltaT,
    heating_curve_water_segments,
    reaction_enthalpy_from_formation,
    clausius_clapeyron_p2,
)


def _fmt(v: float, unit: str, sig: int = 4) -> str:
    if v == 0:
        return f"0 {unit}"
    abs_v = abs(v)
    if abs_v >= 1e4 or abs_v < 1e-2:
        return f"{v:.{sig-1}e} {unit}"
    return f"{v:.{sig}g} {unit}"


def calculate_calorimetry_with_steps(
    mass_g: float,
    delta_T_K: Optional[float] = None,
    T_initial_C: Optional[float] = None,
    T_final_C: Optional[float] = None,
    c_J_per_gK: Optional[float] = None,
    preset: Optional[str] = "water_liquid",
    output_unit: str = "kJ",
) -> Tuple[float, List[str], Dict[str, Any]]:
    """
    q = m c ΔT. Endothermic positive when temperature rises.

    Args:
        mass_g: mass in grams (>=0)
        delta_T_K: temperature change in K (positive or negative)
        T_initial_C: initial temperature in °C (optional if delta_T_K given)
        T_final_C: final temperature in °C (optional if delta_T_K given)
        c_J_per_gK: specific heat; if None, use preset
        preset: one of {"water_ice", "water_liquid", "water_steam"}
        output_unit: "J" or "kJ" (default kJ)
    Returns:
        (q_value in requested unit, steps, metadata)
    """
    steps: List[str] = []
    if mass_g < 0:
        raise ValueError("Mass must be non-negative")

    # Determine c
    if c_J_per_gK is None:
        if preset is None:
            raise ValueError("Either c_J_per_gK or preset must be provided")
        water = get_water_constants()
        if preset == "water_ice":
            c_J_per_gK = water['c_ice_J_per_gK']
        elif preset == "water_liquid":
            c_J_per_gK = water['c_liquid_J_per_gK']
        elif preset == "water_steam":
            c_J_per_gK = water['c_steam_J_per_gK']
        else:
            raise ValueError("Unknown preset for specific heat")

    # Determine ΔT
    if delta_T_K is None:
        if T_initial_C is None or T_final_C is None:
            raise ValueError("Provide either delta_T_K or both T_initial_C and T_final_C")
        delta_T_K = T_final_C - T_initial_C

    steps.append("Calorimetry: q = m c ΔT")
    steps.append(f"Given: m = {_fmt(mass_g, 'g')}, c = {_fmt(c_J_per_gK, 'J/(g·K)')}, ΔT = {_fmt(delta_T_K, 'K')}")

    q_J = q_mc_deltaT(mass_g, c_J_per_gK, delta_T_K)
    steps.append(f"q = m c ΔT = {_fmt(mass_g, 'g')} × {_fmt(c_J_per_gK, 'J/(g·K)')} × {_fmt(delta_T_K, 'K')} = {_fmt(q_J, 'J')}")

    if output_unit == "kJ":
        q_out = q_J / 1000.0
        steps.append(f"Convert to kJ: {_fmt(q_J, 'J')} = {_fmt(q_out, 'kJ')}")
        unit = 'kJ'
    elif output_unit == "J":
        q_out = q_J
        unit = 'J'
    else:
        raise ValueError("output_unit must be 'J' or 'kJ'")

    metadata = {
        'q_J': q_J,
        'delta_T_K': delta_T_K,
        'specific_heat_J_per_gK': c_J_per_gK,
        'unit': unit,
    }
    return q_out, steps, metadata


def calculate_heating_curve_water_with_steps(
    mass_g: float,
    T_initial_C: float,
    T_final_C: float,
) -> Tuple[float, List[str], Dict[str, Any]]:
    """
    Heating/cooling curve for water across phase changes. Returns total q in kJ.
    """
    q_total_J, segments = heating_curve_water_segments(mass_g, T_initial_C, T_final_C)
    steps: List[str] = []
    steps.append("Heating/Cooling Curve (Water)")
    steps.append(f"Mass = {_fmt(mass_g, 'g')}, T_i = {_fmt(T_initial_C, '°C')}, T_f = {_fmt(T_final_C, '°C')}")
    for s in segments:
        if s['type'] == 'sensible':
            phase = s.get('phase', '?')
            steps.append(f"Sensible ({phase}): {s['description']} = {_fmt(s['q_J'], 'J')}")
        else:
            pc = s.get('phase_change', '?')
            steps.append(f"Phase change ({pc}): {s['description']} = {_fmt(s['q_J'], 'J')}")
    steps.append(f"Total q = {_fmt(q_total_J, 'J')} = {_fmt(q_total_J/1000.0, 'kJ')}")
    return q_total_J/1000.0, steps, {'q_J': q_total_J, 'segments': segments}


def calculate_reaction_enthalpy_from_formation_with_steps(
    reaction: str,
) -> Tuple[float, List[str], Dict[str, Any]]:
    """
    ΔH_rxn = Σν ΔHf°(products) − Σν ΔHf°(reactants), returned in kJ/mol.
    """
    deltaH_kJ, contributions = reaction_enthalpy_from_formation(reaction)
    steps: List[str] = ["Reaction enthalpy from standard formation enthalpies"]
    steps.append(f"Reaction: {reaction}")
    steps.append("Contributions (kJ/mol):")
    for k, v in contributions.items():
        steps.append(f"- {k}: {v:.4g}")
    steps.append(f"ΔH_rxn = {deltaH_kJ:.4g} kJ/mol")
    return deltaH_kJ, steps, {'contributions_kJ_per_mol': contributions}


def calculate_clausius_clapeyron_with_steps(
    P1_atm: float,
    T1_K: float,
    T2_K: float,
    deltaHvap_kJ_per_mol: Optional[float] = None,
) -> Tuple[float, List[str], Dict[str, Any]]:
    """
    Two-point Clausius–Clapeyron to compute P2 at T2.
    Returns P2 in atm.
    """
    constants = load_constants()
    if deltaHvap_kJ_per_mol is None:
        deltaHvap_kJ_per_mol = constants['water']['deltaHvap_kJ_per_mol']
    P2 = clausius_clapeyron_p2(P1_atm, T1_K, T2_K, deltaHvap_kJ_per_mol)
    steps: List[str] = []
    steps.append("Clausius–Clapeyron (two-point): ln(P2/P1) = -ΔHvap/R · (1/T2 - 1/T1)")
    steps.append(f"Given: P1 = {_fmt(P1_atm, 'atm')}, T1 = {_fmt(T1_K, 'K')}, T2 = {_fmt(T2_K, 'K')}, ΔHvap = {_fmt(deltaHvap_kJ_per_mol, 'kJ/mol')}")
    steps.append(f"Result: P2 = {_fmt(P2, 'atm')}")
    return P2, steps, {'deltaHvap_kJ_per_mol': deltaHvap_kJ_per_mol}


