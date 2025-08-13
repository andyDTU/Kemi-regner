"""
Core kinetics calculations with unit-safe helpers and step strings.
"""

from typing import Dict, List, Tuple, Optional
import math
from core.thermo import load_constants


def _fmt(v: float, unit: str = "", sig: int = 4) -> str:
    if v == 0:
        return f"0 {unit}".strip()
    abs_v = abs(v)
    if abs_v >= 1e4 or abs_v < 1e-3:
        return f"{v:.{sig-1}e} {unit}".strip()
    return f"{v:.{sig}g} {unit}".strip()


def integrated_rate_law(order: int,
                        C0: Optional[float] = None,
                        Ct: Optional[float] = None,
                        k: Optional[float] = None,
                        t: Optional[float] = None,
                        ) -> Tuple[float, List[str], Dict[str, float]]:
    """
    Solve for one unknown among C0, Ct, k, t for zero/first/second order.
    Units: concentration in M, time in s, k in (M/s, 1/s, 1/(M·s)) for 0,1,2 order respectively.
    Returns (value, steps, metadata). The returned value corresponds to the missing variable.
    """
    vars_provided = sum(x is not None for x in (C0, Ct, k, t))
    if vars_provided != 3:
        raise ValueError("Exactly three of (C0, Ct, k, t) must be provided")
    if C0 is not None and C0 < 0:
        raise ValueError("C0 must be non-negative")
    if Ct is not None and Ct < 0:
        raise ValueError("Ct must be non-negative")
    if k is not None and k <= 0:
        raise ValueError("k must be positive")
    if t is not None and t < 0:
        raise ValueError("t must be non-negative")

    steps: List[str] = []
    if order == 0:
        # Ct = C0 - k t
        steps.append("Zero-order: Ct = C0 − k t")
        if Ct is None:
            Ct_val = C0 - k * t
            steps.append(f"Ct = {C0} − {k}×{t} = {Ct_val}")
            return Ct_val, steps, {"order": 0}
        if C0 is None:
            C0_val = Ct + k * t
            steps.append(f"C0 = Ct + k t = {Ct} + {k}×{t} = {C0_val}")
            return C0_val, steps, {"order": 0}
        if k is None:
            k_val = (C0 - Ct) / t
            steps.append(f"k = (C0 − Ct)/t = ({C0} − {Ct})/{t} = {k_val}")
            return k_val, steps, {"order": 0}
        # t is None
        t_val = (C0 - Ct) / k
        steps.append(f"t = (C0 − Ct)/k = ({C0} − {Ct})/{k} = {t_val}")
        return t_val, steps, {"order": 0}

    if order == 1:
        # Ct = C0 exp(−k t)
        steps.append("First-order: Ct = C0 e^(−k t)")
        if Ct is None:
            Ct_val = C0 * math.exp(-k * t)
            steps.append(f"Ct = {C0}·e^(−{k}×{t}) = {Ct_val}")
            return Ct_val, steps, {"order": 1}
        if C0 is None:
            if Ct <= 0:
                raise ValueError("Ct must be positive for first-order back-calculation")
            C0_val = Ct * math.exp(k * t)
            steps.append(f"C0 = Ct·e^(k t) = {Ct}·e^({k}×{t}) = {C0_val}")
            return C0_val, steps, {"order": 1}
        if k is None:
            if Ct <= 0 or C0 <= 0:
                raise ValueError("C0 and Ct must be positive for first-order k")
            k_val = (math.log(C0) - math.log(Ct)) / t
            steps.append(f"k = (ln C0 − ln Ct)/t = (ln {C0} − ln {Ct})/{t} = {k_val}")
            return k_val, steps, {"order": 1}
        # t is None
        if Ct <= 0 or C0 <= 0:
            raise ValueError("C0 and Ct must be positive for first-order t")
        t_val = (math.log(C0) - math.log(Ct)) / k
        steps.append(f"t = (ln C0 − ln Ct)/k = (ln {C0} − ln {Ct})/{k} = {t_val}")
        return t_val, steps, {"order": 1}

    if order == 2:
        # 1/Ct = 1/C0 + k t
        steps.append("Second-order: 1/Ct = 1/C0 + k t")
        if Ct is None:
            denom = (1.0 / C0) + k * t
            Ct_val = 1.0 / denom
            steps.append(f"1/Ct = 1/{C0} + {k}×{t} → Ct = {Ct_val}")
            return Ct_val, steps, {"order": 2}
        if C0 is None:
            denom = (1.0 / Ct) - k * t
            if denom <= 0:
                raise ValueError("Invalid inputs: computed 1/C0 ≤ 0")
            C0_val = 1.0 / denom
            steps.append(f"1/C0 = 1/{Ct} − {k}×{t} → C0 = {C0_val}")
            return C0_val, steps, {"order": 2}
        if k is None:
            k_val = (1.0 / Ct - 1.0 / C0) / t
            steps.append(f"k = (1/Ct − 1/C0)/t = (1/{Ct} − 1/{C0})/{t} = {k_val}")
            return k_val, steps, {"order": 2}
        # t is None
        t_val = (1.0 / Ct - 1.0 / C0) / k
        steps.append(f"t = (1/Ct − 1/C0)/k = (1/{Ct} − 1/{C0})/{k} = {t_val}")
        return t_val, steps, {"order": 2}

    raise ValueError("Order must be 0, 1, or 2")


def half_life(order: int, C0: Optional[float], k: float) -> Tuple[float, List[str], Dict[str, float]]:
    """Half-life for the specified order."""
    steps: List[str] = []
    if k <= 0:
        raise ValueError("k must be positive")
    if order == 0:
        if C0 is None or C0 <= 0:
            raise ValueError("C0 must be positive for zero-order half-life")
        t_half = C0 / (2.0 * k)
        steps.append("Zero-order: t_1/2 = C0/(2k)")
        return t_half, steps, {"order": 0}
    if order == 1:
        t_half = math.log(2.0) / k
        steps.append("First-order: t_1/2 = ln 2 / k")
        return t_half, steps, {"order": 1}
    if order == 2:
        if C0 is None or C0 <= 0:
            raise ValueError("C0 must be positive for second-order half-life")
        t_half = 1.0 / (k * C0)
        steps.append("Second-order: t_1/2 = 1/(k C0)")
        return t_half, steps, {"order": 2}
    raise ValueError("Order must be 0, 1, or 2")


def determine_order_and_k_two_point(t1: float, C1: float, t2: float, C2: float,
                                    candidate_orders: Optional[List[int]] = None) -> Tuple[Dict, List[str], Dict]:
    """
    Determine reaction order (0,1,2) and k from two points by minimizing relative error.
    Returns (best_result, steps, metadata). best_result has keys: order, k, residuals.
    """
    if candidate_orders is None:
        candidate_orders = [0, 1, 2]
    if any(x < 0 for x in (t1, t2)):
        raise ValueError("Times must be non-negative")
    if any(x <= 0 for x in (C1, C2)):
        raise ValueError("Concentrations must be positive")

    steps: List[str] = ["Determine order & k from two points"]
    residuals = []
    for order in candidate_orders:
        if order == 0:
            k_val = (C1 - C2) / (t2 - t1) if t2 != t1 else float('inf')
            C2_pred = C1 - k_val * (t2 - t1)
        elif order == 1:
            k_val = (math.log(C1) - math.log(C2)) / (t2 - t1) if t2 != t1 else float('inf')
            C2_pred = C1 * math.exp(-k_val * (t2 - t1))
        else:
            # 2nd order
            k_val = (1.0 / C2 - 1.0 / C1) / (t2 - t1) if t2 != t1 else float('inf')
            C2_pred = C1 / (1.0 + k_val * C1 * (t2 - t1))
        rel_err = abs(C2_pred - C2) / C2
        steps.append(f"Order {order}: k = {k_val:.6g}, C2_pred = {C2_pred:.6g}, rel_err = {rel_err:.3e}")
        residuals.append((order, k_val, rel_err))

    residuals.sort(key=lambda x: x[2])
    best_order, best_k, best_err = residuals[0]
    result = {"order": best_order, "k": best_k, "residual": best_err, "residuals": residuals}
    return result, steps, {}


def arrhenius_forward_k2(k1: float, T1_K: float, T2_K: float, Ea_kJ_per_mol: float) -> Tuple[float, List[str], Dict]:
    """Compute k2 given (k1, T1, T2, Ea)."""
    if any(x <= 0 for x in (k1, T1_K, T2_K)):
        raise ValueError("k1 and temperatures must be positive")
    R = load_constants()["R_J_per_molK"]
    Ea_J = Ea_kJ_per_mol * 1000.0
    ln_k2_over_k1 = -(Ea_J / R) * (1.0 / T2_K - 1.0 / T1_K)
    k2 = k1 * math.exp(ln_k2_over_k1)
    steps = [
        "Arrhenius: ln(k2/k1) = −Ea/R · (1/T2 − 1/T1)",
        f"ln(k2/k1) = −{Ea_J:.4g}/{R:.6g} · (1/{T2_K} − 1/{T1_K}) = {ln_k2_over_k1:.6g}",
        f"k2 = {k1} · e^({ln_k2_over_k1:.6g}) = {k2:.6g}",
    ]
    return k2, steps, {"Ea_kJ_per_mol": Ea_kJ_per_mol}


def arrhenius_two_point_Ea(k1: float, T1_K: float, k2: float, T2_K: float) -> Tuple[float, List[str], Dict]:
    """Compute Ea (kJ/mol) from two rate constants and temperatures."""
    if any(x <= 0 for x in (k1, k2, T1_K, T2_K)):
        raise ValueError("k and T must be positive")
    R = load_constants()["R_J_per_molK"]
    Ea_J = R * math.log(k1 / k2) / (1.0 / T2_K - 1.0 / T1_K)
    Ea_kJ = Ea_J / 1000.0
    steps = [
        "Arrhenius two-point: ln(k1/k2) = Ea/R · (1/T2 − 1/T1)",
        f"Ea = R · ln(k1/k2) / (1/T2 − 1/T1) = {R:.6g} · ln({k1}/{k2}) / (1/{T2_K} − 1/{T1_K}) = {Ea_kJ:.5g} kJ/mol",
    ]
    return Ea_kJ, steps, {}



