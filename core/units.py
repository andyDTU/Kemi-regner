"""
Unit handling utilities using pint library.
Provides a global UnitRegistry and helper functions for chemistry calculations.
"""

from typing import Union
import pint

# Global UnitRegistry for the entire application
ureg = pint.UnitRegistry()

def Q(value: Union[int, float], unit: str) -> pint.Quantity:
    """
    Create a pint Quantity with the given value and unit.
    
    Args:
        value: Numeric value
        unit: Unit string (e.g., "J", "kJ", "mol", "K")
    
    Returns:
        pint.Quantity object
    """
    return ureg.Quantity(value, unit)

def convert_energy(quantity: pint.Quantity, target_unit: str) -> pint.Quantity:
    """
    Convert energy to target unit, handling common chemistry units.
    
    Args:
        quantity: Input quantity with energy units
        target_unit: Target unit (e.g., "J", "kJ", "cal", "kcal")
    
    Returns:
        Converted quantity in target unit
    """
    return quantity.to(target_unit)

def convert_temperature(quantity: pint.Quantity, target_unit: str) -> pint.Quantity:
    """
    Convert temperature to target unit.
    
    Args:
        quantity: Input quantity with temperature units
        target_unit: Target unit (e.g., "K", "degC", "degF")
    
    Returns:
        Converted quantity in target unit
    """
    return quantity.to(target_unit)

def normalize_energy(quantity: pint.Quantity) -> pint.Quantity:
    """
    Normalize energy to J/mol for calculations.
    
    Args:
        quantity: Input energy quantity
    
    Returns:
        Energy in J/mol
    """
    if quantity.dimensionality == ureg.dimensionless:
        raise ValueError("Quantity must have energy dimensions")
    
    # Convert to J/mol
    if hasattr(quantity, 'units'):
        return quantity.to('J/mol')
    return quantity

def normalize_temperature(quantity: pint.Quantity) -> pint.Quantity:
    """
    Normalize temperature to K for calculations.
    
    Args:
        quantity: Input temperature quantity
    
    Returns:
        Temperature in K
    """
    if quantity.dimensionality == ureg.dimensionless:
        raise ValueError("Quantity must have temperature dimensions")
    
    # Convert to K
    if hasattr(quantity, 'units'):
        return quantity.to('K')
    return quantity
