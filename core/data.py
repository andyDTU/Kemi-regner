"""
Data loading utilities for periodic table and constants.
"""

import json
import periodictable
from pathlib import Path
from typing import Dict, Any, Optional

# Constants
DATA_DIR = Path(__file__).parent.parent / "data"
CONSTANTS_PATH = DATA_DIR / "constants.json"

def get_atomic_mass(symbol: str) -> float:
    """
    Get atomic mass for a given element symbol using the periodictable library.
    
    Args:
        symbol: Element symbol (e.g., 'H', 'C', 'Fe')
    
    Returns:
        Atomic mass in g/mol
    
    Raises:
        ValueError: If element symbol not found
    """
    symbol = symbol.strip().capitalize()
    
    try:
        # Get the element from periodictable
        element = getattr(periodictable, symbol)
        # Return atomic mass in g/mol
        return float(element.mass)
    except AttributeError:
        raise ValueError(f"Element symbol '{symbol}' not found in periodic table")

def load_constants() -> Dict[str, Any]:
    """
    Load constants from JSON file.
    
    Returns:
        Dictionary of constants
    """
    try:
        with open(CONSTANTS_PATH, 'r') as f:
            constants = json.load(f)
        return constants
    except FileNotFoundError:
        raise FileNotFoundError(f"Constants file not found at {CONSTANTS_PATH}")
    except Exception as e:
        raise Exception(f"Error loading constants: {e}")

def get_gas_constant() -> float:
    """
    Get the gas constant R.
    
    Returns:
        Gas constant in J/(mol·K)
    """
    constants = load_constants()
    return constants.get('R', 8.314462618)

# Initialize constants on module import
try:
    CONSTANTS = load_constants()
except Exception as e:
    print(f"Warning: Could not load constants file: {e}")
    CONSTANTS = None
