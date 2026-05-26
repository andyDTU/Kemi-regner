"""
20 konkrete tests mod parser, regelmotor og kalkulator-wrapper
for underfanen "Tung/let opløselighed".

Regelmodel dokumentation (konsekvent i disse tests):
- CaSO4  → slightly_soluble  (R4_SULFATES_CA_SPECIAL)
- Ca(OH)2 → slightly_soluble  (R5_HYDROXIDES_ALKALINE_EARTH)

Intern status-mapping:
  soluble          → "let opløseligt"    (DA)
  insoluble        → "tungt opløseligt"  (DA)
  slightly_soluble → "svagt opløseligt"  (DA)
  unknown          → "ukendt / kan ikke afgøres sikkert"  (DA)
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.solubility import parse_ionic_salt, evaluate_salt_solubility
from calculators.solubility import analyze_salt_solubility_with_steps


# ---------------------------------------------------------------------------
# TEST 1 – NaCl
# ---------------------------------------------------------------------------
def test_01_nacl():
    """NaCl: Na+ / Cl- / soluble / let opløseligt"""
    r = evaluate_salt_solubility("NaCl")
    assert r["cation"]["symbol"] == "Na+"
    assert r["anion"]["symbol"] == "Cl-"
    assert r["status"] == "soluble"
    assert r["classification_da"] == "let opløseligt"


# ---------------------------------------------------------------------------
# TEST 2 – KNO3
# ---------------------------------------------------------------------------
def test_02_kno3():
    """KNO3: K+ / NO3- / soluble / let opløseligt"""
    r = evaluate_salt_solubility("KNO3")
    assert r["cation"]["symbol"] == "K+"
    assert r["anion"]["symbol"] == "NO3-"
    assert r["status"] == "soluble"
    assert r["classification_da"] == "let opløseligt"


# ---------------------------------------------------------------------------
# TEST 3 – NH4Cl
# ---------------------------------------------------------------------------
def test_03_nh4cl():
    """NH4Cl: NH4+ / Cl- / soluble / let opløseligt"""
    r = evaluate_salt_solubility("NH4Cl")
    assert r["cation"]["symbol"] == "NH4+"
    assert r["anion"]["symbol"] == "Cl-"
    assert r["status"] == "soluble"
    assert r["classification_da"] == "let opløseligt"


# ---------------------------------------------------------------------------
# TEST 4 – AgCl
# ---------------------------------------------------------------------------
def test_04_agcl():
    """AgCl: Ag+ / Cl- / insoluble / tungt opløseligt"""
    r = evaluate_salt_solubility("AgCl")
    assert r["cation"]["symbol"] == "Ag+"
    assert r["anion"]["symbol"] == "Cl-"
    assert r["status"] == "insoluble"
    assert r["classification_da"] == "tungt opløseligt"


# ---------------------------------------------------------------------------
# TEST 5 – PbBr2
# ---------------------------------------------------------------------------
def test_05_pbbr2():
    """PbBr2: Pb2+ / Br- / insoluble / tungt opløseligt"""
    r = evaluate_salt_solubility("PbBr2")
    assert r["cation"]["symbol"] == "Pb2+"
    assert r["anion"]["symbol"] == "Br-"
    assert r["status"] == "insoluble"
    assert r["classification_da"] == "tungt opløseligt"


# ---------------------------------------------------------------------------
# TEST 6 – KI
# ---------------------------------------------------------------------------
def test_06_ki():
    """KI: K+ / I- / soluble / let opløseligt"""
    r = evaluate_salt_solubility("KI")
    assert r["cation"]["symbol"] == "K+"
    assert r["anion"]["symbol"] == "I-"
    assert r["status"] == "soluble"
    assert r["classification_da"] == "let opløseligt"


# ---------------------------------------------------------------------------
# TEST 7 – BaSO4
# ---------------------------------------------------------------------------
def test_07_baso4():
    """BaSO4: Ba2+ / SO4^2- / insoluble / tungt opløseligt"""
    r = evaluate_salt_solubility("BaSO4")
    assert r["cation"]["symbol"] == "Ba2+"
    assert r["anion"]["symbol"] == "SO4^2-"
    assert r["status"] == "insoluble"
    assert r["classification_da"] == "tungt opløseligt"


# ---------------------------------------------------------------------------
# TEST 8 – SrSO4
# ---------------------------------------------------------------------------
def test_08_srso4():
    """SrSO4: Sr2+ / SO4^2- / insoluble / tungt opløseligt"""
    r = evaluate_salt_solubility("SrSO4")
    assert r["cation"]["symbol"] == "Sr2+"
    assert r["anion"]["symbol"] == "SO4^2-"
    assert r["status"] == "insoluble"
    assert r["classification_da"] == "tungt opløseligt"


# ---------------------------------------------------------------------------
# TEST 9 – Na2SO4
# ---------------------------------------------------------------------------
def test_09_na2so4():
    """Na2SO4: Na+ / SO4^2- / soluble / let opløseligt"""
    r = evaluate_salt_solubility("Na2SO4")
    assert r["cation"]["symbol"] == "Na+"
    assert r["anion"]["symbol"] == "SO4^2-"
    assert r["status"] == "soluble"
    assert r["classification_da"] == "let opløseligt"


# ---------------------------------------------------------------------------
# TEST 10 – CaSO4
# Regelmodel: slightly_soluble  (R4_SULFATES_CA_SPECIAL)
# ---------------------------------------------------------------------------
def test_10_cso4():
    """CaSO4: Ca2+ / SO4^2- / slightly_soluble / svagt opløseligt
    
    Regelvalg: CaSO4 klassificeres som svagt opløseligt (R4_SULFATES_CA_SPECIAL).
    Ksp(CaSO4) ≈ 4.93e-5 – lavere end let opløselige sulfater,
    højere end typisk tungt opløselige. Konsekvent modeldokumentation.
    """
    r = evaluate_salt_solubility("CaSO4")
    assert r["cation"]["symbol"] == "Ca2+"
    assert r["anion"]["symbol"] == "SO4^2-"
    assert r["status"] == "slightly_soluble"
    assert r["classification_da"] == "svagt opløseligt"
    assert r["rule_id"] == "R4_SULFATES_CA_SPECIAL"


# ---------------------------------------------------------------------------
# TEST 11 – Na2CO3
# ---------------------------------------------------------------------------
def test_11_na2co3():
    """Na2CO3: Na+ / CO3^2- / soluble / let opløseligt"""
    r = evaluate_salt_solubility("Na2CO3")
    assert r["cation"]["symbol"] == "Na+"
    assert r["anion"]["symbol"] == "CO3^2-"
    assert r["status"] == "soluble"
    assert r["classification_da"] == "let opløseligt"


# ---------------------------------------------------------------------------
# TEST 12 – CaCO3
# ---------------------------------------------------------------------------
def test_12_caco3():
    """CaCO3: Ca2+ / CO3^2- / insoluble / tungt opløseligt"""
    r = evaluate_salt_solubility("CaCO3")
    assert r["cation"]["symbol"] == "Ca2+"
    assert r["anion"]["symbol"] == "CO3^2-"
    assert r["status"] == "insoluble"
    assert r["classification_da"] == "tungt opløseligt"


# ---------------------------------------------------------------------------
# TEST 13 – (NH4)3PO4
# ---------------------------------------------------------------------------
def test_13_nh43po4():
    """(NH4)3PO4: NH4+ / PO4^3- / soluble / let opløseligt"""
    r = evaluate_salt_solubility("(NH4)3PO4")
    assert r["cation"]["symbol"] == "NH4+"
    assert r["anion"]["symbol"] == "PO4^3-"
    assert r["status"] == "soluble"
    assert r["classification_da"] == "let opløseligt"


# ---------------------------------------------------------------------------
# TEST 14 – Mg(OH)2
# ---------------------------------------------------------------------------
def test_14_mg_oh_2():
    """Mg(OH)2: Mg2+ / OH- / insoluble / tungt opløseligt"""
    r = evaluate_salt_solubility("Mg(OH)2")
    assert r["cation"]["symbol"] == "Mg2+"
    assert r["anion"]["symbol"] == "OH-"
    assert r["status"] == "insoluble"
    assert r["classification_da"] == "tungt opløseligt"


# ---------------------------------------------------------------------------
# TEST 15 – Ca(OH)2
# Regelmodel: slightly_soluble  (R5_HYDROXIDES_ALKALINE_EARTH)
# ---------------------------------------------------------------------------
def test_15_ca_oh_2():
    """Ca(OH)2: Ca2+ / OH- / slightly_soluble / svagt opløseligt
    
    Regelvalg: Ca(OH)2, Sr(OH)2 og Ba(OH)2 klassificeres som svagt opløselige
    (R5_HYDROXIDES_ALKALINE_EARTH) – konsekvent med CaSO4's særstatus.
    """
    r = evaluate_salt_solubility("Ca(OH)2")
    assert r["cation"]["symbol"] == "Ca2+"
    assert r["anion"]["symbol"] == "OH-"
    assert r["status"] == "slightly_soluble"
    assert r["classification_da"] == "svagt opløseligt"
    assert r["rule_id"] == "R5_HYDROXIDES_ALKALINE_EARTH"


# ---------------------------------------------------------------------------
# TEST 16 – Al2(SO4)3
# ---------------------------------------------------------------------------
def test_16_al2_so4_3():
    """Al2(SO4)3: Al3+ / SO4^2- / soluble / let opløseligt"""
    r = evaluate_salt_solubility("Al2(SO4)3")
    assert r["cation"]["symbol"] == "Al3+"
    assert r["anion"]["symbol"] == "SO4^2-"
    assert r["status"] == "soluble"
    assert r["classification_da"] == "let opløseligt"


# ---------------------------------------------------------------------------
# TEST 17 – Pb(NO3)2
# ---------------------------------------------------------------------------
def test_17_pb_no3_2():
    """Pb(NO3)2: Pb2+ / NO3- / soluble / let opløseligt  (R2: nitrat)"""
    r = evaluate_salt_solubility("Pb(NO3)2")
    assert r["cation"]["symbol"] == "Pb2+"
    assert r["anion"]["symbol"] == "NO3-"
    assert r["status"] == "soluble"
    assert r["classification_da"] == "let opløseligt"


# ---------------------------------------------------------------------------
# TEST 18 – FePO4
# Parser skal entydigt afgøre Fe3+ (charge-balance: 1×Fe3+ + 1×PO4^3-)
# Fe2+(PO4) kræver Fe3(PO4)2, som ikke matcher FePO4
# ---------------------------------------------------------------------------
def test_18_fepo4():
    """FePO4: Fe3+ / PO4^3- / insoluble / tungt opløseligt
    
    Parser afklaring: FePO4 (Fe:1, P:1, O:4) matches kun af
    1×Fe3+ + 1×PO4^3- via charge-neutralitet (3 = 3).
    Fe2+ ville kræve Fe3(PO4)2. Entydigt match → ingen gætteri.
    """
    r = evaluate_salt_solubility("FePO4")
    assert r["cation"]["symbol"] == "Fe3+"
    assert r["anion"]["symbol"] == "PO4^3-"
    assert r["status"] == "insoluble"
    assert r["classification_da"] == "tungt opløseligt"


# ---------------------------------------------------------------------------
# TEST 19 – ugyldig formel: abc123
# ---------------------------------------------------------------------------
def test_19_invalid_formula_no_crash():
    """abc123 → ingen crash, status=unknown, error_message til stede"""
    result, steps, metadata = analyze_salt_solubility_with_steps("abc123")
    assert result["status"] == "unknown"
    assert "error_message" in result
    assert len(result["error_message"]) > 0
    # Ingen falsk klassifikation
    assert result["classification_da"] == "ukendt / kan ikke afgøres sikkert"


# ---------------------------------------------------------------------------
# TEST 20 – tom streng
# ---------------------------------------------------------------------------
def test_20_empty_string_no_crash():
    """Tom streng → ingen crash, tydelig fejlbesked om manglende input"""
    result, steps, metadata = analyze_salt_solubility_with_steps("")
    assert result["status"] == "unknown"
    assert "error_message" in result
    # Fejlbeskeden skal nævne at input er tomt / mangler
    error_lower = result["error_message"].lower()
    assert "tomt" in error_lower or "mangler" in error_lower or "empty" in error_lower
    # Ingen falsk klassifikation
    assert result["classification_da"] == "ukendt / kan ikke afgøres sikkert"


# ---------------------------------------------------------------------------
# GENERALISERINGS-CHECKS (nabocases til at sikre generelle rettelser)
# ---------------------------------------------------------------------------

class TestHalidGeneralisation:
    """Hvis TEST 4 (AgCl) fejlede: check AgBr og AgI sikrer R3-undtagelsen er generel."""

    def test_agbr_insoluble(self):
        r = evaluate_salt_solubility("AgBr")
        assert r["status"] == "insoluble"

    def test_agi_insoluble(self):
        r = evaluate_salt_solubility("AgI")
        assert r["status"] == "insoluble"

    def test_nacl_soluble(self):
        r = evaluate_salt_solubility("NaCl")
        assert r["status"] == "soluble"


class TestSulfatGeneralisation:
    """Hvis TEST 7/8 (BaSO4/SrSO4) fejlede: check PbSO4."""

    def test_pbso4_insoluble(self):
        r = evaluate_salt_solubility("PbSO4")
        assert r["status"] == "insoluble"


class TestCarbonateGeneralisation:
    """Nabocases for carbonatregel (TEST 11/12)."""

    def test_k2co3_soluble(self):
        r = evaluate_salt_solubility("K2CO3")
        assert r["status"] == "soluble"

    def test_mgco3_insoluble(self):
        r = evaluate_salt_solubility("MgCO3")
        assert r["status"] == "insoluble"


class TestAmmoniumGeneralisation:
    """Nabocases for ammoniumregel (TEST 3/13)."""

    def test_nh4no3_soluble(self):
        r = evaluate_salt_solubility("NH4NO3")
        assert r["status"] == "soluble"

    def test_nh42so4_soluble(self):
        r = evaluate_salt_solubility("(NH4)2SO4")
        assert r["status"] == "soluble"


class TestHydroxidGeneralisation:
    """Nabocases for hydroxidregel (TEST 14/15)."""

    def test_ba_oh_2_slightly_soluble(self):
        r = evaluate_salt_solubility("Ba(OH)2")
        assert r["status"] == "slightly_soluble"

    def test_zn_oh_2_insoluble(self):
        r = evaluate_salt_solubility("Zn(OH)2")
        assert r["status"] == "insoluble"
