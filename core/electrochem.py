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


