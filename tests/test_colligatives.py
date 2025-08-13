import pytest
from calculators.colligatives import (
    freezing_boiling_with_steps,
    osmotic_pressure_with_steps,
    raoult_nonvolatile_with_steps,
)


def test_freezing_point_depression_water_nacl():
    # m = 1.0 molal NaCl → i = 2, ΔTf = 2 × 1.86 × 1.0 = 3.72 °C, Tf = -3.72 °C
    res, steps, meta = freezing_boiling_with_steps(
        solvent="water",
        moles_solute=1.0,  # per 1 kg solvent
        mass_solvent_g=1000.0,
        i=2.0,
    )
    assert abs(res['deltaTf_C'] - 3.72) < 0.05
    assert abs(res['Tf_C'] - (-3.72)) < 0.05


def test_boiling_point_elevation_water_nonelectrolyte():
    # m = 0.5, i = 1 → ΔTb = 0.512 × 0.5 = 0.256 °C → Tb = 100.256 °C
    res, steps, meta = freezing_boiling_with_steps(
        solvent="water",
        moles_solute=0.5,
        mass_solvent_g=1000.0,
        i=1.0,
    )
    assert abs(res['deltaTb_C'] - 0.256) < 0.01
    assert abs(res['Tb_C'] - 100.256) < 0.01


def test_osmotic_pressure_sucrose():
    # 0.100 M at 298.15 K, i=1 → π ≈ 2.447 atm
    pi_atm, steps, meta = osmotic_pressure_with_steps(
        molarity_M=0.100,
        temperature_K=298.15,
        i=1.0,
    )
    assert abs(pi_atm - 2.447) < 0.02


def test_raoult_nonvolatile():
    # x_solvent=0.900, P*_solvent=100 kPa → 90.0 kPa
    P, steps, meta = raoult_nonvolatile_with_steps(
        x_solvent=0.900,
        P_star_solvent=100.0,
    )
    assert abs(P - 90.0) < 0.1


