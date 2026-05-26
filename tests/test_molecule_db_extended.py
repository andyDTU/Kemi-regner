"""
Extended tests for all 20 exam-relevant substances in core/molecule_db.py.
Covers: LiCl, AgCl, KNO3, Pb(NO3)2, Na2CO3, BaCO3, SrSO4, Ca(OH)2, KOH,
        NaOH, NH4Cl, BaSO4, CaCO3, NaCl, K2CO3, Mg(OH)2, Al2(SO4)3, CuSO4,
        HCl, NH3
"""

import pytest
from core.molecule_db import get_substance_by_id, search_substances


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _get(id_: str):
    s = get_substance_by_id(id_)
    assert s is not None, f"Substance with id '{id_}' not found in database"
    return s


# ---------------------------------------------------------------------------
# Presence tests — all 20 substances must exist
# ---------------------------------------------------------------------------

def test_licl_exists():
    assert get_substance_by_id("licl") is not None

def test_agcl_exists():
    assert get_substance_by_id("agcl") is not None

def test_kno3_exists():
    assert get_substance_by_id("kno3") is not None

def test_pb_no3_2_exists():
    assert get_substance_by_id("pb_no3_2") is not None

def test_na2co3_exists():
    assert get_substance_by_id("na2co3") is not None

def test_baco3_exists():
    assert get_substance_by_id("baco3") is not None

def test_srso4_exists():
    assert get_substance_by_id("srso4") is not None

def test_ca_oh_2_exists():
    assert get_substance_by_id("ca_oh_2") is not None

def test_koh_exists():
    assert get_substance_by_id("koh") is not None

def test_naoh_exists():
    assert get_substance_by_id("naoh") is not None

def test_nh4cl_exists():
    assert get_substance_by_id("nh4cl") is not None

def test_baso4_exists():
    assert get_substance_by_id("baso4") is not None

def test_caco3_exists():
    assert get_substance_by_id("caco3") is not None

def test_nacl_exists():
    assert get_substance_by_id("nacl") is not None

def test_k2co3_exists():
    assert get_substance_by_id("k2co3") is not None

def test_mg_oh_2_exists():
    assert get_substance_by_id("mg_oh_2") is not None

def test_al2_so4_3_exists():
    assert get_substance_by_id("al2_so4_3") is not None

def test_cuso4_exists():
    assert get_substance_by_id("cuso4") is not None

def test_hcl_exists():
    assert get_substance_by_id("hcl") is not None

def test_nh3_exists():
    assert get_substance_by_id("nh3") is not None


# ---------------------------------------------------------------------------
# Search tests — formulas yield the right substance
# ---------------------------------------------------------------------------

def test_search_licl_formula():
    results = search_substances("LiCl")
    ids = [s.id for s in results]
    assert "licl" in ids

def test_search_baco3_formula():
    results = search_substances("BaCO3")
    ids = [s.id for s in results]
    assert "baco3" in ids

def test_search_srso4_formula():
    results = search_substances("SrSO4")
    ids = [s.id for s in results]
    assert "srso4" in ids

def test_search_k2co3_formula():
    results = search_substances("K2CO3")
    ids = [s.id for s in results]
    assert "k2co3" in ids

def test_search_mg_oh_2_formula():
    results = search_substances("Mg(OH)2")
    ids = [s.id for s in results]
    assert "mg_oh_2" in ids


# ---------------------------------------------------------------------------
# Solubility note tests — all salts/bases have a solubility_note
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("id_", [
    "licl", "agcl", "kno3", "pb_no3_2", "na2co3", "baco3", "srso4",
    "ca_oh_2", "koh", "naoh", "nh4cl", "baso4", "caco3", "nacl",
    "k2co3", "mg_oh_2", "al2_so4_3", "cuso4",
])
def test_solubility_note_present(id_):
    s = _get(id_)
    assert s.solubility_note, f"{id_} missing solubility_note"


# ---------------------------------------------------------------------------
# Exam-note content tests — solubility rules explicitly mentioned
# ---------------------------------------------------------------------------

def test_kno3_exam_note_mentions_nitrat():
    s = _get("kno3")
    assert "nitrat" in s.common_exam_note.lower()

def test_agcl_exam_note_mentions_undtagelse():
    s = _get("agcl")
    assert "undtagelse" in s.common_exam_note.lower()

def test_baso4_exam_note_mentions_sulfat():
    s = _get("baso4")
    assert "sulfat" in s.common_exam_note.lower()

def test_na2co3_exam_note_mentions_carbonat():
    s = _get("na2co3")
    assert "carbonat" in s.common_exam_note.lower()

def test_caco3_exam_note_mentions_carbonat():
    s = _get("caco3")
    assert "carbonat" in s.common_exam_note.lower()

def test_ca_oh_2_exam_note_mentions_hydroxid():
    s = _get("ca_oh_2")
    assert "hydroxid" in s.common_exam_note.lower()

def test_naoh_exam_note_mentions_hydroxid():
    s = _get("naoh")
    assert "hydroxid" in s.common_exam_note.lower()

def test_koh_exam_note_mentions_hydroxid():
    s = _get("koh")
    assert "hydroxid" in s.common_exam_note.lower()

def test_pb_no3_2_exam_note_mentions_nitrat():
    s = _get("pb_no3_2")
    assert "nitrat" in s.common_exam_note.lower()

def test_nh4cl_exam_note_mentions_chlorid():
    s = _get("nh4cl")
    assert "chlorid" in s.common_exam_note.lower()

def test_baco3_exam_note_mentions_carbonat():
    s = _get("baco3")
    assert "carbonat" in s.common_exam_note.lower()

def test_srso4_exam_note_mentions_sulfat():
    s = _get("srso4")
    assert "sulfat" in s.common_exam_note.lower()

def test_k2co3_exam_note_mentions_carbonat():
    s = _get("k2co3")
    assert "carbonat" in s.common_exam_note.lower()

def test_mg_oh_2_exam_note_mentions_hydroxid():
    s = _get("mg_oh_2")
    assert "hydroxid" in s.common_exam_note.lower()

def test_licl_exam_note_mentions_chlorid():
    s = _get("licl")
    assert "chlorid" in s.common_exam_note.lower()


# ---------------------------------------------------------------------------
# Category and formula correctness
# ---------------------------------------------------------------------------

def test_licl_is_salt():
    assert _get("licl").category == "salt"

def test_baco3_is_salt():
    assert _get("baco3").category == "salt"

def test_srso4_is_salt():
    assert _get("srso4").category == "salt"

def test_k2co3_is_salt():
    assert _get("k2co3").category == "salt"

def test_mg_oh_2_is_base():
    assert _get("mg_oh_2").category == "base"

def test_licl_formula():
    assert _get("licl").formula == "LiCl"

def test_baco3_formula():
    assert _get("baco3").formula == "BaCO3"

def test_srso4_formula():
    assert _get("srso4").formula == "SrSO4"

def test_k2co3_formula():
    assert _get("k2co3").formula == "K2CO3"

def test_mg_oh_2_formula():
    assert _get("mg_oh_2").formula == "Mg(OH)2"


# ---------------------------------------------------------------------------
# Molar mass sanity checks (±5 %)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("id_, expected_mm", [
    ("licl", 42.39),
    ("baco3", 197.34),
    ("srso4", 183.68),
    ("k2co3", 138.21),
    ("mg_oh_2", 58.32),
])
def test_molar_mass_approx(id_, expected_mm):
    s = _get(id_)
    assert abs(s.molar_mass - expected_mm) / expected_mm < 0.05, (
        f"{id_}: molar_mass {s.molar_mass} deviates >5% from {expected_mm}"
    )
