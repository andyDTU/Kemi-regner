"""
Shared solver pattern and step rendering utilities.
Provides a consistent interface for all calculators to return results and steps.
"""

from typing import Tuple, Any, Dict, List
from dataclasses import dataclass

@dataclass
class CalculationResult:
    """
    Container for calculation results and steps.
    
    Attributes:
        result: The calculated result value
        steps: List of step descriptions for showing work
        metadata: Additional information about the calculation
    """
    result: Any
    steps: List[str]
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

def solve_with_steps(calculation_func, *args, **kwargs) -> CalculationResult:
    """
    Wrapper function to execute a calculation and capture steps.
    
    Args:
        calculation_func: Function that returns (result, steps, metadata)
        *args: Arguments to pass to calculation_func
        **kwargs: Keyword arguments to pass to calculation_func
    
    Returns:
        CalculationResult object
    """
    try:
        result, steps, metadata = calculation_func(*args, **kwargs)
        return CalculationResult(result=result, steps=steps, metadata=metadata)
    except Exception as e:
        # Return error result with steps showing the error
        error_steps = [f"Error occurred: {str(e)}"]
        return CalculationResult(
            result=None, 
            steps=error_steps, 
            metadata={"error": True, "error_message": str(e)}
        )

def format_steps_for_display(steps: List[str]) -> str:
    """
    Format calculation steps for display in Streamlit.
    
    Args:
        steps: List of step descriptions
    
    Returns:
        Formatted string with steps numbered
    """
    if not steps:
        return "No steps available."
    
    formatted_steps = []
    for i, step in enumerate(steps, 1):
        formatted_steps.append(f"{i}. {step}")
    
    return "\n\n".join(formatted_steps)

def add_latex_step(step: str, latex: str) -> str:
    """
    Add LaTeX formatting to a step description.
    
    Args:
        step: Step description
        latex: LaTeX expression
    
    Returns:
        Step with LaTeX formatting
    """
    return f"{step} $${latex}$$"

def add_math_step(step: str, expression: str) -> str:
    """
    Add inline math formatting to a step description.
    
    Args:
        step: Step description
        expression: Mathematical expression
    
    Returns:
        Step with inline math formatting
    """
    return f"{step} ${expression}$"

def create_step_summary(calculation_name: str, inputs: Dict[str, Any], result: Any) -> str:
    """
    Create a summary step showing inputs and final result.
    
    Args:
        calculation_name: Name of the calculation
        inputs: Dictionary of input values
        result: Final result
    
    Returns:
        Summary step string
    """
    input_str = ", ".join([f"{k} = {v}" for k, v in inputs.items()])
    return f"**{calculation_name}**: Given {input_str}, we find {result}"

def validate_inputs(inputs: Dict[str, Any], required: List[str], validators: Dict[str, callable] = None) -> None:
    """
    Validate input parameters.
    
    Args:
        inputs: Dictionary of input values
        required: List of required input keys
        validators: Dictionary of validation functions for specific inputs
    
    Raises:
        ValueError: If validation fails
    """
    # Check required inputs
    for key in required:
        if key not in inputs or inputs[key] is None:
            raise ValueError(f"Required input '{key}' is missing")
    
    # Run custom validators
    if validators:
        for key, validator in validators.items():
            if key in inputs and inputs[key] is not None:
                try:
                    validator(inputs[key])
                except Exception as e:
                    raise ValueError(f"Validation failed for '{key}': {e}")

def positive_number_validator(value):
    """Validator for positive numbers."""
    if not isinstance(value, (int, float)) or value <= 0:
        raise ValueError("Value must be a positive number")

def temperature_validator(value):
    """Validator for temperature values (must be positive)."""
    if not isinstance(value, (int, float)) or value <= 0:
        raise ValueError("Temperature must be positive")

def formula_validator(value):
    """Validator for chemical formulas (must be non-empty string)."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Formula must be a non-empty string")
