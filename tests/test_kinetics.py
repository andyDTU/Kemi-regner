import math
from calculators.kinetics import (
    calculate_integrated_rate_with_steps,
    calculate_half_life_with_steps,
    calculate_arrhenius_forward_with_steps,
    calculate_arrhenius_two_point_Ea_with_steps,
)


def test_first_order_decay_ct():
    # C0=0.100 M, k=0.350 s^-1, t=10.0 s -> Ct ≈ 0.00302 M
    val, steps, meta = calculate_integrated_rate_with_steps(
        order=1, C0=0.100, k=0.350, t=10.0, Ct=None
    )
    assert abs(val - 0.00302) < 2e-5


def test_first_order_half_life():
    # k=0.693 s^-1 -> t1/2 ≈ 1.000 s
    t12, steps, meta = calculate_half_life_with_steps(order=1, C0=None, k=0.693)
    assert abs(t12 - 1.000) < 1e-3


def test_second_order_ct():
    # C0=0.100 M, k=0.250 M^-1 s^-1, t=20.0 s -> Ct ≈ 0.0666667 M
    val, steps, meta = calculate_integrated_rate_with_steps(
        order=2, C0=0.100, k=0.250, t=20.0, Ct=None
    )
    assert abs(val - (2.0/30.0)) < 1e-5


def test_arrhenius_forward():
    # k1=1.00e-3 s^-1 at 298.15 K, Ea=50.0 kJ/mol, T2=308.15 K -> k2 ≈ 1.9243e-3 s^-1
    k2, steps, meta = calculate_arrhenius_forward_with_steps(1.00e-3, 298.15, 308.15, 50.0)
    assert abs(k2 - 1.9243e-3) < 5e-6


def test_arrhenius_two_point_Ea():
    # k1=1.00e-3 at 298.15 K; k2=3.00e-3 at 308.15 K -> Ea ≈ 83.92 kJ/mol
    Ea_kJ, steps, meta = calculate_arrhenius_two_point_Ea_with_steps(1.00e-3, 298.15, 3.00e-3, 308.15)
    assert abs(Ea_kJ - 83.92) < 0.1


