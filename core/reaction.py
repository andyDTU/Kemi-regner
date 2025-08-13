"""
Chemical reaction parsing and balancing utilities.
Uses SymPy for linear algebra to balance chemical equations.
"""

import re
from typing import Dict, List, Tuple, Any
import sympy as sp
from core.formula import parse_chemical_formula


def parse_reaction_equation(equation_str: str) -> Dict[str, Any]:
    """
    Parse a chemical reaction equation.
    
    Args:
        equation_str: Reaction string like "Fe2(SO4)3 + KOH -> Fe(OH)3 + K2SO4"
    
    Returns:
        Dictionary with:
        - reactants: List of reactant formulas
        - products: List of product formulas
        - species_order: Combined list of all species in order
        - raw_equation: Original equation string
    """
    if not equation_str or not equation_str.strip():
        raise ValueError("Equation cannot be empty")
    
    # Check if the string looks like a valid chemical reaction
    if len(equation_str.strip()) < 5:  # Too short to be a valid reaction
        raise ValueError("Equation too short to be valid")
    
    # Normalize arrow symbols
    equation = equation_str.strip()
    equation = re.sub(r'[=]=?>?', '->', equation)
    
    # Split by arrow
    if '->' not in equation:
        raise ValueError("Equation must contain an arrow (->, =>, or =)")
    
    left_side, right_side = equation.split('->', 1)
    
    # Parse reactants and products
    reactants = _parse_side(left_side.strip())
    products = _parse_side(right_side.strip())
    
    if not reactants:
        raise ValueError("No reactants found")
    if not products:
        raise ValueError("No products found")
    
    # Validate that all species are valid chemical formulas
    for species in reactants + products:
        try:
            from core.formula import parse_chemical_formula
            parse_chemical_formula(species)
        except ValueError as e:
            raise ValueError(f"Invalid chemical formula '{species}': {e}")
    
    # Create species order list
    species_order = reactants + products
    
    return {
        'reactants': reactants,
        'products': products,
        'species_order': species_order,
        'raw_equation': equation_str
    }


def _parse_side(side_str: str) -> List[str]:
    """
    Parse one side of a reaction equation.
    
    Args:
        side_str: String containing species separated by +
    
    Returns:
        List of chemical formulas
    """
    if not side_str.strip():
        return []
    
    # Split by + and clean up
    species = [s.strip() for s in side_str.split('+')]
    species = [s for s in species if s]
    
    # Remove any existing coefficients and states
    cleaned_species = []
    for species_str in species:
        # Remove coefficients at the beginning
        species_str = re.sub(r'^\d+', '', species_str)
        # Remove state indicators (s), (l), (g), (aq)
        species_str = re.sub(r'\([slgaq]\)', '', species_str)
        # Remove any remaining whitespace
        species_str = species_str.strip()
        if species_str:
            cleaned_species.append(species_str)
    
    return cleaned_species


def balance_equation(equation_str: str) -> Dict[str, Any]:
    """
    Balance a chemical equation using linear algebra.
    
    Args:
        equation_str: Reaction string to balance
    
    Returns:
        Dictionary with:
        - reactants: List of reactant formulas
        - products: List of product formulas
        - coefficients: List of coefficients matching species_order
        - equation_tex: LaTeX formatted balanced equation
        - equation_str: String formatted balanced equation
        - species_order: List of all species in order
        - steps: List of calculation steps
    """
    # Parse the equation
    parsed = parse_reaction_equation(equation_str)
    reactants = parsed['reactants']
    products = parsed['products']
    species_order = parsed['species_order']
    
    # Build element matrix
    element_matrix, elements = _build_element_matrix(species_order)
    
    # Solve the system
    coefficients = _solve_balancing_system(element_matrix, species_order)
    
    # Generate formatted output
    equation_tex = _format_equation_latex(reactants, products, coefficients, species_order)
    equation_str = _format_equation_string(reactants, products, coefficients, species_order)
    
    # Generate steps
    steps = _generate_balancing_steps(elements, element_matrix, coefficients, species_order)
    
    return {
        'reactants': reactants,
        'products': products,
        'coefficients': coefficients,
        'equation_tex': equation_tex,
        'equation_str': equation_str,
        'species_order': species_order,
        'steps': steps
    }


def _build_element_matrix(species_order: List[str]) -> Tuple[List[List[int]], List[str]]:
    """
    Build the element matrix for balancing.
    
    Args:
        species_order: List of all species in the reaction
    
    Returns:
        Tuple of (matrix, elements) where matrix[i][j] is the count of element i in species j
    """
    # Get all unique elements
    all_elements = set()
    for species in species_order:
        element_counts = parse_chemical_formula(species)
        all_elements.update(element_counts.keys())
    
    elements = sorted(list(all_elements))
    
    # Build matrix
    matrix = []
    for element in elements:
        row = []
        for species in species_order:
            element_counts = parse_chemical_formula(species)
            count = element_counts.get(element, 0)
            row.append(count)
        matrix.append(row)
    
    return matrix, elements


def _solve_balancing_system(element_matrix: List[List[int]], species_order: List[str]) -> List[int]:
    """
    Solve the balancing system using SymPy to find smallest integer coefficients.
    
    Args:
        element_matrix: Element count matrix
        species_order: List of species
    
    Returns:
        List of coefficients
    """
    # Convert to SymPy matrix
    matrix = sp.Matrix(element_matrix)
    
    # Use nullspace method to find solution
    nullspace = matrix.nullspace()
    if not nullspace:
        raise ValueError("Could not balance equation - no solution found")
    
    # Take the first nullspace vector
    solution = nullspace[0]
    
    # Convert to floats and find the smallest positive solution
    coefficients = [float(x) for x in solution]
    
    # Find the smallest positive coefficient
    min_pos_coeff = min([c for c in coefficients if c > 0])
    
    # Scale to make the smallest positive coefficient = 1
    scale_factor = 1.0 / min_pos_coeff
    coefficients = [c * scale_factor for c in coefficients]
    
    # Convert to integers using LCM method
    coefficients = _scale_to_integers(coefficients)
    
    # Ensure all coefficients are positive
    coefficients = [abs(c) for c in coefficients]
    
    # Reduce to smallest integers
    coefficients = _reduce_coefficients(coefficients)
    
    return coefficients


def _reduce_coefficients(coefficients: List[int]) -> List[int]:
    """
    Reduce coefficients to smallest possible integers.
    
    Args:
        coefficients: List of integer coefficients
    
    Returns:
        List of reduced coefficients
    """
    if not coefficients:
        return coefficients
    
    # Find the GCD of all coefficients
    gcd_val = coefficients[0]
    for coeff in coefficients[1:]:
        gcd_val = sp.gcd(gcd_val, coeff)
    
    # If GCD > 1, divide all coefficients by it
    if gcd_val > 1:
        coefficients = [c // gcd_val for c in coefficients]
    
    return coefficients


def _verify_solution(element_matrix: List[List[int]], coefficients: List[int]) -> bool:
    """
    Verify that the coefficients balance the equation.
    
    Args:
        element_matrix: Element count matrix
        coefficients: List of coefficients
    
    Returns:
        True if balanced, False otherwise
    """
    for row in element_matrix:
        # Calculate the sum for each element
        element_sum = sum(row[i] * coefficients[i] for i in range(len(coefficients)))
        # The sum should be 0 for a balanced equation
        if abs(element_sum) > 1e-10:  # Allow for small floating point errors
            return False
    return True


def _scale_to_integers(coefficients: List[float]) -> List[int]:
    """
    Scale coefficients to smallest positive integers.
    
    Args:
        coefficients: List of float coefficients
    
    Returns:
        List of integer coefficients
    """
    # Find the least common multiple of denominators
    denominators = []
    for coeff in coefficients:
        if coeff != 0:
            # Convert to fraction and get denominator
            frac = sp.Rational(coeff).limit_denominator(1000)
            denominators.append(frac.denominator)
    
    if not denominators:
        return [1] * len(coefficients)
    
    # Calculate LCM of denominators
    lcm_denom = denominators[0]
    for denom in denominators[1:]:
        lcm_denom = sp.lcm(lcm_denom, denom)
    
    # Scale coefficients
    scaled_coeffs = []
    for coeff in coefficients:
        scaled = int(round(coeff * lcm_denom))
        scaled_coeffs.append(scaled)
    
    # Find GCD and reduce to smallest integers
    gcd_coeffs = scaled_coeffs[0]
    for coeff in scaled_coeffs[1:]:
        gcd_coeffs = sp.gcd(gcd_coeffs, coeff)
    
    if gcd_coeffs > 1:
        scaled_coeffs = [c // gcd_coeffs for c in scaled_coeffs]
    
    return scaled_coeffs


def _format_equation_latex(reactants: List[str], products: List[str], 
                           coefficients: List[int], species_order: List[str]) -> str:
    """Format balanced equation in LaTeX."""
    reactant_coeffs = coefficients[:len(reactants)]
    product_coeffs = coefficients[len(reactants):]
    
    # Format reactants
    reactant_terms = []
    for i, reactant in enumerate(reactants):
        coeff = reactant_coeffs[i]
        if coeff == 1:
            reactant_terms.append(reactant)
        else:
            reactant_terms.append(f"{coeff}{reactant}")
    
    # Format products
    product_terms = []
    for i, product in enumerate(products):
        coeff = product_coeffs[i]
        if coeff == 1:
            product_terms.append(product)
        else:
            product_terms.append(f"{coeff}{product}")
    
    return " + ".join(reactant_terms) + " \\rightarrow " + " + ".join(product_terms)


def _format_equation_string(reactants: List[str], products: List[str], 
                           coefficients: List[int], species_order: List[str]) -> str:
    """Format balanced equation as string."""
    reactant_coeffs = coefficients[:len(reactants)]
    product_coeffs = coefficients[len(reactants):]
    
    # Format reactants
    reactant_terms = []
    for i, reactant in enumerate(reactants):
        coeff = reactant_coeffs[i]
        if coeff == 1:
            reactant_terms.append(reactant)
        else:
            reactant_terms.append(f"{coeff}{reactant}")
    
    # Format products
    product_terms = []
    for i, product in enumerate(products):
        coeff = product_coeffs[i]
        if coeff == 1:
            product_terms.append(product)
        else:
            product_terms.append(f"{coeff}{product}")
    
    return " + ".join(reactant_terms) + " → " + " + ".join(product_terms)


def _generate_balancing_steps(elements: List[str], element_matrix: List[List[int]], 
                             coefficients: List[int], species_order: List[str]) -> List[str]:
    """Generate step-by-step explanation of balancing."""
    steps = []
    
    steps.append("**Step 1: Identify all elements in the reaction**")
    steps.append(f"Elements found: {', '.join(elements)}")
    
    steps.append("\n**Step 2: Build element matrix**")
    steps.append("Each row represents an element, each column represents a species:")
    for i, element in enumerate(elements):
        row_str = f"{element}: " + " ".join([str(x) for x in element_matrix[i]])
        steps.append(row_str)
    
    steps.append("\n**Step 3: Solve the system**")
    steps.append("Using linear algebra to find coefficients that balance all elements:")
    for i, element in enumerate(elements):
        equation = f"{element}: "
        terms = []
        for j, coeff in enumerate(coefficients):
            if element_matrix[i][j] != 0:
                terms.append(f"{coeff} × {element_matrix[i][j]}")
        equation += " + ".join(terms) + " = 0"
        steps.append(equation)
    
    steps.append("\n**Step 4: Scale to smallest integers**")
    steps.append(f"Final coefficients: {coefficients}")
    
    return steps
