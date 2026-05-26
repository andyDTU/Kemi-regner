"""
Equilibrium calculator for chemical calculations.
Includes ICE table solver, Kc/Kp conversions, reaction quotient, and solubility calculations.
"""

import math
from typing import Dict, List, Tuple, Any, Optional
from core.equilibrium import (
    create_ice_table, solve_ice_table, convert_kc_to_kp, convert_kp_to_kc,
    calculate_reaction_quotient, determine_reaction_direction,
    solve_solubility_from_ksp
)
from core.reaction import balance_equation, parse_reaction_equation
from core.formula import parse_chemical_formula


def solve_ice_table_with_steps(reaction_str: str, initial_concentrations: Dict[str, float],
                               kc: float) -> Tuple[Dict[str, Any], List[str], Dict[str, Any]]:
    """
    Solve ICE table for equilibrium concentrations.
    
    Args:
        reaction_str: Balanced reaction string
        initial_concentrations: Initial concentrations for species
        kc: Equilibrium constant Kc
    
    Returns:
        Tuple of (results, steps, metadata)
    """
    steps = []
    
    # Step 1: Parse and balance reaction
    steps.append("**Step 1: Parse and balance reaction**")
    try:
        balanced = balance_equation(reaction_str)
        steps.append(f"Balanced equation: {balanced['equation_str']}")
        steps.append(f"Reactants: {', '.join(balanced['reactants'])}")
        steps.append(f"Products: {', '.join(balanced['products'])}")
        steps.append(f"Coefficients: {balanced['coefficients']}")
        
        # Step 2: Build stoichiometry dictionary
        steps.append("\n**Step 2: Build stoichiometry dictionary**")
        stoichiometry = {}
        for i, species in enumerate(balanced['species_order']):
            if i < len(balanced['reactants']):
                # Reactant - negative coefficient
                stoichiometry[species] = -balanced['coefficients'][i]
            else:
                # Product - positive coefficient
                stoichiometry[species] = balanced['coefficients'][i]
        
        steps.append("Stoichiometry (negative for reactants, positive for products):")
        for species, coeff in stoichiometry.items():
            steps.append(f"  {species}: {coeff:+d}")
        
        # Step 3: Create ICE table
        steps.append("\n**Step 3: Create ICE table**")
        ice_table = create_ice_table(
            balanced['reactants'], balanced['products'], 
            initial_concentrations, stoichiometry
        )
        
        # Display ICE table
        steps.append("ICE Table:")
        for species in balanced['reactants'] + balanced['products']:
            if species in ice_table:
                steps.append(f"  {species}: {ice_table[species]}")
        
        # Step 4: Solve ICE table
        steps.append("\n**Step 4: Solve for equilibrium**")
        try:
            extent, equilibrium_concentrations = solve_ice_table(
                ice_table, stoichiometry, kc
            )
            steps.append(f"Extent of reaction (x) = {extent:.6f}")
            
            # Step 5: Determine reaction direction
            steps.append("\n**Step 5: Determine reaction direction**")
            
            # Calculate initial reaction quotient Q
            from core.equilibrium import calculate_reaction_quotient
            initial_q = calculate_reaction_quotient(initial_concentrations, stoichiometry)
            steps.append(f"Initial Q = {initial_q:.6f}")
            steps.append(f"Kc = {kc:.6f}")
            
            direction = determine_reaction_direction(initial_q, kc)
            steps.append(f"Direction: {direction}")
            
            results = {
                'extent': extent,
                'equilibrium_concentrations': equilibrium_concentrations,
                'direction': direction,
                'ice_table': ice_table
            }
            
            metadata = {
                'reaction': reaction_str,
                'kc': kc,
                'balanced_equation': balanced
            }
            
            return results, steps, metadata
            
        except Exception as e:
            raise ValueError(f"Could not solve ICE table: {e}")
        
    except Exception as e:
        raise ValueError(f"Could not balance equation: {e}")


def convert_equilibrium_constants_with_steps(kc: float = None, kp: float = None,
                                           temperature: float = None, delta_n: int = None) -> Tuple[Dict[str, Any], List[str], Dict[str, Any]]:
    """
    Convert between Kc and Kp equilibrium constants.
    
    Args:
        kc: Concentration-based equilibrium constant
        kp: Pressure-based equilibrium constant
        temperature: Temperature in Kelvin
        delta_n: Change in gas moles (products - reactants)
    
    Returns:
        Tuple of (results, steps, metadata)
    """
    steps = []
    
    # Input validation
    if temperature is None or temperature <= 0:
        raise ValueError("Temperature must be positive")
    if delta_n is None:
        raise ValueError("Delta n must be specified")
    
    # Validate Kc or Kp values
    if kc is not None and kc <= 0:
        raise ValueError("Kc must be positive")
    if kp is not None and kp <= 0:
        raise ValueError("Kp must be positive")
    
    # Step 1: Use appropriate conversion formula
    if kc is not None and kp is None:
        # Convert Kc to Kp
        steps.append("**Step 1: Convert Kc to Kp**")
        steps.append("Formula: Kp = Kc × (RT)^Δn")
        steps.append(f"Where R = 8.314 J/(mol·K), T = {temperature:.1f} K, Δn = {delta_n}")
        
        kp = convert_kc_to_kp(kc, temperature, delta_n)
        steps.append(f"Kp = {kc:.6f} × (8.314 × {temperature:.1f} / 1000)^{delta_n}")
        steps.append(f"Kp = {kc:.6f} × {kp/kc:.6f} = {kp:.6f}")
        
        results = {'kp': kp, 'kc': kc}
        
    elif kp is not None and kc is None:
        # Convert Kp to Kc
        steps.append("**Step 1: Convert Kp to Kc**")
        steps.append("Formula: Kc = Kp / (RT)^Δn")
        steps.append(f"Where R = 8.314 J/(mol·K), T = {temperature:.1f} K, Δn = {delta_n}")
        
        kc = convert_kp_to_kc(kp, temperature, delta_n)
        steps.append(f"Kc = {kp:.6f} / (8.314 × {temperature:.1f} / 1000)^{delta_n}")
        steps.append(f"Kc = {kp:.6f} / {kp/kc:.6f} = {kc:.6f}")
        
        results = {'kc': kc, 'kp': kp}
        
    else:
        raise ValueError("Must provide either Kc or Kp, not both")
    
    metadata = {
        'temperature': temperature,
        'delta_n': delta_n,
        'gas_constant': 8.314
    }
    
    return results, steps, metadata


def calculate_reaction_quotient_with_steps(reaction_str: str, current_concentrations: Dict[str, float],
                                          k: float) -> Tuple[Dict[str, Any], List[str], Dict[str, Any]]:
    """
    Calculate reaction quotient Q and compare to equilibrium constant K.
    
    Args:
        reaction_str: Balanced reaction string
        current_concentrations: Current concentrations for species
        k: Equilibrium constant K
    
    Returns:
        Tuple of (results, steps, metadata)
    """
    steps = []
    
    # Step 1: Parse and balance reaction
    steps.append("**Step 1: Parse and balance reaction**")
    try:
        balanced = balance_equation(reaction_str)
        steps.append(f"Balanced equation: {balanced['equation_str']}")
        steps.append(f"Reactants: {', '.join(balanced['reactants'])}")
        steps.append(f"Products: {', '.join(balanced['products'])}")
        steps.append(f"Coefficients: {balanced['coefficients']}")
        
        # Step 2: Build stoichiometry dictionary
        steps.append("\n**Step 2: Build stoichiometry dictionary**")
        stoichiometry = {}
        for i, species in enumerate(balanced['species_order']):
            if i < len(balanced['reactants']):
                # Reactant - negative coefficient
                stoichiometry[species] = -balanced['coefficients'][i]
            else:
                # Product - positive coefficient
                stoichiometry[species] = balanced['coefficients'][i]
        
        steps.append("Stoichiometry (negative for reactants, positive for products):")
        for species, coeff in stoichiometry.items():
            steps.append(f"  {species}: {coeff:+d}")
        
        # Step 3: Calculate reaction quotient Q
        steps.append("\n**Step 3: Calculate reaction quotient Q**")
        try:
            Q = calculate_reaction_quotient(current_concentrations, stoichiometry)
            steps.append(f"Q = {Q:.6f}")
            
            # Step 4: Compare Q to K
            steps.append("\n**Step 4: Compare Q to K**")
            steps.append(f"K = {k:.6f}")
            
            if Q < k:
                comparison = "Q < K"
                direction = "Reaction proceeds to products (right)"
            elif Q > k:
                comparison = "Q > K"
                direction = "Reaction proceeds to reactants (left)"
            else:
                comparison = "Q = K"
                direction = "System is at equilibrium"
            
            steps.append(f"Comparison: {comparison}")
            steps.append(f"Direction: {direction}")
            
            results = {
                'Q': Q,
                'K': k,
                'comparison': comparison,
                'direction': direction
            }
            
            metadata = {
                'reaction': reaction_str,
                'balanced_equation': balanced
            }
            
            return results, steps, metadata
            
        except Exception as e:
            raise ValueError(f"Could not calculate reaction quotient: {e}")
        
    except Exception as e:
        raise ValueError(f"Could not balance equation: {e}")


def calculate_solubility_with_steps(salt_formula: str, ksp: float,
                                   common_ion_concentrations: Optional[Dict[str, float]] = None) -> Tuple[Dict[str, Any], List[str], Dict[str, Any]]:
    """
    Calculate molar solubility from Ksp.
    
    Args:
        salt_formula: Chemical formula of the salt
        ksp: Solubility product constant
        common_ion_concentrations: Optional initial concentrations of common ions
    
    Returns:
        Tuple of (results, steps, metadata)
    """
    steps = []

    # Input validation
    if not salt_formula or not salt_formula.strip():
        raise ValueError("Salt formula cannot be empty")
    if ksp <= 0:
        raise ValueError("Ksp must be positive")

    if common_ion_concentrations is None:
        common_ion_concentrations = {}
    
    # Step 1: Parse salt formula
    steps.append("**Step 1: Parse salt formula**")
    try:
        element_counts = parse_chemical_formula(salt_formula)
        steps.append(f"Salt: {salt_formula}")
        steps.append("Dissociation: " + salt_formula + " → ")
        
        # Determine ions from formula (simplified approach)
        if len(element_counts) == 2:
            ions = list(element_counts.keys())
            coeffs = list(element_counts.values())
            
            if coeffs[0] == 1 and coeffs[1] == 1:
                # 1:1 salt like AgCl
                ion1, ion2 = ions[0], ions[1]
                steps.append(f"{ion1}⁺ + {ion2}⁻")
                stoichiometry = {ion1: 1, ion2: 1}
            elif coeffs[0] == 1 and coeffs[1] == 2:
                # 1:2 salt like CaF2
                ion1, ion2 = ions[0], ions[1]
                steps.append(f"{ion1}²⁺ + 2{ion2}⁻")
                stoichiometry = {ion1: 1, ion2: 2}
            elif coeffs[0] == 2 and coeffs[1] == 1:
                # 2:1 salt like Na2SO4
                ion1, ion2 = ions[0], ions[1]
                steps.append(f"2{ion1}⁺ + {ion2}²⁻")
                stoichiometry = {ion1: 2, ion2: 1}
            else:
                # General case
                steps.append("complex dissociation")
                stoichiometry = {ion: coeff for ion, coeff in element_counts.items()}
        else:
            # Complex salt
            steps.append("complex dissociation")
            stoichiometry = {ion: coeff for ion, coeff in element_counts.items()}
            
    except Exception as e:
        raise ValueError(f"Could not parse salt formula: {e}")
    
    # Step 2: Write Ksp expression
    steps.append("\n**Step 2: Write Ksp expression**")
    steps.append("Ksp = [Ion1]^coeff1 × [Ion2]^coeff2 × ...")
    
    ksp_expression = "Ksp = "
    terms = []
    for ion, coeff in stoichiometry.items():
        if coeff == 1:
            terms.append(f"[{ion}]")
        else:
            terms.append(f"[{ion}]^{coeff}")
    ksp_expression += " × ".join(terms)
    steps.append(ksp_expression)
    
    # Step 3: Set up solubility equation
    steps.append("\n**Step 3: Set up solubility equation**")
    steps.append("Let s = molar solubility")
    
    if common_ion_concentrations:
        steps.append("With common ion effect:")
        for ion, conc in common_ion_concentrations.items():
            steps.append(f"  [{ion}]₀ = {conc:.6f} M")
    
    # Step 4: Solve for solubility
    steps.append("\n**Step 4: Solve for solubility**")
    try:
        solubility = solve_solubility_from_ksp(ksp, stoichiometry, common_ion_concentrations)
        steps.append(f"Molar solubility s = {solubility:.6f} M")
        
        # Step 5: Calculate equilibrium concentrations
        steps.append("\n**Step 5: Calculate equilibrium concentrations**")
        equilibrium_concentrations = {}
        
        for ion, coeff in stoichiometry.items():
            initial_conc = common_ion_concentrations.get(ion, 0.0)
            equilibrium_conc = coeff * solubility + initial_conc
            equilibrium_concentrations[ion] = equilibrium_conc
            
            if initial_conc > 0:
                steps.append(f"[{ion}] = {coeff} × {solubility:.6f} + {initial_conc:.6f} = {equilibrium_conc:.6f} M")
            else:
                steps.append(f"[{ion}] = {coeff} × {solubility:.6f} = {equilibrium_conc:.6f} M")
        
        # Step 6: Verify Ksp
        steps.append("\n**Step 6: Verify Ksp**")
        calculated_ksp = 1.0
        for ion, coeff in stoichiometry.items():
            calculated_ksp *= equilibrium_concentrations[ion]**coeff
        
        steps.append(f"Calculated Ksp = {calculated_ksp:.2e}")
        steps.append(f"Target Ksp = {ksp:.2e}")
        steps.append(f"Difference = {abs(calculated_ksp - ksp):.2e}")
        
        results = {
            'solubility': solubility,
            'equilibrium_concentrations': equilibrium_concentrations,
            'calculated_ksp': calculated_ksp,
            'stoichiometry': stoichiometry
        }
        
        metadata = {
            'salt_formula': salt_formula,
            'ksp': ksp,
            'target_ksp': ksp,
            'common_ion_concentrations': common_ion_concentrations
        }
        
        return results, steps, metadata
        
    except Exception as e:
        raise ValueError(f"Could not calculate solubility: {e}")


def calculate_solubility_product_with_steps(salt_formula: str, solubility: float) -> Tuple[Dict[str, Any], List[str], Dict[str, Any]]:
    """
    Calculate Ksp from molar solubility.
    
    Args:
        salt_formula: Chemical formula of the salt
        solubility: Molar solubility in mol/L
    
    Returns:
        Tuple of (results, steps, metadata)
    """
    steps = []
    
    # Step 1: Parse salt formula
    steps.append("**Step 1: Parse salt formula**")
    try:
        element_counts = parse_chemical_formula(salt_formula)
        steps.append(f"Salt: {salt_formula}")
        steps.append("Dissociation: " + salt_formula + " → ")
        
        # Determine ions from formula (simplified approach)
        if len(element_counts) == 2:
            ions = list(element_counts.keys())
            coeffs = list(element_counts.values())
            
            if coeffs[0] == 1 and coeffs[1] == 1:
                # 1:1 salt like AgCl
                ion1, ion2 = ions[0], ions[1]
                steps.append(f"{ion1}⁺ + {ion2}⁻")
                stoichiometry = {ion1: 1, ion2: 1}
            elif coeffs[0] == 1 and coeffs[1] == 2:
                # 1:2 salt like CaF2
                ion1, ion2 = ions[0], ions[1]
                steps.append(f"{ion1}²⁺ + 2{ion2}⁻")
                stoichiometry = {ion1: 1, ion2: 2}
            elif coeffs[0] == 2 and coeffs[1] == 1:
                # 2:1 salt like Na2SO4
                ion1, ion2 = ions[0], ions[1]
                steps.append(f"2{ion1}⁺ + {ion2}²⁻")
                stoichiometry = {ion1: 2, ion2: 1}
            else:
                # General case
                steps.append("complex dissociation")
                stoichiometry = {ion: coeff for ion, coeff in element_counts.items()}
        else:
            # Complex salt
            steps.append("complex dissociation")
            stoichiometry = {ion: coeff for ion, coeff in element_counts.items()}
            
    except Exception as e:
        raise ValueError(f"Could not parse salt formula: {e}")
    
    # Step 2: Write Ksp expression
    steps.append("\n**Step 2: Write Ksp expression**")
    steps.append("Ksp = [Ion1]^coeff1 × [Ion2]^coeff2 × ...")
    
    ksp_expression = "Ksp = "
    terms = []
    for ion, coeff in stoichiometry.items():
        if coeff == 1:
            terms.append(f"[{ion}]")
        else:
            terms.append(f"[{ion}]^{coeff}")
    ksp_expression += " × ".join(terms)
    steps.append(ksp_expression)
    
    # Step 3: Calculate equilibrium concentrations
    steps.append("\n**Step 3: Calculate equilibrium concentrations**")
    steps.append(f"Molar solubility s = {solubility:.6f} M")
    
    equilibrium_concentrations = {}
    for ion, coeff in stoichiometry.items():
        equilibrium_conc = coeff * solubility
        equilibrium_concentrations[ion] = equilibrium_conc
        steps.append(f"[{ion}] = {coeff} × {solubility:.6f} = {equilibrium_conc:.6f} M")
    
    # Step 4: Calculate Ksp
    steps.append("\n**Step 4: Calculate Ksp**")
    ksp = 1.0
    for ion, coeff in stoichiometry.items():
        ksp *= equilibrium_concentrations[ion]**coeff
    
    steps.append(f"Ksp = {ksp:.2e}")
    
    results = {
        'ksp': ksp,
        'solubility': solubility,
        'equilibrium_concentrations': equilibrium_concentrations,
        'stoichiometry': stoichiometry
    }
    
    metadata = {
        'salt_formula': salt_formula
    }
    
    return results, steps, metadata
