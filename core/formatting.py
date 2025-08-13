"""
Formatting utilities for chemistry calculations.
Provides functions for significant figures, value formatting, and unit display.
"""

from typing import Union
import math

def sig_round(x: float, n: int) -> float:
    """
    Round a number to n significant figures.
    
    Args:
        x: Number to round
        n: Number of significant figures
    
    Returns:
        Rounded number
    """
    if x == 0:
        return 0
    
    # Handle negative numbers
    sign = 1 if x > 0 else -1
    x = abs(x)
    
    # Calculate the order of magnitude
    if x >= 1:
        order = int(math.floor(math.log10(x))) + 1
    else:
        order = int(math.floor(math.log10(x)))
    
    # Calculate the multiplier for rounding
    multiplier = 10 ** (order - n)
    
    # Round and apply multiplier
    rounded = round(x / multiplier) * multiplier
    
    return sign * rounded

def fmt_quantity(q, sigfigs: int = 4) -> str:
    """
    Format a quantity with value and unit, handling significant figures.
    
    Args:
        q: Quantity (can be pint.Quantity, float, or int)
        sigfigs: Number of significant figures (default: 4)
    
    Returns:
        Formatted string with value and unit
    """
    try:
        # Handle pint quantities
        if hasattr(q, 'magnitude') and hasattr(q, 'units'):
            value = sig_round(q.magnitude, sigfigs)
            unit = str(q.units)
            
            # Format the value nicely
            if value == int(value):
                value_str = str(int(value))
            else:
                value_str = f"{value:.{sigfigs-1}g}"
            
            return f"{value_str} {unit}"
        
        # Handle plain numbers
        else:
            value = sig_round(float(q), sigfigs)
            if value == int(value):
                return str(int(value))
            else:
                return f"{value:.{sigfigs-1}g}"
    
    except Exception:
        # Fallback to string representation
        return str(q)

def fmt_percentage(value: float, sigfigs: int = 3) -> str:
    """
    Format a percentage value with appropriate significant figures.
    
    Args:
        value: Percentage value (0-100)
        sigfigs: Number of significant figures (default: 3)
    
    Returns:
        Formatted percentage string
    """
    rounded = sig_round(value, sigfigs)
    
    if rounded == int(rounded):
        return f"{int(rounded)}%"
    else:
        return f"{rounded:.{sigfigs-1}g}%"

def fmt_scientific(value: float, sigfigs: int = 3) -> str:
    """
    Format a number in scientific notation.
    
    Args:
        value: Number to format
        sigfigs: Number of significant figures (default: 3)
    
    Returns:
        Formatted scientific notation string
    """
    if value == 0:
        return "0"
    
    rounded = sig_round(value, sigfigs)
    
    if abs(rounded) < 0.01 or abs(rounded) >= 10000:
        # Use scientific notation
        exp = int(math.floor(math.log10(abs(rounded))))
        mantissa = rounded / (10 ** exp)
        mantissa_rounded = sig_round(mantissa, sigfigs)
        
        if mantissa_rounded == 1:
            return f"1×10^{exp}"
        else:
            return f"{mantissa_rounded:.{sigfigs-1}g}×10^{exp}"
    else:
        # Use regular decimal notation
        if rounded == int(rounded):
            return str(int(rounded))
        else:
            return f"{rounded:.{sigfigs-1}g}"

def fmt_energy(value: float, unit: str = "J/mol") -> str:
    """
    Format energy values with appropriate units and significant figures.
    
    Args:
        value: Energy value
        unit: Unit string (default: "J/mol")
    
    Returns:
        Formatted energy string
    """
    if abs(value) >= 1000:
        # Convert to kJ
        value_kj = value / 1000
        rounded = sig_round(value_kj, 4)
        if rounded == int(rounded):
            return f"{int(rounded)} kJ/mol"
        else:
            return f"{rounded:.3g} kJ/mol"
    else:
        rounded = sig_round(value, 4)
        if rounded == int(rounded):
            return f"{int(rounded)} {unit}"
        else:
            return f"{rounded:.3g} {unit}"
