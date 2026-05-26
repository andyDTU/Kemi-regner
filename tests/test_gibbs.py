"""
Tests for the Gibbs free energy calculator.
"""

import pytest
import sys
from pathlib import Path

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from calculators.gibbs import (
    calculate_gibbs_free_energy_with_steps,
    analyze_gibbs_temperature_dependence,
    calculate_reaction_gibbs_with_steps,
)

def test_gibbs_spontaneous_reaction():
    """Test Gibbs calculation for a spontaneous reaction."""
    # ΔH = -100 kJ/mol, ΔS = 200 J/(mol·K), T = 298.15 K
    # Expected: ΔG ≈ -159.63 kJ/mol and "spontaneous"
    result, steps, metadata = calculate_gibbs_free_energy_with_steps(
        -100.0, "kJ/mol", 200.0, "J/(mol·K)", 298.15, "K"
    )
    
    # Check result (should be approximately -159.63 kJ/mol)
    assert abs(result - (-159.63)) < 0.05
    
    # Check metadata
    assert metadata['spontaneity'] == "spontaneous"
    assert metadata['delta_g_kj_mol'] == pytest.approx(-159.63, abs=0.05)
    assert metadata['temperature_k'] == pytest.approx(298.15, abs=0.01)
    
    # Check steps
    assert len(steps) > 0
    spontaneity_found = any("spontaneous" in step for step in steps)
    assert spontaneity_found, "Spontaneity step not found in steps"

def test_gibbs_non_spontaneous_reaction():
    """Test Gibbs calculation for a non-spontaneous reaction."""
    # ΔH = +40 kJ/mol, ΔS = +100 J/(mol·K), T = 298.15 K
    # Expected: ΔG > 0 and "non-spontaneous"
    result, steps, metadata = calculate_gibbs_free_energy_with_steps(
        40.0, "kJ/mol", 100.0, "J/(mol·K)", 298.15, "K"
    )
    
    # Check result (should be positive)
    assert result > 0
    
    # Check metadata
    assert metadata['spontaneity'] == "non-spontaneous"
    assert metadata['delta_g_kj_mol'] > 0
    
    # Check steps
    assert len(steps) > 0
    non_spontaneous_found = any("non-spontaneous" in step for step in steps)
    assert non_spontaneous_found, "Non-spontaneous step not found in steps"

def test_gibbs_crossover_temperature():
    """Test crossover temperature calculation."""
    # ΔH = +40 kJ/mol, ΔS = +100 J/(mol·K)
    # Expected: T_eq ≈ 400 K
    result, steps, metadata = calculate_gibbs_free_energy_with_steps(
        40.0, "kJ/mol", 100.0, "J/(mol·K)", 298.15, "K"
    )
    
    # Check crossover temperature
    assert metadata['crossover_temperature_k'] is not None
    t_eq = metadata['crossover_temperature_k']
    assert abs(t_eq - 400.0) < 1.0  # Within 1 K
    
    # Check steps contain crossover temperature
    crossover_found = any("T_eq" in step for step in steps)
    assert crossover_found

def test_gibbs_unit_conversions():
    """Test unit conversions in Gibbs calculations."""
    # Test with different units
    result1, _, metadata1 = calculate_gibbs_free_energy_with_steps(
        -100.0, "kJ/mol", 200.0, "J/(mol·K)", 298.15, "K"
    )
    
    result2, _, metadata2 = calculate_gibbs_free_energy_with_steps(
        -100000.0, "J/mol", 0.2, "kJ/(mol·K)", 298.15, "K"
    )
    
    # Results should be the same (within rounding)
    assert abs(result1 - result2) < 0.01

def test_gibbs_temperature_dependence_analysis():
    """Test temperature dependence analysis."""
    # Test case: ΔH > 0, ΔS > 0 (should have crossover temperature)
    analysis_steps, analysis_metadata = analyze_gibbs_temperature_dependence(
        40.0, "kJ/mol", 100.0, "J/(mol·K)"
    )
    
    # Check analysis
    assert len(analysis_steps) > 0
    assert "crossover temperature" in " ".join(analysis_steps).lower()
    assert analysis_metadata['enthalpy_sign'] == 'positive'
    assert analysis_metadata['entropy_sign'] == 'positive'
    assert analysis_metadata['crossover_temperature_k'] is not None

def test_gibbs_always_spontaneous():
    """Test case where reaction is always spontaneous."""
    # ΔH < 0, ΔS > 0 (always spontaneous)
    analysis_steps, analysis_metadata = analyze_gibbs_temperature_dependence(
        -50.0, "kJ/mol", 100.0, "J/(mol·K)"
    )
    
    # Check analysis
    assert len(analysis_steps) > 0
    assert "always spontaneous" in " ".join(analysis_steps).lower()
    assert analysis_metadata['enthalpy_sign'] == 'negative'
    assert analysis_metadata['entropy_sign'] == 'positive'

def test_gibbs_always_non_spontaneous():
    """Test case where reaction is always non-spontaneous."""
    # ΔH > 0, ΔS < 0 (always non-spontaneous)
    analysis_steps, analysis_metadata = analyze_gibbs_temperature_dependence(
        50.0, "kJ/mol", -100.0, "J/(mol·K)"
    )
    
    # Check analysis
    assert len(analysis_steps) > 0
    assert "always non-spontaneous" in " ".join(analysis_steps).lower()
    assert analysis_metadata['enthalpy_sign'] == 'positive'
    assert analysis_metadata['entropy_sign'] == 'negative'

def test_gibbs_equilibrium_case():
    """Test case where ΔG = 0 (equilibrium)."""
    # This would require very specific values, but we can test the structure
    result, steps, metadata = calculate_gibbs_free_energy_with_steps(
        0.0, "kJ/mol", 0.0, "J/(mol·K)", 298.15, "K"
    )
    
    # Check metadata structure
    assert 'spontaneity' in metadata
    assert 'delta_g_kj_mol' in metadata
    assert 'temperature_k' in metadata

def test_gibbs_invalid_inputs():
    """Test handling of invalid inputs."""
    # Test with zero temperature (should handle gracefully)
    with pytest.raises(Exception):
        calculate_gibbs_free_energy_with_steps(
            -100.0, "kJ/mol", 200.0, "J/(mol·K)", 0.0, "K"
        )


def _haber_rows():
    return [
        {"species": "N2(g)", "side": "reactant", "nu": 1, "dhf": 0.0, "s": 191.5},
        {"species": "H2(g)", "side": "reactant", "nu": 3, "dhf": 0.0, "s": 130.68},
        {"species": "NH3(g)", "side": "product", "nu": 2, "dhf": -46.11, "s": 192.77},
    ]


def test_reaction_gibbs_haber_reference():
    result, steps, metadata = calculate_reaction_gibbs_with_steps(
        _haber_rows(),
        temperature=298.15,
        temp_unit="K",
    )

    assert result["delta_h_rxn_kj_per_mol"] == pytest.approx(-92.22, abs=0.05)
    assert result["delta_s_rxn_j_per_mol_k"] == pytest.approx(-198.0, abs=0.2)
    assert result["delta_g_rxn_kj_per_mol"] == pytest.approx(-33.19, abs=0.2)
    assert result["spontaneity"] == "spontaneous"
    assert result["log10_k"] > 5.0
    assert isinstance(steps, list) and len(steps) > 5
    assert "row_contributions" in metadata


def test_reaction_gibbs_accepts_celsius():
    rows = _haber_rows()
    result_k, _, _ = calculate_reaction_gibbs_with_steps(rows, 298.15, "K")
    result_c, _, _ = calculate_reaction_gibbs_with_steps(rows, 25.0, "°C")
    assert result_c["delta_g_rxn_kj_per_mol"] == pytest.approx(result_k["delta_g_rxn_kj_per_mol"], abs=0.1)


def test_reaction_gibbs_rejects_nonpositive_temperature():
    with pytest.raises(ValueError):
        calculate_reaction_gibbs_with_steps(_haber_rows(), 0.0, "K")


def test_reaction_gibbs_requires_both_sides():
    only_reactants = [
        {"species": "A", "side": "reactant", "nu": 1, "dhf": 0.0, "s": 10.0},
    ]
    with pytest.raises(ValueError):
        calculate_reaction_gibbs_with_steps(only_reactants, 298.15, "K")


def test_reaction_gibbs_requires_positive_coefficients():
    bad_rows = [
        {"species": "A", "side": "reactant", "nu": 0, "dhf": 0.0, "s": 10.0},
        {"species": "B", "side": "product", "nu": 1, "dhf": 0.0, "s": 10.0},
    ]
    with pytest.raises(ValueError):
        calculate_reaction_gibbs_with_steps(bad_rows, 298.15, "K")


def test_reaction_gibbs_missing_fields_are_reported():
    rows = [
        {"species": "A", "side": "reactant", "nu": 1, "dhf": "", "s": 10.0},
        {"species": "B", "side": "product", "nu": 1, "dhf": 0.0, "s": None},
    ]
    with pytest.raises(ValueError) as exc:
        calculate_reaction_gibbs_with_steps(rows, 298.15, "K")
    text = str(exc.value)
    assert "ΔHf° missing" in text
    assert "S° missing" in text


def test_reaction_gibbs_dash_placeholder_is_treated_as_missing():
    rows = [
        {"species": "A", "side": "reactant", "nu": 1, "dhf": "-", "s": 10.0},
        {"species": "B", "side": "product", "nu": 1, "dhf": 0.0, "s": "-"},
    ]
    with pytest.raises(ValueError) as exc:
        calculate_reaction_gibbs_with_steps(rows, 298.15, "K")
    msg = str(exc.value)
    assert "ΔHf° missing" in msg
    assert "S° missing" in msg


def test_reaction_gibbs_unit_conversions_per_row():
    rows_mixed = [
        {"species": "A", "side": "reactant", "nu": 1, "dhf": 1000.0, "dhf_unit": "J/mol", "s": 2.0, "s_unit": "cal/(mol·K)"},
        {"species": "B", "side": "product", "nu": 1, "dhf": 1.0, "dhf_unit": "kJ/mol", "s": 8.368, "s_unit": "J/(mol·K)"},
    ]
    result, _, _ = calculate_reaction_gibbs_with_steps(rows_mixed, 298.15, "K")
    assert result["delta_h_rxn_kj_per_mol"] == pytest.approx(0.0, abs=1e-9)
    assert result["delta_s_rxn_j_per_mol_k"] == pytest.approx(0.0, abs=1e-6)
    assert result["delta_g_rxn_kj_per_mol"] == pytest.approx(0.0, abs=1e-6)


def test_reaction_gibbs_equilibrium_constant_identity():
    rows = [
        {"species": "A", "side": "reactant", "nu": 1, "dhf": 0.0, "s": 10.0},
        {"species": "A", "side": "product", "nu": 1, "dhf": 0.0, "s": 10.0},
    ]
    result, _, _ = calculate_reaction_gibbs_with_steps(rows, 298.15, "K")
    assert result["delta_g_rxn_kj_per_mol"] == pytest.approx(0.0, abs=1e-12)
    assert result["ln_k"] == pytest.approx(0.0, abs=1e-12)
    assert result["k"] == pytest.approx(1.0, abs=1e-12)


def test_reaction_gibbs_large_negative_delta_g_has_stable_large_k_display():
    rows = [
        {"species": "A", "side": "reactant", "nu": 1, "dhf": 5000.0, "s": 0.0},
        {"species": "B", "side": "product", "nu": 1, "dhf": -5000.0, "s": 0.0},
    ]
    result, _, _ = calculate_reaction_gibbs_with_steps(rows, 298.15, "K")
    assert result["k"] == float("inf")
    assert "K > 1e" in result["k_display"]


def test_reaction_gibbs_large_positive_delta_g_has_stable_small_k_display():
    rows = [
        {"species": "A", "side": "reactant", "nu": 1, "dhf": -5000.0, "s": 0.0},
        {"species": "B", "side": "product", "nu": 1, "dhf": 5000.0, "s": 0.0},
    ]
    result, _, _ = calculate_reaction_gibbs_with_steps(rows, 298.15, "K")
    assert result["k"] == pytest.approx(0.0, abs=0.0)
    assert "K < 1e" in result["k_display"]


def test_reaction_gibbs_lnK_log10K_consistency():
    result, _, _ = calculate_reaction_gibbs_with_steps(_haber_rows(), 298.15, "K")
    assert result["log10_k"] == pytest.approx(result["ln_k"] / 2.302585092994046, rel=1e-12)

if __name__ == "__main__":
    pytest.main([__file__])
