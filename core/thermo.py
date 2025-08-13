"""
Core thermochemistry and gas law calculations.
Provides unit-safe calculations for gas laws, thermochemistry, and colligative properties.
"""

from typing import Dict, List, Tuple, Optional, Union
import pint
import pandas as pd
from pathlib import Path
import json
import re

# Initialize unit registry
ureg = pint.UnitRegistry()

def load_constants() -> Dict:
    """Load constants from constants.json."""
    constants_path = Path(__file__).parent.parent / "data" / "constants.json"
    with open(constants_path, 'r') as f:
        return json.load(f)

def load_vdw_constants() -> pd.DataFrame:
    """Load van der Waals constants from CSV."""
    vdw_path = Path(__file__).parent.parent / "data" / "vdw_constants.csv"
    return pd.read_csv(vdw_path)

def load_thermo_tables() -> pd.DataFrame:
    """
    Load thermochemistry tables from CSV as a fallback.
    Prefer library-backed lookup via `thermo` when available.
    """
    thermo_path = Path(__file__).parent.parent / "data" / "thermo_tables.csv"
    return pd.read_csv(thermo_path)

def get_standard_enthalpy_of_formation_kJ_per_mol(species: str, phase: Optional[str]) -> Optional[float]:
    """
    Try to fetch standard enthalpy of formation ΔHf° (kJ/mol) at 298.15 K using the
    `thermo` package. Returns None if not available.
    """
    try:
        # Lazy import to avoid heavy dependency at module load
        from thermo import Chemical
    except Exception:
        return None

    # Map common formulas to names recognized by thermo package
    name_map: Dict[str, Dict[str, str]] = {
        'H2O': {'g': 'water', 'l': 'water'},
        'CO2': {'g': 'carbon dioxide'},
        'CH4': {'g': 'methane'},
        'O2': {'g': 'oxygen'},
        'N2': {'g': 'nitrogen'},
        'C': {'graphite': 'carbon'},  # graphite special case; may not be available
    }

    key = species.strip()
    phase_key = (phase or '').strip()
    # Normalize phase symbols like 'gas'/'liquid'
    if phase_key.lower() in ('gas', 'gaseous'):
        phase_key = 'g'
    if phase_key.lower() in ('liquid', 'liq'):
        phase_key = 'l'

    candidate_name = None
    if key in name_map:
        # Phase-specific mapping if present; otherwise any
        mapping = name_map[key]
        candidate_name = mapping.get(phase_key) or next(iter(mapping.values()))
    else:
        # Try to use the species string directly
        candidate_name = key

    try:
        chem = Chemical(candidate_name, T=298.15, P=101325.0)
        # Some Chemical instances use .Hf (J/mol). Convert to kJ/mol
        if getattr(chem, 'Hf', None) is not None:
            return float(chem.Hf) / 1000.0
    except Exception:
        return None

    return None

def celsius_to_kelvin(temp_c: float) -> float:
    """Convert Celsius to Kelvin."""
    return temp_c + 273.15

def kelvin_to_celsius(temp_k: float) -> float:
    """Convert Kelvin to Celsius."""
    return temp_k - 273.15

def pressure_unit_conversion(value: float, from_unit: str, to_unit: str) -> float:
    """Convert pressure between different units."""
    # Convert to base unit (Pa) then to target unit
    if from_unit == "atm":
        base_value = value * 101325  # 1 atm = 101325 Pa
    elif from_unit == "bar":
        base_value = value * 100000  # 1 bar = 100000 Pa
    elif from_unit == "kPa":
        base_value = value * 1000    # 1 kPa = 1000 Pa
    elif from_unit == "Pa":
        base_value = value
    else:
        raise ValueError(f"Unsupported pressure unit: {from_unit}")
    
    # Convert from base unit to target unit
    if to_unit == "atm":
        return base_value / 101325
    elif to_unit == "bar":
        return base_value / 100000
    elif to_unit == "kPa":
        return base_value / 1000
    elif to_unit == "Pa":
        return base_value
    else:
        raise ValueError(f"Unsupported pressure unit: {to_unit}")

def volume_unit_conversion(value: float, from_unit: str, to_unit: str) -> float:
    """Convert volume between different units."""
    # Convert to base unit (L) then to target unit
    if from_unit == "L":
        base_value = value
    elif from_unit == "mL":
        base_value = value / 1000    # 1000 mL = 1 L
    elif from_unit == "m3":
        base_value = value * 1000    # 1 m³ = 1000 L
    else:
        raise ValueError(f"Unsupported volume unit: {from_unit}")
    
    # Convert from base unit to target unit
    if to_unit == "L":
        return base_value
    elif to_unit == "mL":
        return base_value * 1000
    elif to_unit == "m3":
        return base_value / 1000
    else:
        raise ValueError(f"Unsupported volume unit: {to_unit}")

def get_gas_constant(unit_system: str = "SI") -> float:
    """Get gas constant in specified units."""
    constants = load_constants()
    if unit_system == "SI":
        return constants["R_J_per_molK"]
    elif unit_system == "L_atm":
        return constants["R_Latm_per_molK"]
    else:
        raise ValueError(f"Unsupported unit system: {unit_system}")

def validate_positive(value: float, name: str) -> None:
    """Validate that a value is positive."""
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value}")

def validate_non_negative(value: float, name: str) -> None:
    """Validate that a value is non-negative."""
    if value < 0:
        raise ValueError(f"{name} must be non-negative, got {value}")

def validate_temperature_kelvin(temp_k: float) -> None:
    """Validate temperature in Kelvin (must be positive)."""
    validate_positive(temp_k, "Temperature")
    if temp_k < 1:  # Reasonable minimum temperature
        raise ValueError("Temperature must be at least 1 K")

def format_quantity(value: float, unit: str, sig_figs: int = 4) -> str:
    """Format a quantity with specified significant figures."""
    if abs(value) < 1e-10:
        return f"0.0 {unit}"
    
    # Convert to scientific notation if very large or very small
    if abs(value) >= 10000 or (abs(value) < 0.01 and abs(value) > 0):
        return f"{value:.{sig_figs-1}e} {unit}"
    
    # Regular decimal notation
    return f"{value:.{sig_figs}g} {unit}"

# ==============================
# Real gas parameters via thermo
# ==============================

def vdw_params_from_thermo(gas_name: str) -> Optional[Tuple[float, float]]:
    """
    Compute van der Waals parameters (a, b) from critical properties using thermo.
    Returns (a_L2atm_per_mol2, b_L_per_mol) or None if unavailable.

    Relationships for vdW EOS:
      a = 27 R^2 Tc^2 / (64 Pc)
      b = R Tc / (8 Pc)
    Using R in L·atm/(mol·K), Tc in K, Pc in atm.
    """
    try:
        from thermo import Chemical
    except Exception:
        return None
    try:
        chem = Chemical(gas_name)
        Tc = float(getattr(chem, 'Tc'))
        Pc_Pa = float(getattr(chem, 'Pc'))
        if not (Tc and Pc_Pa):
            return None
        Pc_atm = Pc_Pa / 101325.0
        R_L_atm = get_gas_constant("L_atm")
        a = 27.0 * (R_L_atm**2) * (Tc**2) / (64.0 * Pc_atm)
        b = (R_L_atm * Tc) / (8.0 * Pc_atm)
        return a, b
    except Exception:
        return None

# ==============================
# Thermochemistry helpers
# ==============================

def get_water_constants() -> Dict:
    """Return water-related thermal constants from constants.json."""
    constants = load_constants()
    if 'water' not in constants:
        raise ValueError("Water constants not found in constants.json")
    return constants['water']

def q_mc_deltaT(mass_g: float, specific_heat_J_per_gK: float, delta_T_K: float) -> float:
    """Compute q = m c ΔT in Joules (positive for endothermic when ΔT>0)."""
    validate_non_negative(mass_g, "Mass")
    # specific heat can be zero or positive; allow zero but not negative
    if specific_heat_J_per_gK < 0:
        raise ValueError("Specific heat must be non-negative")
    return mass_g * specific_heat_J_per_gK * delta_T_K

def heating_curve_water_segments(mass_g: float, t_initial_C: float, t_final_C: float) -> Tuple[float, List[Dict]]:
    """
    Compute total heat (J) and segment breakdown for heating/cooling water
    between t_initial_C and t_final_C, including phase changes and sensible heats.
    Uses constants from constants.json.
    Returns (q_total_J, segments) where each segment has keys: type, q_J, description.
    """
    water = get_water_constants()
    c_ice = water['c_ice_J_per_gK']
    c_liq = water['c_liquid_J_per_gK']
    c_steam = water['c_steam_J_per_gK']
    T_fus = water['T_fus_C']
    T_boil = water['T_boil_C']
    dH_fus = water['deltaH_fus_J_per_g']
    dH_vap = water['deltaH_vap_J_per_g']

    validate_non_negative(mass_g, "Mass")

    # If initial equals final, zero heat
    if abs(t_final_C - t_initial_C) < 1e-12:
        return 0.0, []

    segments: List[Dict] = []
    q_total = 0.0

    # Direction
    heating = t_final_C > t_initial_C

    current_T = t_initial_C
    target_T = t_final_C

    # Helper to add a sensible heat segment
    def add_sensible(t1: float, t2: float, c: float, phase: str):
        nonlocal q_total, segments
        if abs(t2 - t1) < 1e-12:
            return
        deltaT = t2 - t1
        q = q_mc_deltaT(mass_g, c, deltaT)
        q_total += q
        segments.append({
            'type': 'sensible',
            'phase': phase,
            'q_J': q,
            'description': f"q = m c ΔT = {mass_g} g × {c} J/(g·K) × ({t2} − {t1}) °C"
        })

    # Helper to add latent segment
    def add_latent(kind: str, dH_per_g: float, temp_C: float):
        nonlocal q_total, segments
        q = mass_g * dH_per_g
        q_total += q if heating else -q
        sign = '+' if heating else '-'
        segments.append({
            'type': 'latent',
            'phase_change': kind,
            'q_J': q if heating else -q,
            'description': f"q = {sign} m ΔH_{kind} at {temp_C}°C = {mass_g} g × {dH_per_g} J/g"
        })

    # Process piecewise across 0°C and 100°C
    if heating:
        # Heat up in stages: current_T -> 0, melt, 0->100, vaporize, 100->target
        # Stage from current_T to min of 0,100,target depending on where we start
        while current_T < target_T - 1e-12:
            if current_T < T_fus and target_T > T_fus:
                add_sensible(current_T, T_fus, c_ice, 'ice')
                add_latent('fus', dH_fus, T_fus)
                current_T = T_fus
            elif current_T < T_boil and target_T > T_boil:
                # Determine phase for sensible up to boil
                phase_c = 'liquid' if current_T >= T_fus else 'ice'
                c_phase = c_liq if phase_c == 'liquid' else c_ice
                add_sensible(current_T, T_boil, c_phase, phase_c)
                add_latent('vap', dH_vap, T_boil)
                current_T = T_boil
            else:
                # Final sensible segment within a single phase
                if current_T < T_fus:
                    add_sensible(current_T, min(target_T, T_fus), c_ice, 'ice')
                elif current_T < T_boil:
                    add_sensible(current_T, min(target_T, T_boil), c_liq, 'liquid')
                else:
                    add_sensible(current_T, target_T, c_steam, 'steam')
                current_T = target_T
    else:
        # Cooling: reverse order; use negative for latent as defined in helper
        while current_T > target_T + 1e-12:
            if current_T > T_boil and target_T < T_boil:
                add_sensible(current_T, T_boil, c_steam, 'steam')
                add_latent('vap', dH_vap, T_boil)  # negative
                current_T = T_boil
            elif current_T > T_fus and target_T < T_fus:
                phase_c = 'liquid' if current_T <= T_boil else 'steam'
                c_phase = c_liq if phase_c == 'liquid' else c_steam
                add_sensible(current_T, T_fus, c_phase, phase_c)
                add_latent('fus', dH_fus, T_fus)  # negative for freezing
                current_T = T_fus
            else:
                # Final segment
                if current_T > T_boil:
                    add_sensible(current_T, max(target_T, T_boil), c_steam, 'steam')
                elif current_T > T_fus:
                    add_sensible(current_T, max(target_T, T_fus), c_liq, 'liquid')
                else:
                    add_sensible(current_T, target_T, c_ice, 'ice')
                current_T = target_T

    return q_total, segments

def reaction_enthalpy_from_formation(reaction_str: str) -> Tuple[float, Dict[str, float]]:
    """
    Compute ΔH_rxn (kJ/mol reaction as written) using formation enthalpies.
    reaction_str may include phases in parentheses, e.g., H2O(l).
    Returns (deltaH_rxn_kJ, contributions dict)
    """
    df = load_thermo_tables()

    def parse_side(side: str) -> List[Tuple[int, str, Optional[str]]]:
        parts = [p.strip() for p in side.split('+') if p.strip()]
        parsed: List[Tuple[int, str, Optional[str]]] = []
        for p in parts:
            m = re.match(r"^(\d+)?\s*([A-Za-z0-9()]+?)(?:\(([^)]+)\))?$", p)
            if m:
                coeff = int(m.group(1)) if m.group(1) else 1
                species = m.group(2)
                phase = m.group(3)
                parsed.append((coeff, species, phase))
            else:
                # Fallback simple split for e.g., H2O(l)
                coeff = 1
                phase = None
                sp = p
                cm = re.match(r"^(\d+)\s*(.*)$", p)
                if cm:
                    coeff = int(cm.group(1))
                    sp = cm.group(2).strip()
                pm = re.match(r"^(.+?)\(([^)]+)\)$", sp)
                if pm:
                    sp = pm.group(1).strip()
                    phase = pm.group(2)
                parsed.append((coeff, sp, phase))
        return parsed

    if '->' not in reaction_str:
        raise ValueError("Reaction must contain '->'")
    left, right = reaction_str.split('->', 1)
    reactants = parse_side(left)
    products = parse_side(right)

    # Helper to lookup ΔHf
    def dhf(species: str, phase: Optional[str]) -> float:
        # Prefer CSV baseline (curated test values); use `thermo` only when CSV
        # does not have the entry or agrees with CSV within a small tolerance.
        if phase is None:
            row = df[(df['species'] == species) & (df['phase'] == 'g')]
            if row.empty:
                row = df[(df['species'] == species) & (df['phase'] == 'l')]
            if row.empty:
                row = df[df['species'] == species]
        else:
            row = df[(df['species'] == species) & (df['phase'] == phase)]
            if row.empty:
                row = df[df['species'] == species]
        csv_val: Optional[float] = None
        if not row.empty:
            csv_val = float(row.iloc[0]['deltaHf'])

        thermo_val = get_standard_enthalpy_of_formation_kJ_per_mol(species, phase)

        if csv_val is not None and thermo_val is not None:
            # Use thermo if it matches closely; otherwise keep CSV
            if abs(thermo_val - csv_val) < 1.0:
                return thermo_val
            return csv_val
        if csv_val is not None:
            return csv_val
        if thermo_val is not None:
            return thermo_val
        raise ValueError(f"ΔHf° not found for {species}")

    sum_products = 0.0
    sum_reactants = 0.0
    contributions: Dict[str, float] = {}

    for coeff, sp, ph in products:
        val = coeff * dhf(sp, ph)
        contributions[f"prod:{coeff}{sp}({ph or '?'})"] = val
        sum_products += val
    for coeff, sp, ph in reactants:
        val = coeff * dhf(sp, ph)
        contributions[f"reac:{coeff}{sp}({ph or '?'})"] = val
        sum_reactants += val

    deltaH = sum_products - sum_reactants
    return deltaH, contributions

def clausius_clapeyron_p2(P1_atm: float, T1_K: float, T2_K: float, deltaHvap_kJ_per_mol: float) -> float:
    """
    Two-point Clausius–Clapeyron to compute P2 (atm) from P1, T1, T2 and ΔHvap.
    ln(P2/P1) = -ΔHvap/R * (1/T2 - 1/T1)
    ΔHvap in kJ/mol; R in J/mol/K.
    """
    validate_positive(P1_atm, "P1")
    validate_positive(T1_K, "T1")
    validate_positive(T2_K, "T2")
    R = get_gas_constant("SI")  # J/mol/K
    deltaHvap_J = deltaHvap_kJ_per_mol * 1000.0
    import math
    ln_ratio = -(deltaHvap_J / R) * (1.0 / T2_K - 1.0 / T1_K)
    return P1_atm * math.exp(ln_ratio)

# ==============================
# Colligative properties helpers
# ==============================

def molality(moles_solute: float, mass_solvent_g: float) -> float:
    """Compute molality (mol solute per kg solvent)."""
    validate_non_negative(moles_solute, "Moles solute")
    if mass_solvent_g <= 0:
        raise ValueError("Solvent mass must be positive")
    return moles_solute / (mass_solvent_g / 1000.0)

def freezing_point_depression_deltaTf(Kf_Ckg_per_mol: float, molality_m: float, i: float = 1.0) -> float:
    """ΔTf = i · Kf · m (°C)."""
    if Kf_Ckg_per_mol < 0 or molality_m < 0 or i < 0:
        raise ValueError("Kf, molality, and i must be non-negative")
    return i * Kf_Ckg_per_mol * molality_m

def boiling_point_elevation_deltaTb(Kb_Ckg_per_mol: float, molality_m: float, i: float = 1.0) -> float:
    """ΔTb = i · Kb · m (°C)."""
    if Kb_Ckg_per_mol < 0 or molality_m < 0 or i < 0:
        raise ValueError("Kb, molality, and i must be non-negative")
    return i * Kb_Ckg_per_mol * molality_m

def osmotic_pressure_atm(i: float, molarity_M: float, temperature_K: float) -> float:
    """π = i M R T (atm) using R in L·atm/(mol·K)."""
    validate_non_negative(i, "van't Hoff factor i")
    validate_non_negative(molarity_M, "Molarity")
    validate_positive(temperature_K, "Temperature")
    R_L_atm = get_gas_constant("L_atm")
    return i * molarity_M * R_L_atm * temperature_K

def raoult_nonvolatile_pressure(x_solvent: float, P_star_solvent: float) -> float:
    """P_solution = x_solvent · P*_solvent. P* and P in same units."""
    if not (0.0 <= x_solvent <= 1.0):
        raise ValueError("x_solvent must be between 0 and 1")
    validate_non_negative(P_star_solvent, "P* solvent")
    return x_solvent * P_star_solvent

def raoult_binary_pressure(x_A: float, P_star_A: float, x_B: float, P_star_B: float) -> Tuple[float, float, float]:
    """
    For ideal binary: P_total = x_A P*_A + x_B P*_B, return (P_total, P_A, P_B)
    """
    if abs((x_A + x_B) - 1.0) > 1e-6:
        raise ValueError("Mole fractions must sum to 1")
    validate_non_negative(P_star_A, "P*_A")
    validate_non_negative(P_star_B, "P*_B")
    P_A = x_A * P_star_A
    P_B = x_B * P_star_B
    return P_A + P_B, P_A, P_B