"""
20 tests for the "Molekyle database" feature.

Tests cover:
  1.  navigation constant contains the new page label
  2.  search field placeholder (data model check)
  3.  search "HCl" finds saltsyre
  4.  search "saltsyre" finds HCl
  5.  search "NH3" finds ammoniak
  6.  search "ammoniak" finds NH3
  7.  search "NaCl" finds natriumchlorid
  8.  search by synonym finds the correct substance
  9.  empty search does not crash and returns empty list
  10. unknown search term returns empty list (no crash)
  11. get_substance_by_id returns full detail object
  12. stærk syre classification is correct (HCl)
  13. svag syre classification is correct (CH3COOH)
  14. stærk base classification is correct (NaOH)
  15. salt classification is correct (NaCl)
  16. ion classification is correct (Cl-)
  17. molar_mass present only when data exists
  18. missing optional fields do not cause AttributeError
  19. category filter works correctly
  20. NAVIGATION_OPTIONS contains new tab; PAGE_LABEL_TO_QUERY maps it
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.molecule_db import (
    search_substances,
    get_substance_by_id,
    SUBSTANCES,
    Substance,
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _find_by_formula(formula: str) -> Substance | None:
    for s in SUBSTANCES:
        if s.formula.lower() == formula.lower():
            return s
    return None


# ---------------------------------------------------------------------------
# TEST 1 – navigation constant contains the new page label
# ---------------------------------------------------------------------------
def test_01_navigation_options_contains_molecule_database():
    """NAVIGATION_OPTIONS must include new tab. Tested via app module attribute."""
    import app as _app
    assert "🔬 Molekyle database" in _app.NAVIGATION_OPTIONS


# ---------------------------------------------------------------------------
# TEST 2 – PAGE_LABEL_TO_QUERY maps the new tab to query key
# ---------------------------------------------------------------------------
def test_02_page_label_to_query_maps_new_tab():
    import app as _app
    assert _app.PAGE_LABEL_TO_QUERY.get("🔬 Molekyle database") == "molecule-db"


# ---------------------------------------------------------------------------
# TEST 3 – search "HCl" finds saltsyre
# ---------------------------------------------------------------------------
def test_03_search_hcl_finds_saltsyre():
    results = search_substances("HCl")
    formulas = [r.formula for r in results]
    assert "HCl" in formulas, "Search for 'HCl' should return substance with formula HCl"
    hcl = next(r for r in results if r.formula == "HCl")
    assert "saltsyre" in hcl.name_da.lower()


# ---------------------------------------------------------------------------
# TEST 4 – search "saltsyre" finds HCl
# ---------------------------------------------------------------------------
def test_04_search_saltsyre_finds_hcl():
    results = search_substances("saltsyre")
    assert results, "Search for 'saltsyre' should return at least one result"
    formulas = [r.formula for r in results]
    assert "HCl" in formulas


# ---------------------------------------------------------------------------
# TEST 5 – search "NH3" finds ammoniak
# ---------------------------------------------------------------------------
def test_05_search_nh3_finds_ammoniak():
    results = search_substances("NH3")
    assert results, "Search for 'NH3' should return at least one result"
    names_lower = [r.name_da.lower() for r in results]
    assert any("ammoniak" in n for n in names_lower)


# ---------------------------------------------------------------------------
# TEST 6 – search "ammoniak" finds NH3
# ---------------------------------------------------------------------------
def test_06_search_ammoniak_finds_nh3():
    results = search_substances("ammoniak")
    assert results, "Search for 'ammoniak' should return at least one result"
    formulas = [r.formula for r in results]
    assert "NH3" in formulas


def test_06b_search_formula_with_phase_suffix_finds_nh3():
    results = search_substances("NH3(aq)")
    formulas = [r.formula for r in results]
    assert "NH3" in formulas


def test_06c_search_condensed_formula_finds_propionic_acid():
    results = search_substances("CH3CH2COOH")
    formulas = [r.formula for r in results]
    assert "C2H5COOH" in formulas


# ---------------------------------------------------------------------------
# TEST 7 – search "NaCl" finds natriumchlorid
# ---------------------------------------------------------------------------
def test_07_search_nacl_finds_natriumchlorid():
    results = search_substances("NaCl")
    assert results, "Search for 'NaCl' should return at least one result"
    nacl = next((r for r in results if r.formula == "NaCl"), None)
    assert nacl is not None
    assert "natriumchlorid" in nacl.name_da.lower()


# ---------------------------------------------------------------------------
# TEST 8 – search by synonym finds correct substance
# ---------------------------------------------------------------------------
def test_08_search_by_synonym():
    # "salpetersyre" is NOT in the DB by default but "nitric acid" is a synonym
    results = search_substances("nitric acid")
    assert results, "Search for synonym 'nitric acid' should find HNO3"
    formulas = [r.formula for r in results]
    assert "HNO3" in formulas

    # Also test Danish synonym "bagepulver" → NaHCO3
    results2 = search_substances("bagepulver")
    assert results2, "Search for 'bagepulver' should find NaHCO3"
    formulas2 = [r.formula for r in results2]
    assert "NaHCO3" in formulas2


# ---------------------------------------------------------------------------
# TEST 9 – empty search does not crash and returns empty list
# ---------------------------------------------------------------------------
def test_09_empty_search_returns_empty_no_crash():
    assert search_substances("") == []
    assert search_substances("   ") == []


# ---------------------------------------------------------------------------
# TEST 10 – unknown search term returns empty list (no crash)
# ---------------------------------------------------------------------------
def test_10_unknown_search_returns_empty():
    result = search_substances("xyzUnknownSubstance999")
    assert result == []


# ---------------------------------------------------------------------------
# TEST 11 – get_substance_by_id returns full detail object
# ---------------------------------------------------------------------------
def test_11_get_by_id_returns_substance():
    s = get_substance_by_id("hcl")
    assert s is not None
    assert s.formula == "HCl"
    assert s.name_da is not None
    assert s.description is not None
    # All required fields present
    assert s.id == "hcl"
    assert s.category == "syre"


def test_11b_get_by_id_unknown_returns_none():
    assert get_substance_by_id("does_not_exist") is None


# ---------------------------------------------------------------------------
# TEST 12 – stærk syre classification correct (HCl)
# ---------------------------------------------------------------------------
def test_12_strong_acid_classification():
    s = get_substance_by_id("hcl")
    assert s is not None
    assert s.category == "syre"
    assert s.acid_base_role == "syre"
    assert s.acid_strength == "stærk"


# ---------------------------------------------------------------------------
# TEST 13 – svag syre classification correct (CH3COOH)
# ---------------------------------------------------------------------------
def test_13_weak_acid_classification():
    s = get_substance_by_id("ch3cooh")
    assert s is not None
    assert s.category == "syre"
    assert s.acid_base_role == "syre"
    assert s.acid_strength == "svag"


# ---------------------------------------------------------------------------
# TEST 14 – stærk base classification correct (NaOH)
# ---------------------------------------------------------------------------
def test_14_strong_base_classification():
    s = get_substance_by_id("naoh")
    assert s is not None
    assert s.category == "base"
    assert s.acid_base_role == "base"
    assert s.base_strength == "stærk"


# ---------------------------------------------------------------------------
# TEST 15 – salt classification correct (NaCl)
# ---------------------------------------------------------------------------
def test_15_salt_classification():
    s = get_substance_by_id("nacl")
    assert s is not None
    assert s.category == "salt"
    assert s.salt_components is not None
    assert "Na+" in s.salt_components
    assert "Cl-" in s.salt_components


# ---------------------------------------------------------------------------
# TEST 16 – ion classification correct (Cl-)
# ---------------------------------------------------------------------------
def test_16_ion_classification():
    s = get_substance_by_id("cl_minus")
    assert s is not None
    assert s.category == "ion"
    assert s.ion_charge == -1
    assert s.formula == "Cl-"


# ---------------------------------------------------------------------------
# TEST 17 – molar_mass present only when data was provided
# ---------------------------------------------------------------------------
def test_17_molar_mass_present_when_data_exists():
    # Substances that should have molar mass
    for substance_id in ["hcl", "naoh", "nacl", "h2o", "nh3"]:
        s = get_substance_by_id(substance_id)
        assert s is not None
        assert s.molar_mass is not None, f"Expected molar_mass for {substance_id}"
        assert s.molar_mass > 0


def test_17b_molar_mass_field_is_float_or_none():
    """All molar_mass values are either None or positive float."""
    for s in SUBSTANCES:
        if s.molar_mass is not None:
            assert isinstance(s.molar_mass, float), f"{s.id}: molar_mass should be float"
            assert s.molar_mass > 0, f"{s.id}: molar_mass should be positive"


# ---------------------------------------------------------------------------
# TEST 18 – missing optional fields do not cause AttributeError
# ---------------------------------------------------------------------------
def test_18_optional_fields_do_not_raise():
    """All substances can be iterated without AttributeError on optional fields."""
    optional_attrs = [
        "name_en", "synonyms", "tags", "subtype",
        "acid_base_role", "acid_strength", "base_strength",
        "molar_mass", "ion_charge", "physical_state",
        "polarity", "solubility_note", "conjugate_acid",
        "conjugate_base", "salt_components", "common_exam_note",
    ]
    for s in SUBSTANCES:
        for attr in optional_attrs:
            # getattr should not raise — value may be None or a list
            val = getattr(s, attr, "MISSING")
            assert val != "MISSING", f"{s.id} missing attribute {attr}"


# ---------------------------------------------------------------------------
# TEST 19 – category filter works correctly
# ---------------------------------------------------------------------------
def test_19_category_filter():
    syrer = [s for s in SUBSTANCES if s.category == "syre"]
    assert len(syrer) >= 5, "Database should contain at least 5 acids"
    for s in syrer:
        assert s.category == "syre"

    salte = [s for s in SUBSTANCES if s.category == "salt"]
    assert len(salte) >= 5, "Database should contain at least 5 salts"

    ioner = [s for s in SUBSTANCES if s.category == "ion"]
    assert len(ioner) >= 5, "Database should contain at least 5 ions"

    baser = [s for s in SUBSTANCES if s.category == "base"]
    assert len(baser) >= 3, "Database should contain at least 3 bases"


def test_19b_search_with_category_filter():
    """search_substances returns results that can be post-filtered by category."""
    all_syre_results = search_substances("syre")
    # Filter post-search (as the UI does)
    acid_only = [s for s in all_syre_results if s.category == "syre"]
    assert len(acid_only) >= 1


# ---------------------------------------------------------------------------
# TEST 20 – new tab present in navigation and does not break existing pages
# ---------------------------------------------------------------------------
def test_20_new_tab_in_navigation_and_no_conflicts():
    import app as _app
    # Tab exists in navigation list
    assert "🔬 Molekyle database" in _app.NAVIGATION_OPTIONS
    # Route mapping is present and unique
    assert "🔬 Molekyle database" in _app.PAGE_LABEL_TO_QUERY
    query_val = _app.PAGE_LABEL_TO_QUERY["🔬 Molekyle database"]
    assert query_val == "molecule-db"
    # The query key is unique (not shared with another page)
    values = list(_app.PAGE_LABEL_TO_QUERY.values())
    assert values.count(query_val) == 1, "Query key 'molecule-db' must be unique"
    # No duplicate labels in NAVIGATION_OPTIONS
    assert len(_app.NAVIGATION_OPTIONS) == len(set(_app.NAVIGATION_OPTIONS)), \
        "NAVIGATION_OPTIONS should have no duplicate entries"
    # Function exists in app module
    assert hasattr(_app, "show_molecule_database_page"), \
        "app.py should define show_molecule_database_page()"
    assert callable(_app.show_molecule_database_page)
