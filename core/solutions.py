"""
Core solution concentration calculators with unit-safe conversions and step strings.
"""

from typing import List, Tuple, Dict, Optional
from core.formatting import fmt_scientific
from core.formula import calculate_molar_mass_from_formula


def _fmt(v: float, unit: str = "", sig: int = 4) -> str:
    if v == 0:
        return f"0 {unit}".strip()
    abs_v = abs(v)
    if abs_v >= 1e5 or abs_v < 1e-3:
        return f"{v:.{sig-1}e} {unit}".strip()
    return f"{v:.{sig}g} {unit}".strip()


def solve_molarity(M: Optional[float], n_mol: Optional[float], V_L: Optional[float]) -> Tuple[Dict[str, float], str]:
    """Solve M = n/V for one unknown. Return dict with the solved variable and steps string."""
    provided = sum(x is not None for x in (M, n_mol, V_L))
    if provided != 2:
        raise ValueError("Provide exactly two of (M, n, V)")
    steps = "Molarity: M = n / V\n"
    if M is None:
        if V_L is None or V_L <= 0:
            raise ValueError("Volume must be positive")
        M_val = n_mol / V_L
        steps += f"M = {n_mol} mol / {V_L} L = {M_val} mol/L"
        return {"M": M_val}, steps
    if n_mol is None:
        if V_L is None or V_L <= 0:
            raise ValueError("Volume must be positive")
        n = M * V_L
        steps += f"n = M V = {M} mol/L × {V_L} L = {n} mol"
        return {"n_mol": n}, steps
    # V unknown
    if M <= 0:
        raise ValueError("M must be positive")
    V = n_mol / M
    steps += f"V = n / M = {n_mol} mol / {M} mol/L = {V} L"
    return {"V_L": V}, steps


def grams_for_solution(formula: str, M_target: float, V_L: float) -> Tuple[float, str]:
    """Grams of solid to prepare M_target (mol/L) × V_L (L) for given formula."""
    if M_target <= 0 or V_L <= 0:
        raise ValueError("Target molarity and volume must be positive")
    MW = calculate_molar_mass_from_formula(formula)
    n = M_target * V_L
    grams = n * MW
    steps = (
        f"Make solution from solid: grams = n × MW\n"
        f"MW({formula}) = {MW:.5g} g/mol\n"
        f"n = M V = {M_target} mol/L × {V_L} L = {n:.6g} mol\n"
        f"grams = {n:.6g} × {MW:.5g} = {grams:.6g} g"
    )
    return grams, steps


def volume_stock_for_dilution(M_stock: float, M_target: float, V_final_L: float) -> Tuple[float, str]:
    """V_stock from M1 V1 = M2 V2."""
    if any(x <= 0 for x in (M_stock, M_target, V_final_L)):
        raise ValueError("All inputs must be positive")
    V_stock = M_target * V_final_L / M_stock
    steps = (
        "Dilution: M1 V1 = M2 V2\n"
        f"V1 = (M2 V2)/M1 = ({M_target}×{V_final_L})/{M_stock} = {V_stock:.6g} L"
    )
    return V_stock, steps


def solve_molality(m: Optional[float], n_mol: Optional[float], m_solvent_kg: Optional[float]) -> Tuple[Dict[str, float], str]:
    """m = n / kg_solvent. Solve one unknown."""
    provided = sum(x is not None for x in (m, n_mol, m_solvent_kg))
    if provided != 2:
        raise ValueError("Provide exactly two of (m, n_mol, m_solvent_kg)")
    steps = "Molality: m = n / kg_solvent\n"
    if m is None:
        if m_solvent_kg is None or m_solvent_kg <= 0:
            raise ValueError("Solvent mass must be positive")
        m_val = n_mol / m_solvent_kg
        steps += f"m = {n_mol} mol / {m_solvent_kg} kg = {m_val} mol/kg"
        return {"m": m_val}, steps
    if n_mol is None:
        n = m * m_solvent_kg
        steps += f"n = m × kg_solvent = {m} × {m_solvent_kg} = {n} mol"
        return {"n_mol": n}, steps
    # m_solvent unknown
    if m <= 0:
        raise ValueError("Molality must be positive")
    kg = n_mol / m
    steps += f"kg_solvent = n/m = {n_mol}/{m} = {kg} kg"
    return {"m_solvent_kg": kg}, steps


def percent_w_w(m_solute_g: Optional[float], m_total_g: Optional[float], unknown: str) -> Tuple[float, str]:
    """w/w% = 100 * m_solute/m_total."""
    if unknown == "%":
        if m_total_g is None or m_total_g <= 0:
            raise ValueError("Total mass must be positive")
        pct = 100.0 * m_solute_g / m_total_g
        steps = f"w/w% = 100·(m_solute/m_total) = 100·({m_solute_g}/{m_total_g}) = {pct:.6g}%"
        return pct, steps
    if unknown == "m_solute":
        pct = m_solute_g  # overload: input is percent
        if m_total_g is None or m_total_g <= 0:
            raise ValueError("Total mass must be positive")
        m = (pct / 100.0) * m_total_g
        steps = f"m_solute = (%/100)·m_total = ({pct}/100)·{m_total_g} = {m:.6g} g"
        return m, steps
    if unknown == "m_total":
        pct = m_total_g  # overload: input is percent
        if m_solute_g is None or pct <= 0:
            raise ValueError("Percent must be positive and solute mass provided")
        total = (m_solute_g * 100.0) / pct
        steps = f"m_total = (m_solute·100)/% = ({m_solute_g}·100)/{pct} = {total:.6g} g"
        return total, steps
    raise ValueError("unknown must be one of {'%','m_solute','m_total'}")


def percent_v_v(V_solute_mL: Optional[float], V_total_mL: Optional[float], unknown: str) -> Tuple[float, str]:
    if unknown == "%":
        if V_total_mL is None or V_total_mL <= 0:
            raise ValueError("Total volume must be positive")
        pct = 100.0 * V_solute_mL / V_total_mL
        steps = f"v/v% = 100·(V_solute/V_total) = 100·({V_solute_mL}/{V_total_mL}) = {pct:.6g}%"
        return pct, steps
    if unknown == "V_solute":
        pct = V_solute_mL
        if V_total_mL is None or V_total_mL <= 0:
            raise ValueError("Total volume must be positive")
        V = (pct / 100.0) * V_total_mL
        steps = f"V_solute = (%/100)·V_total = ({pct}/100)·{V_total_mL} = {V:.6g} mL"
        return V, steps
    if unknown == "V_total":
        pct = V_total_mL
        if V_solute_mL is None or pct <= 0:
            raise ValueError("Percent must be positive and V_solute provided")
        total = (V_solute_mL * 100.0) / pct
        steps = f"V_total = (V_solute·100)/% = ({V_solute_mL}·100)/{pct} = {total:.6g} mL"
        return total, steps
    raise ValueError("unknown must be one of {'%','V_solute','V_total'}")


def percent_w_v(m_solute_g: Optional[float], V_solution_mL: Optional[float], unknown: str) -> Tuple[float, str]:
    # w/v% = 100·(g solute / mL solution)
    if unknown == "%":
        if V_solution_mL is None or V_solution_mL <= 0:
            raise ValueError("Solution volume must be positive")
        pct = 100.0 * (m_solute_g / V_solution_mL)
        steps = f"w/v% = 100·(g/mL) = 100·({m_solute_g}/{V_solution_mL}) = {pct:.6g}% (g per 100 mL)"
        return pct, steps
    if unknown == "m_solute":
        pct = m_solute_g
        if V_solution_mL is None or V_solution_mL <= 0:
            raise ValueError("Solution volume must be positive")
        m = (pct / 100.0) * V_solution_mL
        steps = f"g = (%/100)·mL = ({pct}/100)·{V_solution_mL} = {m:.6g} g"
        return m, steps
    if unknown == "V_solution":
        pct = V_solution_mL
        if m_solute_g is None or pct <= 0:
            raise ValueError("Percent must be positive and mass provided")
        V = (m_solute_g * 100.0) / pct
        steps = f"mL = (g·100)/% = ({m_solute_g}·100)/{pct} = {V:.6g} mL"
        return V, steps
    raise ValueError("unknown must be one of {'%','m_solute','V_solution'}")


def ppm_general(solute: float, total: float, basis: str, to_unit: str = "ppm") -> Tuple[float, str]:
    """
    ppm/ppb from mass or volume basis.
    - basis: 'mass' or 'volume'
    - to_unit: 'ppm' (1e6) or 'ppb' (1e9)
    """
    if total <= 0:
        raise ValueError("Total must be positive")
    factor = 1e6 if to_unit == "ppm" else 1e9
    value = factor * (solute / total)
    steps = f"{to_unit} = {factor:.0f} · ({solute}/{total}) = {value:.6g}"
    return value, steps


def ppm_aqueous_from_mg_per_L(mg_per_L: float) -> Tuple[float, str]:
    """For dilute aqueous solutions, ppm ≈ mg/L."""
    if mg_per_L < 0:
        raise ValueError("mg/L must be non-negative")
    steps = f"Aqueous shortcut: ppm ≈ mg/L → {mg_per_L:.6g} ppm"
    return mg_per_L, steps


def mix_solutions(volumes_L: List[float], molarities_M: List[float]) -> Tuple[float, str]:
    if len(volumes_L) != len(molarities_M) or len(volumes_L) == 0:
        raise ValueError("Provide equal-length non-empty lists")
    if any(v < 0 for v in volumes_L):
        raise ValueError("Volumes must be non-negative")
    Vtot = sum(volumes_L)
    if Vtot <= 0:
        raise ValueError("Total volume must be positive")
    n_total = sum(V * M for V, M in zip(volumes_L, molarities_M))
    M_final = n_total / Vtot
    steps = (
        "Mixing same-solute solutions: M_f = (Σ n_i) / (Σ V_i)\n"
        f"Σn = Σ(M_i V_i) = {n_total:.6g} mol, V_tot = {Vtot:.6g} L → M_f = {M_final:.6g} M"
    )
    return M_final, steps


def mole_fraction_from_masses(formula_A: str, mA_g: float, formula_B: str, mB_g: float) -> Tuple[float, float, str]:
    if mA_g < 0 or mB_g < 0:
        raise ValueError("Masses must be non-negative")
    MW_A = calculate_molar_mass_from_formula(formula_A)
    MW_B = calculate_molar_mass_from_formula(formula_B)
    nA = mA_g / MW_A
    nB = mB_g / MW_B
    denom = nA + nB
    if denom <= 0:
        raise ValueError("Total moles must be positive")
    xA = nA / denom
    xB = nB / denom
    steps = (
        f"Moles: n_A = {mA_g}/{MW_A:.5g} = {nA:.6g}; n_B = {mB_g}/{MW_B:.5g} = {nB:.6g}\n"
        f"x_A = n_A/(n_A+n_B) = {xA:.6g}, x_B = {xB:.6g}"
    )
    return xA, xB, steps


def mole_fraction_from_moles(nA: float, nB: float) -> Tuple[float, float, str]:
    if nA < 0 or nB < 0:
        raise ValueError("Moles must be non-negative")
    denom = nA + nB
    if denom <= 0:
        raise ValueError("Total moles must be positive")
    xA = nA / denom
    xB = nB / denom
    steps = f"x_A = {nA}/({nA}+{nB}) = {xA:.6g}; x_B = {xB:.6g}"
    return xA, xB, steps


def ionic_strength(species: List[Tuple[str, float, int]]) -> Tuple[float, str]:
    """I = 0.5 Σ c_i z_i^2; species entries are (name, c_M, z)."""
    total = 0.0
    parts = []
    for name, c, z in species:
        if c < 0:
            raise ValueError("Concentrations must be non-negative")
        term = c * (z ** 2)
        total += term
        parts.append(f"{name}: {c}×{z}^2 = {term:.6g}")
    I = 0.5 * total
    steps = "Ionic strength: I = 0.5 Σ c_i z_i^2\n" + "\n".join(parts) + f"\nI = 0.5×{total:.6g} = {I:.6g}"
    return I, steps


