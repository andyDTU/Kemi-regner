"""
Tests for acids and bases calculator.
"""
import pytest
import sys
import math
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from calculators.acids_bases import (
    calculate_strong_acid_ph, calculate_strong_base_ph,
    calculate_strong_acid_base_mixture, calculate_weak_acid_ph,
    calculate_weak_base_ph, calculate_buffer_ph,
    calculate_buffer_mixing_ph, calculate_target_buffer_ratio,
    calculate_titration_strong_acid_strong_base,
    calculate_titration_weak_acid_strong_base
)


def test_strong_acid_ph():
    """Test strong acid pH calculation."""
    ph, steps, metadata = calculate_strong_acid_ph(0.1, 1.0)
    assert abs(ph - 1.0) < 0.01
    assert len(steps) > 0
    assert metadata['concentration'] == 0.1
    assert metadata['volume'] == 1.0


def test_strong_base_ph():
    """Test strong base pH calculation."""
    ph, steps, metadata = calculate_strong_base_ph(0.01, 1.0)
    assert abs(ph - 12.0) < 0.01
    assert len(steps) > 0
    assert metadata['concentration'] == 0.01
    assert metadata['volume'] == 1.0


def test_strong_acid_base_mixture():
    """Test strong acid-base mixture calculation."""
    ph, steps, metadata = calculate_strong_acid_base_mixture(0.1, 1.0, 0.05, 1.0)
    # Acid is in excess: 0.1 - 0.05 = 0.05 M excess acid
    # Total volume = 2.0 L, excess acid = 0.05 mol, so [H+] = 0.05/2.0 = 0.025 M
    expected_ph = -math.log10(0.025)
    assert abs(ph - expected_ph) < 0.01
    assert len(steps) > 0
    assert metadata['limiting'] == 'base'


def test_weak_acid_ph():
    """Test weak acid pH calculation."""
    ph, steps, metadata = calculate_weak_acid_ph(0.1, 1.8e-5)
    # For weak acid: [H+] = sqrt(Ka * C0)
    expected_h = math.sqrt(1.8e-5 * 0.1)
    expected_ph = -math.log10(expected_h)
    assert abs(ph - expected_ph) < 0.01
    assert len(steps) > 0
    assert metadata['ka'] == 1.8e-5
    assert metadata['concentration'] == 0.1


def test_weak_base_ph():
    """Test weak base pH calculation using Kb."""
    ph, steps, metadata = calculate_weak_base_ph(0.1, 1.8e-5)
    # For weak base: [OH-] = sqrt(Kb * C0)
    expected_oh = math.sqrt(1.8e-5 * 0.1)
    expected_ph = 14 + math.log10(expected_oh)
    assert abs(ph - expected_ph) < 0.01
    assert len(steps) > 0
    assert metadata['kb'] == 1.8e-5


def test_weak_base_ph_with_ka_conjugate():
    """Test weak base pH calculation using Ka of conjugate acid."""
    ph, steps, metadata = calculate_weak_base_ph(0.1, ka_conjugate=5.6e-10)
    # Kb = Kw/Ka = 1e-14/5.6e-10 = 1.79e-5
    expected_kb = 1e-14 / 5.6e-10
    expected_oh = math.sqrt(expected_kb * 0.1)
    expected_ph = 14 + math.log10(expected_oh)
    assert abs(ph - expected_ph) < 0.01
    assert len(steps) > 0


def test_buffer_ph():
    """Test buffer pH calculation using Henderson-Hasselbalch."""
    ph, steps, metadata = calculate_buffer_ph(0.1, 0.1, 1.8e-5)
    # pH = pKa + log([A-]/[HA]) = pKa + log(1) = pKa
    expected_pka = -math.log10(1.8e-5)
    assert abs(ph - expected_pka) < 0.01
    assert len(steps) > 0
    assert metadata['ka'] == 1.8e-5


def test_buffer_ph_with_pka():
    """Test buffer pH calculation using pKa directly."""
    ph, steps, metadata = calculate_buffer_ph(0.1, 0.1, ka=1.8e-5, pka=4.74)
    # pH = pKa + log([A-]/[HA]) = 4.74 + log(1) = 4.74
    assert abs(ph - 4.74) < 0.01
    assert len(steps) > 0
    assert metadata['pka'] == 4.74


def test_buffer_mixing_ph():
    """Test buffer pH calculation from mixing solutions."""
    ph, steps, metadata = calculate_buffer_mixing_ph(0.1, 1.0, 0.1, 1.0, 1.8e-5)
    # Equal volumes and concentrations should give pH = pKa
    expected_pka = -math.log10(1.8e-5)
    assert abs(ph - expected_pka) < 0.01
    assert len(steps) > 0


def test_target_buffer_ratio():
    """Test target buffer ratio calculation."""
    ratio, steps, metadata = calculate_target_buffer_ratio(5.0, 4.74)
    # pH = pKa + log([A-]/[HA])
    # 5.0 = 4.74 + log(ratio)
    # log(ratio) = 0.26
    # ratio = 10^0.26 ≈ 1.82
    expected_ratio = 10**0.26
    assert abs(ratio - expected_ratio) < 0.01
    assert len(steps) > 0
    assert metadata['target_ph'] == 5.0
    assert metadata['pka'] == 4.74


def test_titration_strong_acid_strong_base():
    """Test strong acid-strong base titration."""
    ph, region, steps, metadata = calculate_titration_strong_acid_strong_base(0.1, 1.0, 0.1, 1.0)
    # Equal amounts should give pH = 7 (equivalence point)
    assert abs(ph - 7.0) < 0.01
    assert region == "at equivalence"
    assert len(steps) > 0


def test_titration_weak_acid_strong_base():
    """Test weak acid-strong base titration."""
    ph, region, steps, metadata = calculate_titration_weak_acid_strong_base(0.1, 1.0, 1.8e-5, 0.1, 1.0)
    # At equivalence point, pH should be > 7 due to weak acid
    assert ph > 7.0
    assert region == "at equivalence"
    assert len(steps) > 0


def test_acid_base_errors():
    """Test error handling for invalid inputs."""
    with pytest.raises(ValueError):
        calculate_strong_acid_ph(-0.1, 1.0)
    
    with pytest.raises(ValueError):
        calculate_weak_acid_ph(0.1, -1.8e-5)
    
    with pytest.raises(ValueError):
        calculate_buffer_ph(0.1, 0.1, ka=0, pka=None)


def test_edge_cases():
    """Test edge cases and boundary conditions."""
    # Very dilute strong acid
    ph, steps, metadata = calculate_strong_acid_ph(1e-7, 1.0)
    assert ph > 6.0  # Should be close to neutral
    
    # Very dilute strong base
    ph, steps, metadata = calculate_strong_base_ph(1e-7, 1.0)
    assert ph < 8.0  # Should be close to neutral
    
    # Buffer with very different concentrations
    ph, steps, metadata = calculate_buffer_ph(0.01, 0.1, 1.8e-5)
    expected_pka = -math.log10(1.8e-5)
    expected_ph = expected_pka + math.log10(0.01/0.1)
    assert abs(ph - expected_ph) < 0.01
