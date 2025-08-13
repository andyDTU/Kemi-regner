import math
from calculators.electrochemistry import (
    calculate_standard_cell_with_steps,
    calculate_nernst_with_steps,
    calculate_deltaG_from_E_with_steps,
    calculate_K_from_E0_with_steps,
    calculate_daniell_Q,
)


def test_daniell_standard_cell():
    # Cathode: Cu2+/Cu (0.34 V); Anode: Zn2+/Zn (-0.76 V) → E° = 1.10 V, n=2
    res, steps, meta = calculate_standard_cell_with_steps(
        "Cu2+ + 2e- -> Cu(s)",
        "Zn2+ + 2e- -> Zn(s)",
    )
    assert abs(res['E0_cell_V'] - 1.10) < 1e-3
    assert res['n'] == 2


def test_nernst_daniell_298K():
    # [Zn2+]=0.10 M, [Cu2+]=1.00 M at 298.15 K
    Q = calculate_daniell_Q(0.10, 1.00)
    E, steps, meta = calculate_nernst_with_steps(1.10, n=2, T_K=298.15, Q=Q)
    assert abs(E - 1.1296) < 5e-4


def test_deltaG_from_E0():
    dG_kJ, steps, meta = calculate_deltaG_from_E_with_steps(n=2, E_V=1.10)
    assert abs(dG_kJ - (-212.27)) < 0.2


def test_K_from_E0():
    K, log10K, steps, meta = calculate_K_from_E0_with_steps(n=2, E0_V=1.10, T_K=298.15)
    assert abs(log10K - 37.181) < 0.02


