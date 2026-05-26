"""Clausius-Clapeyron utilities for pressure-vapor calculations.

This module keeps the math, unit conversion, and validation separate from the
Streamlit UI so the calculation logic stays testable and reusable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import exp, isfinite, log
from typing import Any, Dict, List, Optional, Literal

from core.thermo import load_constants


PressureUnit = Literal["Pa", "kPa", "bar", "atm", "mmHg", "torr"]
TemperatureUnit = Literal["K", "°C"]
EnthalpyUnit = Literal["J/mol", "kJ/mol", "J/g", "kJ/g"]
UnknownVariable = Literal["P1", "P2", "T1", "T2", "deltaHvap"]

PRESSURE_TO_PA: Dict[str, float] = {
    "Pa": 1.0,
    "kPa": 1_000.0,
    "bar": 100_000.0,
    "atm": 101_325.0,
    "mmHg": 133.322387415,
    "torr": 101_325.0 / 760.0,
}

TEMPERATURE_UNITS = {"K", "°C"}
ENTHALPY_UNITS = {"J/mol", "kJ/mol", "J/g", "kJ/g"}
UNKNOWN_VARIABLES = {"P1", "P2", "T1", "T2", "deltaHvap"}


@dataclass(frozen=True)
class ClausiusClapeyronProblem:
    """Input bundle for a single Clausius-Clapeyron solve."""

    unknown: UnknownVariable
    p1: Optional[float] = None
    p1_unit: PressureUnit = "atm"
    p2: Optional[float] = None
    p2_unit: PressureUnit = "atm"
    t1: Optional[float] = None
    t1_unit: TemperatureUnit = "K"
    t2: Optional[float] = None
    t2_unit: TemperatureUnit = "K"
    delta_hvap: Optional[float] = None
    delta_hvap_unit: EnthalpyUnit = "kJ/mol"
    molar_mass_g_per_mol: Optional[float] = None


@dataclass(frozen=True)
class ClausiusClapeyronSolution:
    """Structured result for UI rendering and tests."""

    unknown: UnknownVariable
    value: float
    unit: str
    value_si: float
    si_unit: str
    steps: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


def _format_quantity(value: float, unit: str, significant_digits: int = 6) -> str:
    if value == 0:
        return f"0 {unit}"
    abs_value = abs(value)
    if abs_value >= 1e4 or abs_value < 1e-3:
        return f"{value:.{significant_digits - 1}e} {unit}"
    return f"{value:.{significant_digits}g} {unit}"


def pressure_to_pa(value: float, unit: PressureUnit) -> float:
    """Convert pressure to pascal."""
    _validate_number(value, "Pressure")
    _validate_positive(value, "Pressure")
    try:
        return value * PRESSURE_TO_PA[unit]
    except KeyError as exc:
        raise ValueError(f"Unsupported pressure unit: {unit}") from exc


def pressure_from_pa(value_pa: float, unit: PressureUnit) -> float:
    """Convert pressure from pascal."""
    _validate_number(value_pa, "Pressure")
    _validate_positive(value_pa, "Pressure")
    try:
        return value_pa / PRESSURE_TO_PA[unit]
    except KeyError as exc:
        raise ValueError(f"Unsupported pressure unit: {unit}") from exc


def temperature_to_kelvin(value: float, unit: TemperatureUnit) -> float:
    """Convert temperature to kelvin."""
    _validate_number(value, "Temperature")
    if unit not in TEMPERATURE_UNITS:
        raise ValueError(f"Unsupported temperature unit: {unit}")
    value_k = value if unit == "K" else value + 273.15
    if value_k <= 0:
        raise ValueError("Temperature must be greater than 0 K")
    return value_k


def temperature_from_kelvin(value_k: float, unit: TemperatureUnit) -> float:
    """Convert temperature from kelvin."""
    _validate_number(value_k, "Temperature")
    _validate_positive(value_k, "Temperature")
    if unit not in TEMPERATURE_UNITS:
        raise ValueError(f"Unsupported temperature unit: {unit}")
    return value_k if unit == "K" else value_k - 273.15


def enthalpy_to_j_per_mol(
    value: float,
    unit: EnthalpyUnit,
    molar_mass_g_per_mol: Optional[float] = None,
) -> float:
    """Convert vaporization enthalpy to J/mol."""
    _validate_number(value, "ΔHvap")
    if unit not in ENTHALPY_UNITS:
        raise ValueError(f"Unsupported enthalpy unit: {unit}")
    if unit in {"J/mol", "kJ/mol"}:
        return value * 1000.0 if unit == "kJ/mol" else value
    _validate_molar_mass(molar_mass_g_per_mol)
    factor = 1_000.0 if unit == "kJ/g" else 1.0
    return value * factor * float(molar_mass_g_per_mol)


def enthalpy_from_j_per_mol(
    value_j_per_mol: float,
    unit: EnthalpyUnit,
    molar_mass_g_per_mol: Optional[float] = None,
) -> float:
    """Convert vaporization enthalpy from J/mol."""
    _validate_number(value_j_per_mol, "ΔHvap")
    if unit not in ENTHALPY_UNITS:
        raise ValueError(f"Unsupported enthalpy unit: {unit}")
    if unit in {"J/mol", "kJ/mol"}:
        return value_j_per_mol / 1000.0 if unit == "kJ/mol" else value_j_per_mol
    _validate_molar_mass(molar_mass_g_per_mol)
    factor = 1_000.0 if unit == "kJ/g" else 1.0
    return value_j_per_mol / (factor * float(molar_mass_g_per_mol))


def collect_validation_errors(problem: ClausiusClapeyronProblem) -> List[str]:
    """Collect user-facing validation errors without raising immediately."""
    errors: List[str] = []

    if problem.unknown not in UNKNOWN_VARIABLES:
        errors.append(f"Ukendt variabel '{problem.unknown}' understøttes ikke.")

    if problem.p1 is None and problem.unknown != "P1":
        errors.append("P1 mangler.")
    if problem.p2 is None and problem.unknown != "P2":
        errors.append("P2 mangler.")
    if problem.t1 is None and problem.unknown != "T1":
        errors.append("T1 mangler.")
    if problem.t2 is None and problem.unknown != "T2":
        errors.append("T2 mangler.")
    if problem.delta_hvap is None and problem.unknown != "deltaHvap":
        errors.append("ΔHvap mangler.")

    if problem.unknown == "P1" and problem.p1 is not None:
        errors.append("P1 skal være tom, når P1 beregnes.")
    if problem.unknown == "P2" and problem.p2 is not None:
        errors.append("P2 skal være tom, når P2 beregnes.")
    if problem.unknown == "T1" and problem.t1 is not None:
        errors.append("T1 skal være tom, når T1 beregnes.")
    if problem.unknown == "T2" and problem.t2 is not None:
        errors.append("T2 skal være tom, når T2 beregnes.")
    if problem.unknown == "deltaHvap" and problem.delta_hvap is not None:
        errors.append("ΔHvap skal være tom, når ΔHvap beregnes.")

    if _is_invalid_value(problem.p1):
        errors.append("P1 skal være større end 0.")
    if _is_invalid_value(problem.p2):
        errors.append("P2 skal være større end 0.")
    if _is_invalid_temperature(problem.t1, problem.t1_unit):
        errors.append("T1 skal være større end 0 K.")
    if _is_invalid_temperature(problem.t2, problem.t2_unit):
        errors.append("T2 skal være større end 0 K.")
    if problem.delta_hvap is not None and problem.delta_hvap <= 0:
        errors.append("ΔHvap skal være større end 0.")

    if problem.unknown in {"T1", "T2", "deltaHvap"}:
        if problem.p1 is None or problem.p2 is None:
            errors.append("P1 og P2 skal begge være angivet for denne beregning.")
        if problem.t1 is None and problem.unknown != "T1":
            errors.append("T1 skal være angivet for denne beregning.")
        if problem.t2 is None and problem.unknown != "T2":
            errors.append("T2 skal være angivet for denne beregning.")

    if _unit_requires_molar_mass(problem.delta_hvap_unit) and problem.molar_mass_g_per_mol is None:
        errors.append("Molarmasse er påkrævet, når ΔHvap angives i J/g eller kJ/g.")

    if problem.molar_mass_g_per_mol is not None:
        try:
            _validate_molar_mass(problem.molar_mass_g_per_mol)
        except ValueError as exc:
            errors.append(str(exc))

    return errors


def validate_problem(problem: ClausiusClapeyronProblem) -> None:
    """Raise a human-readable ValueError if the problem is inconsistent."""
    errors = collect_validation_errors(problem)
    if errors:
        raise ValueError("; ".join(errors))


def solve_clausius_clapeyron(problem: ClausiusClapeyronProblem) -> ClausiusClapeyronSolution:
    """Solve the two-point Clausius-Clapeyron equation for the missing variable."""
    validate_problem(problem)

    constants = load_constants()
    gas_constant = float(constants["R_J_per_molK"])

    p1_pa = pressure_to_pa(problem.p1, problem.p1_unit) if problem.p1 is not None else None
    p2_pa = pressure_to_pa(problem.p2, problem.p2_unit) if problem.p2 is not None else None
    t1_k = temperature_to_kelvin(problem.t1, problem.t1_unit) if problem.t1 is not None else None
    t2_k = temperature_to_kelvin(problem.t2, problem.t2_unit) if problem.t2 is not None else None
    delta_hvap_j_per_mol = (
        enthalpy_to_j_per_mol(problem.delta_hvap, problem.delta_hvap_unit, problem.molar_mass_g_per_mol)
        if problem.delta_hvap is not None
        else None
    )

    if problem.unknown == "P2":
        result_si = _solve_for_p2(p1_pa, t1_k, t2_k, delta_hvap_j_per_mol, gas_constant)
        result_value = pressure_from_pa(result_si, problem.p2_unit)
        result_unit = problem.p2_unit
        si_unit = "Pa"
    elif problem.unknown == "P1":
        result_si = _solve_for_p1(p2_pa, t1_k, t2_k, delta_hvap_j_per_mol, gas_constant)
        result_value = pressure_from_pa(result_si, problem.p1_unit)
        result_unit = problem.p1_unit
        si_unit = "Pa"
    elif problem.unknown == "T2":
        result_si = _solve_for_t2(p1_pa, p2_pa, t1_k, delta_hvap_j_per_mol, gas_constant)
        result_value = temperature_from_kelvin(result_si, problem.t2_unit)
        result_unit = problem.t2_unit
        si_unit = "K"
    elif problem.unknown == "T1":
        result_si = _solve_for_t1(p1_pa, p2_pa, t2_k, delta_hvap_j_per_mol, gas_constant)
        result_value = temperature_from_kelvin(result_si, problem.t1_unit)
        result_unit = problem.t1_unit
        si_unit = "K"
    else:
        result_si = _solve_for_delta_hvap(p1_pa, p2_pa, t1_k, t2_k, gas_constant)
        result_value = enthalpy_from_j_per_mol(
            result_si,
            problem.delta_hvap_unit,
            problem.molar_mass_g_per_mol,
        )
        result_unit = problem.delta_hvap_unit
        si_unit = "J/mol"

    steps = _build_steps(
        problem=problem,
        p1_pa=p1_pa,
        p2_pa=p2_pa,
        t1_k=t1_k,
        t2_k=t2_k,
        delta_hvap_j_per_mol=delta_hvap_j_per_mol,
        gas_constant=gas_constant,
        result_si=result_si,
        result_value=result_value,
        result_unit=result_unit,
        si_unit=si_unit,
    )

    metadata = {
        "p1_pa": p1_pa,
        "p2_pa": p2_pa,
        "t1_k": t1_k,
        "t2_k": t2_k,
        "delta_hvap_j_per_mol": delta_hvap_j_per_mol,
        "gas_constant_j_per_molk": gas_constant,
        "result_si": result_si,
    }
    return ClausiusClapeyronSolution(
        unknown=problem.unknown,
        value=result_value,
        unit=result_unit,
        value_si=result_si,
        si_unit=si_unit,
        steps=steps,
        metadata=metadata,
    )


def _solve_for_p2(p1_pa: float, t1_k: float, t2_k: float, delta_hvap_j_per_mol: float, gas_constant: float) -> float:
    exponent = -(delta_hvap_j_per_mol / gas_constant) * (1.0 / t2_k - 1.0 / t1_k)
    return p1_pa * exp(exponent)


def _solve_for_p1(p2_pa: float, t1_k: float, t2_k: float, delta_hvap_j_per_mol: float, gas_constant: float) -> float:
    exponent = -(delta_hvap_j_per_mol / gas_constant) * (1.0 / t2_k - 1.0 / t1_k)
    return p2_pa / exp(exponent)


def _solve_for_t2(p1_pa: float, p2_pa: float, t1_k: float, delta_hvap_j_per_mol: float, gas_constant: float) -> float:
    ratio = p2_pa / p1_pa
    denominator = (1.0 / t1_k) - (gas_constant / delta_hvap_j_per_mol) * log(ratio)
    if abs(denominator) < 1e-15:
        raise ValueError("Inputværdierne giver en umulig løsning for T2.")
    result = 1.0 / denominator
    _validate_positive(result, "T2")
    return result


def _solve_for_t1(p1_pa: float, p2_pa: float, t2_k: float, delta_hvap_j_per_mol: float, gas_constant: float) -> float:
    ratio = p2_pa / p1_pa
    denominator = (1.0 / t2_k) + (gas_constant / delta_hvap_j_per_mol) * log(ratio)
    if abs(denominator) < 1e-15:
        raise ValueError("Inputværdierne giver en umulig løsning for T1.")
    result = 1.0 / denominator
    _validate_positive(result, "T1")
    return result


def _solve_for_delta_hvap(p1_pa: float, p2_pa: float, t1_k: float, t2_k: float, gas_constant: float) -> float:
    denominator = (1.0 / t2_k) - (1.0 / t1_k)
    if abs(denominator) < 1e-15:
        raise ValueError("T1 og T2 må ikke være ens, når ΔHvap skal beregnes.")
    result = -gas_constant * log(p2_pa / p1_pa) / denominator
    if result <= 0:
        raise ValueError("De angivne værdier giver en ikke-positiv ΔHvap.")
    return result


def _build_steps(
    *,
    problem: ClausiusClapeyronProblem,
    p1_pa: Optional[float],
    p2_pa: Optional[float],
    t1_k: Optional[float],
    t2_k: Optional[float],
    delta_hvap_j_per_mol: Optional[float],
    gas_constant: float,
    result_si: float,
    result_value: float,
    result_unit: str,
    si_unit: str,
) -> List[str]:
    steps: List[str] = []
    steps.append("Clausius-Clapeyron: ln(P2 / P1) = -(ΔHvap / R) · (1/T2 - 1/T1)")

    if p1_pa is not None:
        steps.append(f"P1 konverteret til SI: {_format_quantity(p1_pa, 'Pa')}")
    if p2_pa is not None:
        steps.append(f"P2 konverteret til SI: {_format_quantity(p2_pa, 'Pa')}")
    if t1_k is not None:
        steps.append(f"T1 konverteret til SI: {_format_quantity(t1_k, 'K')}")
    if t2_k is not None:
        steps.append(f"T2 konverteret til SI: {_format_quantity(t2_k, 'K')}")
    if delta_hvap_j_per_mol is not None:
        steps.append(f"ΔHvap konverteret til SI: {_format_quantity(delta_hvap_j_per_mol, 'J/mol')}")

    steps.append(f"Anvendt gaskonstant: {_format_quantity(gas_constant, 'J/(mol·K)')}")

    if problem.unknown == "P2":
        steps.append("Isolering: P2 = P1 · exp[-(ΔHvap/R) · (1/T2 - 1/T1)]")
    elif problem.unknown == "P1":
        steps.append("Isolering: P1 = P2 / exp[-(ΔHvap/R) · (1/T2 - 1/T1)]")
    elif problem.unknown == "T2":
        steps.append("Isolering: T2 = 1 / (1/T1 - (R/ΔHvap) · ln(P2/P1))")
    elif problem.unknown == "T1":
        steps.append("Isolering: T1 = 1 / (1/T2 + (R/ΔHvap) · ln(P2/P1))")
    else:
        steps.append("Isolering: ΔHvap = -R · ln(P2/P1) / (1/T2 - 1/T1)")

    if problem.unknown in {"P1", "P2"}:
        steps.append(f"Resultat i SI: {_format_quantity(result_si, si_unit)}")
        steps.append(f"Resultat i valgt enhed: {_format_quantity(result_value, result_unit)}")
    elif problem.unknown in {"T1", "T2"}:
        steps.append(f"Resultat i SI: {_format_quantity(result_si, si_unit)}")
        steps.append(f"Resultat i valgt enhed: {_format_quantity(result_value, result_unit)}")
    else:
        steps.append(f"Resultat i SI: {_format_quantity(result_si, si_unit)}")
        steps.append(f"Resultat i valgt enhed: {_format_quantity(result_value, result_unit)}")

    return steps


def _validate_number(value: float, name: str) -> None:
    if not isfinite(float(value)):
        raise ValueError(f"{name} skal være et gyldigt tal.")


def _validate_positive(value: float, name: str) -> None:
    if value <= 0:
        raise ValueError(f"{name} skal være større end 0.")


def _validate_molar_mass(value: Optional[float]) -> None:
    if value is None:
        raise ValueError("Molarmasse er påkrævet.")
    _validate_number(value, "Molarmasse")
    if value <= 0:
        raise ValueError("Molarmasse skal være større end 0.")


def _unit_requires_molar_mass(unit: EnthalpyUnit) -> bool:
    return unit.endswith("/g")


def _is_invalid_value(value: Optional[float]) -> bool:
    return value is not None and (not isfinite(float(value)) or value <= 0)


def _is_invalid_temperature(value: Optional[float], unit: TemperatureUnit) -> bool:
    if value is None:
        return False
    try:
        return temperature_to_kelvin(value, unit) <= 0
    except ValueError:
        return True
