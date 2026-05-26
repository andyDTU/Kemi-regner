import pytest

from core.clausius_clapeyron import (
    ClausiusClapeyronProblem,
    collect_validation_errors,
    enthalpy_from_j_per_mol,
    enthalpy_to_j_per_mol,
    pressure_from_pa,
    pressure_to_pa,
    solve_clausius_clapeyron,
    temperature_from_kelvin,
    temperature_to_kelvin,
)


def test_pressure_conversions():
    assert pressure_to_pa(1.0, "atm") == pytest.approx(101325.0)
    assert pressure_from_pa(101325.0, "atm") == pytest.approx(1.0)
    assert pressure_to_pa(1.0, "bar") == pytest.approx(100000.0)
    assert pressure_from_pa(1000.0, "kPa") == pytest.approx(1.0)
    assert pressure_to_pa(760.0, "torr") == pytest.approx(101325.0)


def test_temperature_conversions():
    assert temperature_to_kelvin(25.0, "°C") == pytest.approx(298.15)
    assert temperature_from_kelvin(298.15, "°C") == pytest.approx(25.0)
    assert temperature_to_kelvin(373.15, "K") == pytest.approx(373.15)


def test_enthalpy_conversions_with_molar_mass():
    molar_mass = 18.01528
    assert enthalpy_to_j_per_mol(40.65, "kJ/mol") == pytest.approx(40650.0)
    assert enthalpy_from_j_per_mol(40650.0, "kJ/mol") == pytest.approx(40.65)
    j_per_g = 40650.0 / molar_mass
    assert enthalpy_to_j_per_mol(j_per_g, "J/g", molar_mass) == pytest.approx(40650.0)
    assert enthalpy_from_j_per_mol(40650.0, "J/g", molar_mass) == pytest.approx(j_per_g)


def test_solve_for_p2():
    problem = ClausiusClapeyronProblem(
        unknown="P2",
        p1=1.0,
        p1_unit="atm",
        t1=373.15,
        t1_unit="K",
        t2=353.15,
        t2_unit="K",
        delta_hvap=40.65,
        delta_hvap_unit="kJ/mol",
    )
    solution = solve_clausius_clapeyron(problem)
    assert solution.value == pytest.approx(0.473, rel=0.01)
    assert solution.unit == "atm"
    assert solution.value_si == pytest.approx(0.473 * 101325.0, rel=0.01)


def test_solve_for_p1():
    problem = ClausiusClapeyronProblem(
        unknown="P1",
        p2=0.473,
        p2_unit="atm",
        t1=373.15,
        t1_unit="K",
        t2=353.15,
        t2_unit="K",
        delta_hvap=40.65,
        delta_hvap_unit="kJ/mol",
    )
    solution = solve_clausius_clapeyron(problem)
    assert solution.value == pytest.approx(1.0, rel=0.01)
    assert solution.unit == "atm"


def test_solve_for_t2():
    problem = ClausiusClapeyronProblem(
        unknown="T2",
        p1=1.0,
        p1_unit="atm",
        p2=0.473,
        p2_unit="atm",
        t1=373.15,
        t1_unit="K",
        delta_hvap=40.65,
        delta_hvap_unit="kJ/mol",
    )
    solution = solve_clausius_clapeyron(problem)
    assert solution.value == pytest.approx(353.15, abs=0.5)
    assert solution.unit == "K"


def test_solve_for_t1():
    problem = ClausiusClapeyronProblem(
        unknown="T1",
        p1=1.0,
        p1_unit="atm",
        p2=0.473,
        p2_unit="atm",
        t2=353.15,
        t2_unit="K",
        delta_hvap=40.65,
        delta_hvap_unit="kJ/mol",
    )
    solution = solve_clausius_clapeyron(problem)
    assert solution.value == pytest.approx(373.15, abs=0.5)
    assert solution.unit == "K"


def test_solve_for_delta_hvap():
    problem = ClausiusClapeyronProblem(
        unknown="deltaHvap",
        p1=1.0,
        p1_unit="atm",
        p2=0.473,
        p2_unit="atm",
        t1=373.15,
        t1_unit="K",
        t2=353.15,
        t2_unit="K",
        delta_hvap_unit="kJ/mol",
    )
    solution = solve_clausius_clapeyron(problem)
    assert solution.value == pytest.approx(40.65, rel=0.01)
    assert solution.unit == "kJ/mol"


def test_solve_for_delta_hvap_per_gram():
    molar_mass = 18.01528
    problem = ClausiusClapeyronProblem(
        unknown="deltaHvap",
        p1=1.0,
        p1_unit="atm",
        p2=0.473,
        p2_unit="atm",
        t1=373.15,
        t1_unit="K",
        t2=353.15,
        t2_unit="K",
        delta_hvap_unit="kJ/g",
        molar_mass_g_per_mol=molar_mass,
    )
    solution = solve_clausius_clapeyron(problem)
    assert solution.unit == "kJ/g"
    assert solution.value == pytest.approx(40.65 / molar_mass, rel=0.01)


def test_delta_hvap_per_gram_requires_molar_mass():
    problem = ClausiusClapeyronProblem(
        unknown="P2",
        p1=1.0,
        p1_unit="atm",
        t1=373.15,
        t1_unit="K",
        t2=353.15,
        t2_unit="K",
        delta_hvap=2.256,
        delta_hvap_unit="kJ/g",
    )
    errors = collect_validation_errors(problem)
    assert any("Molarmasse" in error for error in errors)


def test_invalid_inputs_raise_human_readable_error():
    problem = ClausiusClapeyronProblem(
        unknown="deltaHvap",
        p1=1.0,
        p1_unit="atm",
        p2=1.0,
        p2_unit="atm",
        t1=373.15,
        t1_unit="K",
        t2=373.15,
        t2_unit="K",
        delta_hvap_unit="kJ/mol",
    )
    with pytest.raises(ValueError, match="T1 og T2"):
        solve_clausius_clapeyron(problem)
