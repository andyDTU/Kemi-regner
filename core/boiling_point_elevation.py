"""Core calculation helpers for boiling-point elevation.

The module is UI-agnostic and returns explicit intermediate values so the
interface can display both final results and step-by-step reasoning.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


def convert_mass_to_g(value: float, unit: str) -> float:
    unit_map = {
        "g": 1.0,
        "kg": 1000.0,
        "mg": 0.001,
    }
    if unit not in unit_map:
        raise ValueError(f"Ukendt masseenhed: {unit}")
    return value * unit_map[unit]


def convert_mass_to_kg(value: float, unit: str) -> float:
    unit_map = {
        "kg": 1.0,
        "g": 0.001,
        "mg": 0.000001,
    }
    if unit not in unit_map:
        raise ValueError(f"Ukendt masseenhed: {unit}")
    return value * unit_map[unit]


def convert_molar_mass_to_g_per_mol(value: float, unit: str) -> float:
    unit_map = {
        "g/mol": 1.0,
        "kg/mol": 1000.0,
    }
    if unit not in unit_map:
        raise ValueError(f"Ukendt molarmasseenhed: {unit}")
    return value * unit_map[unit]


def convert_temperature_to_c(value: float, unit: str) -> float:
    if unit == "°C":
        return value
    if unit == "K":
        return value - 273.15
    if unit == "°F":
        return (value - 32.0) * 5.0 / 9.0
    raise ValueError(f"Ukendt temperaturenhed: {unit}")


def convert_kb_to_c_kg_per_mol(value: float, unit: str) -> float:
    if unit in ("°C·kg/mol", "K·kg/mol"):
        return value
    raise ValueError(f"Ukendt Kb-enhed: {unit}")


@dataclass(frozen=True)
class BoilingPointElevationInput:
    mass_solute_g: float
    mass_solute_unit: str
    molar_mass_g_per_mol: float
    molar_mass_unit: str
    mass_solvent_kg: float
    mass_solvent_unit: str
    vant_hoff_i: float
    kb_c_kg_per_mol: float
    kb_unit: str
    start_boiling_point_c: float
    start_boiling_point_unit: str


@dataclass(frozen=True)
class BoilingPointElevationResult:
    n_mol: float
    molality_mol_per_kg: float
    delta_tb_c: float
    new_boiling_point_c: float
    steps: List[str] = field(default_factory=list)
    metadata: Dict[str, float] = field(default_factory=dict)


def validate_boiling_point_inputs(data: BoilingPointElevationInput) -> List[str]:
    errors: List[str] = []
    if data.mass_solute_g <= 0:
        errors.append("Massen af opløst stof skal være større end 0.")
    if data.molar_mass_g_per_mol <= 0:
        errors.append("Molarmassen skal være større end 0.")
    if data.mass_solvent_kg <= 0:
        errors.append("Massen af opløsningsmiddel skal være større end 0.")
    if data.vant_hoff_i <= 0:
        errors.append("van't Hoff-faktoren i skal være større end 0.")
    if data.kb_c_kg_per_mol <= 0:
        errors.append("Kogepunktskonstanten K_b skal være større end 0.")
    return errors


def solve_boiling_point_elevation(data: BoilingPointElevationInput) -> BoilingPointElevationResult:
    errors = validate_boiling_point_inputs(data)
    if errors:
        raise ValueError("; ".join(errors))

    mass_solute_g = convert_mass_to_g(data.mass_solute_g, data.mass_solute_unit)
    molar_mass_g_per_mol = convert_molar_mass_to_g_per_mol(data.molar_mass_g_per_mol, data.molar_mass_unit)
    mass_solvent_kg = convert_mass_to_kg(data.mass_solvent_kg, data.mass_solvent_unit)
    kb_c_kg_per_mol = convert_kb_to_c_kg_per_mol(data.kb_c_kg_per_mol, data.kb_unit)
    start_boiling_point_c = convert_temperature_to_c(data.start_boiling_point_c, data.start_boiling_point_unit)

    n_mol = mass_solute_g / molar_mass_g_per_mol
    molality = n_mol / mass_solvent_kg
    delta_tb = data.vant_hoff_i * kb_c_kg_per_mol * molality
    new_boiling_point_c = start_boiling_point_c + delta_tb

    steps = [
        "1) Beregning af stofmængde:",
        f"n = masse / molarmasse = {mass_solute_g:.6g} g / {molar_mass_g_per_mol:.6g} g/mol = {n_mol:.6g} mol",
        "2) Beregning af molalitet:",
        f"m = n / kg opløsningsmiddel = {n_mol:.6g} mol / {mass_solvent_kg:.6g} kg = {molality:.6g} mol/kg",
        "3) Beregning af kogepunktsstigning:",
        f"ΔT_b = i · K_b · m = {data.vant_hoff_i:.6g} · {kb_c_kg_per_mol:.6g} · {molality:.6g} = {delta_tb:.6g} °C",
        "4) Beregning af nyt kogepunkt:",
        f"nyt_kogepunkt = start_kogepunkt + ΔT_b = {start_boiling_point_c:.6g} + {delta_tb:.6g} = {new_boiling_point_c:.6g} °C",
    ]

    metadata = {
        "mass_solute_g": mass_solute_g,
        "molar_mass_g_per_mol": molar_mass_g_per_mol,
        "mass_solvent_kg": mass_solvent_kg,
        "vant_hoff_i": data.vant_hoff_i,
        "kb_c_kg_per_mol": kb_c_kg_per_mol,
        "start_boiling_point_c": start_boiling_point_c,
    }

    return BoilingPointElevationResult(
        n_mol=n_mol,
        molality_mol_per_kg=molality,
        delta_tb_c=delta_tb,
        new_boiling_point_c=new_boiling_point_c,
        steps=steps,
        metadata=metadata,
    )
