"""Core calculation helpers for freezing-point depression.

The module is UI-agnostic and returns explicit intermediate values so the
interface can display both results and between-steps clearly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class FreezingPointDepressionInput:
    mass_solute_g: float
    molar_mass_g_per_mol: float
    mass_solvent_kg: float
    vant_hoff_i: float
    kf_c_kg_per_mol: float


@dataclass(frozen=True)
class FreezingPointDepressionResult:
    n_mol: float
    molality_mol_per_kg: float
    delta_tf_c: float
    steps: List[str] = field(default_factory=list)
    metadata: Dict[str, float] = field(default_factory=dict)


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


def convert_delta_temperature_from_c(delta_c: float, unit: str) -> float:
    if unit in ("°C", "K"):
        return delta_c
    if unit == "°F":
        return delta_c * 9.0 / 5.0
    raise ValueError(f"Ukendt delta-temperaturenhed: {unit}")


def convert_kf_to_c_kg_per_mol(value: float, unit: str) -> float:
    if unit in ("°C·kg/mol", "K·kg/mol"):
        return value
    raise ValueError(f"Ukendt Kf-enhed: {unit}")


def validate_freezing_point_inputs(data: FreezingPointDepressionInput) -> List[str]:
    errors: List[str] = []
    if data.mass_solute_g <= 0:
        errors.append("Massen af opløst stof skal være større end 0 g.")
    if data.molar_mass_g_per_mol <= 0:
        errors.append("Molarmassen skal være større end 0 g/mol.")
    if data.mass_solvent_kg <= 0:
        errors.append("Massen af opløsningsmiddel skal være større end 0 kg.")
    if data.vant_hoff_i <= 0:
        errors.append("van't Hoff-faktoren i skal være større end 0.")
    if data.kf_c_kg_per_mol <= 0:
        errors.append("Frysepunktskonstanten Kf skal være større end 0.")
    return errors


def solve_freezing_point_depression(data: FreezingPointDepressionInput) -> FreezingPointDepressionResult:
    errors = validate_freezing_point_inputs(data)
    if errors:
        raise ValueError("; ".join(errors))

    n_mol = data.mass_solute_g / data.molar_mass_g_per_mol
    molality = n_mol / data.mass_solvent_kg
    delta_tf = data.vant_hoff_i * data.kf_c_kg_per_mol * molality

    steps = [
        "1) Beregning af stofmængde:",
        f"n = masse / molarmasse = {data.mass_solute_g:.6g} g / {data.molar_mass_g_per_mol:.6g} g/mol = {n_mol:.6g} mol",
        "2) Beregning af molalitet:",
        f"m = n / kg opløsningsmiddel = {n_mol:.6g} mol / {data.mass_solvent_kg:.6g} kg = {molality:.6g} mol/kg",
        "3) Beregning af frysepunktsfald:",
        f"ΔT_f = i · K_f · m = {data.vant_hoff_i:.6g} · {data.kf_c_kg_per_mol:.6g} · {molality:.6g} = {delta_tf:.6g} °C",
    ]

    metadata = {
        "mass_solute_g": data.mass_solute_g,
        "molar_mass_g_per_mol": data.molar_mass_g_per_mol,
        "mass_solvent_kg": data.mass_solvent_kg,
        "vant_hoff_i": data.vant_hoff_i,
        "kf_c_kg_per_mol": data.kf_c_kg_per_mol,
    }

    return FreezingPointDepressionResult(
        n_mol=n_mol,
        molality_mol_per_kg=molality,
        delta_tf_c=delta_tf,
        steps=steps,
        metadata=metadata,
    )
