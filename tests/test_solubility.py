"""Tests for solubility parser and rule engine."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.solubility import parse_ionic_salt, evaluate_salt_solubility
from calculators.solubility import analyze_salt_solubility_with_steps


@pytest.mark.parametrize(
    "formula, cation, anion",
    [
        ("NaCl", "Na+", "Cl-"),
        ("KNO3", "K+", "NO3-"),
        ("AgCl", "Ag+", "Cl-"),
        ("BaSO4", "Ba2+", "SO4^2-"),
        ("(NH4)2SO4", "NH4+", "SO4^2-"),
        ("Al2(SO4)3", "Al3+", "SO4^2-"),
        ("Pb(NO3)2", "Pb2+", "NO3-"),
        ("Ca3(PO4)2", "Ca2+", "PO4^3-"),
        ("Mg(OH)2", "Mg2+", "OH-"),
    ],
)
def test_parse_supported_salts(formula, cation, anion):
    parsed = parse_ionic_salt(formula)
    assert parsed["cation"]["symbol"] == cation
    assert parsed["anion"]["symbol"] == anion


@pytest.mark.parametrize("bad_formula", ["", "   ", "abc123", "CH4"]) 
def test_parse_invalid_or_non_salt_input(bad_formula):
    with pytest.raises(ValueError):
        parse_ionic_salt(bad_formula)


@pytest.mark.parametrize(
    "formula, expected_status",
    [
        ("NaCl", "soluble"),
        ("KNO3", "soluble"),
        ("NH4Cl", "soluble"),
        ("AgCl", "insoluble"),
        ("PbBr2", "insoluble"),
        ("BaSO4", "insoluble"),
        ("SrSO4", "insoluble"),
        ("CaSO4", "slightly_soluble"),
        ("Na2CO3", "soluble"),
        ("CaCO3", "insoluble"),
        ("(NH4)3PO4", "soluble"),
        ("Mg(OH)2", "insoluble"),
        ("Ba(OH)2", "slightly_soluble"),
    ],
)
def test_solubility_classification_cases(formula, expected_status):
    result = evaluate_salt_solubility(formula)
    assert result["status"] == expected_status


def test_unknown_or_unsupported_formula_does_not_crash():
    result, steps, metadata = analyze_salt_solubility_with_steps("XeF2")
    assert result["status"] == "unknown"
    assert result["classification_en"].startswith("unknown")


def test_result_contains_requested_fields():
    result = evaluate_salt_solubility("AgCl")
    assert result["cation"]["symbol"] == "Ag+"
    assert result["anion"]["symbol"] == "Cl-"
    assert "classification_da" in result
    assert "classification_en" in result
    assert "rule_id" in result
    assert "reason" in result
