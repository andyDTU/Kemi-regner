import pytest

from core.osmotic_pressure import (
    OsmoticPressureInput,
    solve_osmotic_pressure,
    validate_osmotic_pressure_inputs,
)
from calculators.kogepunkt_frysepunkt import _parse_required_float


R_ATM = 0.082057366080960
R_PA = 8.31446261815324


def _mass_to_g(value, unit):
    if unit == "g":
        return value
    if unit == "kg":
        return value * 1000.0
    if unit == "mg":
        return value / 1000.0
    raise AssertionError(unit)


def _molar_mass_to_g_per_mol(value, unit):
    if unit == "g/mol":
        return value
    if unit == "kg/mol":
        return value * 1000.0
    raise AssertionError(unit)


def _volume_to_l(value, unit):
    if unit == "L":
        return value
    if unit == "mL":
        return value / 1000.0
    if unit == "m³":
        return value * 1000.0
    raise AssertionError(unit)


def _temperature_to_k(value, unit):
    if unit == "K":
        return value
    if unit == "°C":
        return value + 273.15
    if unit == "°F":
        return (value - 32.0) * 5.0 / 9.0 + 273.15
    raise AssertionError(unit)


def _expected_osmotic_pressure(
    mass_solute_value,
    mass_solute_unit,
    molar_mass_value,
    molar_mass_unit,
    volume_value,
    volume_unit,
    temperature_value,
    temperature_unit,
    vant_hoff_i,
    pressure_unit,
):
    mass_g = _mass_to_g(mass_solute_value, mass_solute_unit)
    molar_mass_g_per_mol = _molar_mass_to_g_per_mol(molar_mass_value, molar_mass_unit)
    volume_l = _volume_to_l(volume_value, volume_unit)
    temperature_k = _temperature_to_k(temperature_value, temperature_unit)

    moles = mass_g / molar_mass_g_per_mol
    molarity = moles / volume_l

    gas_constant = R_ATM if pressure_unit == "atm" else R_PA
    if pressure_unit == "atm":
        return vant_hoff_i * molarity * gas_constant * temperature_k

    volume_m3 = volume_l / 1000.0
    molarity_m3 = moles / volume_m3
    return vant_hoff_i * molarity_m3 * gas_constant * temperature_k


def test_na_cl_example_in_atm():
    data = OsmoticPressureInput(
        mass_solute_g=10.0,
        mass_solute_unit="g",
        molar_mass_g_per_mol=58.44,
        molar_mass_unit="g/mol",
        volume_solution_l=1.0,
        volume_unit="L",
        temperature_c=25.0,
        temperature_unit="°C",
        vant_hoff_i=2.0,
        pressure_unit="atm",
    )
    result = solve_osmotic_pressure(data)

    assert result.n_mol == pytest.approx(0.171, rel=5e-3)
    assert result.molarity_mol_per_l == pytest.approx(0.171, rel=5e-3)
    assert result.temperature_k == pytest.approx(298.15, rel=1e-4)
    assert result.osmotic_pressure == pytest.approx(8.37, rel=2e-2)


def test_na_cl_example_in_pa():
    data = OsmoticPressureInput(
        mass_solute_g=10.0,
        mass_solute_unit="g",
        molar_mass_g_per_mol=58.44,
        molar_mass_unit="g/mol",
        volume_solution_l=1.0,
        volume_unit="L",
        temperature_c=25.0,
        temperature_unit="°C",
        vant_hoff_i=2.0,
        pressure_unit="Pa",
    )
    result = solve_osmotic_pressure(data)

    assert result.osmotic_pressure == pytest.approx(8.5e5, rel=5e-2)
    assert any("m³" in step for step in result.steps)
    assert any("8.314" in step for step in result.steps)


def test_validation_constraints():
    data = OsmoticPressureInput(
        mass_solute_g=0.0,
        mass_solute_unit="g",
        molar_mass_g_per_mol=-1.0,
        molar_mass_unit="g/mol",
        volume_solution_l=0.0,
        volume_unit="L",
        temperature_c=-10.0,
        temperature_unit="°C",
        vant_hoff_i=0.0,
        pressure_unit="atm",
    )
    errors = validate_osmotic_pressure_inputs(data)
    assert len(errors) == 4
    assert any("Volumen" in error for error in errors)


def test_solver_raises_for_invalid_input():
    data = OsmoticPressureInput(
        mass_solute_g=10.0,
        mass_solute_unit="g",
        molar_mass_g_per_mol=58.44,
        molar_mass_unit="g/mol",
        volume_solution_l=0.0,
        volume_unit="L",
        temperature_c=25.0,
        temperature_unit="°C",
        vant_hoff_i=2.0,
        pressure_unit="atm",
    )
    with pytest.raises(ValueError, match="Volumen af opløsningen"):
        solve_osmotic_pressure(data)


def test_steps_separate_all_subcalculations():
    data = OsmoticPressureInput(
        mass_solute_g=5.0,
        mass_solute_unit="g",
        molar_mass_g_per_mol=58.44,
        molar_mass_unit="g/mol",
        volume_solution_l=2.0,
        volume_unit="L",
        temperature_c=-5.0,
        temperature_unit="°C",
        vant_hoff_i=1.0,
        pressure_unit="atm",
    )
    result = solve_osmotic_pressure(data)

    assert any("n = masse / molarmasse" in step for step in result.steps)
    assert any("M = n / volumen" in step for step in result.steps)
    assert any("T(K) = °C + 273.15" in step for step in result.steps)
    assert any("π = i · M · R · T" in step for step in result.steps)


@pytest.mark.parametrize(
    (
        "mass_solute_value",
        "mass_solute_unit",
        "molar_mass_value",
        "molar_mass_unit",
        "volume_value",
        "volume_unit",
        "temperature_value",
        "temperature_unit",
        "vant_hoff_i",
        "pressure_unit",
    ),
    [
        (10.0, "g", 58.44, "g/mol", 1.0, "L", 25.0, "°C", 2.0, "atm"),
        (0.01, "kg", 0.05844, "kg/mol", 1000.0, "mL", 298.15, "K", 2.0, "atm"),
        (10000.0, "mg", 58.44, "g/mol", 0.001, "m³", 77.0, "°F", 2.0, "Pa"),
        (5.0, "g", 58.44, "g/mol", 500.0, "mL", 25.0, "°C", 2.0, "atm"),
        (5000.0, "mg", 0.05844, "kg/mol", 0.5, "L", 298.15, "K", 2.0, "Pa"),
        (20.0, "g", 180.156, "g/mol", 2.0, "L", 20.0, "°C", 1.0, "atm"),
        (0.02, "kg", 0.180156, "kg/mol", 2000.0, "mL", 68.0, "°F", 1.0, "Pa"),
        (2.5, "g", 250.0, "g/mol", 250.0, "mL", 300.0, "K", 1.0, "atm"),
        (2500.0, "mg", 0.25, "kg/mol", 0.00025, "m³", 26.85, "°C", 1.0, "Pa"),
        (15.0, "g", 75.0, "g/mol", 1.5, "L", 10.0, "°C", 3.0, "atm"),
        (0.015, "kg", 0.075, "kg/mol", 1500.0, "mL", 283.15, "K", 3.0, "Pa"),
        (7.5, "g", 50.0, "g/mol", 750.0, "mL", 25.0, "°C", 1.5, "atm"),
        (7500.0, "mg", 0.05, "kg/mol", 0.75, "L", 298.15, "K", 1.5, "Pa"),
        (12.0, "g", 60.0, "g/mol", 3.0, "L", -5.0, "°C", 1.0, "atm"),
        (0.012, "kg", 0.060, "kg/mol", 3000.0, "mL", 268.15, "K", 1.0, "Pa"),
    ],
)
def test_solver_with_unit_conversions(
    mass_solute_value,
    mass_solute_unit,
    molar_mass_value,
    molar_mass_unit,
    volume_value,
    volume_unit,
    temperature_value,
    temperature_unit,
    vant_hoff_i,
    pressure_unit,
):
    data = OsmoticPressureInput(
        mass_solute_g=mass_solute_value,
        mass_solute_unit=mass_solute_unit,
        molar_mass_g_per_mol=molar_mass_value,
        molar_mass_unit=molar_mass_unit,
        volume_solution_l=volume_value,
        volume_unit=volume_unit,
        temperature_c=temperature_value,
        temperature_unit=temperature_unit,
        vant_hoff_i=vant_hoff_i,
        pressure_unit=pressure_unit,
    )
    result = solve_osmotic_pressure(data)

    expected = _expected_osmotic_pressure(
        mass_solute_value,
        mass_solute_unit,
        molar_mass_value,
        molar_mass_unit,
        volume_value,
        volume_unit,
        temperature_value,
        temperature_unit,
        vant_hoff_i,
        pressure_unit,
    )
    assert result.osmotic_pressure == pytest.approx(expected, rel=1e-4, abs=1e-4)


def test_ui_parse_helper_rejects_empty_and_text_values():
    with pytest.raises(ValueError, match="mangler"):
        _parse_required_float("", "Felt")
    with pytest.raises(ValueError, match="gyldigt tal"):
        _parse_required_float("abc", "Felt")
