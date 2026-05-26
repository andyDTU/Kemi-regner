"""Core calculation helpers for osmotic pressure.

The module is UI-agnostic and returns explicit intermediate values so the
interface can display both results and step-by-step reasoning.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from core.thermo import celsius_to_kelvin, get_gas_constant


@dataclass(frozen=True)
class OsmoticPressureInput:
    mass_solute_g: float
    mass_solute_unit: str
    molar_mass_g_per_mol: float
    molar_mass_unit: str
    volume_solution_l: float
    volume_unit: str
    temperature_c: float
    temperature_unit: str
    vant_hoff_i: float
    pressure_unit: str


@dataclass(frozen=True)
class OsmoticPressureResult:
    n_mol: float
    molarity_mol_per_l: float
    temperature_k: float
    osmotic_pressure: float
    pressure_unit: str
    steps: List[str] = field(default_factory=list)
    metadata: Dict[str, float] = field(default_factory=dict)


def validate_osmotic_pressure_inputs(data: OsmoticPressureInput) -> List[str]:
    errors: List[str] = []
    if data.mass_solute_g <= 0:
        errors.append("Massen af opløst stof skal være større end 0.")
    if data.molar_mass_g_per_mol <= 0:
        errors.append("Molarmassen skal være større end 0.")
    if data.volume_solution_l <= 0:
        errors.append("Volumen af opløsningen skal være større end 0.")
    if data.vant_hoff_i <= 0:
        errors.append("van't Hoff-faktoren i skal være større end 0.")
    if data.pressure_unit not in {"atm", "Pa"}:
        errors.append("Trykenheden skal være atm eller Pa.")
    if data.mass_solute_unit not in {"g", "kg", "mg"}:
        errors.append("Massenhed for opløst stof skal være g, kg eller mg.")
    if data.molar_mass_unit not in {"g/mol", "kg/mol"}:
        errors.append("Molarmasseenheden skal være g/mol eller kg/mol.")
    if data.volume_unit not in {"L", "mL", "m³"}:
        errors.append("Volumenenheden skal være L, mL eller m³.")
    if data.temperature_unit not in {"°C", "K", "°F"}:
        errors.append("Temperaturenheden skal være °C, K eller °F.")
    if data.temperature_unit == "K" and data.temperature_c <= 0:
        errors.append("Temperaturen i Kelvin skal være større end 0 K.")
    return errors


def convert_mass_to_g(value: float, unit: str) -> float:
    if unit == "g":
        return value
    if unit == "kg":
        return value * 1000.0
    if unit == "mg":
        return value * 0.001
    raise ValueError(f"Ukendt masseenhed: {unit}")


def convert_molar_mass_to_g_per_mol(value: float, unit: str) -> float:
    if unit == "g/mol":
        return value
    if unit == "kg/mol":
        return value * 1000.0
    raise ValueError(f"Ukendt molarmasseenhed: {unit}")


def convert_volume_to_l(value: float, unit: str) -> float:
    if unit == "L":
        return value
    if unit == "mL":
        return value / 1000.0
    if unit == "m³":
        return value * 1000.0
    raise ValueError(f"Ukendt volumenenhed: {unit}")


def convert_temperature_to_c(value: float, unit: str) -> float:
    if unit == "°C":
        return value
    if unit == "K":
        return value - 273.15
    if unit == "°F":
        return (value - 32.0) * 5.0 / 9.0
    raise ValueError(f"Ukendt temperaturenhed: {unit}")


def solve_osmotic_pressure(data: OsmoticPressureInput) -> OsmoticPressureResult:
    errors = validate_osmotic_pressure_inputs(data)
    if errors:
        raise ValueError("; ".join(errors))

    mass_solute_g = convert_mass_to_g(data.mass_solute_g, data.mass_solute_unit)
    molar_mass_g_per_mol = convert_molar_mass_to_g_per_mol(data.molar_mass_g_per_mol, data.molar_mass_unit)
    volume_solution_l = convert_volume_to_l(data.volume_solution_l, data.volume_unit)
    temperature_c = convert_temperature_to_c(data.temperature_c, data.temperature_unit)

    n_mol = mass_solute_g / molar_mass_g_per_mol
    molarity_l = n_mol / volume_solution_l
    temperature_k = celsius_to_kelvin(temperature_c)

    if data.pressure_unit == "atm":
        gas_constant = get_gas_constant("L_atm")
        molarity_for_pressure = molarity_l
        osmotic_pressure = data.vant_hoff_i * molarity_for_pressure * gas_constant * temperature_k
        gas_constant_label = "0.08206 L·atm/(mol·K)"
        molarity_label = "mol/L"
        volume_label = f"{volume_solution_l:.6g} L"
        molarity_for_pressure_label = f"{molarity_for_pressure:.6g} mol/L"
    else:
        gas_constant = get_gas_constant("SI")
        volume_m3 = volume_solution_l * 0.001
        molarity_for_pressure = n_mol / volume_m3
        osmotic_pressure = data.vant_hoff_i * molarity_for_pressure * gas_constant * temperature_k
        gas_constant_label = "8.314 Pa·m³/(mol·K)"
        molarity_label = "mol/L"
        volume_label = f"{volume_solution_l:.6g} L = {volume_m3:.6g} m³"
        molarity_for_pressure_label = f"{molarity_for_pressure:.6g} mol/m³"

    steps = [
        "1) Beregning af stofmængde:",
        f"n = masse / molarmasse = {mass_solute_g:.6g} g / {molar_mass_g_per_mol:.6g} g/mol = {n_mol:.6g} mol",
        "2) Beregning af molaritet:",
        f"M = n / volumen = {n_mol:.6g} mol / {volume_label} = {molarity_l:.6g} mol/L",
        "3) Beregning af temperatur i Kelvin:",
        f"T(K) = °C + 273.15 = {temperature_c:.6g} + 273.15 = {temperature_k:.6g} K",
        "4) Beregning af osmotisk tryk:",
        f"π = i · M · R · T = {data.vant_hoff_i:.6g} · {molarity_for_pressure_label} · {gas_constant_label} · {temperature_k:.6g} K = {osmotic_pressure:.6g} {data.pressure_unit}",
    ]

    metadata = {
        "mass_solute_g": mass_solute_g,
        "molar_mass_g_per_mol": molar_mass_g_per_mol,
        "volume_solution_l": volume_solution_l,
        "temperature_c": temperature_c,
        "vant_hoff_i": data.vant_hoff_i,
        "osmotic_pressure_unit": data.pressure_unit,
    }

    return OsmoticPressureResult(
        n_mol=n_mol,
        molarity_mol_per_l=molarity_l,
        temperature_k=temperature_k,
        osmotic_pressure=osmotic_pressure,
        pressure_unit=data.pressure_unit,
        steps=steps,
        metadata=metadata,
    )