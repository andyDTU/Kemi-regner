"""
Gibbs Free Energy Calculator
Calculates Gibbs free energy change and related thermodynamic properties.

This module provides two APIs:
- direct scalar-input Gibbs relation (legacy UI/tests)
- reaction-table Gibbs workflow for thermochemistry tab
"""

import math
from typing import Tuple, Dict, List, Any
from core.units import Q, normalize_energy, normalize_temperature
from core.formatting import fmt_quantity, fmt_energy
from core.solver import add_latex_step, add_math_step

R_GAS_J_PER_MOL_K = 8.31446261815324
LOG10_E = math.log10(math.e)
MAX_EXP_ARGUMENT = 700.0


def _to_kelvin(temperature: float, temp_unit: str) -> float:
    if not math.isfinite(temperature):
        raise ValueError("Temperature must be finite")

    temp_unit_norm = str(temp_unit or "K").strip()
    if temp_unit_norm == "K":
        t_k = float(temperature)
    elif temp_unit_norm in ("°C", "C"):
        t_k = float(temperature) + 273.15
    else:
        raise ValueError("Unsupported temperature unit. Use 'K' or '°C'.")

    if t_k <= 0:
        raise ValueError("Temperature in Kelvin must be positive")
    return t_k


def _convert_dhf_to_kj_per_mol(value: float, unit: str) -> float:
    if not math.isfinite(value):
        raise ValueError("ΔHf° values must be finite")
    unit_norm = str(unit or "kJ/mol").strip()
    if unit_norm == "kJ/mol":
        return float(value)
    if unit_norm == "J/mol":
        return float(value) / 1000.0
    if unit_norm == "cal/mol":
        return float(value) * 4.184 / 1000.0
    if unit_norm == "kcal/mol":
        return float(value) * 4.184
    raise ValueError("Unsupported ΔHf° unit")


def _convert_entropy_to_j_per_mol_k(value: float, unit: str) -> float:
    if not math.isfinite(value):
        raise ValueError("S° values must be finite")
    unit_norm = str(unit or "J/(mol·K)").strip()
    if unit_norm in ("J/(mol·K)", "J/(mol*K)"):
        return float(value)
    if unit_norm in ("kJ/(mol·K)", "kJ/(mol*K)"):
        return float(value) * 1000.0
    if unit_norm in ("cal/(mol·K)", "cal/(mol*K)"):
        return float(value) * 4.184
    raise ValueError("Unsupported S° unit")


def _safe_float(value: Any, field_name: str, species_name: str) -> float:
    try:
        out = float(value)
    except Exception as exc:
        raise ValueError(f"Invalid {field_name} for {species_name}: {value}") from exc
    if not math.isfinite(out):
        raise ValueError(f"{field_name} must be finite for {species_name}")
    return out


def _is_missing_value(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() in ("", "-", "—", "–")
    if isinstance(value, float) and math.isnan(value):
        return True
    return False


def _format_row_term(nu: float, species: str) -> str:
    if abs(nu - 1.0) < 1e-12:
        return species
    if abs(nu - int(nu)) < 1e-12:
        return f"{int(nu)} {species}"
    return f"{nu:g} {species}"


def _reaction_string(reactants: List[Dict[str, Any]], products: List[Dict[str, Any]]) -> str:
    left = " + ".join(_format_row_term(row["nu"], row["species"]) for row in reactants)
    right = " + ".join(_format_row_term(row["nu"], row["species"]) for row in products)
    return f"{left} -> {right}"


def calculate_reaction_gibbs_with_steps(
    species_rows: List[Dict[str, Any]],
    temperature: float,
    temp_unit: str = "K",
    dhf_unit_default: str = "kJ/mol",
    entropy_unit_default: str = "J/(mol·K)",
) -> Tuple[Dict[str, Any], List[str], Dict[str, Any]]:
    """
    Calculate ΔH°rxn, ΔS°rxn, ΔG° and equilibrium constant K from tabular species data.

    Each row should contain:
    - species: chemical label (str)
    - side: reactant/product (case-insensitive)
    - nu: stoichiometric coefficient (>0)
    - dhf: ΔHf° numeric value
    - s: S° numeric value

    Optional per-row units:
    - dhf_unit: defaults to dhf_unit_default
    - s_unit: defaults to entropy_unit_default
    """
    if not isinstance(species_rows, list) or len(species_rows) == 0:
        raise ValueError("Provide at least one reaction row")

    t_k = _to_kelvin(temperature, temp_unit)

    reactants: List[Dict[str, Any]] = []
    products: List[Dict[str, Any]] = []
    contributions: List[Dict[str, Any]] = []
    missing_fields: List[str] = []

    for idx, raw_row in enumerate(species_rows, start=1):
        if not isinstance(raw_row, dict):
            raise ValueError(f"Row {idx} must be an object")

        species = str(raw_row.get("species", "")).strip()
        if not species:
            species = f"row {idx}"

        side_raw = str(raw_row.get("side", "")).strip().lower()
        if side_raw in ("reactant", "reaktant"):
            side = "reactant"
            sign = -1.0
        elif side_raw in ("product", "produkt"):
            side = "product"
            sign = 1.0
        else:
            raise ValueError(f"Invalid side for {species}. Use reactant/product.")

        nu = _safe_float(raw_row.get("nu"), "coefficient", species)
        if nu <= 0:
            raise ValueError(f"Coefficient must be > 0 for {species}")

        if _is_missing_value(raw_row.get("dhf")):
            missing_fields.append(f"ΔHf° missing for {species}")
            continue
        if _is_missing_value(raw_row.get("s")):
            missing_fields.append(f"S° missing for {species}")
            continue

        dhf_value = _safe_float(raw_row.get("dhf"), "ΔHf°", species)
        s_value = _safe_float(raw_row.get("s"), "S°", species)
        dhf_unit = str(raw_row.get("dhf_unit", dhf_unit_default) or dhf_unit_default)
        s_unit = str(raw_row.get("s_unit", entropy_unit_default) or entropy_unit_default)

        dhf_kj_per_mol = _convert_dhf_to_kj_per_mol(dhf_value, dhf_unit)
        s_j_per_mol_k = _convert_entropy_to_j_per_mol_k(s_value, s_unit)

        normalized = {
            "species": species,
            "side": side,
            "nu": nu,
            "dhf_kj_per_mol": dhf_kj_per_mol,
            "s_j_per_mol_k": s_j_per_mol_k,
        }

        if side == "reactant":
            reactants.append(normalized)
        else:
            products.append(normalized)

        contributions.append(
            {
                "species": species,
                "side": side,
                "nu": nu,
                "dhf_kj_per_mol": dhf_kj_per_mol,
                "s_j_per_mol_k": s_j_per_mol_k,
                "signed_nu_dhf_kj_per_mol": sign * nu * dhf_kj_per_mol,
                "signed_nu_s_j_per_mol_k": sign * nu * s_j_per_mol_k,
            }
        )

    if missing_fields:
        raise ValueError("; ".join(missing_fields))
    if not reactants:
        raise ValueError("At least one reactant row is required")
    if not products:
        raise ValueError("At least one product row is required")

    sum_products_h = sum(r["nu"] * r["dhf_kj_per_mol"] for r in products)
    sum_reactants_h = sum(r["nu"] * r["dhf_kj_per_mol"] for r in reactants)
    delta_h_rxn_kj_per_mol = sum_products_h - sum_reactants_h

    sum_products_s = sum(r["nu"] * r["s_j_per_mol_k"] for r in products)
    sum_reactants_s = sum(r["nu"] * r["s_j_per_mol_k"] for r in reactants)
    delta_s_rxn_j_per_mol_k = sum_products_s - sum_reactants_s

    delta_g_rxn_kj_per_mol = delta_h_rxn_kj_per_mol - (t_k * delta_s_rxn_j_per_mol_k / 1000.0)
    delta_g_rxn_j_per_mol = delta_g_rxn_kj_per_mol * 1000.0

    ln_k = -delta_g_rxn_j_per_mol / (R_GAS_J_PER_MOL_K * t_k)
    log10_k = ln_k * LOG10_E

    if ln_k > MAX_EXP_ARGUMENT:
        k_value = math.inf
        k_display = f"K > 1e{MAX_EXP_ARGUMENT * LOG10_E:.1f}"
    elif ln_k < -MAX_EXP_ARGUMENT:
        k_value = 0.0
        k_display = f"K < 1e{-MAX_EXP_ARGUMENT * LOG10_E:.1f}"
    else:
        k_value = math.exp(ln_k)
        k_display = f"{k_value:.6g}"

    spontaneity = "spontaneous" if delta_g_rxn_kj_per_mol < 0 else (
        "non-spontaneous" if delta_g_rxn_kj_per_mol > 0 else "at equilibrium"
    )

    reaction_str = _reaction_string(reactants, products)

    steps: List[str] = []
    steps.append("**Reaction-based Gibbs workflow**")
    steps.append(f"Reaction: {reaction_str}")
    steps.append(f"T = {t_k:.6g} K")
    steps.append("ΔH°rxn = Σ(νΔHf°)_products - Σ(νΔHf°)_reactants")
    steps.append(f"Σ products (H) = {sum_products_h:.6g} kJ/mol")
    steps.append(f"Σ reactants (H) = {sum_reactants_h:.6g} kJ/mol")
    steps.append(f"ΔH°rxn = {delta_h_rxn_kj_per_mol:.6g} kJ/mol")
    steps.append("ΔS°rxn = Σ(νS°)_products - Σ(νS°)_reactants")
    steps.append(f"Σ products (S) = {sum_products_s:.6g} J/(mol·K)")
    steps.append(f"Σ reactants (S) = {sum_reactants_s:.6g} J/(mol·K)")
    steps.append(f"ΔS°rxn = {delta_s_rxn_j_per_mol_k:.6g} J/(mol·K)")
    steps.append("ΔG° = ΔH° - TΔS°")
    steps.append(f"ΔG° = {delta_g_rxn_kj_per_mol:.6g} kJ/mol")
    steps.append("ln K = -ΔG°/(RT)")
    steps.append(f"ln K = {ln_k:.6g}, log10 K = {log10_k:.6g}")
    steps.append(f"K ≈ {k_display}")

    result = {
        "delta_h_rxn_kj_per_mol": delta_h_rxn_kj_per_mol,
        "delta_s_rxn_j_per_mol_k": delta_s_rxn_j_per_mol_k,
        "delta_g_rxn_kj_per_mol": delta_g_rxn_kj_per_mol,
        "ln_k": ln_k,
        "log10_k": log10_k,
        "k": k_value,
        "k_display": k_display,
        "temperature_k": t_k,
        "spontaneity": spontaneity,
        "reaction": reaction_str,
    }

    metadata = {
        "sum_products_h_kj_per_mol": sum_products_h,
        "sum_reactants_h_kj_per_mol": sum_reactants_h,
        "sum_products_s_j_per_mol_k": sum_products_s,
        "sum_reactants_s_j_per_mol_k": sum_reactants_s,
        "row_contributions": contributions,
        "constants": {
            "R_J_per_mol_K": R_GAS_J_PER_MOL_K,
        },
    }

    return result, steps, metadata

def calculate_gibbs_free_energy_with_steps(delta_h: float, delta_h_unit: str, 
                                         delta_s: float, delta_s_unit: str,
                                         temperature: float, temp_unit: str) -> Tuple[float, List[str], Dict[str, Any]]:
    """
    Calculate Gibbs free energy change with step-by-step breakdown.
    
    Args:
        delta_h: Enthalpy change
        delta_h_unit: Unit for enthalpy change
        delta_s: Entropy change
        delta_s_unit: Unit for entropy change
        temperature: Temperature
        temp_unit: Unit for temperature
    
    Returns:
        Tuple of (delta_g, steps, metadata)
    """
    # Validate inputs
    if temperature <= 0:
        raise ValueError("Temperature must be positive")
    
    steps = []
    metadata = {}
    
    # Step 1: Convert all values to standard units
    steps.append("**Step 1: Convert all values to standard units**")
    
    # Convert enthalpy to J/mol
    h_quantity = Q(delta_h, delta_h_unit)
    h_j_mol = normalize_energy(h_quantity)
    steps.append(f"ΔH = {fmt_quantity(h_quantity)} = {fmt_quantity(h_j_mol)}")
    
    # Convert entropy to J/(mol·K) - handle the conversion properly
    s_quantity = Q(delta_s, delta_s_unit)
    # For entropy, we need to convert to J/(mol·K) if it's in different units
    if "kJ" in delta_s_unit:
        s_j_mol_k = s_quantity.to("kJ/(mol·K)")
        s_j_mol_k = Q(s_j_mol_k.magnitude * 1000, "J/(mol·K)")  # Convert kJ to J
    elif "cal" in delta_s_unit:
        s_j_mol_k = s_quantity.to("cal/(mol·K)")
        s_j_mol_k = Q(s_j_mol_k.magnitude * 4.184, "J/(mol·K)")  # Convert cal to J
    else:
        s_j_mol_k = s_quantity.to("J/(mol·K)")
    
    steps.append(f"ΔS = {fmt_quantity(s_quantity)} = {fmt_quantity(s_j_mol_k)}")
    
    # Convert temperature to K
    t_quantity = Q(temperature, temp_unit)
    t_k = normalize_temperature(t_quantity)
    steps.append(f"T = {fmt_quantity(t_quantity)} = {fmt_quantity(t_k)}")
    
    # Step 2: Apply the Gibbs free energy equation
    steps.append("\n**Step 2: Apply the Gibbs free energy equation**")
    
    # Calculate TΔS term
    t_delta_s = t_k.magnitude * s_j_mol_k.magnitude
    steps.append(f"T × ΔS = {fmt_quantity(t_k)} × {fmt_quantity(s_j_mol_k)} = {fmt_quantity(t_delta_s)}")
    
    # Calculate ΔG
    delta_g_j_mol = h_j_mol.magnitude - t_delta_s
    steps.append(add_latex_step("ΔG = ΔH - TΔS", 
                               f"\\Delta G = {fmt_quantity(h_j_mol)} - {fmt_quantity(t_delta_s)}"))
    
    steps.append(f"ΔG = {fmt_quantity(delta_g_j_mol)}")
    
    # Step 3: Convert to kJ/mol for display
    steps.append("\n**Step 3: Convert to kJ/mol for display**")
    
    delta_g_kj_mol = delta_g_j_mol / 1000
    steps.append(f"ΔG = {fmt_quantity(delta_g_j_mol)} = {fmt_quantity(delta_g_kj_mol)}")
    
    # Step 4: Determine spontaneity
    steps.append("\n**Step 4: Determine spontaneity**")
    
    if delta_g_j_mol < 0:
        spontaneity = "spontaneous"
        steps.append("Since ΔG < 0, the reaction is **spontaneous** at this temperature.")
    elif delta_g_j_mol > 0:
        spontaneity = "non-spontaneous"
        steps.append("Since ΔG > 0, the reaction is **non-spontaneous** at this temperature.")
    else:
        spontaneity = "at equilibrium"
        steps.append("Since ΔG = 0, the reaction is **at equilibrium** at this temperature.")
    
    # Step 5: Calculate crossover temperature (if applicable)
    steps.append("\n**Step 5: Calculate crossover temperature**")
    
    if abs(s_j_mol_k.magnitude) > 1e-10:  # Avoid division by zero
        t_eq = h_j_mol.magnitude / s_j_mol_k.magnitude
        steps.append(f"At equilibrium: ΔG = 0")
        steps.append(add_latex_step("0 = ΔH - T_eq × ΔS", 
                                   "0 = \\Delta H - T_{eq} \\times \\Delta S"))
        steps.append(add_latex_step("T_eq = ΔH / ΔS", 
                                   "T_{eq} = \\frac{\\Delta H}{\\Delta S}"))
        steps.append(f"T_eq = {fmt_quantity(h_j_mol)} / {fmt_quantity(s_j_mol_k)}")
        steps.append(f"T_eq = {fmt_quantity(t_eq)}")
        
        # Check if this temperature is physically meaningful
        if t_eq > 0:
            if t_eq < 1000:  # Reasonable temperature range
                steps.append(f"This corresponds to {fmt_quantity(t_eq - 273.15)}°C")
            else:
                steps.append(f"This is a very high temperature: {fmt_quantity(t_eq)} K")
        else:
            steps.append("This temperature is not physically meaningful (negative or zero)")
    else:
        t_eq = None
        steps.append("Cannot calculate crossover temperature: ΔS is zero")
    
    # Metadata
    metadata = {
        'delta_h_j_mol': h_j_mol.magnitude,
        'delta_s_j_mol_k': s_j_mol_k.magnitude,
        'temperature_k': t_k.magnitude,
        'delta_g_j_mol': delta_g_j_mol,
        'delta_g_kj_mol': delta_g_kj_mol,
        'spontaneity': spontaneity,
        'crossover_temperature_k': t_eq,
        'units': {
            'enthalpy': 'J/mol',
            'entropy': 'J/(mol·K)',
            'temperature': 'K',
            'gibbs': 'J/mol'
        }
    }
    
    return delta_g_kj_mol, steps, metadata

def analyze_gibbs_temperature_dependence(delta_h: float, delta_h_unit: str,
                                       delta_s: float, delta_s_unit: str) -> Tuple[List[str], Dict[str, Any]]:
    """
    Analyze how Gibbs free energy changes with temperature.
    
    Args:
        delta_h: Enthalpy change
        delta_h_unit: Unit for enthalpy change
        delta_s: Entropy change
        delta_s_unit: Unit for entropy change
    
    Returns:
        Tuple of (analysis_steps, metadata)
    """
    steps = []
    
    # Convert to standard units
    h_quantity = Q(delta_h, delta_h_unit)
    h_j_mol = normalize_energy(h_quantity)
    
    # Convert entropy properly
    s_quantity = Q(delta_s, delta_s_unit)
    if "kJ" in delta_s_unit:
        s_j_mol_k = s_quantity.to("kJ/(mol·K)")
        s_j_mol_k = Q(s_j_mol_k.magnitude * 1000, "J/(mol·K)")
    elif "cal" in delta_s_unit:
        s_j_mol_k = s_quantity.to("cal/(mol·K)")
        s_j_mol_k = Q(s_j_mol_k.magnitude * 4.184, "J/(mol·K)")
    else:
        s_j_mol_k = s_quantity.to("J/(mol·K)")
    
    steps.append("**Temperature Dependence Analysis**")
    steps.append(f"ΔH = {fmt_quantity(h_j_mol)}")
    steps.append(f"ΔS = {fmt_quantity(s_j_mol_k)}")
    
    # Analyze the relationship
    if h_j_mol.magnitude > 0 and s_j_mol_k.magnitude > 0:
        steps.append("Both ΔH > 0 and ΔS > 0")
        steps.append("• At low T: TΔS term is small, so ΔG ≈ ΔH > 0 (non-spontaneous)")
        steps.append("• At high T: TΔS term dominates, so ΔG < 0 (spontaneous)")
        steps.append("• There is a crossover temperature where the reaction becomes spontaneous")
        
    elif h_j_mol.magnitude < 0 and s_j_mol_k.magnitude < 0:
        steps.append("Both ΔH < 0 and ΔS < 0")
        steps.append("• At low T: TΔS term is small, so ΔG ≈ ΔH < 0 (spontaneous)")
        steps.append("• At high T: TΔS term dominates, so ΔG > 0 (non-spontaneous)")
        steps.append("• There is a crossover temperature where the reaction becomes non-spontaneous")
        
    elif h_j_mol.magnitude < 0 and s_j_mol_k.magnitude > 0:
        steps.append("ΔH < 0 and ΔS > 0")
        steps.append("• Always spontaneous at all temperatures")
        steps.append("• ΔG = ΔH - TΔS < 0 for all T > 0")
        
    else:  # h_j_mol.magnitude > 0 and s_j_mol_k.magnitude < 0
        steps.append("ΔH > 0 and ΔS < 0")
        steps.append("• Always non-spontaneous at all temperatures")
        steps.append("• ΔG = ΔH - TΔS > 0 for all T > 0")
    
    # Calculate crossover temperature if applicable
    if abs(s_j_mol_k.magnitude) > 1e-10:
        t_eq = h_j_mol.magnitude / s_j_mol_k.magnitude
        if t_eq > 0:
            steps.append(f"\nCrossover temperature: T_eq = {fmt_quantity(t_eq)}")
            if t_eq < 1000:
                steps.append(f"T_eq = {fmt_quantity(t_eq - 273.15)}°C")
    
    metadata = {
        'enthalpy_sign': 'positive' if h_j_mol.magnitude > 0 else 'negative',
        'entropy_sign': 'positive' if s_j_mol_k.magnitude > 0 else 'negative',
        'crossover_temperature_k': t_eq if abs(s_j_mol_k.magnitude) > 1e-10 else None
    }
    
    return steps, metadata
