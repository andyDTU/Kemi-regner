"""Tests for periodic table data helpers."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.periodic_table import get_element_by_symbol, get_periodic_table_elements


def test_periodic_table_contains_118_elements():
    elements = get_periodic_table_elements()
    assert len(elements) == 118
    numbers = {element["atomicNumber"] for element in elements}
    assert numbers == set(range(1, 119))


def test_oxygen_has_expected_core_fields():
    oxygen = get_element_by_symbol("O")
    assert oxygen is not None
    assert oxygen["atomicNumber"] == 8
    assert oxygen["period"] == 2
    assert oxygen["group"] == 16
    assert oxygen["category"] in {"nonmetal", "halogen"}
    assert oxygen["electronConfiguration"]


def test_lanthanide_and_actinide_rows_are_present():
    la = get_element_by_symbol("La")
    u = get_element_by_symbol("U")
    assert la is not None
    assert u is not None
    assert la["seriesRow"] == 1
    assert u["seriesRow"] == 2
