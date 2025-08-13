import math
import pandas as pd
from calculators.thermochemistry import (
    calculate_reaction_enthalpy_from_formation_with_steps,
)


def _thermo_dhf_kj_per_mol(name: str):
    # Helper for expected values from thermo package
    from thermo import Chemical
    chem = Chemical(name, T=298.15, P=101325.0)
    return float(chem.Hf) / 1000.0


def test_rxn_enthalpy_uses_thermo_for_species_not_in_csv():
    # Reaction with species not present in CSV: H2, Cl2, HCl
    # H2(g) + Cl2(g) -> 2 HCl(g)
    rxn = "H2(g) + Cl2(g) -> 2 HCl(g)"
    val, steps, meta = calculate_reaction_enthalpy_from_formation_with_steps(rxn)

    # Expected from thermo package only
    Hf_H2 = _thermo_dhf_kj_per_mol("hydrogen")
    Hf_Cl2 = _thermo_dhf_kj_per_mol("chlorine")
    Hf_HCl = _thermo_dhf_kj_per_mol("hydrogen chloride")
    expected = 2.0 * Hf_HCl - Hf_H2 - Hf_Cl2

    assert math.isfinite(val)
    assert abs(val - expected) < 2.0  # allow small tolerance across data sources


def test_rxn_enthalpy_mixed_csv_and_thermo_sources():
    # Mixed case: 2 CO(g) + O2(g) -> 2 CO2(g)
    # CO not in CSV → thermo; O2, CO2 from CSV
    rxn = "2 CO(g) + O2(g) -> 2 CO2(g)"
    val, steps, meta = calculate_reaction_enthalpy_from_formation_with_steps(rxn)

    # Read CSV values for CO2 and O2
    df = pd.read_csv("data/thermo_tables.csv")
    Hf_CO2_csv = float(df[(df['species'] == 'CO2') & (df['phase'] == 'g')].iloc[0]['deltaHf'])
    Hf_O2_csv = float(df[(df['species'] == 'O2') & (df['phase'] == 'g')].iloc[0]['deltaHf'])

    # Get thermo value for CO
    Hf_CO_thermo = _thermo_dhf_kj_per_mol("carbon monoxide")

    expected_mixed = 2.0 * Hf_CO2_csv - (2.0 * Hf_CO_thermo + Hf_O2_csv)

    assert abs(val - expected_mixed) < 2.0


