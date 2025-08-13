import pytest
from calculators.thermochemistry import (
    calculate_calorimetry_with_steps,
    calculate_heating_curve_water_with_steps,
    calculate_reaction_enthalpy_from_formation_with_steps,
    calculate_clausius_clapeyron_with_steps,
)


def test_calorimetry_water_liquid():
    # 100 g water, c=4.184 J/g/K, ΔT = 25 K → q = 10460 J = 10.46 kJ
    q_kJ, steps, meta = calculate_calorimetry_with_steps(
        mass_g=100.0,
        delta_T_K=25.0,
        preset="water_liquid",
        output_unit="kJ",
    )
    assert abs(q_kJ - 10.46) < 0.02


def test_heating_curve_water_total_q():
    # 10 g from -10 °C to 110 °C
    # Expected total ≈ 30.5 kJ within 0.3 kJ
    q_kJ, steps, meta = calculate_heating_curve_water_with_steps(
        mass_g=10.0,
        T_initial_C=-10.0,
        T_final_C=110.0,
    )
    assert abs(q_kJ - 30.5) < 0.3


def test_reaction_enthalpy_from_formation():
    # CH4 + 2 O2 -> CO2 + 2 H2O(l) → ≈ -890.4 kJ/mol
    dh_kJ, steps, meta = calculate_reaction_enthalpy_from_formation_with_steps(
        "CH4 + 2 O2 -> CO2 + 2 H2O(l)"
    )
    assert abs(dh_kJ + 890.4) < 0.5


def test_clausius_clapeyron_water():
    # ΔHvap=40.65 kJ/mol, P1=1 atm at 373.15 K; T2=353.15 K → P2 ≈ 0.473 atm
    P2, steps, meta = calculate_clausius_clapeyron_with_steps(
        P1_atm=1.0,
        T1_K=373.15,
        T2_K=353.15,
        deltaHvap_kJ_per_mol=40.65,
    )
    assert abs(P2 - 0.473) < 0.005


