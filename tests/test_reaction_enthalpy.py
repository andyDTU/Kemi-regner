import pytest
import json
from pathlib import Path

from core.dhf_database import load_dhf_database, normalizeSpeciesKey, getDhf
from core.reaction_enthalpy import (
    parseReaction,
    computeRxnEnthalpy,
    balanceReaction,
    isReactionBalanced,
)


def test_parse_reaction_with_phases_and_coeffs():
    ast = parseReaction("N2(g) + 3 H2(g) -> 2 NH3(g)")
    assert len(ast["reactants"]) == 2
    assert len(ast["products"]) == 1
    assert float(ast["reactants"][1]["coefficient"]) == 3.0
    assert ast["products"][0]["species_key"] == "NH3(g)"


def test_parse_reaction_with_equals_arrow():
    ast = parseReaction("H2(g) + O2(g) = H2O(g)")
    assert ast["reactants"][0]["species_key"] == "H2(g)"
    assert ast["products"][0]["species_key"] == "H2O(g)"


def test_parse_reaction_default_phase_warning():
    ast = parseReaction("CH4 + 2 O2 -> CO2 + 2 H2O")
    assert len(ast["warnings"]) >= 1
    assert "defaulted to (g)" in " ".join(ast["warnings"])


def test_parse_reaction_parentheses_formulas():
    ast = parseReaction("Ca(OH)2(s) + H2SO4(aq) -> CaSO4(s) + 2 H2O(l)")
    assert ast["reactants"][0]["formula"] == "Ca(OH)2"
    assert ast["reactants"][1]["formula"] == "H2SO4"


def test_parse_reaction_fractional_coefficients():
    ast = parseReaction("H2(g) + 1/2 O2(g) -> H2O(g)")
    assert float(ast["reactants"][1]["coefficient"]) == 0.5


def test_compute_rxn_enthalpy_ammonia_acceptance_case():
    db = load_dhf_database()
    ast = parseReaction("N2(g) + 3 H2(g) -> 2 NH3(g)")
    result = computeRxnEnthalpy(ast, db, overrides={})
    assert result["missing_species"] == []
    assert result["delta_h_rxn_kj_per_mol"] is not None
    assert abs(result["delta_h_rxn_kj_per_mol"] - (-92.22)) < 0.02


def test_compute_rxn_enthalpy_combustion_ch4():
    db = load_dhf_database()
    ast = parseReaction("CH4(g) + 2 O2(g) -> CO2(g) + 2 H2O(l)")
    result = computeRxnEnthalpy(ast, db, overrides={})
    assert result["delta_h_rxn_kj_per_mol"] is not None
    assert abs(result["delta_h_rxn_kj_per_mol"] - (-890.36)) < 0.1


def test_compute_rxn_enthalpy_missing_species_and_override():
    db = load_dhf_database()
    ast = parseReaction("KrF2(g) -> Kr(g) + F2(g)")

    result_missing = computeRxnEnthalpy(ast, db, overrides={})
    assert "KrF2(g)" in result_missing["missing_species"]
    assert result_missing["delta_h_rxn_kj_per_mol"] is None

    overrides = {"KrF2(g)": 15.0, "Kr(g)": 0.0}
    result_with_override = computeRxnEnthalpy(ast, db, overrides=overrides)
    assert result_with_override["missing_species"] == []
    assert result_with_override["delta_h_rxn_kj_per_mol"] is not None


def test_balance_reaction_simple_water():
    ast = parseReaction("H2(g) + O2(g) -> H2O(g)")
    balanced = balanceReaction(ast)
    out = balanced["ast"]
    coeffs = [int(item["coefficient"]) for item in out["reactants"] + out["products"]]
    assert coeffs == [2, 1, 2]


def test_balance_reaction_parentheses_case():
    ast = parseReaction("Fe2(SO4)3(aq) + KOH(aq) -> Fe(OH)3(s) + K2SO4(aq)")
    balanced = balanceReaction(ast)
    out = balanced["ast"]
    coeffs = [int(item["coefficient"]) for item in out["reactants"] + out["products"]]
    assert coeffs == [1, 6, 2, 3]


def test_unbalanced_warning_detection():
    ast = parseReaction("N2(g) + H2(g) -> NH3(g)")
    balanced, imbalance = isReactionBalanced(ast)
    assert not balanced
    assert "H" in imbalance


def test_balance_then_compute_fraction_case():
    db = load_dhf_database()
    ast = parseReaction("H2(g) + 1/2 O2(g) -> H2O(g)")
    balanced, imbalance = isReactionBalanced(ast)
    assert balanced
    assert imbalance == {}

    result = computeRxnEnthalpy(ast, db, overrides={})
    assert result["delta_h_rxn_kj_per_mol"] is not None
    assert abs(result["delta_h_rxn_kj_per_mol"] - (-241.826)) < 0.05


def test_exampack_db_loaded_and_known_values_present():
    db = load_dhf_database()
    assert "CO2(g)" in db
    assert "CaCO3(s)" in db
    assert abs(float(db["CO2(g)"]["dhf_kj_per_mol"]) - (-393.51)) < 1e-9


def test_openstax_generated_database_has_large_coverage():
    path = Path(__file__).resolve().parent.parent / "data" / "dhf.openstax.tableG1.json"
    assert path.exists(), "Missing generated OpenStax DB; run build:dhf"

    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    assert len(data) > 300

    assert "CO2(g)" in data
    assert "BaO(s)" in data


def test_normalize_species_key_examples():
    assert normalizeSpeciesKey("H2O ( L )") == "H2O(l)"
    assert normalizeSpeciesKey("SO4 2-(aq)") == "SO4^2-(aq)"


def test_caco3_decomposition_enthalpy_target():
    db = load_dhf_database()
    ast = parseReaction("CaCO3(s) -> CaO(s) + CO2(g)")
    result = computeRxnEnthalpy(ast, db, overrides={})
    assert result["missing_species"] == []
    assert result["delta_h_rxn_kj_per_mol"] is not None
    assert abs(result["delta_h_rxn_kj_per_mol"] - 178.29) < 0.05


def test_getdhf_lookups_for_new_exam_entries():
    db = load_dhf_database()

    keys = [
        "CH3OH(g)",
        "CCl4(l)",
        "HNO3(aq)",
        "S2O3^2-(aq)",
        "P4O10(s)",
    ]

    for key in keys:
        lookup = getDhf(key, overrides={}, db=db)
        assert lookup["found"], f"Expected {key} to be found"
        assert lookup["value"] is not None


def test_getdhf_required_openstax_lookups():
    db = load_dhf_database()

    for key in ["CO2(g)", "BaO(s)"]:
        lookup = getDhf(key, overrides={}, db=db)
        assert lookup["found"], f"Expected {key} to be found"
        assert lookup["value"] is not None


def test_co2_value_remains_expected_after_large_merge():
    db = load_dhf_database()
    lookup = getDhf("CO2(g)", overrides={}, db=db)
    assert lookup["found"]
    assert abs(lookup["value"] - (-393.51)) < 1e-9


def test_baco3_decomposition_enthalpy_target():
    db = load_dhf_database()
    ast = parseReaction("BaCO3(s) -> BaO(s) + CO2(g)")
    result = computeRxnEnthalpy(ast, db, overrides={})
    assert result["missing_species"] == []
    assert result["delta_h_rxn_kj_per_mol"] is not None
    assert abs(result["delta_h_rxn_kj_per_mol"] - 277.29) < 0.2
