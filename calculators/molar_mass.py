"""
Molar mass calculator for chemical compounds.
Uses the shared formula parsing module from core.formula.
"""

from typing import Tuple, Dict, List, Any
from core.formula import get_formula_metadata


def calculate_molar_mass_with_steps(formula: str) -> Tuple[float, List[str], Dict[str, Any]]:
    """
    Calculate molar mass with step-by-step breakdown.
    
    Args:
        formula: Chemical formula string
    
    Returns:
        Tuple of (molar_mass, steps, metadata)
    """
    steps = []
    
    # Step 1: Parse the formula
    steps.append("**Step 1: Parse the chemical formula**")
    steps.append(f"Formula: {formula}")
    
    try:
        metadata = get_formula_metadata(formula)
        element_counts = metadata['element_counts']
        molar_mass = metadata['molar_mass']
        composition = metadata['composition']
        element_contributions = metadata['element_contributions']
    except Exception as e:
        raise ValueError(f"Error parsing formula: {e}")
    
    steps.append(f"Elements found: {', '.join(element_counts.keys())}")
    
    # Step 2: Calculate individual contributions
    steps.append("\n**Step 2: Calculate element contributions**")
    for element, data in element_contributions.items():
        count = data['count']
        atomic_mass = data['atomic_mass']
        contribution = data['contribution']
        
        if count == 1:
            steps.append(f"{element}: {count} × {atomic_mass:.3f} g/mol = {contribution:.3f} g/mol")
        else:
            steps.append(f"{element}: {count} × {atomic_mass:.3f} g/mol = {contribution:.3f} g/mol")
    
    # Step 3: Sum all contributions
    steps.append("\n**Step 3: Sum all contributions**")
    total_calculation = " + ".join([f"{data['contribution']:.3f}" for data in element_contributions.values()])
    steps.append(f"Total = {total_calculation} = {molar_mass:.3f} g/mol")
    
    # Step 4: Final result
    steps.append(f"\n**Molar Mass: {molar_mass:.3f} g/mol**")
    
    return molar_mass, steps, metadata


def format_composition_table(composition: Dict[str, float]) -> str:
    """
    Format composition data as a markdown table.
    
    Args:
        composition: Dictionary mapping elements to percentages
    
    Returns:
        Markdown formatted table string
    """
    table = "| Element | Percentage |\n|---------|------------|\n"
    
    for element, percentage in composition.items():
        table += f"| {element} | {percentage:.2f}% |\n"
    
    return table
