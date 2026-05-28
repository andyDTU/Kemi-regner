"""
Kinetics calculators wrapping core functions with step strings.
"""

from typing import Dict, List, Tuple, Optional
from core.kinetics import (
    integrated_rate_law,
    half_life,
    determine_order_and_k_two_point,
    arrhenius_forward_k2,
    arrhenius_two_point_Ea,
)


def calculate_integrated_rate_with_steps(order: int, C0: Optional[float] = None, Ct: Optional[float] = None,
                                         k: Optional[float] = None, t: Optional[float] = None):
    return integrated_rate_law(order, C0=C0, Ct=Ct, k=k, t=t)


def calculate_half_life_with_steps(order: int, C0: Optional[float], k: float):
    return half_life(order, C0, k)


def calculate_determine_order_k_with_steps(C0: float, t1: float, C1: float, t2: float, C2: float, candidate_orders=None):
    return determine_order_and_k_two_point(C0, t1, C1, t2, C2, candidate_orders)


def calculate_arrhenius_forward_with_steps(k1: float, T1_K: float, T2_K: float, Ea_kJ_per_mol: float):
    return arrhenius_forward_k2(k1, T1_K, T2_K, Ea_kJ_per_mol)


def calculate_arrhenius_two_point_Ea_with_steps(k1: float, T1_K: float, k2: float, T2_K: float):
    return arrhenius_two_point_Ea(k1, T1_K, k2, T2_K)


