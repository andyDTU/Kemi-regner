"""
Unit tests for the redox balance calculator.
"""

import unittest
import sys
import os

# Add the project root to the path to import the calculator
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from calculators.redox_balance import (
    balance_redox_with_steps,
    normalize_equation,
    is_balanced,
    analyze_oxidation_numbers,
    _oxidation_states_for_species,
)


class TestRedoxBalance(unittest.TestCase):
    """Test cases for redox balance functionality."""

    def test_normalize_equation(self):
        """Test equation normalization."""
        # Test arrow to equals conversion
        self.assertEqual(normalize_equation("A + B -> C"), "A + B = C")
        self.assertEqual(normalize_equation("A + B --> C"), "A + B = C")
        self.assertEqual(normalize_equation("A + B = C"), "A + B = C")
        self.assertEqual(normalize_equation("A + B → C"), "A + B = C")
        
        # Test whitespace cleaning
        self.assertEqual(normalize_equation("  A  +  B  ->  C  "), "A + B = C")

    def test_is_balanced_checks_atoms_and_charge(self):
        """Test strict balancing validator."""
        self.assertTrue(is_balanced("5 Fe2+ + MnO4- + 8 H+ -> 5 Fe3+ + Mn2+ + 4 H2O"))
        self.assertTrue(is_balanced("Cl2 + 2 OH- -> ClO- + Cl- + H2O"))
        self.assertFalse(is_balanced("Fe2+ + MnO4- + H+ -> Fe3+ + Mn2+ + H2O"))
        self.assertFalse(is_balanced("H2 + O2 -> H2O"))



    def test_neutral_medium_balancing(self):
        """Test balancing in neutral medium."""
        equation = "C6H12O6 + O2 -> CO2 + H2O"
        result, steps, meta = balance_redox_with_steps(equation, "neutral")
        
        # Check that we get the expected balanced equation
        expected = "C6H12O6 + 6 O2 -> 6 CO2 + 6 H2O"
        self.assertEqual(result, expected)
        
        # Check metadata
        self.assertEqual(meta['medium_used'], 'neutral')
        self.assertEqual(meta['auto_added'], [])
        self.assertEqual(meta['coefficients'], [1, 6, 6, 6])
        self.assertEqual(meta['species_order'], ['C6H12O6', 'O2', 'CO2', 'H2O'])
        
        # Check steps
        self.assertTrue(len(steps) > 0)
        self.assertIn("Normalize the equation", steps[0])

    def test_acidic_medium_balancing(self):
        """Test balancing in acidic medium."""
        equation = "Fe2+ + MnO4- + H+ -> Fe3+ + Mn2+ + H2O"
        result, steps, meta = balance_redox_with_steps(equation, "acid")
        
        # Check that we get the expected balanced equation
        expected = "5 Fe2+ + MnO4- + 8 H+ -> 5 Fe3+ + Mn2+ + 4 H2O"
        self.assertEqual(result, expected)
        
        # Check metadata
        self.assertEqual(meta['medium_used'], 'acid')
        self.assertEqual(meta['coefficients'], [5, 1, 8, 5, 1, 4])
        self.assertEqual(meta['species_order'], ['Fe2+', 'MnO4-', 'H+', 'Fe3+', 'Mn2+', 'H2O'])
        
        # Check steps
        self.assertTrue(len(steps) > 0)
        self.assertTrue(any("balanced" in step.lower() for step in steps))

    def test_acidic_medium_example_from_readme(self):
        """Test the specific example from the README."""
        equation = "NH3 + MnO4- + H+ = NO2 + Mn2+ + H2O"
        result, steps, meta = balance_redox_with_steps(equation, "acid")
        
        # Check that we get the expected balanced equation
        expected = "5 NH3 + 7 MnO4- + 21 H+ -> 5 NO2 + 7 Mn2+ + 18 H2O"
        self.assertEqual(result, expected)
        
        # Check metadata
        self.assertEqual(meta['medium_used'], 'acid')
        self.assertEqual(meta['coefficients'], [5, 7, 21, 5, 7, 18])
        self.assertEqual(meta['species_order'], ['NH3', 'MnO4-', 'H+', 'NO2', 'Mn2+', 'H2O'])

    def test_basic_medium_balancing(self):
        """Test balancing in basic medium."""
        equation = "Cl2 + OH- -> ClO- + Cl- + H2O"
        result, steps, meta = balance_redox_with_steps(equation, "base")
        
        # Check that we get the expected balanced equation
        expected = "Cl2 + 2 OH- -> ClO- + Cl- + H2O"
        self.assertEqual(result, expected)
        
        # Check metadata
        self.assertEqual(meta['medium_used'], 'base')
        self.assertEqual(meta['coefficients'], [1, 2, 1, 1, 1])
        self.assertEqual(meta['species_order'], ['Cl2', 'OH-', 'ClO-', 'Cl-', 'H2O'])

    def test_already_balanced_input(self):
        """Test that already balanced inputs remain unchanged."""
        equation = "2 H2 + O2 -> 2 H2O"
        result, steps, meta = balance_redox_with_steps(equation, "neutral")
        
        # Should still produce a balanced result
        self.assertEqual(result, "2 H2 + O2 -> 2 H2O")
        self.assertTrue(is_balanced(result))
        self.assertTrue(len(meta['coefficients']) > 0)

    def test_error_handling_invalid_equation(self):
        """Test error handling for invalid equations."""
        with self.assertRaises(ValueError):
            balance_redox_with_steps("", "neutral")
        
        with self.assertRaises(ValueError):
            balance_redox_with_steps("A + B", "neutral")  # No equals sign

    def test_error_handling_unsolvable_equation(self):
        """Test error handling for unsolvable equations."""
        # This should be a very complex or impossible equation
        equation = "A + B + C + D + E + F + G + H = I + J + K + L + M + N + O + P"
        with self.assertRaises(ValueError):
            balance_redox_with_steps(equation, "neutral")

    def test_medium_specific_helper_species(self):
        """Helper species can be inferred for supported acid/base cases."""
        equation = "Fe2+ + MnO4- -> Fe3+ + Mn2+"

        result, _steps, meta = balance_redox_with_steps(equation, "acid")
        self.assertEqual(result, "5 Fe2+ + MnO4- + 8 H+ -> 5 Fe3+ + Mn2+ + 4 H2O")
        self.assertEqual(meta['medium_used'], 'acid')

        result_base, _steps_base, meta_base = balance_redox_with_steps(equation, "base")
        self.assertEqual(result_base, "5 Fe2+ + MnO4- + 4 H2O -> 5 Fe3+ + Mn2+ + 8 OH-")
        self.assertEqual(meta_base['medium_used'], 'base')
        self.assertIn('OH-', meta_base['auto_added'])
        self.assertIn('H2O', meta_base['auto_added'])

        with self.assertRaises(ValueError):
            balance_redox_with_steps(equation, "neutral")

    def test_medium_alias_basic_is_supported(self):
        """Test that 'basic' medium alias is normalized to 'base'."""
        equation = "Cl2 + OH- -> ClO- + Cl- + H2O"
        result, _steps, meta = balance_redox_with_steps(equation, "basic")
        self.assertEqual(result, "Cl2 + 2 OH- -> ClO- + Cl- + H2O")
        self.assertEqual(meta['medium_used'], 'base')

    def test_charge_notation_variants_are_supported(self):
        """Fe2+, Fe^2+ and Fe_2+ style charge notation should be equivalent."""
        expected = "5 Fe2+ + MnO4- + 8 H+ -> 5 Fe3+ + Mn2+ + 4 H2O"

        eq_plain = "Fe2+ + MnO4- + H+ -> Fe3+ + Mn2+ + H2O"
        eq_caret = "Fe^2+ + MnO4^- + H^+ -> Fe^3+ + Mn^2+ + H2O"
        eq_underscore = "Fe_2+ + MnO4_- + H_+ -> Fe_3+ + Mn_2+ + H2O"

        r1, _s1, _m1 = balance_redox_with_steps(eq_plain, "acid")
        r2, _s2, _m2 = balance_redox_with_steps(eq_caret, "acid")
        r3, _s3, _m3 = balance_redox_with_steps(eq_underscore, "acid")

        self.assertEqual(r1, expected)
        self.assertEqual(r2, expected)
        self.assertEqual(r3, expected)

    def test_oxidation_number_analysis_identifies_changes(self):
        equation = "5 Fe2+ + MnO4- + 8 H+ -> 5 Fe3+ + Mn2+ + 4 H2O"
        analysis = analyze_oxidation_numbers(equation)

        self.assertIn("Fe", analysis["oxidized_elements"])
        self.assertIn("Mn", analysis["reduced_elements"])

        changes = {item["element"]: item for item in analysis["element_changes"]}
        self.assertEqual(changes["Fe"]["change"], "oxidized")
        self.assertEqual(changes["Mn"]["change"], "reduced")

    def test_oxidation_number_values_for_key_species(self):
        equation = "5 Fe2+ + MnO4- + 8 H+ -> 5 Fe3+ + Mn2+ + 4 H2O"
        analysis = analyze_oxidation_numbers(equation)

        species_rows = {row["species"]: row for row in analysis["species_analysis"]}
        self.assertEqual(species_rows["Fe2+"]["oxidation_states"]["Fe"], 2)
        self.assertEqual(species_rows["Fe3+"]["oxidation_states"]["Fe"], 3)
        self.assertEqual(species_rows["MnO4-"]["oxidation_states"]["Mn"], 7)
        self.assertEqual(species_rows["Mn2+"]["oxidation_states"]["Mn"], 2)

    def test_basic_clo_i_to_cl_io3_balances(self):
        equation = "ClO^- + I^- -> Cl^- + IO3^-"
        result, _steps, meta = balance_redox_with_steps(equation, "base")

        self.assertEqual(result, "3 ClO- + I- -> 3 Cl- + IO3-")
        self.assertTrue(is_balanced(result))
        self.assertEqual(meta["coefficients"], [3, 1, 3, 1])

    def test_advanced_acidic_dichromate_sulfite_balances(self):
        equation = "(Cr2O7)^2- + SO3^2- -> Cr3+ + SO4^2-"
        result, _steps, meta = balance_redox_with_steps(equation, "acid")

        self.assertEqual(result, "(Cr2O7)2- + 3 SO32- + 8 H+ -> 2 Cr3+ + 3 SO42- + 4 H2O")
        self.assertTrue(is_balanced(result))
        self.assertEqual(meta["medium_used"], "acid")
        self.assertIn("H+", meta["species_order"])
        self.assertIn("H2O", meta["species_order"])

    def test_user_benchmark_six_variations(self):
        cases = [
            ("Fe2+ + Ag+ -> Fe3+ + Ag", "neutral", "Fe2+ + Ag+ -> Fe3+ + Ag"),
            ("MnO4- + Fe2+ -> Mn2+ + Fe3+", "acid", "MnO4- + 5 Fe2+ + 8 H+ -> Mn2+ + 5 Fe3+ + 4 H2O"),
            ("Cr2O7^2- + SO3^2- -> Cr3+ + SO4^2-", "acid", "Cr2O72- + 3 SO32- + 8 H+ -> 2 Cr3+ + 3 SO42- + 4 H2O"),
            ("ClO- + I- -> Cl- + IO3-", "base", "3 ClO- + I- -> 3 Cl- + IO3-"),
            ("MnO4- + H2O2 -> MnO2 + O2", "base", "2 MnO4- + 3 H2O2 -> 2 MnO2 + 3 O2 + 2 OH- + 2 H2O"),
            ("Cu + HNO3 -> Cu(NO3)2 + NO2 + H2O", "neutral", "Cu + 4 HNO3 -> Cu(NO3)2 + 2 NO2 + 2 H2O"),
        ]

        for equation, medium, expected in cases:
            result, _steps, _meta = balance_redox_with_steps(equation, medium)
            self.assertEqual(result, expected)
            self.assertTrue(is_balanced(result))

    def test_oxidation_rules_test1_peroxide(self):
        h2o2 = _oxidation_states_for_species("H2O2")
        h2o = _oxidation_states_for_species("H2O")
        o2 = _oxidation_states_for_species("O2")

        self.assertEqual(h2o2["H"], 1)
        self.assertEqual(h2o2["O"], -1)
        self.assertEqual(h2o["H"], 1)
        self.assertEqual(h2o["O"], -2)
        self.assertEqual(o2["O"], 0)

    def test_oxidation_rules_test2_superoxide(self):
        ko2 = _oxidation_states_for_species("KO2")
        self.assertEqual(ko2["K"], 1)
        self.assertEqual(ko2["O"], -0.5)

    def test_oxidation_rules_test3_of2(self):
        of2 = _oxidation_states_for_species("OF2")
        self.assertEqual(of2["F"], -1)
        self.assertEqual(of2["O"], 2)

    def test_oxidation_rules_test4_metal_hydride(self):
        nah = _oxidation_states_for_species("NaH")
        self.assertEqual(nah["Na"], 1)
        self.assertEqual(nah["H"], -1)

    def test_oxidation_rules_test5_complex_ion_reaction(self):
        analysis = analyze_oxidation_numbers("MnO4- + C2O4^2- + H+ -> Mn2+ + CO2 + H2O")
        by_species = {row["species"]: row["oxidation_states"] for row in analysis["species_analysis"]}

        self.assertEqual(by_species["MnO4-"]["Mn"], 7)
        self.assertEqual(by_species["MnO4-"]["O"], -2)
        self.assertEqual(by_species["C2O42-"]["C"], 3)
        self.assertEqual(by_species["C2O42-"]["O"], -2)
        self.assertEqual(by_species["Mn2+"]["Mn"], 2)
        self.assertEqual(by_species["CO2"]["C"], 4)
        self.assertEqual(by_species["CO2"]["O"], -2)

    def test_phase_annotations_are_supported(self):
        result_1, _steps_1, _meta_1 = balance_redox_with_steps(
            "Fe2+ + Ag+ -> Fe3+ + Ag(s)",
            "neutral",
        )
        self.assertEqual(result_1, "Fe2+ + Ag+ -> Fe3+ + Ag(s)")
        self.assertTrue(is_balanced(result_1))

        result_2, _steps_2, _meta_2 = balance_redox_with_steps(
            "MnO4- + H2O2 -> MnO2(s) + O2",
            "base",
        )
        self.assertEqual(result_2, "2 MnO4- + 3 H2O2 -> 2 MnO2(s) + 3 O2 + 2 OH- + 2 H2O")
        self.assertTrue(is_balanced(result_2))

    def test_acidic_dichromate_hydrogen_peroxide_balances(self):
        equation = "Cr2O7^2- + H2O2 -> Cr^3+ + O2"
        result, _steps, meta = balance_redox_with_steps(equation, "acid")

        self.assertEqual(result, "Cr2O72- + 3 H2O2 + 8 H+ -> 2 Cr3+ + 7 H2O + 3 O2")
        self.assertTrue(is_balanced(result))
        self.assertEqual(meta["medium_used"], "acid")

    def test_species_do_not_disappear_from_input(self):
        with self.assertRaises(ValueError):
            balance_redox_with_steps("Cr2O7^2- + H2O2 -> Cr^3+ + O2", "neutral")

    def test_acidic_permanganate_hydrogen_peroxide_balances(self):
        equation = "MnO4- + H2O2 -> Mn2+ + O2"
        result, _steps, meta = balance_redox_with_steps(equation, "acid")

        self.assertEqual(result, "2 MnO4- + 5 H2O2 + 6 H+ -> 2 Mn2+ + 8 H2O + 5 O2")
        self.assertTrue(is_balanced(result))
        self.assertEqual(meta["medium_used"], "acid")

    def test_ko2_disproportionation_balances(self):
        equation = "KO2 + H2O -> KOH + H2O2 + O2"
        result, _steps, meta = balance_redox_with_steps(equation, "neutral")

        self.assertEqual(result, "2 KO2 + 2 H2O -> 2 KOH + H2O2 + O2")
        self.assertTrue(is_balanced(result))
        self.assertEqual(meta["medium_used"], "neutral")

    def test_tricky_15_case_benchmark(self):
        redox_cases = [
            ("Cr2O7^2- + H2O2 -> Cr3+ + O2", "acid", "Cr2O72- + 3 H2O2 + 8 H+ -> 2 Cr3+ + 7 H2O + 3 O2"),
            ("MnO4- + H2O2 -> Mn2+ + O2", "acid", "2 MnO4- + 5 H2O2 + 6 H+ -> 2 Mn2+ + 8 H2O + 5 O2"),
            ("KO2 + H2O -> KOH + H2O2 + O2", "neutral", "2 KO2 + 2 H2O -> 2 KOH + H2O2 + O2"),
            ("NaH + H2O -> NaOH + H2", "neutral", "NaH + H2O -> NaOH + H2"),
            ("Cl2 + OH- -> Cl- + ClO-", "base", "Cl2 + 2 OH- -> Cl- + ClO- + H2O"),
            ("H2O2 -> H2O + O2", "neutral", "2 H2O2 -> 2 H2O + O2"),
            ("Cu + HNO3 -> Cu(NO3)2 + NO2 + H2O", "neutral", "Cu + 4 HNO3 -> Cu(NO3)2 + 2 NO2 + 2 H2O"),
            ("Cu + HNO3 -> Cu(NO3)2 + NO + H2O", "neutral", "3 Cu + 8 HNO3 -> 3 Cu(NO3)2 + 2 NO + 4 H2O"),
            ("ClO- + I- -> Cl- + IO3-", "base", "3 ClO- + I- -> 3 Cl- + IO3-"),
            ("Cr2O7^2- + SO3^2- -> Cr3+ + SO4^2-", "acid", "Cr2O72- + 3 SO32- + 8 H+ -> 2 Cr3+ + 3 SO42- + 4 H2O"),
            ("MnO4- + C2O4^2- -> Mn2+ + CO2", "acid", "2 MnO4- + 5 C2O42- + 16 H+ -> 2 Mn2+ + 10 CO2 + 8 H2O"),
            ("O3 -> O2", "neutral", "2 O3 -> 3 O2"),
            ("I2 + S2O3^2- -> I- + S4O6^2-", "neutral", "I2 + 2 S2O32- -> 2 I- + S4O62-"),
            # Chemically charge-balanced acidic form (facit text without H+/H2O is charge-inconsistent)
            ("ClO3- -> ClO2 + ClO4-", "acid", "3 ClO3- + 2 H+ -> 2 ClO2 + ClO4- + H2O"),
        ]

        for equation, medium, expected in redox_cases:
            result, _steps, _meta = balance_redox_with_steps(equation, medium)
            self.assertEqual(result, expected)
            self.assertTrue(is_balanced(result))

        of2 = _oxidation_states_for_species("OF2")
        self.assertEqual(of2["O"], 2)
        self.assertEqual(of2["F"], -1)


if __name__ == '__main__':
    unittest.main()
