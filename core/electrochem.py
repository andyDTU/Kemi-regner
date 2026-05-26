"""
Core electrochemistry helpers: standard potentials, Nernst, ΔG and K.
"""

from typing import Dict, List, Tuple, Optional
import math
import pandas as pd
from pathlib import Path
from core.thermo import load_constants


def load_reduction_potentials() -> pd.DataFrame:
    path = Path(__file__).parent.parent / "data" / "reduction_potentials.csv"
    return pd.read_csv(path)


def standard_cell_potential(cathode_half: str, anode_half: str) -> Tuple[Dict, List[str], Dict]:
    """
    Compute E°cell and electron count n from selected reduction half-reactions.
    E°cell = E°cathode − E°anode. n = lcm(n_cathode, n_anode).
    """
    df = load_reduction_potentials()
    def row_for(hr: str) -> pd.Series:
        row = df[df['half_reaction'] == hr]
        if row.empty:
            raise ValueError(f"Half-reaction not found: {hr}")
        return row.iloc[0]

    rc = row_for(cathode_half)
    ra = row_for(anode_half)
    E_c = float(rc['E0_V'])
    E_a = float(ra['E0_V'])
    n_c = int(rc['n_electrons'])
    n_a = int(ra['n_electrons'])

    def lcm(a: int, b: int) -> int:
        import math
        return abs(a*b) // math.gcd(a, b)

    n = lcm(n_c, n_a)
    E_cell = E_c - E_a
    steps = [
        f"Cathode (reduction): {cathode_half}, E° = {E_c:.4g} V",
        f"Anode (reduction, reversed for oxidation): {anode_half}, E° = {E_a:.4g} V",
        f"E°cell = E°cathode − E°anode = {E_c:.4g} − {E_a:.4g} = {E_cell:.4g} V",
        f"n (electrons transferred) = lcm({n_c}, {n_a}) = {n}",
    ]
    return {"E0_cell_V": E_cell, "n": n}, steps, {}


def nernst_potential(E0_cell_V: float, n: int, T_K: float, Q: float) -> Tuple[float, List[str], Dict]:
    if n < 1:
        raise ValueError("n must be ≥ 1")
    if T_K <= 0:
        raise ValueError("Temperature must be > 0 K")
    if Q <= 0:
        raise ValueError("Q must be > 0")
    const = load_constants()
    R = const["R_J_per_molK"]
    F = const.get("F_C_per_mol", 96485.33212)
    term = (R * T_K) / (n * F)
    E = E0_cell_V - term * math.log(Q)
    steps = [
        "Nernst: E = E° − (RT/nF) ln Q",
        f"RT/nF = ({R:.6g}×{T_K})/({n}×{F:.5g}) = {term:.6g} V",
        f"E = {E0_cell_V:.6g} − {term:.6g}×ln({Q:.6g}) = {E:.6g} V",
        f"Log10 form: E = E° − (2.303 RT/nF) log10 Q",
    ]
    return E, steps, {"RT_over_nF": term}


def daniell_Q(Zn2_M: float, Cu2_M: float) -> float:
    if Zn2_M <= 0 or Cu2_M <= 0:
        raise ValueError("Concentrations must be positive")
    return Zn2_M / Cu2_M


def deltaG_from_E(n: int, E_V: float) -> Tuple[float, List[str], Dict]:
    const = load_constants()
    F = const.get("F_C_per_mol", 96485.33212)
    dG_J = -n * F * E_V
    dG_kJ = dG_J / 1000.0
    steps = [
        "ΔG = −n F E",
        f"ΔG = −{n}×{F:.5g}×{E_V:.6g} = {dG_J:.6g} J/mol = {dG_kJ:.6g} kJ/mol",
    ]
    return dG_kJ, steps, {}


def K_from_E0(n: int, E0_V: float, T_K: float) -> Tuple[float, float, List[str], Dict]:
    const = load_constants()
    R = const["R_J_per_molK"]
    F = const.get("F_C_per_mol", 96485.33212)
    if n < 1:
        raise ValueError("n must be ≥ 1")
    if T_K <= 0:
        raise ValueError("Temperature must be > 0 K")
    exponent = (n * F * E0_V) / (R * T_K)
    K = math.exp(exponent)
    log10K = exponent / 2.303
    steps = [
        "K from E°: K = exp(n F E° / (R T))",
        f"Exponent = (n F E°)/(R T) = ({n}×{F:.5g}×{E0_V:.6g})/({R:.6g}×{T_K}) = {exponent:.6g}",
        f"K = exp({exponent:.6g})",
        f"log10 K = (n F E°)/(2.303 R T) = {log10K:.6g}",
    ]
    return K, log10K, steps, {}


def convert_gibbs_to_j(value: float, unit: str) -> float:
    unit_norm = (unit or "").strip().lower()
    if "kj" in unit_norm:
        return value * 1000.0
    if "j" in unit_norm:
        return value
    raise ValueError("Unsupported Gibbs unit (use J/mol or kJ/mol)")


def convert_temperature_to_k(value: float, unit: str) -> float:
    unit_norm = (unit or "").strip().lower().replace(" ", "")
    if unit_norm in {"k", "kelvin"}:
        return value
    if unit_norm in {"c", "°c", "celsius"}:
        return value + 273.15
    raise ValueError("Unsupported temperature unit (use K or °C)")


def validate_n(n_value: float) -> int:
    if not isinstance(n_value, (int, float)):
        raise ValueError("n must be a positive integer")
    if n_value <= 0:
        raise ValueError("n must be positive")
    rounded = int(round(n_value))
    if abs(n_value - rounded) > 1e-9:
        raise ValueError("n should be an integer")
    return rounded


def validate_k(k_value: float) -> None:
    if not isinstance(k_value, (int, float)):
        raise ValueError("K must be a number")
    if k_value <= 0:
        raise ValueError("K must be > 0")


def validate_potential(e_value: float) -> None:
    if not isinstance(e_value, (int, float)) or math.isnan(e_value) or math.isinf(e_value):
        raise ValueError("Potential must be a finite number")


def _normalize_potential_type(value: str) -> str:
    value_norm = (value or "").strip().lower()
    if value_norm in {"red", "reduction", "reduction potential", "e°red", "e0red"}:
        return "red"
    if value_norm in {"ox", "oxidation", "oxidation potential", "e°ox", "e0ox"}:
        return "ox"
    if value_norm in {"actual", "actual half-reaction direction", "direction"}:
        return "actual"
    raise ValueError("Potential type must be red, ox, or actual")


def _normalize_electrode_side(value: str) -> str:
    value_norm = (value or "").strip().lower()
    if value_norm in {"cathode", "katode"}:
        return "cathode"
    if value_norm in {"anode", "anoda", "anode"}:
        return "anode"
    raise ValueError("Electrode must be cathode or anode")


def _to_actual_potential(e_value: float, potential_type: str, electrode: str) -> float:
    p_type = _normalize_potential_type(potential_type)
    side = _normalize_electrode_side(electrode)
    if p_type == "actual":
        return e_value
    if side == "cathode":
        return e_value if p_type == "red" else -e_value
    return e_value if p_type == "ox" else -e_value


def _from_actual_potential(actual_value: float, potential_type: str, electrode: str) -> float:
    p_type = _normalize_potential_type(potential_type)
    side = _normalize_electrode_side(electrode)
    if p_type == "actual":
        return actual_value
    if side == "cathode":
        return actual_value if p_type == "red" else -actual_value
    return actual_value if p_type == "ox" else -actual_value


def _formula_label(cathode_type: str, anode_type: str) -> str:
    cath = _normalize_potential_type(cathode_type)
    an = _normalize_potential_type(anode_type)
    if cath == "red" and an == "red":
        return "E°cell = E°red,cathode − E°red,anode"
    if cath == "red" and an == "ox":
        return "E°cell = E°red,cathode + E°ox,anode"
    if cath == "ox" and an == "ox":
        return "E°cell = E°ox,anode − E°ox,cathode"
    if cath == "actual" and an == "actual":
        return "E°cell = E°cathode + E°anode"
    return "E°cell = E°cathode(actual) + E°anode(actual)"


def e_cell_from_half_potentials(
    cathode_E: float,
    cathode_type: str,
    anode_E: float,
    anode_type: str,
) -> Tuple[Dict, List[str], Dict]:
    validate_potential(cathode_E)
    validate_potential(anode_E)
    cathode_actual = _to_actual_potential(cathode_E, cathode_type, "cathode")
    anode_actual = _to_actual_potential(anode_E, anode_type, "anode")
    e_cell = cathode_actual + anode_actual

    warnings: List[str] = []
    if _normalize_potential_type(cathode_type) == "ox":
        warnings.append("Cathode is reduction; oxidation potential was negated.")
    if _normalize_potential_type(anode_type) == "red":
        warnings.append("Anode is oxidation; reduction potential was negated.")

    formula = _formula_label(cathode_type, anode_type)
    steps = [
        "Given half-cell potentials and types",
        f"Formula: {formula}",
        f"E°cathode(actual) = {cathode_actual:.6g} V",
        f"E°anode(actual) = {anode_actual:.6g} V",
        f"E°cell = {cathode_actual:.6g} + {anode_actual:.6g} = {e_cell:.6g} V",
    ]
    return {
        "E_cell_V": e_cell,
        "cathode_actual_V": cathode_actual,
        "anode_actual_V": anode_actual,
        "formula": formula,
        "warnings": warnings,
    }, steps, {}


def e_cell_from_gibbs(dG_value: float, dG_unit: str, n_value: float) -> Tuple[Dict, List[str], Dict]:
    n = validate_n(n_value)
    dG_J = convert_gibbs_to_j(dG_value, dG_unit)
    const = load_constants()
    F = const.get("F_C_per_mol", 96485.33212)
    e_cell = -dG_J / (n * F)
    steps = [
        "ΔG° = −n F E°cell",
        f"ΔG° = {dG_value:.6g} {dG_unit} = {dG_J:.6g} J/mol",
        f"E°cell = −ΔG°/(nF) = −({dG_J:.6g})/({n}×{F:.6g}) = {e_cell:.6g} V",
    ]
    return {"E_cell_V": e_cell, "dG_J": dG_J, "n": n}, steps, {}


def unknown_potential_from_e_cell(
    e_cell_V: float,
    known_E: float,
    known_side: str,
    known_type: str,
    unknown_side: str,
    unknown_type: str,
) -> Tuple[Dict, List[str], Dict]:
    validate_potential(e_cell_V)
    validate_potential(known_E)
    known_actual = _to_actual_potential(known_E, known_type, known_side)
    unknown_actual = e_cell_V - known_actual
    unknown_value = _from_actual_potential(unknown_actual, unknown_type, unknown_side)
    steps = [
        "E°cell = E°cathode(actual) + E°anode(actual)",
        f"Known actual potential = {known_actual:.6g} V",
        f"Unknown actual potential = {e_cell_V:.6g} − {known_actual:.6g} = {unknown_actual:.6g} V",
        f"Converted unknown = {unknown_value:.6g} V",
    ]
    return {
        "unknown_V": unknown_value,
        "unknown_actual_V": unknown_actual,
        "E_cell_V": e_cell_V,
    }, steps, {}


def unknown_potential_from_gibbs(
    dG_value: float,
    dG_unit: str,
    n_value: float,
    known_E: float,
    known_side: str,
    known_type: str,
    unknown_side: str,
    unknown_type: str,
) -> Tuple[Dict, List[str], Dict]:
    e_cell_data, e_steps, _ = e_cell_from_gibbs(dG_value, dG_unit, n_value)
    e_cell_V = e_cell_data["E_cell_V"]
    unknown_data, unknown_steps, _ = unknown_potential_from_e_cell(
        e_cell_V,
        known_E,
        known_side,
        known_type,
        unknown_side,
        unknown_type,
    )
    steps = e_steps + ["Then:"] + unknown_steps
    return {
        **unknown_data,
        "dG_J": e_cell_data["dG_J"],
        "n": e_cell_data["n"],
    }, steps, {}


def match_candidate_potential(
    target_value: float,
    target_type: str,
    candidates: List[Dict],
    tolerance: float = 0.005,
) -> Dict:
    if not candidates:
        return {}
    target_type_norm = _normalize_potential_type(target_type)
    if target_type_norm == "actual":
        raise ValueError("Target type cannot be 'actual' for candidate matching")

    best = None
    for candidate in candidates:
        value = candidate.get("value")
        c_type = _normalize_potential_type(candidate.get("type", ""))
        if not isinstance(value, (int, float)):
            continue
        compare_value = value if c_type == target_type_norm else -value
        diff = abs(compare_value - target_value)
        if best is None or diff < best["diff"]:
            best = {
                "label": candidate.get("label", ""),
                "value": value,
                "type": c_type,
                "converted_value": compare_value,
                "diff": diff,
            }

    if best and best["diff"] <= tolerance:
        return best
    return {}


def gibbs_from_e_cell(n_value: float, e_cell_V: float) -> Tuple[Dict, List[str], Dict]:
    n = validate_n(n_value)
    const = load_constants()
    F = const.get("F_C_per_mol", 96485.33212)
    dG_J = -n * F * e_cell_V
    steps = [
        "ΔG° = −n F E°cell",
        f"ΔG° = −{n}×{F:.6g}×{e_cell_V:.6g} = {dG_J:.6g} J/mol",
    ]
    return {"dG_J": dG_J, "n": n}, steps, {}


def gibbs_from_k(k_value: float, t_value: float, t_unit: str) -> Tuple[Dict, List[str], Dict]:
    validate_k(k_value)
    t_k = convert_temperature_to_k(t_value, t_unit)
    if t_k <= 0:
        raise ValueError("Temperature must be > 0 K")
    const = load_constants()
    R = const["R_J_per_molK"]
    dG_J = -R * t_k * math.log(k_value)
    steps = [
        "ΔG° = −R T ln(K)",
        f"T = {t_k:.6g} K",
        f"ΔG° = −{R:.6g}×{t_k:.6g}×ln({k_value:.6g}) = {dG_J:.6g} J/mol",
    ]
    return {"dG_J": dG_J, "T_K": t_k}, steps, {}


def k_from_gibbs(dG_value: float, dG_unit: str, t_value: float, t_unit: str) -> Tuple[Dict, List[str], Dict]:
    dG_J = convert_gibbs_to_j(dG_value, dG_unit)
    t_k = convert_temperature_to_k(t_value, t_unit)
    if t_k <= 0:
        raise ValueError("Temperature must be > 0 K")
    const = load_constants()
    R = const["R_J_per_molK"]
    exponent = -dG_J / (R * t_k)
    k_value = math.exp(exponent)
    steps = [
        "K = exp(−ΔG°/(R T))",
        f"ΔG° = {dG_J:.6g} J/mol, T = {t_k:.6g} K",
        f"K = exp({exponent:.6g}) = {k_value:.6g}",
    ]
    return {"K": k_value, "T_K": t_k, "dG_J": dG_J}, steps, {}


def k_from_e_cell(n_value: float, e_cell_V: float, t_value: float, t_unit: str) -> Tuple[Dict, List[str], Dict]:
    n = validate_n(n_value)
    t_k = convert_temperature_to_k(t_value, t_unit)
    if t_k <= 0:
        raise ValueError("Temperature must be > 0 K")
    const = load_constants()
    R = const["R_J_per_molK"]
    F = const.get("F_C_per_mol", 96485.33212)
    exponent = (n * F * e_cell_V) / (R * t_k)
    k_value = math.exp(exponent)
    steps = [
        "K = exp(n F E°cell / (R T))",
        f"Exponent = ({n}×{F:.6g}×{e_cell_V:.6g})/({R:.6g}×{t_k:.6g}) = {exponent:.6g}",
        f"K = exp({exponent:.6g}) = {k_value:.6g}",
    ]
    return {"K": k_value, "T_K": t_k, "n": n}, steps, {}


def e_cell_from_k(n_value: float, k_value: float, t_value: float, t_unit: str) -> Tuple[Dict, List[str], Dict]:
    n = validate_n(n_value)
    validate_k(k_value)
    t_k = convert_temperature_to_k(t_value, t_unit)
    if t_k <= 0:
        raise ValueError("Temperature must be > 0 K")
    const = load_constants()
    R = const["R_J_per_molK"]
    F = const.get("F_C_per_mol", 96485.33212)
    e_cell = (R * t_k / (n * F)) * math.log(k_value)
    steps = [
        "E°cell = (R T / n F) ln(K)",
        f"E°cell = ({R:.6g}×{t_k:.6g}/({n}×{F:.6g}))×ln({k_value:.6g}) = {e_cell:.6g} V",
    ]
    return {"E_cell_V": e_cell, "T_K": t_k, "n": n}, steps, {}


