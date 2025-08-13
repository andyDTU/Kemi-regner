"""
Tests for the gas laws calculator.
"""

import pytest
from calculators.gases import (
    calculate_ideal_gas_law_with_steps,
    calculate_dalton_law_with_steps,
    calculate_gas_stoichiometry_with_steps,
    calculate_van_der_waals_with_steps
)

class TestIdealGasLaw:
    """Test ideal gas law calculations."""
    
    def test_calculate_volume_from_pressure_moles_temperature(self):
        """Test calculating volume from P, n, T."""
        result = calculate_ideal_gas_law_with_steps(
            pressure=1.000, moles=1.000, temperature=298.15,
            pressure_unit="atm", volume_unit="L", temperature_unit="K"
        )
        
        # Expected: V = nRT/P = 1.000 × 0.082057 × 298.15 / 1.000 = 24.465 L
        expected_volume = 24.465
        assert abs(result['result'] - expected_volume) < 0.02
        assert result['unit'] == "L"
        assert "Ideal Gas Law: PV = nRT" in result['steps']
        assert "V = nRT/P" in result['steps']
    
    def test_calculate_pressure_from_volume_moles_temperature(self):
        """Test calculating pressure from V, n, T."""
        result = calculate_ideal_gas_law_with_steps(
            volume=24.465, moles=1.000, temperature=298.15,
            pressure_unit="atm", volume_unit="L", temperature_unit="K"
        )
        
        expected_pressure = 1.000
        assert abs(result['result'] - expected_pressure) < 0.001
        assert result['unit'] == "atm"
        assert "P = nRT/V" in result['steps']
    
    def test_calculate_moles_from_pressure_volume_temperature(self):
        """Test calculating moles from P, V, T."""
        result = calculate_ideal_gas_law_with_steps(
            pressure=1.000, volume=24.465, temperature=298.15,
            pressure_unit="atm", volume_unit="L", temperature_unit="K"
        )
        
        expected_moles = 1.000
        assert abs(result['result'] - expected_moles) < 0.001
        assert result['unit'] == "mol"
        assert "n = PV/(RT)" in result['steps']
    
    def test_calculate_temperature_from_pressure_volume_moles(self):
        """Test calculating temperature from P, V, n."""
        result = calculate_ideal_gas_law_with_steps(
            pressure=1.000, volume=24.465, moles=1.000,
            pressure_unit="atm", volume_unit="L", temperature_unit="K"
        )
        
        expected_temperature = 298.15
        assert abs(result['result'] - expected_temperature) < 0.01
        assert result['unit'] == "K"
        assert "T = PV/(nR)" in result['steps']
    
    def test_celsius_temperature_conversion(self):
        """Test temperature conversion from Celsius to Kelvin."""
        result = calculate_ideal_gas_law_with_steps(
            pressure=1.000, volume=24.465, moles=1.000,
            pressure_unit="atm", volume_unit="L", temperature_unit="°C"
        )
        
        # 25°C = 298.15 K
        expected_temperature = 298.15
        assert abs(result['result'] - expected_temperature) < 0.01
        assert "25°C = 298.15 K" in result['steps']
    
    def test_different_pressure_units(self):
        """Test pressure unit conversions."""
        result = calculate_ideal_gas_law_with_steps(
            pressure=101.325, moles=1.000, temperature=298.15,
            pressure_unit="kPa", volume_unit="L", temperature_unit="K"
        )
        
        # 101.325 kPa = 1.000 atm, so V should be 24.465 L
        expected_volume = 24.465
        assert abs(result['result'] - expected_volume) < 0.02
        assert result['unit'] == "L"
    
    def test_different_volume_units(self):
        """Test volume unit conversions."""
        result = calculate_ideal_gas_law_with_steps(
            pressure=1.000, moles=1.000, temperature=298.15,
            pressure_unit="atm", volume_unit="mL", temperature_unit="K"
        )
        
        # 24.465 L = 24465 mL
        expected_volume = 24465
        assert abs(result['result'] - expected_volume) < 20
        assert result['unit'] == "mL"
    
    def test_invalid_inputs(self):
        """Test error handling for invalid inputs."""
        # Too few variables
        with pytest.raises(ValueError, match="Exactly three variables"):
            calculate_ideal_gas_law_with_steps(
                pressure=1.0, volume=1.0, moles=None, temperature=None
            )
        
        # Too many variables
        with pytest.raises(ValueError, match="Exactly three variables"):
            calculate_ideal_gas_law_with_steps(
                pressure=1.0, volume=1.0, moles=1.0, temperature=298.15
            )
        
        # Negative values
        with pytest.raises(ValueError, match="Volume must be positive"):
            calculate_ideal_gas_law_with_steps(
                pressure=1.0, volume=-1.0, moles=1.0, temperature=298.15
            )

class TestDaltonLaw:
    """Test Dalton's law calculations."""
    
    def test_partial_pressures_from_moles(self):
        """Test calculating partial pressures from moles."""
        species_data = [
            {"name": "O2", "moles": 0.5},
            {"name": "N2", "moles": 1.0}
        ]
        
        result = calculate_dalton_law_with_steps(
            species_data=species_data,
            total_pressure=1.200,
            pressure_unit="atm"
        )
        
        # O2: 0.5/1.5 = 0.3333... × 1.200 = 0.400 atm
        # N2: 1.0/1.5 = 0.6666... × 1.200 = 0.800 atm
        o2_pp = next(pp for pp in result['partial_pressures'] if pp['name'] == 'O2')
        n2_pp = next(pp for pp in result['partial_pressures'] if pp['name'] == 'N2')
        
        assert abs(o2_pp['partial_pressure'] - 0.400) < 0.001
        assert abs(n2_pp['partial_pressure'] - 0.800) < 0.001
        assert "Dalton's Law: P_total = ΣP_i" in result['steps']
    
    def test_partial_pressures_from_mole_fractions(self):
        """Test calculating partial pressures from mole fractions."""
        species_data = [
            {"name": "O2", "mole_fraction": 0.25},
            {"name": "N2", "mole_fraction": 0.75}
        ]
        
        result = calculate_dalton_law_with_steps(
            species_data=species_data,
            total_pressure=1.000,
            pressure_unit="atm"
        )
        
        o2_pp = next(pp for pp in result['partial_pressures'] if pp['name'] == 'O2')
        n2_pp = next(pp for pp in result['partial_pressures'] if pp['name'] == 'N2')
        
        assert abs(o2_pp['partial_pressure'] - 0.250) < 0.001
        assert abs(n2_pp['partial_pressure'] - 0.750) < 0.001
    
    def test_collected_over_water(self):
        """Test gas collected over water calculation."""
        species_data = [
            {"name": "O2", "moles": 0.5},
            {"name": "N2", "moles": 1.0}
        ]
        
        result = calculate_dalton_law_with_steps(
            species_data=species_data,
            total_pressure=1.200,
            pressure_unit="atm",
            collected_over_water=True,
            water_vapor_pressure=0.050
        )
        
        # Gas pressure should be 1.200 - 0.050 = 1.150 atm
        assert abs(result['gas_pressure'] - 1.150) < 0.001
        assert "Collected over water" in result['steps']
        assert "P_gas = P_total - P_water" in result['steps']
    
    def test_invalid_inputs(self):
        """Test error handling for invalid inputs."""
        # Empty species data
        with pytest.raises(ValueError, match="At least one species"):
            calculate_dalton_law_with_steps([], 1.0)
        
        # Mixed moles and mole fractions
        with pytest.raises(ValueError, match="Cannot mix moles and mole fractions"):
            calculate_dalton_law_with_steps([
                {"name": "O2", "moles": 0.5},
                {"name": "N2", "mole_fraction": 0.5}
            ], 1.0)
        
        # Mole fractions don't sum to 1
        with pytest.raises(ValueError, match="Mole fractions must sum to 1.0"):
            calculate_dalton_law_with_steps([
                {"name": "O2", "mole_fraction": 0.3},
                {"name": "N2", "mole_fraction": 0.3}
            ], 1.0)
        
        # Water vapor pressure exceeds total pressure
        with pytest.raises(ValueError, match="Water vapor pressure cannot exceed total pressure"):
            calculate_dalton_law_with_steps([
                {"name": "O2", "moles": 0.5}
            ], 1.0, collected_over_water=True, water_vapor_pressure=1.5)

class TestGasStoichiometry:
    """Test gas stoichiometry calculations."""
    
    def test_gas_stoichiometry_volume_based(self):
        """Test gas stoichiometry with volume inputs."""
        reactant_data = [
            {"formula": "H2", "volume": 5.00},
            {"formula": "O2", "volume": 2.00}
        ]
        
        result = calculate_gas_stoichiometry_with_steps(
            reaction="2 H2 + O2 -> 2 H2O(g)",
            reactant_data=reactant_data,
            temperature=298.15,
            pressure=1.000,
            temperature_unit="K",
            pressure_unit="atm",
            volume_unit="L"
        )
        
        # H2: 5.00 L → 5.00/(0.082057 × 298.15) = 0.204 mol
        # O2: 2.00 L → 2.00/(0.082057 × 298.15) = 0.0816 mol
        # H2 limiting: 0.204/2 = 0.102 mol
        # H2O produced: 0.102 × 2 = 0.204 mol
        # Volume: 0.204 × 0.082057 × 298.15 / 1.000 = 4.00 L
        expected_volume = 4.00
        assert abs(result['product_volume'] - expected_volume) < 0.02
        assert result['limiting_reactant']['formula'] == "H2"
        assert "Gas Stoichiometry: 2 H2 + O2 -> 2 H2O(g)" in result['steps']
    
    def test_gas_stoichiometry_mass_based(self):
        """Test gas stoichiometry with mass inputs."""
        reactant_data = [
            {"formula": "H2", "mass": 2.00},  # 2.00 g / 2.016 g/mol = 0.992 mol
            {"formula": "O2", "mass": 32.00}  # 32.00 g / 32.00 g/mol = 1.000 mol
        ]
        
        result = calculate_gas_stoichiometry_with_steps(
            reaction="2 H2 + O2 -> 2 H2O(g)",
            reactant_data=reactant_data,
            temperature=298.15,
            pressure=1.000,
            temperature_unit="K",
            pressure_unit="atm",
            volume_unit="L"
        )
        
        # H2 limiting: 0.992/2 = 0.496 mol
        # H2O produced: 0.496 × 2 = 0.992 mol
        # Volume: 0.992 × 0.082057 × 298.15 / 1.000 = 24.3 L
        expected_volume = 24.3
        assert abs(result['product_volume'] - expected_volume) < 0.2
        assert result['limiting_reactant']['formula'] == "H2"
    
    def test_invalid_reaction(self):
        """Test error handling for invalid reactions."""
        with pytest.raises(ValueError, match="Invalid reaction"):
            calculate_gas_stoichiometry_with_steps(
                reaction="invalid reaction",
                reactant_data=[{"formula": "H2", "volume": 1.0}],
                temperature=298.15,
                pressure=1.0
            )
    
    def test_no_gaseous_products(self):
        """Test error handling when no gaseous products exist."""
        with pytest.raises(ValueError, match="No gaseous products found"):
            calculate_gas_stoichiometry_with_steps(
                reaction="H2 + O2 -> H2O(l)",
                reactant_data=[{"formula": "H2", "volume": 1.0}],
                temperature=298.15,
                pressure=1.0
            )

class TestVanDerWaals:
    """Test van der Waals equation calculations."""
    
    def test_van_der_waals_co2(self):
        """Test van der Waals calculation for CO2."""
        result = calculate_van_der_waals_with_steps(
            gas="CO2",
            moles=1.0,
            volume=1.000,
            temperature=300.0,
            volume_unit="L",
            temperature_unit="K",
            pressure_unit="atm"
        )
        
        # Expected P_vdW ≈ 22.12 atm for CO2 with a=3.592, b=0.04267
        expected_pressure = 22.12
        assert abs(result['pressure_vdw'] - expected_pressure) < 0.1
        assert result['unit'] == "atm"
        assert "van der Waals Equation: P = nRT/(V - nb) - a(n/V)²" in result['steps']
        assert "a = 3.592 L²·atm/mol²" in result['steps']
        assert "b = 0.04267 L/mol" in result['steps']
    
    def test_van_der_waals_n2(self):
        """Test van der Waals calculation for N2."""
        result = calculate_van_der_waals_with_steps(
            gas="N2",
            moles=1.0,
            volume=1.000,
            temperature=298.15,
            volume_unit="L",
            temperature_unit="K",
            pressure_unit="atm"
        )
        
        # N2 should have lower pressure than CO2 due to smaller a, b values
        assert result['pressure_vdw'] < 25.0
        assert result['compressibility_factor'] > 0
    
    def test_van_der_waals_volume_conversion(self):
        """Test van der Waals with different volume units."""
        result = calculate_van_der_waals_with_steps(
            gas="O2",
            moles=1.0,
            volume=1000.0,  # 1000 mL = 1.000 L
            temperature=298.15,
            volume_unit="mL",
            temperature_unit="K",
            pressure_unit="atm"
        )
        
        # Should get same result as 1.000 L
        result_l = calculate_van_der_waals_with_steps(
            gas="O2",
            moles=1.0,
            volume=1.000,
            temperature=298.15,
            volume_unit="L",
            temperature_unit="K",
            pressure_unit="atm"
        )
        
        assert abs(result['pressure_vdw'] - result_l['pressure_vdw']) < 0.01
    
    def test_van_der_waals_celsius_temperature(self):
        """Test van der Waals with Celsius temperature."""
        result = calculate_van_der_waals_with_steps(
            gas="CO2",
            moles=1.0,
            volume=1.000,
            temperature=27.0,  # 27°C = 300.15 K
            volume_unit="L",
            temperature_unit="°C",
            pressure_unit="atm"
        )
        
        # Should be close to 300 K result
        result_k = calculate_van_der_waals_with_steps(
            gas="CO2",
            moles=1.0,
            volume=1.000,
            temperature=300.0,
            volume_unit="L",
            temperature_unit="K",
            pressure_unit="atm"
        )
        
        assert abs(result['pressure_vdw'] - result_k['pressure_vdw']) < 0.1
    
    def test_van_der_waals_different_pressure_units(self):
        """Test van der Waals with different pressure units."""
        result_atm = calculate_van_der_waals_with_steps(
            gas="CO2",
            moles=1.0,
            volume=1.000,
            temperature=300.0,
            pressure_unit="atm"
        )
        
        result_kpa = calculate_van_der_waals_with_steps(
            gas="CO2",
            moles=1.0,
            volume=1.000,
            temperature=300.0,
            pressure_unit="kPa"
        )
        
        # 1 atm = 101.325 kPa
        expected_kpa = result_atm['pressure_vdw'] * 101.325
        assert abs(result_kpa['pressure_vdw'] - expected_kpa) < 1.0
    
    def test_invalid_gas(self):
        """Test error handling for invalid gas names."""
        with pytest.raises(ValueError, match="Gas 'InvalidGas' not found"):
            calculate_van_der_waals_with_steps(
                gas="InvalidGas",
                moles=1.0,
                volume=1.0,
                temperature=298.15
            )
    
    def test_invalid_inputs(self):
        """Test error handling for invalid inputs."""
        with pytest.raises(ValueError, match="Moles must be positive"):
            calculate_van_der_waals_with_steps(
                gas="CO2",
                moles=-1.0,
                volume=1.0,
                temperature=298.15
            )
        
        with pytest.raises(ValueError, match="Volume must be positive"):
            calculate_van_der_waals_with_steps(
                gas="CO2",
                moles=1.0,
                volume=-1.0,
                temperature=298.15
            )
        
        with pytest.raises(ValueError, match="Temperature must be positive"):
            calculate_van_der_waals_with_steps(
                gas="CO2",
                moles=1.0,
                volume=1.0,
                temperature=-100.0
            )
