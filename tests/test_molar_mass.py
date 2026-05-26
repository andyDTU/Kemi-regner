"""
Tests for molar mass calculator.
"""

import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.formula import parse_chemical_formula, calculate_molar_mass_from_formula
from calculators.molar_mass import calculate_molar_mass_with_steps


def test_parse_chemical_formula_simple():
    """Test parsing simple chemical formulas."""
    # Test H2O
    result = parse_chemical_formula("H2O")
    assert result == {'H': 2, 'O': 1}
    
    # Test CO2
    result = parse_chemical_formula("CO2")
    assert result == {'C': 1, 'O': 2}
    
    # Test NaCl
    result = parse_chemical_formula("NaCl")
    assert result == {'Na': 1, 'Cl': 1}


def test_parse_chemical_formula_with_parentheses():
    """Test parsing formulas with parentheses."""
    # Test Ca(OH)2
    result = parse_chemical_formula("Ca(OH)2")
    assert result == {'Ca': 1, 'O': 2, 'H': 2}
    
    # Test Fe2(SO4)3
    result = parse_chemical_formula("Fe2(SO4)3")
    assert result == {'Fe': 2, 'S': 3, 'O': 12}


def test_parse_chemical_formula_complex():
    """Test parsing complex formulas."""
    # Test C6H12O6 (glucose)
    result = parse_chemical_formula("C6H12O6")
    assert result == {'C': 6, 'H': 12, 'O': 6}
    
    # Test Al2(SO4)3
    result = parse_chemical_formula("Al2(SO4)3")
    assert result == {'Al': 2, 'S': 3, 'O': 12}


def test_parse_chemical_formula_invalid():
    """Test parsing invalid formulas."""
    # Test empty formula
    with pytest.raises(ValueError, match="cannot be empty"):
        parse_chemical_formula("")
    
    # Test formula with unmatched parentheses
    with pytest.raises(ValueError, match="Unmatched"):
        parse_chemical_formula("H2O(")
    
    # Test formula with invalid characters
    with pytest.raises(ValueError, match="Invalid character"):
        parse_chemical_formula("H2O@")


def test_calculate_molar_mass_h2o():
    """Test molar mass calculation for H2O."""
    result, steps, metadata = calculate_molar_mass_with_steps("H2O")
    
    # Check result (should be approximately 18.015 g/mol)
    assert abs(result - 18.015) < 0.1
    
    # Check metadata
    assert 'element_counts' in metadata
    assert 'composition' in metadata
    assert 'element_contributions' in metadata
    
    # Check steps
    h2o_found = any("H2O" in step for step in steps)
    assert h2o_found


def test_calculate_molar_mass_c6h12o6():
    """Test molar mass calculation for C6H12O6 (glucose)."""
    result, steps, metadata = calculate_molar_mass_with_steps("C6H12O6")
    
    # Check result (should be approximately 180.156 g/mol)
    assert abs(result - 180.156) < 0.1
    
    # Check metadata
    assert 'element_counts' in metadata
    assert metadata['element_counts']['C'] == 6
    assert metadata['element_counts']['H'] == 12
    assert metadata['element_counts']['O'] == 6


def test_calculate_molar_mass_with_parentheses():
    """Test molar mass calculation with parentheses."""
    result, steps, metadata = calculate_molar_mass_with_steps("Ca(OH)2")
    
    # Check result (should be approximately 74.093 g/mol)
    assert abs(result - 74.093) < 0.1
    
    # Check element counts
    assert metadata['element_counts']['Ca'] == 1
    assert metadata['element_counts']['O'] == 2
    assert metadata['element_counts']['H'] == 2


def test_calculate_molar_mass_unknown_element():
    """Test molar mass calculation with unknown element."""
    with pytest.raises(ValueError, match="Unknown element"):
        calculate_molar_mass_with_steps("X2O")


def test_calculate_molar_mass_invalid_formula():
    """Test molar mass calculation with invalid formula."""
    with pytest.raises(ValueError, match="Error parsing formula"):
        calculate_molar_mass_with_steps("H2O(")


if __name__ == "__main__":
    pytest.main([__file__])
