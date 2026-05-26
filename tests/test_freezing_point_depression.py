import pytest

from core.freezing_point_depression import (
    FreezingPointDepressionInput,
    convert_kf_to_c_kg_per_mol,
    convert_mass_to_g,
    convert_mass_to_kg,
    convert_molar_mass_to_g_per_mol,
    solve_freezing_point_depression,
    validate_freezing_point_inputs,
)


def test_glucose_example_from_prompt():
    data = FreezingPointDepressionInput(
        mass_solute_g=60.0,
        molar_mass_g_per_mol=180.156,
        mass_solvent_kg=0.200,
        vant_hoff_i=1.0,
        kf_c_kg_per_mol=1.86,
    )
    result = solve_freezing_point_depression(data)

    assert result.n_mol == pytest.approx(0.3330, rel=5e-3)
    assert result.molality_mol_per_kg == pytest.approx(1.665, rel=5e-3)
    assert result.delta_tf_c == pytest.approx(3.10, rel=5e-3)


def test_validation_positive_constraints():
    data = FreezingPointDepressionInput(
        mass_solute_g=0.0,
        molar_mass_g_per_mol=0.0,
        mass_solvent_kg=-1.0,
        vant_hoff_i=0.0,
        kf_c_kg_per_mol=0.0,
    )
    errors = validate_freezing_point_inputs(data)
    assert len(errors) >= 5


def test_solver_raises_for_invalid_input():
    data = FreezingPointDepressionInput(
        mass_solute_g=-1.0,
        molar_mass_g_per_mol=58.44,
        mass_solvent_kg=1.0,
        vant_hoff_i=1.0,
        kf_c_kg_per_mol=1.86,
    )
    with pytest.raises(ValueError, match="Massen af opløst stof"):
        solve_freezing_point_depression(data)


@pytest.mark.parametrize(
    (
        "mass_solute_value",
        "mass_solute_unit",
        "molar_mass_value",
        "molar_mass_unit",
        "mass_solvent_value",
        "mass_solvent_unit",
        "vant_hoff_i",
        "kf_value",
        "kf_unit",
        "expected_delta_c",
    ),
    [
        (60.0, "g", 180.156, "g/mol", 0.200, "kg", 1.0, 1.86, "°C·kg/mol", 3.10065),
        (5.0, "g", 58.44, "g/mol", 100.0, "g", 2.0, 1.86, "°C·kg/mol", 3.18344),
        (0.0180156, "kg", 0.180156, "kg/mol", 500.0, "g", 1.0, 1.86, "K·kg/mol", 0.372),
        (2500.0, "mg", 110.98, "g/mol", 250.0, "g", 3.0, 1.86, "°C·kg/mol", 0.50347),
        (12.0, "g", 60.0, "g/mol", 0.4, "kg", 1.0, 2.0, "K·kg/mol", 1.0),
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
    kf_value,
    kf_unit,
    expected_delta_c,
):
    data = FreezingPointDepressionInput(
        mass_solute_g=convert_mass_to_g(mass_solute_value, mass_solute_unit),
        molar_mass_g_per_mol=convert_molar_mass_to_g_per_mol(molar_mass_value, molar_mass_unit),
        mass_solvent_kg=convert_mass_to_kg(mass_solvent_value, mass_solvent_unit),
        vant_hoff_i=vant_hoff_i,
        kf_c_kg_per_mol=convert_kf_to_c_kg_per_mol(kf_value, kf_unit),
    )
    result = solve_freezing_point_depression(data)

    assert result.delta_tf_c == pytest.approx(expected_delta_c, rel=2e-3, abs=2e-3)
