import math
from calculators.electrochemistry import (
    calculate_standard_cell_with_steps,
    calculate_nernst_with_steps,
    calculate_deltaG_from_E_with_steps,
    calculate_K_from_E0_with_steps,
    calculate_daniell_Q,
    calculate_e_cell_from_gibbs_with_steps,
    calculate_e_cell_from_half_potentials_with_steps,
    calculate_unknown_potential_from_e_cell_with_steps,
    calculate_k_from_e_cell_with_steps,
    calculate_gibbs_from_k_with_steps,
    convert_gibbs_to_j_units,
    convert_temperature_to_k_units,
    validate_k_value,
    match_candidate_potential_value,
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


def test_e_cell_from_gibbs():
    res, steps, meta = calculate_e_cell_from_gibbs_with_steps(-356.9, "kJ/mol", 2)
    assert abs(res["E_cell_V"] - 1.849) < 1e-3


def test_find_anode_oxidation_potential_from_e_cell():
    res, steps, meta = calculate_unknown_potential_from_e_cell_with_steps(
        1.849,
        1.087,
        "cathode",
        "red",
        "anode",
        "ox",
    )
    assert abs(res["unknown_V"] - 0.762) < 1e-3


def test_candidate_match():
    candidates = [
        {"label": "Zn", "value": 0.762, "type": "ox"},
        {"label": "Pt", "value": -1.180, "type": "ox"},
        {"label": "Pb", "value": 0.126, "type": "ox"},
        {"label": "Ca", "value": 2.868, "type": "ox"},
        {"label": "Ni", "value": 0.257, "type": "ox"},
    ]
    match = match_candidate_potential_value(0.762, "ox", candidates, tolerance=0.005)
    assert match["label"] == "Zn"


def test_convert_gibbs_kj_to_j():
    assert convert_gibbs_to_j_units(-356.9, "kJ/mol") == -356900.0


def test_convert_temperature_c_to_k():
    assert abs(convert_temperature_to_k_units(25, "°C") - 298.15) < 1e-6


def test_k_from_e_cell():
    res, steps, meta = calculate_k_from_e_cell_with_steps(1, 0.585, 298.15, "K")
    expected = math.exp((1 * 96485.33212 * 0.585) / (8.314462618 * 298.15))
    assert abs(res["K"] - expected) / expected < 1e-6


def test_gibbs_from_k_positive():
    res, steps, meta = calculate_gibbs_from_k_with_steps(1.8e-10, 298.15, "K")
    assert res["dG_J"] > 0


def test_invalid_k_raises():
    try:
        validate_k_value(0)
    except ValueError:
        assert True
    else:
        assert False


def test_both_reduction_potentials():
    res, steps, meta = calculate_e_cell_from_half_potentials_with_steps(
        1.087,
        "red",
        -0.762,
        "red",
    )
    assert abs(res["E_cell_V"] - 1.849) < 1e-3


def test_reduction_and_oxidation_potentials():
    res, steps, meta = calculate_e_cell_from_half_potentials_with_steps(
        1.087,
        "red",
        0.762,
        "ox",
    )
    assert abs(res["E_cell_V"] - 1.849) < 1e-3


