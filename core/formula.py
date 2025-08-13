"""
Chemical formula parsing utilities.
Shared between molar mass and stoichiometry calculators.
"""

import re
from typing import Dict, List, Tuple, Any
from core.data import get_atomic_mass


def parse_chemical_formula(formula: str) -> Dict[str, int]:
    """
    Parse a chemical formula and return element counts.
    
    Args:
        formula: Chemical formula string (e.g., "H2O", "Fe2(SO4)3")
    
    Returns:
        Dictionary mapping element symbols to their counts
    
    Raises:
        ValueError: If formula is malformed or contains invalid elements
    """
    if not formula or not formula.strip():
        raise ValueError("Formula cannot be empty")
    
    formula = formula.strip()
    
    # Remove any existing coefficients at the beginning
    formula = re.sub(r'^\d+', '', formula)
    
    # Parse the formula recursively
    element_counts = {}
    _parse_formula_recursive(formula, 1, element_counts)
    
    return element_counts


def _parse_formula_recursive(formula: str, multiplier: int, element_counts: Dict[str, int]) -> None:
    """
    Recursively parse a chemical formula.
    
    Args:
        formula: Formula string to parse
        multiplier: Current multiplier for this section
        element_counts: Dictionary to accumulate element counts
    """
    i = 0
    while i < len(formula):
        char = formula[i]
        
        if char.isupper():
            # Start of an element
            element = char
            i += 1
            
            # Check for second lowercase letter (e.g., Fe, Cl)
            if i < len(formula) and formula[i].islower():
                element += formula[i]
                i += 1
            
            # Check for subscript number
            count = 1
            if i < len(formula) and formula[i].isdigit():
                count_str = ""
                while i < len(formula) and formula[i].isdigit():
                    count_str += formula[i]
                    i += 1
                count = int(count_str)
            
            # Validate element exists and add to counts
            try:
                # Verify element exists by getting its atomic mass
                get_atomic_mass(element)
                element_counts[element] = element_counts.get(element, 0) + (count * multiplier)
            except ValueError:
                raise ValueError(f"Unknown element: {element}")
        
        elif char == '(':
            # Start of parentheses group
            i += 1
            start = i
            paren_count = 1
            
            # Find matching closing parenthesis
            while i < len(formula) and paren_count > 0:
                if formula[i] == '(':
                    paren_count += 1
                elif formula[i] == ')':
                    paren_count -= 1
                i += 1
            
            if paren_count > 0:
                raise ValueError("Unmatched opening parenthesis")
            
            # Extract content inside parentheses
            content = formula[start:i-1]
            
            # Check for subscript after closing parenthesis
            group_multiplier = 1
            if i < len(formula) and formula[i].isdigit():
                group_mult_str = ""
                while i < len(formula) and formula[i].isdigit():
                    group_mult_str += formula[i]
                    i += 1
                group_multiplier = int(group_mult_str)
            
            # Recursively parse the content inside parentheses
            _parse_formula_recursive(content, multiplier * group_multiplier, element_counts)
        
        elif char == ')':
            raise ValueError("Unmatched closing parenthesis")
        
        elif char.isspace():
            # Skip whitespace
            i += 1
        
        else:
            # Invalid character
            raise ValueError(f"Invalid character in formula: {char}")


def calculate_molar_mass_from_formula(formula: str) -> float:
    """
    Calculate molar mass from a chemical formula.
    
    Args:
        formula: Chemical formula string
    
    Returns:
        Molar mass in g/mol
    """
    element_counts = parse_chemical_formula(formula)
    total_mass = 0.0
    
    for element, count in element_counts.items():
        atomic_mass = get_atomic_mass(element)
        total_mass += count * atomic_mass
    
    return total_mass


def get_formula_metadata(formula: str) -> Dict[str, Any]:
    """
    Get comprehensive metadata about a chemical formula.
    
    Args:
        formula: Chemical formula string
    
    Returns:
        Dictionary containing:
        - element_counts: Dict[str, int]
        - molar_mass: float
        - composition: Dict[str, float] (percentage by mass)
        - element_contributions: Dict[str, Dict] (detailed breakdown)
    """
    element_counts = parse_chemical_formula(formula)
    molar_mass = calculate_molar_mass_from_formula(formula)
    
    # Calculate composition percentages
    composition = {}
    element_contributions = {}
    
    for element, count in element_counts.items():
        atomic_mass = get_atomic_mass(element)
        contribution = count * atomic_mass
        percentage = (contribution / molar_mass) * 100
        
        composition[element] = percentage
        element_contributions[element] = {
            'count': count,
            'atomic_mass': atomic_mass,
            'contribution': contribution,
            'percentage': percentage
        }
    
    return {
        'element_counts': element_counts,
        'molar_mass': molar_mass,
        'composition': composition,
        'element_contributions': element_contributions
    }
