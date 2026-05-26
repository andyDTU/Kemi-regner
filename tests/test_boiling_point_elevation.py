import pytest

from calculators.kogepunkt_frysepunkt import _parse_required_float
from core.boiling_point_elevation import (
    BoilingPointElevationInput,
    solve_boiling_point_elevation,
    validate_boiling_point_inputs,
)


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


def _mass_to_kg(value, unit):
    if unit == "kg":
        return value
    if unit == "g":
        return value / 1000.0
    if unit == "mg":
        return value / 1_000_000.0
    raise AssertionError(unit)


def _temperature_to_c(value, unit):
    if unit == "°C":
        return value
    if unit == "K":
        return value - 273.15
    if unit == "°F":
        return (value - 32.0) * 5.0 / 9.0
    raise AssertionError(unit)


def _kb_to_c_kg_per_mol(value, unit):
    if unit in ("°C·kg/mol", "K·kg/mol"):
        return value
    raise AssertionError(unit)


def _expected_boiling_point(
    mass_solute_value,
    mass_solute_unit,
    molar_mass_value,
    molar_mass_unit,
    mass_solvent_value,
    mass_solvent_unit,
    vant_hoff_i,
    kb_value,
    kb_unit,
    start_boiling_value,
    start_boiling_unit,
):
    mass_g = _mass_to_g(mass_solute_value, mass_solute_unit)
    molar_mass_g_per_mol = _molar_mass_to_g_per_mol(molar_mass_value, molar_mass_unit)
    mass_solvent_kg = _mass_to_kg(mass_solvent_value, mass_solvent_unit)
    kb_c_kg_per_mol = _kb_to_c_kg_per_mol(kb_value, kb_unit)
    start_c = _temperature_to_c(start_boiling_value, start_boiling_unit)

    n_mol = mass_g / molar_mass_g_per_mol
    molality = n_mol / mass_solvent_kg
    delta_tb = vant_hoff_i * kb_c_kg_per_mol * molality
    return n_mol, molality, delta_tb, start_c + delta_tb


def test_non_electrolyte_in_water_example():
    data = BoilingPointElevationInput(
        mass_solute_g=60.0,
        mass_solute_unit="g",
        molar_mass_g_per_mol=180.156,
        molar_mass_unit="g/mol",
        mass_solvent_kg=0.200,
        mass_solvent_unit="kg",
        vant_hoff_i=1.0,
        kb_c_kg_per_mol=0.512,
        kb_unit="°C·kg/mol",
        start_boiling_point_c=100.0,
        start_boiling_point_unit="°C",
    )

    result = solve_boiling_point_elevation(data)

    assert result.n_mol == pytest.approx(0.3330, rel=5e-3)
    assert result.molality_mol_per_kg == pytest.approx(1.665, rel=5e-3)
    assert result.delta_tb_c == pytest.approx(0.85, rel=2e-2)
    assert result.new_boiling_point_c == pytest.approx(100.85, rel=2e-2)


def test_simple_ionic_substance_example():
    data = BoilingPointElevationInput(
        mass_solute_g=5.84,
        mass_solute_unit="g",
        molar_mass_g_per_mol=58.44,
        molar_mass_unit="g/mol",
        mass_solvent_kg=0.500,
        mass_solvent_unit="kg",
        vant_hoff_i=2.0,
        kb_c_kg_per_mol=0.512,
        kb_unit="°C·kg/mol",
        start_boiling_point_c=100.0,
        start_boiling_point_unit="°C",
    )

    result = solve_boiling_point_elevation(data)

    assert result.n_mol == pytest.approx(0.1, rel=5e-3)
    assert result.molality_mol_per_kg == pytest.approx(0.2, rel=5e-3)
    assert result.delta_tb_c == pytest.approx(0.205, rel=2e-2)
    assert result.new_boiling_point_c == pytest.approx(100.205, rel=2e-2)


def test_validation_constraints():
    data = BoilingPointElevationInput(
        mass_solute_g=0.0,
        mass_solute_unit="g",
        molar_mass_g_per_mol=-1.0,
        molar_mass_unit="g/mol",
        mass_solvent_kg=0.0,
        mass_solvent_unit="kg",
        vant_hoff_i=0.0,
        kb_c_kg_per_mol=0.0,
        kb_unit="°C·kg/mol",
        start_boiling_point_c=-17.0,
        start_boiling_point_unit="°C",
    )

    errors = validate_boiling_point_inputs(data)
    assert len(errors) == 5


def test_solver_raises_for_invalid_input():
    data = BoilingPointElevationInput(
        mass_solute_g=0.0,
        mass_solute_unit="g",
        molar_mass_g_per_mol=180.0,
        molar_mass_unit="g/mol",
        mass_solvent_kg=0.5,
        mass_solvent_unit="kg",
        vant_hoff_i=1.0,
        kb_c_kg_per_mol=0.512,
        kb_unit="°C·kg/mol",
        start_boiling_point_c=100.0,
        start_boiling_point_unit="°C",
    )

    with pytest.raises(ValueError, match="Massen af opløst stof"):
        solve_boiling_point_elevation(data)


def test_steps_include_clear_result_separation():
    data = BoilingPointElevationInput(
        mass_solute_g=10.0,
        mass_solute_unit="g",
        molar_mass_g_per_mol=50.0,
        molar_mass_unit="g/mol",
        mass_solvent_kg=1.0,
        mass_solvent_unit="kg",
        vant_hoff_i=1.0,
        kb_c_kg_per_mol=0.512,
        kb_unit="°C·kg/mol",
        start_boiling_point_c=95.0,
        start_boiling_point_unit="°C",
    )

    result = solve_boiling_point_elevation(data)

    assert any("ΔT_b = i · K_b · m" in step for step in result.steps)
    assert any("nyt_kogepunkt = start_kogepunkt + ΔT_b" in step for step in result.steps)
    assert result.new_boiling_point_c == pytest.approx(result.delta_tb_c + 95.0)


@pytest.mark.parametrize(
    (
        "mass_solute_value",
        "mass_solute_unit",
        "molar_mass_value",
        "molar_mass_unit",
        "mass_solvent_value",
        "mass_solvent_unit",
        "vant_hoff_i",
        "kb_value",
        "kb_unit",
        "start_boiling_value",
        "start_boiling_unit",
    ),
    [
        (60.0, "g", 180.156, "g/mol", 0.200, "kg", 1.0, 0.512, "°C·kg/mol", 100.0, "°C"),
        (0.060, "kg", 0.180156, "kg/mol", 200.0, "g", 1.0, 0.512, "K·kg/mol", 373.15, "K"),
        (60000.0, "mg", 180.156, "g/mol", 200000.0, "mg", 1.0, 0.512, "°C·kg/mol", 212.0, "°F"),
        (5.84, "g", 58.44, "g/mol", 500.0, "g", 2.0, 0.512, "K·kg/mol", 100.0, "°C"),
        (5840.0, "mg", 58.44, "g/mol", 0.5, "kg", 2.0, 0.512, "°C·kg/mol", 373.15, "K"),
        (10.0, "g", 50.0, "g/mol", 250.0, "g", 1.0, 0.512, "°C·kg/mol", 95.0, "°C"),
        (0.010, "kg", 0.050, "kg/mol", 0.250, "kg", 1.0, 0.512, "K·kg/mol", 368.15, "K"),
        (2500.0, "mg", 25.0, "g/mol", 100.0, "g", 1.5, 0.512, "°C·kg/mol", 77.0, "°F"),
        (2.5, "g", 250.0, "g/mol", 1_000_000.0, "mg", 1.5, 0.512, "K·kg/mol", 298.15, "K"),
        (12.0, "g", 60.0, "g/mol", 3000.0, "g", 1.0, 0.512, "°C·kg/mol", 25.0, "°C"),
        (0.012, "kg", 0.060, "kg/mol", 3000.0, "g", 1.0, 0.512, "K·kg/mol", 298.15, "K"),
        (75.0, "g", 150.0, "g/mol", 0.750, "kg", 3.0, 0.512, "°C·kg/mol", 80.0, "°C"),
        (75000.0, "mg", 0.150, "kg/mol", 750.0, "g", 3.0, 0.512, "K·kg/mol", 353.15, "K"),
        (1.0, "g", 100.0, "g/mol", 0.050, "kg", 1.0, 0.512, "°C·kg/mol", 32.0, "°F"),
        (1000.0, "mg", 0.100, "kg/mol", 50.0, "g", 1.0, 0.512, "K·kg/mol", 305.15, "K"),
    ],
)
def test_solver_with_unit_conversions(
    mass_solute_value,
    mass_solute_unit,
    molar_mass_value,
    molar_mass_unit,
    mass_solvent_value,
    mass_solvent_unit,
    vant_hoff_i,
    kb_value,
    kb_unit,
    start_boiling_value,
    start_boiling_unit,
):
    data = BoilingPointElevationInput(
        mass_solute_g=mass_solute_value,
        mass_solute_unit=mass_solute_unit,
        molar_mass_g_per_mol=molar_mass_value,
        molar_mass_unit=molar_mass_unit,
        mass_solvent_kg=mass_solvent_value,
        mass_solvent_unit=mass_solvent_unit,
        vant_hoff_i=vant_hoff_i,
        kb_c_kg_per_mol=kb_value,
        kb_unit=kb_unit,
        start_boiling_point_c=start_boiling_value,
        start_boiling_point_unit=start_boiling_unit,
    )

    result = solve_boiling_point_elevation(data)
    expected_n, expected_m, expected_delta, expected_new = _expected_boiling_point(
        mass_solute_value,
        mass_solute_unit,
        molar_mass_value,
        molar_mass_unit,
        mass_solvent_value,
        mass_solvent_unit,
        vant_hoff_i,
        kb_value,
        kb_unit,
        start_boiling_value,
        start_boiling_unit,
    )

    assert result.n_mol == pytest.approx(expected_n, rel=1e-4, abs=1e-4)
    assert result.molality_mol_per_kg == pytest.approx(expected_m, rel=1e-4, abs=1e-4)
    assert result.delta_tb_c == pytest.approx(expected_delta, rel=1e-4, abs=1e-4)
    assert result.new_boiling_point_c == pytest.approx(expected_new, rel=1e-4, abs=1e-4)


def test_ui_parse_helper_rejects_empty_and_text_values():
    with pytest.raises(ValueError, match="mangler"):
        _parse_required_float("", "Felt")
    with pytest.raises(ValueError, match="gyldigt tal"):
        _parse_required_float("abc", "Felt")