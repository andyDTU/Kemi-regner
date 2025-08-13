import math
import pytest
from calculators.solutions import (
    solve_molarity,
    grams_for_solution,
    volume_stock_for_dilution,
    solve_molality,
    percent_w_w,
    ppm_general,
    ppm_aqueous_from_mg_per_L,
    mix_solutions,
    mole_fraction_from_masses,
    ionic_strength,
)


def test_molarity_basic():
    res, steps = solve_molarity(M=None, n_mol=0.250, V_L=0.500)
    assert abs(res['M'] - 0.5) < 1e-6


def test_grams_to_prepare_solid():
    grams, steps = grams_for_solution("NaCl", 0.1000, 1.00)
    assert abs(grams - 5.844) < 0.005


def test_molality_from_masses():
    # 10.0 g NaCl; 100.0 g H2O → m = n/kg_solvent
    # n(NaCl) = 10/58.44 = 0.1711 mol; kg_solvent = 0.100 kg; m ≈ 1.711
    n = 0.0  # not used directly
    res, steps = solve_molality(m=None, n_mol=10.0/58.44, m_solvent_kg=0.100)
    assert abs(res['m'] - 1.7112) < 1e-3


def test_percent_ww():
    pct, steps = percent_w_w(m_solute_g=10.0, m_total_g=110.0, unknown="%")
    assert abs(pct - 9.0909) < 1e-4


def test_ppm_aqueous():
    # 0.0500 g in 2.00 L water; using aqueous shortcut via mg/L ≈ ppm
    mg_per_L = (0.0500 * 1000.0) / 2.00
    ppm, steps = ppm_aqueous_from_mg_per_L(mg_per_L)
    assert abs(ppm - 25.0) < 0.05


def test_mixing_same_solute():
    # 100.0 mL of 1.000 M with 400.0 mL of 0.200 M -> Mf = (0.1*1 + 0.4*0.2)/0.5 = 0.36
    Mf, steps = mix_solutions([0.100, 0.400], [1.000, 0.200])
    assert abs(Mf - 0.3600) < 1e-4


def test_mole_fraction_from_masses():
    # 10.0 g NaCl + 100.0 g H2O
    xA, xB, steps = mole_fraction_from_masses("NaCl", 10.0, "H2O", 100.0)
    assert abs(xA - 0.02990) < 5e-5


def test_ionic_strength():
    I, steps = ionic_strength([("Na+", 0.200, +1), ("SO4^2-", 0.100, -2)])
    assert abs(I - 0.3000) < 1e-6


def test_stock_dilution():
    V1, steps = volume_stock_for_dilution(M_stock=2.00, M_target=0.500, V_final_L=0.250)
    assert abs(V1 - 0.06250) < 1e-6


def test_input_guard_negative_mass():
    with pytest.raises(ValueError):
        _ = mole_fraction_from_masses("NaCl", -1.0, "H2O", 10.0)


