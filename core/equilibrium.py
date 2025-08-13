"""
Core equilibrium utilities for chemical calculations.
Includes ICE table helpers, Kc/Kp conversions, and solubility calculations.
"""

import sympy as sp
from typing import Dict, List, Tuple, Any, Optional
from core.data import get_gas_constant


def solve_quadratic_equation(a: float, b: float, c: float) -> float:
    """
    Solve quadratic equation ax² + bx + c = 0.
    
    Args:
        a, b, c: Coefficients of quadratic equation
    
    Returns:
        Positive root (or smallest positive if multiple positive roots)
    
    Raises:
        ValueError: If no positive roots exist
    """
    if a == 0:
        # Linear equation bx + c = 0
        if b == 0:
            raise ValueError("No solution: both a and b are zero")
        x = -c / b
        if x > 0:
            return x
        else:
            raise ValueError("No positive solution")
    
    # Quadratic equation
    discriminant = b**2 - 4*a*c
    
    if discriminant < 0:
        raise ValueError("No real solutions")
    
    sqrt_disc = discriminant**0.5
    x1 = (-b + sqrt_disc) / (2*a)
    x2 = (-b - sqrt_disc) / (2*a)
    
    # Return the positive root, or the smaller positive if both are positive
    positive_roots = [x for x in [x1, x2] if x > 0]
    
    if not positive_roots:
        raise ValueError("No positive solutions")
    
    return min(positive_roots)


def solve_cubic_equation(a: float, b: float, c: float, d: float) -> float:
    """
    Solve cubic equation ax³ + bx² + cx + d = 0.
    
    Args:
        a, b, c, d: Coefficients of cubic equation
    
    Returns:
        Smallest positive real root
    
    Raises:
        ValueError: If no positive real roots exist
    """
    if a == 0:
        # Fall back to quadratic
        return solve_quadratic_equation(b, c, d)
    
    # Use SymPy for cubic equations
    x = sp.Symbol('x')
    equation = a*x**3 + b*x**2 + c*x + d
    solutions = sp.solve(equation, x)
    
    # Find positive real roots
    positive_real_roots = []
    for sol in solutions:
        if sol.is_real and sol > 0:
            positive_real_roots.append(float(sol))
    
    if not positive_real_roots:
        raise ValueError("No positive real solutions")
    
    return min(positive_real_roots)


def solve_polynomial_equation(coefficients: List[float]) -> float:
    """
    Solve polynomial equation using SymPy.
    
    Args:
        coefficients: List of coefficients [a_n, a_{n-1}, ..., a_0] for a_n*x^n + ...
    
    Returns:
        Smallest positive real root
    
    Raises:
        ValueError: If no positive real roots exist
    """
    x = sp.Symbol('x')
    
    # Build polynomial
    polynomial = 0
    for i, coeff in enumerate(coefficients):
        if coeff != 0:
            polynomial += coeff * x**(len(coefficients) - 1 - i)
    
    solutions = sp.solve(polynomial, x)
    
    # Find positive real roots
    positive_real_roots = []
    for sol in solutions:
        if sol.is_real and sol > 0:
            positive_real_roots.append(float(sol))
    
    if not positive_real_roots:
        raise ValueError("No positive real solutions")
    
    return min(positive_real_roots)


def convert_kc_to_kp(kc: float, temperature: float, delta_n: int) -> float:
    """
    Convert equilibrium constant Kc to Kp.
    
    Args:
        kc: Equilibrium constant in concentration units
        temperature: Temperature in Kelvin
        delta_n: Change in moles of gas (products - reactants)
    
    Returns:
        Equilibrium constant Kp in pressure units
    """
    R = get_gas_constant()  # J/(mol·K)
    
    if delta_n == 0:
        return kc
    
    # Kp = Kc * (RT)^(Δn)
    kp = kc * (R * temperature / 1000)**delta_n  # Convert to kPa for reasonable numbers
    
    return kp


def convert_kp_to_kc(kp: float, temperature: float, delta_n: int) -> float:
    """
    Convert equilibrium constant Kp to Kc.
    
    Args:
        kp: Equilibrium constant in pressure units
        temperature: Temperature in Kelvin
        delta_n: Change in moles of gas (products - reactants)
    
    Returns:
        Equilibrium constant Kc in concentration units
    """
    R = get_gas_constant()  # J/(mol·K)
    
    if delta_n == 0:
        return kp
    
    # Kc = Kp / (RT)^(Δn)
    kc = kp / (R * temperature / 1000)**delta_n
    
    return kc


def calculate_reaction_quotient(concentrations: Dict[str, float], 
                               stoichiometry: Dict[str, int]) -> float:
    """
    Calculate reaction quotient Q.
    
    Args:
        concentrations: Dictionary mapping species to concentrations
        stoichiometry: Dictionary mapping species to stoichiometric coefficients
    
    Returns:
        Reaction quotient Q
    """
    numerator = 1.0
    denominator = 1.0
    
    for species, coeff in stoichiometry.items():
        if coeff > 0:  # Product
            conc = concentrations.get(species, 0.0)
            if conc < 0:  # Handle negative concentrations gracefully
                conc = 0.0
            numerator *= conc**coeff
        else:  # Reactant
            conc = concentrations.get(species, 0.0)
            if conc < 0:  # Handle negative concentrations gracefully
                conc = 0.0
            denominator *= conc**abs(coeff)
    
    if denominator == 0:
        return float('inf')
    
    result = numerator / denominator
    
    # Ensure we return a real number
    if isinstance(result, complex):
        return float(result.real)
    
    return float(result)


def determine_reaction_direction(Q: float, K: float) -> str:
    """
    Determine reaction direction based on Q vs K.
    
    Args:
        Q: Reaction quotient
        K: Equilibrium constant
    
    Returns:
        Direction: "Reaction proceeds to products (right)", "Reaction proceeds to reactants (left)", or "System is at equilibrium"
    """
    if abs(Q - K) < 1e-10:
        return "System is at equilibrium"
    elif Q < K:
        return "Reaction proceeds to products (right)"
    else:
        return "Reaction proceeds to reactants (left)"


def calculate_solubility_product(solubility: float, stoichiometry: Dict[str, int]) -> float:
    """
    Calculate solubility product Ksp from molar solubility.
    
    Args:
        solubility: Molar solubility in mol/L
        stoichiometry: Dictionary mapping ions to stoichiometric coefficients
    
    Returns:
        Solubility product Ksp
    """
    ksp = 1.0
    
    for ion, coeff in stoichiometry.items():
        if coeff > 0:
            ksp *= (solubility * coeff)**coeff
    
    return ksp


def solve_solubility_from_ksp(ksp: float, stoichiometry: Dict[str, int], 
                              common_ion_concentrations: Optional[Dict[str, float]] = None) -> float:
    """
    Solve for molar solubility from Ksp.
    
    Args:
        ksp: Solubility product constant
        stoichiometry: Dictionary mapping ions to stoichiometric coefficients
        common_ion_concentrations: Optional initial concentrations of common ions
    
    Returns:
        Molar solubility in mol/L
    """
    if common_ion_concentrations is None:
        common_ion_concentrations = {}
    
    # Handle simple cases first
    if len(stoichiometry) == 2:  # Binary salt
        ions = list(stoichiometry.keys())
        coeff1, coeff2 = stoichiometry[ions[0]], stoichiometry[ions[1]]
        
        if coeff1 == 1 and coeff2 == 1:  # 1:1 salt
            return ksp**0.5
        elif coeff1 == 1 and coeff2 == 2:  # 1:2 salt
            return (ksp / 4)**(1/3)
        elif coeff1 == 2 and coeff2 == 1:  # 2:1 salt
            return (ksp / 4)**(1/3)
        elif coeff1 == 1 and coeff2 == 3:  # 1:3 salt
            return (ksp / 27)**(1/4)
        elif coeff1 == 3 and coeff2 == 1:  # 3:1 salt
            return (ksp / 27)**(1/4)
    
    # General case: solve polynomial equation
    # Build polynomial coefficients for solubility equation
    # This is complex and depends on the specific stoichiometry
    # For now, use a numerical approach
    
    # Use SymPy's nsolve for numerical solution
    s = sp.Symbol('s')
    
    # Build Ksp expression
    ksp_expr = 1.0
    for ion, coeff in stoichiometry.items():
        if coeff > 0:
            # [ion] = coeff * s + initial_conc
            initial_conc = common_ion_concentrations.get(ion, 0.0)
            ksp_expr *= (coeff * s + initial_conc)**coeff
    
    # Solve Ksp_expr = Ksp
    equation = ksp_expr - ksp
    
    try:
        # Try to find solution starting from a reasonable guess
        guess = (ksp / 10)**0.5  # Rough estimate
        solution = sp.nsolve(equation, s, guess)
        
        if solution > 0:
            return float(solution)
        else:
            raise ValueError("No positive solubility found")
    except:
        raise ValueError("Could not solve solubility equation numerically")


def create_ice_table(reactants: List[str], products: List[str], 
                    initial_concentrations: Dict[str, float],
                    stoichiometry: Dict[str, int]) -> Dict[str, List[float]]:
    """
    Create ICE table for equilibrium calculations.
    
    Args:
        reactants: List of reactant species
        products: List of product species
        initial_concentrations: Initial concentrations
        stoichiometry: Stoichiometric coefficients
    
    Returns:
        Dictionary with ICE table data
    """
    all_species = reactants + products
    
    # Initialize ICE table
    ice_table = {
        'species': all_species,
        'initial': [],
        'change': [],
        'equilibrium': []
    }
    
    for species in all_species:
        # Initial concentration
        initial = initial_concentrations.get(species, 0.0)
        ice_table['initial'].append(initial)
        
        # Change (will be filled in later)
        ice_table['change'].append(0.0)
        
        # Equilibrium (will be filled in later)
        ice_table['equilibrium'].append(0.0)
    
    return ice_table


def solve_ice_table(ice_table: Dict[str, List[float]], 
                   stoichiometry: Dict[str, int], 
                   K: float) -> Tuple[float, Dict[str, float]]:
    """
    Solve ICE table for equilibrium concentrations.
    
    Args:
        ice_table: ICE table data
        stoichiometry: Stoichiometric coefficients
        K: Equilibrium constant
    
    Returns:
        Tuple of (extent of reaction, equilibrium concentrations)
    """
    species = ice_table['species']
    initial = ice_table['initial']
    
    # Set up equation: K = [C]^c[D]^d / ([A]^a[B]^b)
    # where [A] = [A]_0 - a*x, [B] = [B]_0 - b*x, etc.
    # and [C] = [C]_0 + c*x, [D] = [D]_0 + d*x, etc.
    
    x = sp.Symbol('x')
    
    # Build K expression
    numerator = 1.0
    denominator = 1.0
    
    for i, species_name in enumerate(species):
        coeff = stoichiometry.get(species_name, 0)
        if coeff > 0:  # Product
            conc_expr = initial[i] + coeff * x
            numerator *= conc_expr**coeff
        elif coeff < 0:  # Reactant
            conc_expr = initial[i] + coeff * x  # coeff is negative
            denominator *= conc_expr**abs(coeff)
    
    # Equation: K = numerator / denominator
    equation = numerator - K * denominator
    
    # Solve for x
    try:
        # Try different initial guesses including negative values for product-heavy systems
        guesses = [0.1, 0.01, 0.001, 1.0, -0.1, -0.01, -0.001, -1.0]
        solution = None
        
        for guess in guesses:
            try:
                sol = sp.nsolve(equation, x, guess)
                # Check if all concentrations are non-negative
                valid = True
                for i, species_name in enumerate(species):
                    coeff = stoichiometry.get(species_name, 0)
                    if coeff > 0:  # Product
                        conc = initial[i] + coeff * float(sol)
                    else:  # Reactant
                        conc = initial[i] + coeff * float(sol)
                    
                    if conc < -1e-10:  # Allow small negative values due to numerical precision
                        valid = False
                        break
                
                if valid:
                    solution = float(sol)
                    break
            except:
                continue
        
        if solution is None:
            raise ValueError("Could not find valid solution")
        
        # Calculate equilibrium concentrations
        equilibrium_concentrations = {}
        for i, species_name in enumerate(species):
            coeff = stoichiometry.get(species_name, 0)
            if coeff > 0:  # Product
                conc = initial[i] + coeff * solution
            else:  # Reactant
                conc = initial[i] + coeff * solution
            
            equilibrium_concentrations[species_name] = max(0.0, conc)
        
        return solution, equilibrium_concentrations
        
    except Exception as e:
        raise ValueError(f"Could not solve ICE table: {e}")
