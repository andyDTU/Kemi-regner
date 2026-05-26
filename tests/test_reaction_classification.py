"""Regression tests for reaction parsing and classification."""

import pytest

from calculators.reaction_classification import (
    ReactionParseError,
    classify_reaction_text,
    parse_reaction_text,
)


def _assert_classification(
    reaction: str,
    expected_primary: str,
    must_include_secondary: list[str] | None = None,
    expected_secondary_exact: list[str] | None = None,
) -> None:
    result = classify_reaction_text(reaction)["classification"]
    assert result["primaryType"] == expected_primary
    if must_include_secondary:
        for sec in must_include_secondary:
            assert sec in result["secondaryTypes"]
    if expected_secondary_exact is not None:
        assert result["secondaryTypes"] == expected_secondary_exact


@pytest.mark.parametrize(
    "reaction",
    [
        "HCl+NaOH->NaCl+H2O",
        "HCl + NaOH -> NaCl + H2O",
        "AgNO3(aq)+NaCl(aq)->AgCl(s)+NaNO3(aq)",
        "2H2 + O2 -> 2H2O",
        "CaCO3 -> CaO + CO2",
        "Pb(NO3)2 (aq) + 2KI (aq) -> PbI2 (s) + 2KNO3 (aq)",
    ],
)
def test_parser_required_success_cases(reaction: str) -> None:
    parsed = parse_reaction_text(reaction)
    assert len(parsed.reactants) >= 1
    assert len(parsed.products) >= 1


def test_parser_keeps_coefficients_and_states() -> None:
    parsed = parse_reaction_text("Pb(NO3)2 (aq) + 2KI (aq) -> PbI2 (s) + 2KNO3 (aq)")
    assert parsed.reactants[0].coefficient == 1
    assert parsed.reactants[1].coefficient == 2
    assert parsed.reactants[0].state == "aq"
    assert parsed.products[0].state == "s"
    assert parsed.products[1].coefficient == 2


@pytest.mark.parametrize(
    "bad_reaction",
    [
        "",
        "NaCl +",
        "-> H2O",
        "H2 + O2",
        "HCl + NaOH -> -> NaCl + H2O",
        "????",
    ],
)
def test_parser_required_negative_cases(bad_reaction: str) -> None:
    with pytest.raises(ReactionParseError):
        parse_reaction_text(bad_reaction)


def test_arrow_variants_supported() -> None:
    assert parse_reaction_text("H2 + Cl2 = 2HCl").arrow == "="
    assert parse_reaction_text("N2 + 3H2 <-> 2NH3").arrow == "<->"
    assert parse_reaction_text("N2 + 3H2 ⇌ 2NH3").arrow == "⇌"
    assert parse_reaction_text("N2 + 3H2 → 2NH3").arrow == "→"


def test_classification_case_01() -> None:
    _assert_classification(
        "CaBr2 (aq) + K2SO4 (aq) -> CaSO4 (s) + 2KBr (aq)",
        "Fældningsreaktion",
        must_include_secondary=["Dobbeltforskydning"],
    )


def test_classification_case_02() -> None:
    _assert_classification(
        "AgNO3 (aq) + NaCl (aq) -> AgCl (s) + NaNO3 (aq)",
        "Fældningsreaktion",
        must_include_secondary=["Dobbeltforskydning"],
    )


def test_classification_case_03() -> None:
    _assert_classification(
        "BaCl2 (aq) + Na2SO4 (aq) -> BaSO4 (s) + 2NaCl (aq)",
        "Fældningsreaktion",
        must_include_secondary=["Dobbeltforskydning"],
    )


def test_classification_case_04() -> None:
    _assert_classification(
        "Na2CO3 (aq) + CaCl2 (aq) -> CaCO3 (s) + 2NaCl (aq)",
        "Fældningsreaktion",
        must_include_secondary=["Dobbeltforskydning"],
    )


def test_classification_case_05() -> None:
    _assert_classification(
        "Pb(NO3)2 (aq) + 2KI (aq) -> PbI2 (s) + 2KNO3 (aq)",
        "Fældningsreaktion",
        must_include_secondary=["Dobbeltforskydning"],
    )


def test_classification_case_06() -> None:
    _assert_classification("HCl (aq) + NaOH (aq) -> NaCl (aq) + H2O (l)", "Syre-base-reaktion")


def test_classification_case_07() -> None:
    _assert_classification("H2SO4 (aq) + 2KOH (aq) -> K2SO4 (aq) + 2H2O (l)", "Syre-base-reaktion")


def test_classification_case_08() -> None:
    _assert_classification("HNO3 (aq) + KOH (aq) -> KNO3 (aq) + H2O (l)", "Syre-base-reaktion")


def test_classification_case_09() -> None:
    _assert_classification("2HCl (aq) + Ca(OH)2 (aq) -> CaCl2 (aq) + 2H2O (l)", "Syre-base-reaktion")


def test_classification_case_10() -> None:
    _assert_classification("CH3COOH (aq) + NaOH (aq) -> CH3COONa (aq) + H2O (l)", "Syre-base-reaktion")


def test_classification_case_11() -> None:
    _assert_classification(
        "Zn (s) + 2HCl (aq) -> ZnCl2 (aq) + H2 (g)",
        "Enkeltforskydning",
        must_include_secondary=["Redoxreaktion"],
    )


def test_classification_case_12() -> None:
    _assert_classification(
        "Mg (s) + 2HCl (aq) -> MgCl2 (aq) + H2 (g)",
        "Enkeltforskydning",
        must_include_secondary=["Redoxreaktion"],
    )


def test_classification_case_13() -> None:
    _assert_classification(
        "Fe (s) + CuSO4 (aq) -> FeSO4 (aq) + Cu (s)",
        "Enkeltforskydning",
        must_include_secondary=["Redoxreaktion"],
    )


def test_classification_case_14() -> None:
    _assert_classification(
        "Cl2 (g) + 2KI (aq) -> 2KCl (aq) + I2 (s)",
        "Enkeltforskydning",
        must_include_secondary=["Redoxreaktion"],
    )


def test_classification_case_15() -> None:
    _assert_classification(
        "Cu (s) + 2AgNO3 (aq) -> Cu(NO3)2 (aq) + 2Ag (s)",
        "Enkeltforskydning",
        must_include_secondary=["Redoxreaktion"],
    )


def test_classification_case_16() -> None:
    _assert_classification(
        "2H2 (g) + O2 (g) -> 2H2O (l)",
        "Syntese/foreningsreaktion",
        must_include_secondary=["Redoxreaktion"],
    )


def test_classification_case_17() -> None:
    _assert_classification("N2 (g) + 3H2 (g) -> 2NH3 (g)", "Syntese/foreningsreaktion")


def test_classification_case_18() -> None:
    _assert_classification(
        "2Na (s) + Cl2 (g) -> 2NaCl (s)",
        "Syntese/foreningsreaktion",
        must_include_secondary=["Redoxreaktion"],
    )


def test_classification_case_19() -> None:
    _assert_classification("CaO (s) + CO2 (g) -> CaCO3 (s)", "Syntese/foreningsreaktion")


def test_classification_case_20() -> None:
    _assert_classification("SO3 (g) + H2O (l) -> H2SO4 (aq)", "Syntese/foreningsreaktion")


def test_classification_case_21() -> None:
    _assert_classification("CaCO3 (s) -> CaO (s) + CO2 (g)", "Nedbrydningsreaktion")


def test_classification_case_22() -> None:
    _assert_classification("2KClO3 (s) -> 2KCl (s) + 3O2 (g)", "Nedbrydningsreaktion")


def test_classification_case_23() -> None:
    _assert_classification(
        "2H2O2 (aq) -> 2H2O (l) + O2 (g)",
        "Nedbrydningsreaktion",
        must_include_secondary=["Redoxreaktion"],
    )


def test_classification_case_24() -> None:
    _assert_classification(
        "2HgO (s) -> 2Hg (l) + O2 (g)",
        "Nedbrydningsreaktion",
        must_include_secondary=["Redoxreaktion"],
    )


def test_classification_case_25() -> None:
    _assert_classification(
        "CH4 (g) + 2O2 (g) -> CO2 (g) + 2H2O (l)",
        "Forbrændingsreaktion",
        must_include_secondary=["Redoxreaktion"],
    )


def test_classification_case_26() -> None:
    _assert_classification(
        "C3H8 (g) + 5O2 (g) -> 3CO2 (g) + 4H2O (l)",
        "Forbrændingsreaktion",
        must_include_secondary=["Redoxreaktion"],
    )


def test_classification_case_27() -> None:
    _assert_classification(
        "2C2H6 (g) + 7O2 (g) -> 4CO2 (g) + 6H2O (l)",
        "Forbrændingsreaktion",
        must_include_secondary=["Redoxreaktion"],
    )


def test_classification_case_28() -> None:
    _assert_classification(
        "2Mg (s) + O2 (g) -> 2MgO (s)",
        "Forbrændingsreaktion",
        must_include_secondary=["Redoxreaktion"],
    )


def test_classification_case_29() -> None:
    _assert_classification(
        "NaCl (aq) + KNO3 (aq) -> NaNO3 (aq) + KCl (aq)",
        "Dobbeltforskydning",
        expected_secondary_exact=[],
    )


def test_classification_case_30() -> None:
    _assert_classification(
        "NH4Cl (aq) + NaNO3 (aq) -> NH4NO3 (aq) + NaCl (aq)",
        "Dobbeltforskydning",
        expected_secondary_exact=[],
    )
