"""
Acids and bases calculator for chemical calculations.
Includes strong/weak acids/bases, buffers, and titration calculations.
"""

import math
from typing import Dict, List, Tuple, Any, Optional
from core.equilibrium import solve_quadratic_equation


# Constants
KW = 1.0e-14  # Water dissociation constant at 25°C


def calculate_strong_acid_ph(concentration: float, volume: float) -> Tuple[float, List[str], Dict[str, Any]]:
    """
    Calculate pH of a strong acid solution.
    
    Args:
        concentration: Acid concentration in M
        volume: Volume in L
    
    Returns:
        Tuple of (pH, steps, metadata)
    """
    steps = []
    
    # Step 1: Strong acid completely dissociates
    steps.append("**Step 1: Strong acid completely dissociates**")
    steps.append(f"HA → H⁺ + A⁻")
    steps.append(f"Since this is a strong acid, [H⁺] = [HA]₀ = {concentration:.4f} M")
    
    # Step 2: Calculate pH
    steps.append("\n**Step 2: Calculate pH**")
    h_plus = concentration
    ph = -math.log10(h_plus)
    steps.append(f"pH = -log₁₀[H⁺] = -log₁₀({h_plus:.4f}) = {ph:.4f}")
    
    # Step 3: Calculate pOH
    steps.append("\n**Step 3: Calculate pOH**")
    poh = 14 - ph
    steps.append(f"pOH = 14 - pH = 14 - {ph:.4f} = {poh:.4f}")
    
    metadata = {
        'h_plus': h_plus,
        'ph': ph,
        'poh': poh,
        'concentration': concentration,
        'volume': volume
    }
    
    return ph, steps, metadata


def calculate_strong_base_ph(concentration: float, volume: float) -> Tuple[float, List[str], Dict[str, Any]]:
    """
    Calculate pH of a strong base solution.
    
    Args:
        concentration: Base concentration in M
        volume: Volume in L
    
    Returns:
        Tuple of (pH, steps, metadata)
    """
    steps = []
    
    # Step 1: Strong base completely dissociates
    steps.append("**Step 1: Strong base completely dissociates**")
    steps.append(f"BOH → B⁺ + OH⁻")
    steps.append(f"Since this is a strong base, [OH⁻] = [BOH]₀ = {concentration:.4f} M")
    
    # Step 2: Calculate pOH
    steps.append("\n**Step 2: Calculate pOH**")
    oh_minus = concentration
    poh = -math.log10(oh_minus)
    steps.append(f"pOH = -log₁₀[OH⁻] = -log₁₀({oh_minus:.4f}) = {poh:.4f}")
    
    # Step 3: Calculate pH
    steps.append("\n**Step 3: Calculate pH**")
    ph = 14 - poh
    steps.append(f"pH = 14 - pOH = 14 - {poh:.4f} = {ph:.4f}")
    
    metadata = {
        'oh_minus': oh_minus,
        'ph': ph,
        'poh': poh,
        'concentration': concentration,
        'volume': volume
    }
    
    return ph, steps, metadata


def calculate_strong_acid_base_mixture(acid_conc: float, acid_vol: float, 
                                      base_conc: float, base_vol: float) -> Tuple[float, List[str], Dict[str, Any]]:
    """
    Calculate pH when mixing strong acid and strong base.
    
    Args:
        acid_conc: Acid concentration in M
        acid_vol: Acid volume in L
        base_conc: Base concentration in M
        base_vol: Base volume in L
    
    Returns:
        Tuple of (pH, steps, metadata)
    """
    steps = []
    
    # Step 1: Calculate moles
    steps.append("**Step 1: Calculate moles of acid and base**")
    acid_moles = acid_conc * acid_vol
    base_moles = base_conc * base_vol
    steps.append(f"Moles of acid = {acid_conc:.4f} M × {acid_vol:.4f} L = {acid_moles:.6f} mol")
    steps.append(f"Moles of base = {base_conc:.4f} M × {base_vol:.4f} L = {base_moles:.6f} mol")
    
    # Step 2: Determine limiting species
    steps.append("\n**Step 2: Determine limiting species**")
    if acid_moles > base_moles:
        limiting = "base"
        excess_moles = acid_moles - base_moles
        steps.append(f"Base is limiting. Excess acid = {acid_moles:.6f} - {base_moles:.6f} = {excess_moles:.6f} mol")
    elif base_moles > acid_moles:
        limiting = "acid"
        excess_moles = base_moles - acid_moles
        steps.append(f"Acid is limiting. Excess base = {base_moles:.6f} - {acid_moles:.6f} = {excess_moles:.6f} mol")
    else:
        # Equal moles - neutral solution
        steps.append("Equal moles of acid and base - neutral solution")
        metadata = {
            'ph': 7.0,
            'acid_moles': acid_moles,
            'base_moles': base_moles,
            'excess_moles': 0.0,
            'limiting': "equal"
        }
        return 7.0, steps, metadata
    
    # Step 3: Calculate final concentration
    steps.append("\n**Step 3: Calculate final concentration**")
    total_volume = acid_vol + base_vol
    excess_concentration = excess_moles / total_volume
    steps.append(f"Total volume = {acid_vol:.4f} L + {base_vol:.4f} L = {total_volume:.4f} L")
    steps.append(f"Excess concentration = {excess_moles:.6f} mol ÷ {total_volume:.4f} L = {excess_concentration:.6f} M")
    
    # Step 4: Calculate pH
    steps.append("\n**Step 4: Calculate pH**")
    if limiting == "base":
        # Excess acid
        ph = -math.log10(excess_concentration)
        steps.append(f"Excess acid: pH = -log₁₀({excess_concentration:.6f}) = {ph:.4f}")
    else:
        # Excess base
        poh = -math.log10(excess_concentration)
        ph = 14 - poh
        steps.append(f"Excess base: pOH = -log₁₀({excess_concentration:.6f}) = {poh:.4f}")
        steps.append(f"pH = 14 - {poh:.4f} = {ph:.4f}")
    
    metadata = {
        'ph': ph,
        'acid_moles': acid_moles,
        'base_moles': base_moles,
        'excess_moles': excess_moles,
        'excess_concentration': excess_concentration,
        'limiting': limiting,
        'total_volume': total_volume
    }
    
    return ph, steps, metadata


def calculate_weak_acid_ph(concentration: float, ka: float) -> Tuple[float, List[str], Dict[str, Any]]:
    """
    Calculate pH of a weak acid solution.
    
    Args:
        concentration: Acid concentration in M
        ka: Acid dissociation constant
    
    Returns:
        Tuple of (pH, steps, metadata)
    """
    steps = []
    
    # Step 1: Set up ICE table
    steps.append("**Step 1: Set up ICE table**")
    steps.append("HA ⇌ H⁺ + A⁻")
    steps.append("Initial: [HA]₀ = C₀, [H⁺]₀ = 0, [A⁻]₀ = 0")
    steps.append("Change: -x, +x, +x")
    steps.append("Equilibrium: C₀ - x, x, x")
    
    # Step 2: Write Ka expression
    steps.append("\n**Step 2: Write Ka expression**")
    steps.append("Ka = [H⁺][A⁻] / [HA] = x² / (C₀ - x)")
    steps.append(f"Ka = {ka:.2e} = x² / ({concentration:.4f} - x)")
    
    # Step 3: Check if approximation is valid
    steps.append("\n**Step 3: Check if approximation is valid**")
    x_approx = math.sqrt(ka * concentration)
    percent_ionization = (x_approx / concentration) * 100
    steps.append(f"Approximate solution: x ≈ √(Ka × C₀) = √({ka:.2e} × {concentration:.4f}) = {x_approx:.6f}")
    steps.append(f"Percent ionization = {percent_ionization:.2f}%")
    
    if percent_ionization < 5:
        steps.append("Since percent ionization < 5%, approximation is valid")
        x = x_approx
        steps.append("Using approximation: x = √(Ka × C₀)")
    else:
        steps.append("Since percent ionization ≥ 5%, must solve quadratic equation")
        steps.append("x² + Ka·x - Ka·C₀ = 0")
        steps.append(f"x² + {ka:.2e}·x - {ka:.2e}·{concentration:.4f} = 0")
        
        # Solve quadratic: x² + Ka·x - Ka·C₀ = 0
        a = 1.0
        b = ka
        c = -ka * concentration
        
        try:
            x = solve_quadratic_equation(a, b, c)
            steps.append(f"Quadratic solution: x = {x:.6f}")
        except ValueError as e:
            steps.append(f"Error solving quadratic: {e}")
            # Fall back to approximation
            x = x_approx
            steps.append("Using approximation instead")
    
    # Step 4: Calculate pH
    steps.append("\n**Step 4: Calculate pH**")
    h_plus = x
    ph = -math.log10(h_plus)
    steps.append(f"[H⁺] = x = {h_plus:.6f} M")
    steps.append(f"pH = -log₁₀({h_plus:.6f}) = {ph:.4f}")
    
    # Step 5: Verify approximation accuracy
    if percent_ionization >= 5:
        steps.append("\n**Step 5: Verify approximation accuracy**")
        error = abs(x - x_approx) / x * 100
        steps.append(f"Approximation error = |{x:.6f} - {x_approx:.6f}| / {x:.6f} × 100% = {error:.2f}%")
        if error > 5:
            steps.append("⚠️ Warning: Approximation error > 5%")
        else:
            steps.append("✅ Approximation error ≤ 5%")
    
    metadata = {
        'h_plus': h_plus,
        'ph': ph,
        'ka': ka,
        'concentration': concentration,
        'x_approx': x_approx,
        'percent_ionization': percent_ionization,
        'approximation_valid': percent_ionization < 5
    }
    
    return ph, steps, metadata


def calculate_weak_base_ph(concentration: float, kb: float = None, ka_conjugate: float = None) -> Tuple[float, List[str], Dict[str, Any]]:
    """
    Calculate pH of a weak base solution.
    
    Args:
        concentration: Base concentration in M
        kb: Base dissociation constant (if provided)
        ka_conjugate: Ka of conjugate acid (if kb not provided)
    
    Returns:
        Tuple of (pH, steps, metadata)
    """
    steps = []
    
    # Step 1: Determine Kb
    if kb is None and ka_conjugate is not None:
        steps.append("**Step 1: Calculate Kb from conjugate acid Ka**")
        kb = KW / ka_conjugate
        steps.append(f"Kb = Kw / Ka = {KW:.2e} / {ka_conjugate:.2e} = {kb:.2e}")
    elif kb is None:
        raise ValueError("Either kb or ka_conjugate must be provided")
    
    # Step 2: Set up ICE table
    steps.append("\n**Step 2: Set up ICE table**")
    steps.append("B + H₂O ⇌ BH⁺ + OH⁻")
    steps.append("Initial: [B]₀ = C₀, [BH⁺]₀ = 0, [OH⁻]₀ = 0")
    steps.append("Change: -x, +x, +x")
    steps.append("Equilibrium: C₀ - x, x, x")
    
    # Step 3: Write Kb expression
    steps.append("\n**Step 3: Write Kb expression**")
    steps.append("Kb = [BH⁺][OH⁻] / [B] = x² / (C₀ - x)")
    steps.append(f"Kb = {kb:.2e} = x² / ({concentration:.4f} - x)")
    
    # Step 4: Check if approximation is valid
    steps.append("\n**Step 4: Check if approximation is valid**")
    x_approx = math.sqrt(kb * concentration)
    percent_ionization = (x_approx / concentration) * 100
    steps.append(f"Approximate solution: x ≈ √(Kb × C₀) = √({kb:.2e} × {concentration:.4f}) = {x_approx:.6f}")
    steps.append(f"Percent ionization = {percent_ionization:.2f}%")
    
    if percent_ionization < 5:
        steps.append("Since percent ionization < 5%, approximation is valid")
        x = x_approx
        steps.append("Using approximation: x = √(Kb × C₀)")
    else:
        steps.append("Since percent ionization ≥ 5%, must solve quadratic equation")
        steps.append("x² + Kb·x - Kb·C₀ = 0")
        steps.append(f"x² + {kb:.2e}·x - {kb:.2e}·{concentration:.4f} = 0")
        
        # Solve quadratic: x² + Kb·x - Kb·C₀ = 0
        a = 1.0
        b = kb
        c = -kb * concentration
        
        try:
            x = solve_quadratic_equation(a, b, c)
            steps.append(f"Quadratic solution: x = {x:.6f}")
        except ValueError as e:
            steps.append(f"Error solving quadratic: {e}")
            # Fall back to approximation
            x = x_approx
            steps.append("Using approximation instead")
    
    # Step 5: Calculate pH
    steps.append("\n**Step 5: Calculate pH**")
    oh_minus = x
    poh = -math.log10(oh_minus)
    ph = 14 - poh
    steps.append(f"[OH⁻] = x = {oh_minus:.6f} M")
    steps.append(f"pOH = -log₁₀({oh_minus:.6f}) = {poh:.4f}")
    steps.append(f"pH = 14 - pOH = 14 - {poh:.4f} = {ph:.4f}")
    
    metadata = {
        'oh_minus': oh_minus,
        'ph': ph,
        'poh': poh,
        'kb': kb,
        'concentration': concentration,
        'x_approx': x_approx,
        'percent_ionization': percent_ionization
    }
    
    return ph, steps, metadata


def calculate_buffer_ph(concentration_a_minus: float, concentration_ha: float, 
                       ka: float, pka: float = None) -> Tuple[float, List[str], Dict[str, Any]]:
    """
    Calculate pH of a buffer solution using Henderson-Hasselbalch equation.
    
    Args:
        concentration_a_minus: Concentration of conjugate base A⁻ in M
        concentration_ha: Concentration of weak acid HA in M
        ka: Acid dissociation constant
        pka: pKa value (if provided, overrides ka)
    
    Returns:
        Tuple of (pH, steps, metadata)
    """
    steps = []
    
    # Step 1: Determine pKa
    if pka is not None:
        steps.append("**Step 1: Use provided pKa**")
        steps.append(f"pKa = {pka:.4f}")
    else:
        steps.append("**Step 1: Calculate pKa from Ka**")
        pka = -math.log10(ka)
        steps.append(f"pKa = -log₁₀(Ka) = -log₁₀({ka:.2e}) = {pka:.4f}")
    
    # Step 2: Henderson-Hasselbalch equation
    steps.append("\n**Step 2: Henderson-Hasselbalch equation**")
    steps.append("pH = pKa + log₁₀([A⁻] / [HA])")
    steps.append(f"pH = {pka:.4f} + log₁₀({concentration_a_minus:.4f} / {concentration_ha:.4f})")
    
    # Step 3: Calculate ratio
    ratio = concentration_a_minus / concentration_ha
    steps.append(f"Ratio [A⁻] / [HA] = {concentration_a_minus:.4f} / {concentration_ha:.4f} = {ratio:.4f}")
    
    # Step 4: Calculate pH
    steps.append("\n**Step 3: Calculate pH**")
    log_ratio = math.log10(ratio)
    ph = pka + log_ratio
    steps.append(f"log₁₀({ratio:.4f}) = {log_ratio:.4f}")
    steps.append(f"pH = {pka:.4f} + {log_ratio:.4f} = {ph:.4f}")
    
    metadata = {
        'ph': ph,
        'pka': pka,
        'ka': ka,
        'concentration_a_minus': concentration_a_minus,
        'concentration_ha': concentration_ha,
        'ratio': ratio,
        'log_ratio': log_ratio
    }
    
    return ph, steps, metadata


def calculate_buffer_mixing_ph(acid_conc: float, acid_vol: float, 
                              base_conc: float, base_vol: float, 
                              ka: float) -> Tuple[float, List[str], Dict[str, Any]]:
    """
    Calculate pH when mixing weak acid and conjugate base solutions.
    
    Args:
        acid_conc: Weak acid concentration in M
        acid_vol: Weak acid volume in L
        base_conc: Conjugate base concentration in M
        base_vol: Conjugate base volume in L
        ka: Acid dissociation constant
    
    Returns:
        Tuple of (pH, steps, metadata)
    """
    steps = []
    
    # Step 1: Calculate moles
    steps.append("**Step 1: Calculate moles of acid and conjugate base**")
    acid_moles = acid_conc * acid_vol
    base_moles = base_conc * base_vol
    steps.append(f"Moles of HA = {acid_conc:.4f} M × {acid_vol:.4f} L = {acid_moles:.6f} mol")
    steps.append(f"Moles of A⁻ = {base_conc:.4f} M × {base_vol:.4f} L = {base_moles:.6f} mol")
    
    # Step 2: Calculate final concentrations
    steps.append("\n**Step 2: Calculate final concentrations**")
    total_volume = acid_vol + base_vol
    final_ha_conc = acid_moles / total_volume
    final_a_minus_conc = base_moles / total_volume
    steps.append(f"Total volume = {acid_vol:.4f} L + {base_vol:.4f} L = {total_volume:.4f} L")
    steps.append(f"[HA] = {acid_moles:.6f} mol ÷ {total_volume:.4f} L = {final_ha_conc:.6f} M")
    steps.append(f"[A⁻] = {base_moles:.6f} mol ÷ {total_volume:.4f} L = {final_a_minus_conc:.6f} M")
    
    # Step 3: Use Henderson-Hasselbalch
    steps.append("\n**Step 3: Use Henderson-Hasselbalch equation**")
    ph, buffer_steps, buffer_metadata = calculate_buffer_ph(
        final_a_minus_conc, final_ha_conc, ka
    )
    
    # Add buffer calculation steps
    steps.extend(buffer_steps[1:])  # Skip the first step since we already have pKa
    
    metadata = {
        'ph': ph,
        'acid_moles': acid_moles,
        'base_moles': base_moles,
        'total_volume': total_volume,
        'final_ha_conc': final_ha_conc,
        'final_a_minus_conc': final_a_minus_conc,
        'ka': ka
    }
    
    return ph, steps, metadata


def calculate_target_buffer_ratio(target_ph: float, pka: float, ka: float = None) -> Tuple[float, List[str], Dict[str, Any]]:
    """
    Calculate required ratio [A⁻]/[HA] for target pH.
    
    Args:
        target_ph: Target pH
        pka: pKa value
        ka: Ka value (if provided, overrides pka)
    
    Returns:
        Tuple of (ratio, steps, metadata)
    """
    steps = []
    
    # Step 1: Determine pKa
    if ka is not None:
        steps.append("**Step 1: Calculate pKa from Ka**")
        pka = -math.log10(ka)
        steps.append(f"pKa = -log₁₀(Ka) = -log₁₀({ka:.2e}) = {pka:.4f}")
    
    # Step 2: Henderson-Hasselbalch equation
    steps.append("\n**Step 2: Henderson-Hasselbalch equation**")
    steps.append("pH = pKa + log₁₀([A⁻] / [HA])")
    steps.append(f"Target pH = {target_ph:.4f}")
    steps.append(f"pKa = {pka:.4f}")
    
    # Step 3: Solve for ratio
    steps.append("\n**Step 3: Solve for ratio**")
    steps.append("[A⁻] / [HA] = 10^(pH - pKa)")
    ph_diff = target_ph - pka
    ratio = 10**ph_diff
    steps.append(f"pH - pKa = {target_ph:.4f} - {pka:.4f} = {ph_diff:.4f}")
    steps.append(f"[A⁻] / [HA] = 10^({ph_diff:.4f}) = {ratio:.4f}")
    
    metadata = {
        'target_ph': target_ph,
        'pka': pka,
        'ph_diff': ph_diff,
        'ratio': ratio
    }
    
    return ratio, steps, metadata


def calculate_titration_strong_acid_strong_base(acid_conc: float, acid_vol: float,
                                              base_conc: float, base_vol: float) -> Tuple[float, str, List[str], Dict[str, Any]]:
    """
    Calculate pH for strong acid-strong base titration.
    
    Args:
        acid_conc: Initial acid concentration in M
        acid_vol: Initial acid volume in L
        base_conc: Base concentration in M
        base_vol: Base volume added in L
    
    Returns:
        Tuple of (pH, region, steps, metadata)
    """
    steps = []
    
    # Step 1: Calculate initial moles
    steps.append("**Step 1: Calculate initial moles**")
    acid_moles = acid_conc * acid_vol
    base_moles = base_conc * base_vol
    steps.append(f"Initial moles of acid = {acid_conc:.4f} M × {acid_vol:.4f} L = {acid_moles:.6f} mol")
    steps.append(f"Moles of base added = {base_conc:.4f} M × {base_vol:.4f} L = {base_moles:.6f} mol")
    
    # Step 2: Determine region
    steps.append("\n**Step 2: Determine titration region**")
    if base_moles < acid_moles:
        region = "before equivalence"
        steps.append(f"Base moles ({base_moles:.6f}) < Acid moles ({acid_moles:.6f})")
        steps.append("Region: Before equivalence point")
        
        # Calculate excess acid
        excess_acid_moles = acid_moles - base_moles
        total_volume = acid_vol + base_vol
        excess_acid_conc = excess_acid_moles / total_volume
        
        steps.append(f"Excess acid = {acid_moles:.6f} - {base_moles:.6f} = {excess_acid_moles:.6f} mol")
        steps.append(f"Total volume = {acid_vol:.4f} + {base_vol:.4f} = {total_volume:.4f} L")
        steps.append(f"[H⁺] = {excess_acid_moles:.6f} ÷ {total_volume:.4f} = {excess_acid_conc:.6f} M")
        
        ph = -math.log10(excess_acid_conc)
        steps.append(f"pH = -log₁₀({excess_acid_conc:.6f}) = {ph:.4f}")
        
    elif abs(base_moles - acid_moles) < 1e-10:
        region = "at equivalence"
        steps.append(f"Base moles ({base_moles:.6f}) = Acid moles ({acid_moles:.6f})")
        steps.append("Region: At equivalence point")
        steps.append("Strong acid + strong base → neutral solution")
        ph = 7.0
        steps.append("pH = 7.0 (neutral)")
        
    else:
        region = "after equivalence"
        steps.append(f"Base moles ({base_moles:.6f}) > Acid moles ({acid_moles:.6f})")
        steps.append("Region: After equivalence point")
        
        # Calculate excess base
        excess_base_moles = base_moles - acid_moles
        total_volume = acid_vol + base_vol
        excess_base_conc = excess_base_moles / total_volume
        
        steps.append(f"Excess base = {base_moles:.6f} - {acid_moles:.6f} = {excess_base_moles:.6f} mol")
        steps.append(f"Total volume = {acid_vol:.4f} + {base_vol:.4f} = {total_volume:.4f} L")
        steps.append(f"[OH⁻] = {excess_base_moles:.6f} ÷ {total_volume:.4f} = {excess_base_conc:.6f} M")
        
        poh = -math.log10(excess_base_conc)
        ph = 14 - poh
        steps.append(f"pOH = -log₁₀({excess_base_conc:.6f}) = {poh:.4f}")
        steps.append(f"pH = 14 - {poh:.4f} = {ph:.4f}")
    
    metadata = {
        'ph': ph,
        'region': region,
        'acid_moles': acid_moles,
        'base_moles': base_moles,
        'acid_conc': acid_conc,
        'acid_vol': acid_vol,
        'base_conc': base_conc,
        'base_vol': base_vol
    }
    
    return ph, region, steps, metadata


def calculate_titration_weak_acid_strong_base(acid_conc: float, acid_vol: float, ka: float,
                                             base_conc: float, base_vol: float) -> Tuple[float, str, List[str], Dict[str, Any]]:
    """
    Calculate pH for weak acid-strong base titration.
    
    Args:
        acid_conc: Initial acid concentration in M
        acid_vol: Initial acid volume in L
        ka: Acid dissociation constant
        base_conc: Base concentration in M
        base_vol: Base volume added in L
    
    Returns:
        Tuple of (pH, region, steps, metadata)
    """
    steps = []
    
    # Step 1: Calculate initial moles
    steps.append("**Step 1: Calculate initial moles**")
    acid_moles = acid_conc * acid_vol
    base_moles = base_conc * base_vol
    steps.append(f"Initial moles of weak acid = {acid_conc:.4f} M × {acid_vol:.4f} L = {acid_moles:.6f} mol")
    steps.append(f"Moles of strong base added = {base_conc:.4f} M × {base_vol:.4f} L = {base_moles:.6f} mol")
    
    # Step 2: Determine region
    steps.append("\n**Step 2: Determine titration region**")
    if base_moles < acid_moles:
        region = "before equivalence"
        steps.append(f"Base moles ({base_moles:.6f}) < Acid moles ({acid_moles:.6f})")
        steps.append("Region: Before equivalence point - buffer region")
        
        # Calculate buffer composition
        remaining_acid_moles = acid_moles - base_moles
        conjugate_base_moles = base_moles
        total_volume = acid_vol + base_vol
        
        remaining_acid_conc = remaining_acid_moles / total_volume
        conjugate_base_conc = conjugate_base_moles / total_volume
        
        steps.append(f"Remaining acid = {acid_moles:.6f} - {base_moles:.6f} = {remaining_acid_moles:.6f} mol")
        steps.append(f"Conjugate base formed = {base_moles:.6f} mol")
        steps.append(f"Total volume = {acid_vol:.4f} + {base_vol:.4f} = {total_volume:.4f} L")
        steps.append(f"[HA] = {remaining_acid_moles:.6f} ÷ {total_volume:.4f} = {remaining_acid_conc:.6f} M")
        steps.append(f"[A⁻] = {conjugate_base_moles:.6f} ÷ {total_volume:.4f} = {conjugate_base_conc:.6f} M")
        
        # Use Henderson-Hasselbalch
        steps.append("\n**Step 3: Use Henderson-Hasselbalch equation**")
        ph, buffer_steps, buffer_metadata = calculate_buffer_ph(
            conjugate_base_conc, remaining_acid_conc, ka
        )
        steps.extend(buffer_steps[1:])  # Skip first step
        
    elif abs(base_moles - acid_moles) < 1e-10:
        region = "at equivalence"
        steps.append(f"Base moles ({base_moles:.6f}) = Acid moles ({acid_moles:.6f})")
        steps.append("Region: At equivalence point")
        steps.append("Weak acid + strong base → solution of conjugate base")
        
        # Calculate conjugate base concentration
        total_volume = acid_vol + base_vol
        conjugate_base_conc = acid_moles / total_volume
        steps.append(f"Total volume = {acid_vol:.4f} + {base_vol:.4f} = {total_volume:.4f} L")
        steps.append(f"[A⁻] = {acid_moles:.6f} ÷ {total_volume:.4f} = {conjugate_base_conc:.6f} M")
        
        # Calculate Kb and [OH-]
        kb = KW / ka
        steps.append(f"Kb = Kw / Ka = {KW:.2e} / {ka:.2e} = {kb:.2e}")
        
        # Solve for [OH-] using approximation (since conjugate base is weak)
        oh_minus = math.sqrt(kb * conjugate_base_conc)
        steps.append(f"[OH⁻] = √(Kb × [A⁻]) = √({kb:.2e} × {conjugate_base_conc:.6f}) = {oh_minus:.6f}")
        
        poh = -math.log10(oh_minus)
        ph = 14 - poh
        steps.append(f"pOH = -log₁₀({oh_minus:.6f}) = {poh:.4f}")
        steps.append(f"pH = 14 - {poh:.4f} = {ph:.4f}")
        
    else:
        region = "after equivalence"
        steps.append(f"Base moles ({base_moles:.6f}) > Acid moles ({acid_moles:.6f})")
        steps.append("Region: After equivalence point - excess strong base")
        
        # Calculate excess base
        excess_base_moles = base_moles - acid_moles
        total_volume = acid_vol + base_vol
        excess_base_conc = excess_base_moles / total_volume
        
        steps.append(f"Excess base = {base_moles:.6f} - {acid_moles:.6f} = {excess_base_moles:.6f} mol")
        steps.append(f"Total volume = {acid_vol:.4f} + {base_vol:.4f} = {total_volume:.4f} L")
        steps.append(f"[OH⁻] = {excess_base_moles:.6f} ÷ {total_volume:.4f} = {excess_base_conc:.6f} M")
        
        poh = -math.log10(excess_base_conc)
        ph = 14 - poh
        steps.append(f"pOH = -log₁₀({excess_base_conc:.6f}) = {poh:.4f}")
        steps.append(f"pH = 14 - {poh:.4f} = {ph:.4f}")
    
    metadata = {
        'ph': ph,
        'region': region,
        'acid_moles': acid_moles,
        'base_moles': base_moles,
        'ka': ka,
        'acid_conc': acid_conc,
        'acid_vol': acid_vol,
        'base_conc': base_conc,
        'base_vol': base_vol
    }
    
    return ph, region, steps, metadata
