"""
Gibbs Free Energy Calculator
Calculates Gibbs free energy change and related thermodynamic properties.
"""

from typing import Tuple, Dict, List, Any
from core.units import Q, normalize_energy, normalize_temperature
from core.formatting import fmt_quantity, fmt_energy
from core.solver import add_latex_step, add_math_step

def calculate_gibbs_free_energy_with_steps(delta_h: float, delta_h_unit: str, 
                                         delta_s: float, delta_s_unit: str,
                                         temperature: float, temp_unit: str) -> Tuple[float, List[str], Dict[str, Any]]:
    """
    Calculate Gibbs free energy change with step-by-step breakdown.
    
    Args:
        delta_h: Enthalpy change
        delta_h_unit: Unit for enthalpy change
        delta_s: Entropy change
        delta_s_unit: Unit for entropy change
        temperature: Temperature
        temp_unit: Unit for temperature
    
    Returns:
        Tuple of (delta_g, steps, metadata)
    """
    # Validate inputs
    if temperature <= 0:
        raise ValueError("Temperature must be positive")
    
    steps = []
    metadata = {}
    
    # Step 1: Convert all values to standard units
    steps.append("**Step 1: Convert all values to standard units**")
    
    # Convert enthalpy to J/mol
    h_quantity = Q(delta_h, delta_h_unit)
    h_j_mol = normalize_energy(h_quantity)
    steps.append(f"ΔH = {fmt_quantity(h_quantity)} = {fmt_quantity(h_j_mol)}")
    
    # Convert entropy to J/(mol·K) - handle the conversion properly
    s_quantity = Q(delta_s, delta_s_unit)
    # For entropy, we need to convert to J/(mol·K) if it's in different units
    if "kJ" in delta_s_unit:
        s_j_mol_k = s_quantity.to("kJ/(mol·K)")
        s_j_mol_k = Q(s_j_mol_k.magnitude * 1000, "J/(mol·K)")  # Convert kJ to J
    elif "cal" in delta_s_unit:
        s_j_mol_k = s_quantity.to("cal/(mol·K)")
        s_j_mol_k = Q(s_j_mol_k.magnitude * 4.184, "J/(mol·K)")  # Convert cal to J
    else:
        s_j_mol_k = s_quantity.to("J/(mol·K)")
    
    steps.append(f"ΔS = {fmt_quantity(s_quantity)} = {fmt_quantity(s_j_mol_k)}")
    
    # Convert temperature to K
    t_quantity = Q(temperature, temp_unit)
    t_k = normalize_temperature(t_quantity)
    steps.append(f"T = {fmt_quantity(t_quantity)} = {fmt_quantity(t_k)}")
    
    # Step 2: Apply the Gibbs free energy equation
    steps.append("\n**Step 2: Apply the Gibbs free energy equation**")
    
    # Calculate TΔS term
    t_delta_s = t_k.magnitude * s_j_mol_k.magnitude
    steps.append(f"T × ΔS = {fmt_quantity(t_k)} × {fmt_quantity(s_j_mol_k)} = {fmt_quantity(t_delta_s)}")
    
    # Calculate ΔG
    delta_g_j_mol = h_j_mol.magnitude - t_delta_s
    steps.append(add_latex_step("ΔG = ΔH - TΔS", 
                               f"\\Delta G = {fmt_quantity(h_j_mol)} - {fmt_quantity(t_delta_s)}"))
    
    steps.append(f"ΔG = {fmt_quantity(delta_g_j_mol)}")
    
    # Step 3: Convert to kJ/mol for display
    steps.append("\n**Step 3: Convert to kJ/mol for display**")
    
    delta_g_kj_mol = delta_g_j_mol / 1000
    steps.append(f"ΔG = {fmt_quantity(delta_g_j_mol)} = {fmt_quantity(delta_g_kj_mol)}")
    
    # Step 4: Determine spontaneity
    steps.append("\n**Step 4: Determine spontaneity**")
    
    if delta_g_j_mol < 0:
        spontaneity = "spontaneous"
        steps.append("Since ΔG < 0, the reaction is **spontaneous** at this temperature.")
    elif delta_g_j_mol > 0:
        spontaneity = "non-spontaneous"
        steps.append("Since ΔG > 0, the reaction is **non-spontaneous** at this temperature.")
    else:
        spontaneity = "at equilibrium"
        steps.append("Since ΔG = 0, the reaction is **at equilibrium** at this temperature.")
    
    # Step 5: Calculate crossover temperature (if applicable)
    steps.append("\n**Step 5: Calculate crossover temperature**")
    
    if abs(s_j_mol_k.magnitude) > 1e-10:  # Avoid division by zero
        t_eq = h_j_mol.magnitude / s_j_mol_k.magnitude
        steps.append(f"At equilibrium: ΔG = 0")
        steps.append(add_latex_step("0 = ΔH - T_eq × ΔS", 
                                   "0 = \\Delta H - T_{eq} \\times \\Delta S"))
        steps.append(add_latex_step("T_eq = ΔH / ΔS", 
                                   "T_{eq} = \\frac{\\Delta H}{\\Delta S}"))
        steps.append(f"T_eq = {fmt_quantity(h_j_mol)} / {fmt_quantity(s_j_mol_k)}")
        steps.append(f"T_eq = {fmt_quantity(t_eq)}")
        
        # Check if this temperature is physically meaningful
        if t_eq > 0:
            if t_eq < 1000:  # Reasonable temperature range
                steps.append(f"This corresponds to {fmt_quantity(t_eq - 273.15)}°C")
            else:
                steps.append(f"This is a very high temperature: {fmt_quantity(t_eq)} K")
        else:
            steps.append("This temperature is not physically meaningful (negative or zero)")
    else:
        t_eq = None
        steps.append("Cannot calculate crossover temperature: ΔS is zero")
    
    # Metadata
    metadata = {
        'delta_h_j_mol': h_j_mol.magnitude,
        'delta_s_j_mol_k': s_j_mol_k.magnitude,
        'temperature_k': t_k.magnitude,
        'delta_g_j_mol': delta_g_j_mol,
        'delta_g_kj_mol': delta_g_kj_mol,
        'spontaneity': spontaneity,
        'crossover_temperature_k': t_eq,
        'units': {
            'enthalpy': 'J/mol',
            'entropy': 'J/(mol·K)',
            'temperature': 'K',
            'gibbs': 'J/mol'
        }
    }
    
    return delta_g_kj_mol, steps, metadata

def analyze_gibbs_temperature_dependence(delta_h: float, delta_h_unit: str,
                                       delta_s: float, delta_s_unit: str) -> Tuple[List[str], Dict[str, Any]]:
    """
    Analyze how Gibbs free energy changes with temperature.
    
    Args:
        delta_h: Enthalpy change
        delta_h_unit: Unit for enthalpy change
        delta_s: Entropy change
        delta_s_unit: Unit for entropy change
    
    Returns:
        Tuple of (analysis_steps, metadata)
    """
    steps = []
    
    # Convert to standard units
    h_quantity = Q(delta_h, delta_h_unit)
    h_j_mol = normalize_energy(h_quantity)
    
    # Convert entropy properly
    s_quantity = Q(delta_s, delta_s_unit)
    if "kJ" in delta_s_unit:
        s_j_mol_k = s_quantity.to("kJ/(mol·K)")
        s_j_mol_k = Q(s_j_mol_k.magnitude * 1000, "J/(mol·K)")
    elif "cal" in delta_s_unit:
        s_j_mol_k = s_quantity.to("cal/(mol·K)")
        s_j_mol_k = Q(s_j_mol_k.magnitude * 4.184, "J/(mol·K)")
    else:
        s_j_mol_k = s_quantity.to("J/(mol·K)")
    
    steps.append("**Temperature Dependence Analysis**")
    steps.append(f"ΔH = {fmt_quantity(h_j_mol)}")
    steps.append(f"ΔS = {fmt_quantity(s_j_mol_k)}")
    
    # Analyze the relationship
    if h_j_mol.magnitude > 0 and s_j_mol_k.magnitude > 0:
        steps.append("Both ΔH > 0 and ΔS > 0")
        steps.append("• At low T: TΔS term is small, so ΔG ≈ ΔH > 0 (non-spontaneous)")
        steps.append("• At high T: TΔS term dominates, so ΔG < 0 (spontaneous)")
        steps.append("• There is a crossover temperature where the reaction becomes spontaneous")
        
    elif h_j_mol.magnitude < 0 and s_j_mol_k.magnitude < 0:
        steps.append("Both ΔH < 0 and ΔS < 0")
        steps.append("• At low T: TΔS term is small, so ΔG ≈ ΔH < 0 (spontaneous)")
        steps.append("• At high T: TΔS term dominates, so ΔG > 0 (non-spontaneous)")
        steps.append("• There is a crossover temperature where the reaction becomes non-spontaneous")
        
    elif h_j_mol.magnitude < 0 and s_j_mol_k.magnitude > 0:
        steps.append("ΔH < 0 and ΔS > 0")
        steps.append("• Always spontaneous at all temperatures")
        steps.append("• ΔG = ΔH - TΔS < 0 for all T > 0")
        
    else:  # h_j_mol.magnitude > 0 and s_j_mol_k.magnitude < 0
        steps.append("ΔH > 0 and ΔS < 0")
        steps.append("• Always non-spontaneous at all temperatures")
        steps.append("• ΔG = ΔH - TΔS > 0 for all T > 0")
    
    # Calculate crossover temperature if applicable
    if abs(s_j_mol_k.magnitude) > 1e-10:
        t_eq = h_j_mol.magnitude / s_j_mol_k.magnitude
        if t_eq > 0:
            steps.append(f"\nCrossover temperature: T_eq = {fmt_quantity(t_eq)}")
            if t_eq < 1000:
                steps.append(f"T_eq = {fmt_quantity(t_eq - 273.15)}°C")
    
    metadata = {
        'enthalpy_sign': 'positive' if h_j_mol.magnitude > 0 else 'negative',
        'entropy_sign': 'positive' if s_j_mol_k.magnitude > 0 else 'negative',
        'crossover_temperature_k': t_eq if abs(s_j_mol_k.magnitude) > 1e-10 else None
    }
    
    return steps, metadata
