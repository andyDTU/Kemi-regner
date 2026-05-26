"""
Stoichiometry calculator for chemical reactions.
Includes limiting reagent analysis, theoretical yield, and dilution calculations.
"""

from typing import Dict, List, Tuple, Any
from core.reaction import balance_equation, parse_reaction_equation
from core.formula import calculate_molar_mass_from_formula
from core.units import Q, normalize_energy
from core.formatting import fmt_quantity, fmt_percentage
from core.solver import add_math_step, add_latex_step


def calculate_limiting_reagent_with_steps(
    equation_str: str,
    reactant_inputs: List[Dict[str, Any]],
    target_product: str,
    actual_yield: float = None
) -> Tuple[Dict[str, Any], List[str], Dict[str, Any]]:
    """
    Calculate limiting reagent and theoretical yield.
    
    Args:
        equation_str: Chemical equation string
        reactant_inputs: List of dicts with keys: 'formula', 'mode', 'value', 'unit', 'volume' (if mode='solution')
        target_product: Formula of the target product
        actual_yield: Optional actual yield in grams
    
    Returns:
        Tuple of (results_dict, steps_list, metadata_dict)
    """
    steps = []
    
    # Step 1: Balance the equation
    steps.append("**Step 1: Balance the chemical equation**")
    try:
        balanced = balance_equation(equation_str)
        steps.append(f"Balanced equation: {balanced['equation_str']}")
        steps.append(f"Reactants: {', '.join(balanced['reactants'])}")
        steps.append(f"Products: {', '.join(balanced['products'])}")
        steps.append(f"Coefficients: {balanced['coefficients']}")
    except Exception as e:
        raise ValueError(f"Could not balance equation: {e}")
    
    # Step 2: Convert all inputs to moles
    steps.append("\n**Step 2: Convert all inputs to moles**")
    reactant_moles = {}
    reactant_masses = {}
    
    for i, input_data in enumerate(reactant_inputs):
        formula = input_data['formula']
        mode = input_data['mode']
        value = input_data['value']
        unit = input_data['unit']
        
        if mode == 'moles':
            moles = value
            mass = moles * calculate_molar_mass_from_formula(formula)
            steps.append(f"{formula}: {value} {unit} = {moles:.4f} mol")
        elif mode == 'mass':
            mass = value
            moles = mass / calculate_molar_mass_from_formula(formula)
            steps.append(f"{formula}: {value} {unit} ÷ {calculate_molar_mass_from_formula(formula):.3f} g/mol = {moles:.4f} mol")
        elif mode == 'solution':
            volume = input_data['volume']  # in mL
            molarity = value  # in M
            # Convert mL to L and calculate moles
            volume_l = volume / 1000
            moles = molarity * volume_l
            mass = moles * calculate_molar_mass_from_formula(formula)
            steps.append(f"{formula}: {value} M × {volume} mL × (1 L/1000 mL) = {moles:.4f} mol")
        
        reactant_moles[formula] = moles
        reactant_masses[formula] = mass
    
    # Step 3: Find limiting reagent
    steps.append("\n**Step 3: Determine limiting reagent**")
    limiting_reagent = None
    limiting_moles = float('inf')
    stoichiometric_ratios = {}
    
    for i, reactant in enumerate(balanced['reactants']):
        if reactant in reactant_moles:
            # Get stoichiometric coefficient for this reactant
            reactant_coeff = balanced['coefficients'][i]
            # Calculate how many moles of product can be made from this reactant
            product_moles_possible = reactant_moles[reactant] / reactant_coeff
            stoichiometric_ratios[reactant] = product_moles_possible
            
            steps.append(f"{reactant}: {reactant_moles[reactant]:.4f} mol ÷ {reactant_coeff} = {product_moles_possible:.4f} mol of product possible")
            
            if product_moles_possible < limiting_moles:
                limiting_moles = product_moles_possible
                limiting_reagent = reactant
    
    steps.append(f"\n**Limiting reagent: {limiting_reagent}**")
    steps.append(f"Maximum product possible: {limiting_moles:.4f} mol")
    
    # Step 4: Calculate theoretical yield
    steps.append("\n**Step 4: Calculate theoretical yield**")
    
    # Find target product coefficient
    target_product_idx = None
    for i, product in enumerate(balanced['products']):
        if product == target_product:
            target_product_idx = i
            break
    
    if target_product_idx is None:
        raise ValueError(f"Target product {target_product} not found in products")
    
    target_coeff = balanced['coefficients'][len(balanced['reactants']) + target_product_idx]
    theoretical_yield_moles = limiting_moles * target_coeff
    theoretical_yield_mass = theoretical_yield_moles * calculate_molar_mass_from_formula(target_product)
    
    steps.append(f"Target product coefficient: {target_coeff}")
    steps.append(f"Theoretical yield: {theoretical_yield_moles:.4f} mol × {calculate_molar_mass_from_formula(target_product):.3f} g/mol = {theoretical_yield_mass:.3f} g")
    
    # Step 5: Calculate excess reactants
    steps.append("\n**Step 5: Calculate excess reactants**")
    excess_data = {}
    
    for i, reactant in enumerate(balanced['reactants']):
        if reactant in reactant_moles:
            reactant_coeff = balanced['coefficients'][i]
            moles_consumed = limiting_moles * reactant_coeff
            moles_excess = reactant_moles[reactant] - moles_consumed
            mass_excess = moles_excess * calculate_molar_mass_from_formula(reactant)
            
            excess_data[reactant] = {
                'moles_excess': moles_excess,
                'mass_excess': mass_excess
            }
            
            if moles_excess > 0:
                steps.append(f"{reactant}: {reactant_moles[reactant]:.4f} mol - {moles_consumed:.4f} mol = {moles_excess:.4f} mol excess")
                steps.append(f"  Excess mass: {moles_excess:.4f} mol × {calculate_molar_mass_from_formula(reactant):.3f} g/mol = {mass_excess:.3f} g")
            else:
                steps.append(f"{reactant}: {reactant_moles[reactant]:.4f} mol - {moles_consumed:.4f} mol = 0 mol excess (completely consumed)")
    
    # Step 6: Calculate percent yield (if actual yield provided)
    percent_yield = None
    if actual_yield is not None:
        steps.append("\n**Step 6: Calculate percent yield**")
        percent_yield = (actual_yield / theoretical_yield_mass) * 100
        steps.append(f"Percent yield = (actual yield ÷ theoretical yield) × 100%")
        steps.append(f"Percent yield = ({actual_yield:.3f} g ÷ {theoretical_yield_mass:.3f} g) × 100% = {percent_yield:.1f}%")
    
    # Prepare results
    results = {
        'limiting_reagent': limiting_reagent,
        'theoretical_yield_moles': theoretical_yield_moles,
        'theoretical_yield_mass': theoretical_yield_mass,
        'target_product': target_product,
        'excess_data': excess_data,
        'percent_yield': percent_yield
    }
    
    metadata = {
        'balanced_equation': balanced,
        'reactant_moles': reactant_moles,
        'reactant_masses': reactant_masses,
        'stoichiometric_ratios': stoichiometric_ratios
    }
    
    return results, steps, metadata


def calculate_dilution_with_steps(
    m1: float = None, v1: float = None, 
    m2: float = None, v2: float = None,
    m1_unit: str = "M", v1_unit: str = "L",
    m2_unit: str = "M", v2_unit: str = "L"
) -> Tuple[Dict[str, Any], List[str], Dict[str, Any]]:
    """
    Solve dilution problem M1V1 = M2V2.
    
    Args:
        m1, v1, m2, v2: Three of these must be provided, one will be calculated
        m1_unit, v1_unit, m2_unit, v2_unit: Units for each value
    
    Returns:
        Tuple of (results_dict, steps_list, metadata_dict)
    """
    steps = []
    
    # Determine which variable to solve for
    unknowns = []
    if m1 is None:
        unknowns.append('M1')
    if v1 is None:
        unknowns.append('V1')
    if m2 is None:
        unknowns.append('M2')
    if v2 is None:
        unknowns.append('V2')
    
    if len(unknowns) != 1:
        raise ValueError("Exactly three of M1, V1, M2, V2 must be provided")
    
    unknown = unknowns[0]
    steps.append(f"**Solving for {unknown} using the dilution equation: M₁V₁ = M₂V₂**")
    
    # Convert all volumes to liters for consistency
    v1_l = v1 if v1_unit == "L" else v1 / 1000 if v1_unit == "mL" else v1
    v2_l = v2 if v2_unit == "L" else v2 / 1000 if v2_unit == "mL" else v2
    
    if v1 is not None and v1_unit == "mL":
        steps.append(f"V₁: {v1} mL = {v1_l:.6f} L")
    if v2 is not None and v2_unit == "mL":
        steps.append(f"V₂: {v2} mL = {v2_l:.6f} L")
    
    # Solve for the unknown
    if unknown == 'M1':
        result = (m2 * v2_l) / v1_l
        steps.append(f"M₁ = (M₂ × V₂) ÷ V₁")
        steps.append(f"M₁ = ({m2} M × {v2_l:.6f} L) ÷ {v1_l:.6f} L")
        steps.append(f"M₁ = {result:.6f} M")
        
        # Convert back to appropriate unit if needed
        if m1_unit != "M":
            if m1_unit == "mM":
                result = result * 1000
                steps.append(f"M₁ = {result:.3f} mM")
            elif m1_unit == "μM":
                result = result * 1000000
                steps.append(f"M₁ = {result:.0f} μM")
        
    elif unknown == 'V1':
        result = (m2 * v2_l) / m1
        steps.append(f"V₁ = (M₂ × V₂) ÷ M₁")
        steps.append(f"V₁ = ({m2} M × {v2_l:.6f} L) ÷ {m1} M")
        steps.append(f"V₁ = {result:.6f} L")
        
        # Convert to appropriate unit if needed
        if v1_unit == "mL":
            result = result * 1000
            steps.append(f"V₁ = {result:.3f} mL")
        
    elif unknown == 'M2':
        result = (m1 * v1_l) / v2_l
        steps.append(f"M₂ = (M₁ × V₁) ÷ V₂")
        steps.append(f"M₂ = ({m1} M × {v1_l:.6f} L) ÷ {v2_l:.6f} L")
        steps.append(f"M₂ = {result:.6f} M")
        
        # Convert back to appropriate unit if needed
        if m2_unit != "M":
            if m2_unit == "mM":
                result = result * 1000
                steps.append(f"M₂ = {result:.3f} mM")
            elif m2_unit == "μM":
                result = result * 1000000
                steps.append(f"M₂ = {result:.0f} μM")
        
    elif unknown == 'V2':
        result = (m1 * v1_l) / m2
        steps.append(f"V₂ = (M₁ × V₁) ÷ M₂")
        steps.append(f"V₂ = ({m1} M × {v1_l:.6f} L) ÷ {m2} M")
        steps.append(f"V₂ = {result:.6f} L")
        
        # Convert to appropriate unit if needed
        if v2_unit == "mL":
            result = result * 1000
            steps.append(f"V₂ = {result:.3f} mL")
    
    # Prepare results
    results = {
        'unknown': unknown,
        'result': result,
        'result_unit': m1_unit if unknown.startswith('M') else v1_unit if unknown.startswith('V') else 'L'
    }
    
    metadata = {
        'equation': 'M₁V₁ = M₂V₂',
        'inputs': {
            'M1': m1, 'V1': v1, 'M2': m2, 'V2': v2,
            'M1_unit': m1_unit, 'V1_unit': v1_unit,
            'M2_unit': m2_unit, 'V2_unit': v2_unit
        }
    }
    
    return results, steps, metadata
