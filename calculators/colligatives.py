"""
Colligative properties calculators:
- Freezing point depression / Boiling point elevation
- Osmotic pressure
- Raoult's law (nonvolatile and binary ideal solutions)

All functions return (result, steps, metadata) when appropriate.
"""

from typing import Dict, List, Tuple, Optional, Any
from core.thermo import (
    load_constants,
    molality,
    freezing_point_depression_deltaTf,
    boiling_point_elevation_deltaTb,
    osmotic_pressure_atm,
    raoult_nonvolatile_pressure,
    raoult_binary_pressure,
)


def _fmt(v: float, unit: str, sig: int = 4) -> str:
    if v == 0:
        return f"0 {unit}"
    abs_v = abs(v)
    if abs_v >= 1e4 or abs_v < 1e-3:
        return f"{v:.{sig-1}e} {unit}"
    return f"{v:.{sig}g} {unit}"


def freezing_boiling_with_steps(
    solvent: str = "water",
    moles_solute: Optional[float] = None,
    mass_solute_g: Optional[float] = None,
    molar_mass_solute_g_per_mol: Optional[float] = None,
    mass_solvent_g: float = 1000.0,
    i: float = 1.0,
    Kf_Ckg_per_mol: Optional[float] = None,
    Kb_Ckg_per_mol: Optional[float] = None,
) -> Tuple[Dict[str, float], List[str], Dict[str, Any]]:
    """
    Compute ΔTf and ΔTb and new Tf, Tb for a solvent. Defaults for water.
    Returns dict with keys: deltaTf_C, deltaTb_C, Tf_C, Tb_C.
    """
    constants = load_constants()
    if solvent == "water":
        water = constants['water']
        Kf = water['Kf_Ckg_per_mol'] if Kf_Ckg_per_mol is None else Kf_Ckg_per_mol
        Kb = water['Kb_Ckg_per_mol'] if Kb_Ckg_per_mol is None else Kb_Ckg_per_mol
        Tf0 = water['T_fus_C']
        Tb0 = water['T_boil_C']
    else:
        if Kf_Ckg_per_mol is None or Kb_Ckg_per_mol is None or 'T_fus_C' not in constants.get(solvent, {}):
            raise ValueError("Provide Kf, Kb and baseline Tf/Tb for custom solvent")
        sol = constants[solvent]
        Kf = Kf_Ckg_per_mol
        Kb = Kb_Ckg_per_mol
        Tf0 = sol['T_fus_C']
        Tb0 = sol['T_boil_C']

    if moles_solute is None:
        if mass_solute_g is None or molar_mass_solute_g_per_mol is None:
            raise ValueError("Provide moles_solute or mass + molar mass")
        if mass_solute_g < 0 or molar_mass_solute_g_per_mol <= 0:
            raise ValueError("Invalid mass or molar mass")
        moles_solute = mass_solute_g / molar_mass_solute_g_per_mol

    if mass_solvent_g <= 0:
        raise ValueError("Solvent mass must be positive")
    if i < 0:
        raise ValueError("van't Hoff factor i must be non-negative")

    m = molality(moles_solute, mass_solvent_g)
    dTf = freezing_point_depression_deltaTf(Kf, m, i)
    dTb = boiling_point_elevation_deltaTb(Kb, m, i)
    Tf = Tf0 - dTf
    Tb = Tb0 + dTb

    steps: List[str] = []
    steps.append("Colligative properties: ΔTf = i Kf m, ΔTb = i Kb m")
    steps.append(f"Molality: m = n_solute / kg_solvent = {_fmt(moles_solute, 'mol')} / {_fmt(mass_solvent_g/1000.0, 'kg')} = {_fmt(m, 'mol/kg')}")
    steps.append(f"ΔTf = i Kf m = {i} × {_fmt(Kf, '°C·kg/mol')} × {_fmt(m, 'mol/kg')} = {_fmt(dTf, '°C')}")
    steps.append(f"ΔTb = i Kb m = {i} × {_fmt(Kb, '°C·kg/mol')} × {_fmt(m, 'mol/kg')} = {_fmt(dTb, '°C')}")
    steps.append(f"Tf = {Tf0:.3g} °C − ΔTf = {Tf:.3g} °C; Tb = {Tb0:.3g} °C + ΔTb = {Tb:.3g} °C")

    res = {
        'deltaTf_C': dTf,
        'deltaTb_C': dTb,
        'Tf_C': Tf,
        'Tb_C': Tb,
        'molality': m,
    }
    return res, steps, {'molality': m, 'Kf': Kf, 'Kb': Kb}


def osmotic_pressure_with_steps(
    molarity_M: Optional[float] = None,
    moles_solute: Optional[float] = None,
    solution_volume_L: Optional[float] = None,
    temperature_K: float = 298.15,
    i: float = 1.0,
) -> Tuple[float, List[str], Dict[str, Any]]:
    """
    π = i M R T (atm). Compute M from moles/volume if needed.
    """
    if molarity_M is None:
        if moles_solute is None or solution_volume_L is None or solution_volume_L <= 0:
            raise ValueError("Provide molarity or moles and volume > 0")
        molarity_M = moles_solute / solution_volume_L

    pi_atm = osmotic_pressure_atm(i, molarity_M, temperature_K)
    steps: List[str] = []
    steps.append("Osmotic pressure: π = i M R T")
    steps.append(f"Given: i = {i}, M = {molarity_M:.6g} M, T = {temperature_K:.3g} K")
    steps.append("Using R = 0.082057 L·atm·mol⁻¹·K⁻¹")
    steps.append(f"π = {i} × {molarity_M:.6g} × 0.082057 × {temperature_K:.3g} = {pi_atm:.4g} atm")
    return pi_atm, steps, {'M': molarity_M}


def raoult_nonvolatile_with_steps(
    x_solvent: float,
    P_star_solvent: float,
) -> Tuple[float, List[str], Dict[str, Any]]:
    """For nonvolatile solute: P_solution = x_solvent P*_solvent (units preserved)."""
    P_solution = raoult_nonvolatile_pressure(x_solvent, P_star_solvent)
    steps: List[str] = []
    steps.append("Raoult's law (nonvolatile solute): P = x_solvent P*_solvent")
    steps.append(f"x_solvent = {x_solvent:.4f}, P*_solvent = {P_star_solvent:.4g} → P = {P_solution:.4g}")
    return P_solution, steps, {}


def raoult_binary_with_steps(
    x_A: float,
    P_star_A: float,
    x_B: float,
    P_star_B: float,
) -> Tuple[Dict[str, float], List[str], Dict[str, Any]]:
    """
    For volatile binary: P_total = x_A P*_A + x_B P*_B; return totals and components.
    """
    P_total, P_A, P_B = raoult_binary_pressure(x_A, P_star_A, x_B, P_star_B)
    steps: List[str] = []
    steps.append("Raoult's law (binary): P_total = x_A P*_A + x_B P*_B")
    steps.append(f"x_A = {x_A:.4f}, P*_A = {P_star_A:.4g} → P_A = {P_A:.4g}")
    steps.append(f"x_B = {x_B:.4f}, P*_B = {P_star_B:.4g} → P_B = {P_B:.4g}")
    steps.append(f"P_total = {P_A:.4g} + {P_B:.4g} = {P_total:.4g}")
    res = {'P_total': P_total, 'P_A': P_A, 'P_B': P_B}
    return res, steps, {}


