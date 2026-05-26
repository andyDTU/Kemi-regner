"""
Tests for stoichiometry calculator.
"""

import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.reaction import balance_equation, parse_reaction_equation
from calculators.stoichiometry import calculate_limiting_reagent_with_steps, calculate_dilution_with_steps


def test_parse_reaction_equation():
    """Test reaction equation parsing."""
    # Test basic parsing
    result = parse_reaction_equation("Fe2(SO4)3 + KOH -> Fe(OH)3 + K2SO4")
    assert result['reactants'] == ['Fe2(SO4)3', 'KOH']
    assert result['products'] == ['Fe(OH)3', 'K2SO4']
    assert result['species_order'] == ['Fe2(SO4)3', 'KOH', 'Fe(OH)3', 'K2SO4']
    
    # Test different arrow symbols
    result = parse_reaction_equation("C2H5OH + O2 => CO2 + H2O")
    assert result['reactants'] == ['C2H5OH', 'O2']
    assert result['products'] == ['CO2', 'H2O']
    
    # Test with existing coefficients (should be removed)
    result = parse_reaction_equation("2H2 + O2 -> 2H2O")
    assert result['reactants'] == ['H2', 'O2']
    assert result['products'] == ['H2O']


def test_balance_equation_fe2so4():
    """Test balancing Fe2(SO4)3 + KOH -> Fe(OH)3 + K2SO4."""
    result = balance_equation("Fe2(SO4)3 + KOH -> Fe(OH)3 + K2SO4")
    
    assert result['reactants'] == ['Fe2(SO4)3', 'KOH']
    assert result['products'] == ['Fe(OH)3', 'K2SO4']
    
    # Check coefficients: [1, 6, 2, 3] in species order
    expected_coeffs = [1, 6, 2, 3]
    assert result['coefficients'] == expected_coeffs
    
    # Check formatted equation
    assert "Fe2(SO4)3 + 6KOH → 2Fe(OH)3 + 3K2SO4" in result['equation_str']


def test_balance_equation_ethanol():
    """Test balancing C2H5OH + O2 -> CO2 + H2O."""
    result = balance_equation("C2H5OH + O2 -> CO2 + H2O")
    
    assert result['reactants'] == ['C2H5OH', 'O2']
    assert result['products'] == ['CO2', 'H2O']
    
    # Check coefficients: [1, 3, 2, 3] in species order
    expected_coeffs = [1, 3, 2, 3]
    assert result['coefficients'] == expected_coeffs
    
    # Check formatted equation
    assert "C2H5OH + 3O2 → 2CO2 + 3H2O" in result['equation_str']


def test_balance_equation_simple():
    """Test balancing simple reactions."""
    # H2 + O2 -> H2O
    result = balance_equation("H2 + O2 -> H2O")
    assert result['coefficients'] == [2, 1, 2]
    
    # N2 + H2 -> NH3
    result = balance_equation("N2 + H2 -> NH3")
    assert result['coefficients'] == [1, 3, 2]


def test_limiting_reagent_n2_h2():
    """Test limiting reagent calculation for N2 + H2 -> NH3."""
    equation = "N2 + H2 -> NH3"
    reactant_inputs = [
        {'formula': 'N2', 'mode': 'mass', 'value': 10.0, 'unit': 'g'},
        {'formula': 'H2', 'mode': 'mass', 'value': 10.0, 'unit': 'g'}
    ]
    
    result, steps, metadata = calculate_limiting_reagent_with_steps(
        equation, reactant_inputs, 'NH3'
    )
    
    # Check limiting reagent
    assert result['limiting_reagent'] == 'N2'
    
    # Check theoretical yield (should be approximately 12.17 g)
    theoretical_yield = result['theoretical_yield_mass']
    assert abs(theoretical_yield - 12.17) < 0.05
    
    # Check that steps contain key information
    steps_text = '\n'.join(steps)
    assert 'Limiting reagent: N2' in steps_text
    assert 'theoretical yield' in steps_text.lower()


def test_limiting_reagent_with_percent_yield():
    """Test limiting reagent with percent yield calculation."""
    equation = "N2 + H2 -> NH3"
    reactant_inputs = [
        {'formula': 'N2', 'mode': 'mass', 'value': 10.0, 'unit': 'g'},
        {'formula': 'H2', 'mode': 'mass', 'value': 10.0, 'unit': 'g'}
    ]
    
    result, steps, metadata = calculate_limiting_reagent_with_steps(
        equation, reactant_inputs, 'NH3', actual_yield=10.00
    )
    
    # Check percent yield (should be approximately 82.2%)
    percent_yield = result['percent_yield']
    assert abs(percent_yield - 82.2) < 0.3
    
    # Check that steps contain percent yield calculation
    steps_text = '\n'.join(steps)
    assert 'percent yield' in steps_text.lower()


def test_limiting_reagent_solution_mode():
    """Test limiting reagent with solution inputs."""
    equation = "HCl + NaOH -> NaCl + H2O"
    reactant_inputs = [
        {'formula': 'HCl', 'mode': 'solution', 'value': 2.0, 'unit': 'M', 'volume': 100},
        {'formula': 'NaOH', 'mode': 'solution', 'value': 1.0, 'unit': 'M', 'volume': 150}
    ]
    
    result, steps, metadata = calculate_limiting_reagent_with_steps(
        equation, reactant_inputs, 'NaCl'
    )
    
    # Check that solution mode works
    assert result['limiting_reagent'] is not None
    assert result['theoretical_yield_moles'] > 0
    
    # Check that steps contain solution calculations
    steps_text = '\n'.join(steps)
    assert 'M ×' in steps_text  # Should show molarity × volume calculation


def test_dilution_calculation():
    """Test dilution calculation M1V1 = M2V2."""
    # Given M1=2.00 M, M2=0.250 M, V2=0.250 L → expect V1 ≈ 0.03125 L
    result, steps, metadata = calculate_dilution_with_steps(
        m1=2.00, m2=0.250, v2=0.250,
        m1_unit="M", m2_unit="M", v2_unit="L"
    )
    
    assert result['unknown'] == 'V1'
    expected_v1 = 0.03125
    assert abs(result['result'] - expected_v1) < 1e-5
    
    # Check that steps contain the calculation
    steps_text = '\n'.join(steps)
    assert 'M₁V₁ = M₂V₂' in steps_text
    assert 'V₁ = (M₂ × V₂) ÷ M₁' in steps_text


def test_dilution_with_milliliters():
    """Test dilution with milliliter units."""
    result, steps, metadata = calculate_dilution_with_steps(
        m1=1.0, v1=50, m2=0.1, v2=None,
        m1_unit="M", v1_unit="mL", m2_unit="M", v2_unit="L"
    )
    
    assert result['unknown'] == 'V2'
    expected_v2 = 0.5  # 1.0 M × 50 mL = 0.1 M × 500 mL
    assert abs(result['result'] - expected_v2) < 1e-5
    
    # Check that steps show unit conversion
    steps_text = '\n'.join(steps)
    assert 'mL =' in steps_text


def test_dilution_error_handling():
    """Test dilution error handling."""
    # Test with too many unknowns
    with pytest.raises(ValueError, match="Exactly three"):
        calculate_dilution_with_steps(m1=1.0, v1=1.0, m2=1.0, v2=1.0)
    
    # Test with too few knowns
    with pytest.raises(ValueError, match="Exactly three"):
        calculate_dilution_with_steps(m1=1.0, v1=1.0)


def test_reaction_parsing_errors():
    """Test reaction parsing error handling."""
    # Test empty equation
    with pytest.raises(ValueError, match="cannot be empty"):
        parse_reaction_equation("")
    
    # Test equation without arrow
    with pytest.raises(ValueError, match="must contain an arrow"):
        parse_reaction_equation("H2 + O2 H2O")
    
    # Test equation with no reactants
    with pytest.raises(ValueError, match="No reactants found"):
        parse_reaction_equation("-> H2O")
    
    # Test equation with no products
    with pytest.raises(ValueError, match="No products found"):
        parse_reaction_equation("H2 + O2 ->")


def test_limiting_reagent_errors():
    """Test limiting reagent error handling."""
    # Test with invalid equation
    with pytest.raises(ValueError, match="Could not balance equation"):
        calculate_limiting_reagent_with_steps(
            "Invalid -> Equation", [], 'Product'
        )
    
    # Test with target product not in equation
    equation = "H2 + O2 -> H2O"
    reactant_inputs = [
        {'formula': 'H2', 'mode': 'mass', 'value': 10.0, 'unit': 'g'}
    ]
    
    with pytest.raises(ValueError, match="not found in products"):
        calculate_limiting_reagent_with_steps(
            equation, reactant_inputs, 'CO2'
        )


if __name__ == "__main__":
    pytest.main([__file__])
