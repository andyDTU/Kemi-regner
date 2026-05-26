"""
Tests for electron configuration parser and engine.
"""

import pytest
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.electron_configuration import electron_configuration, parse_element_charge_input
from core.electron_configuration import distribute_subshell
from core.electron_configuration import parse_electron_configuration, render_shell_sorted, sort_by_shell_order
from core.electron_configuration import (
    count_d_electrons,
    count_d_unpaired_electrons,
    count_total_unpaired_electrons,
    format_configuration_long,
    format_configuration_noble,
    ground_state_configuration_structured,
    subshell_orbital_occupancy,
)
from core.radius import resolve_radius
from calculators.electron_configuration import calculate_electron_configuration_with_steps


def test_na_configuration():
    result = electron_configuration(11, 0)
    assert result["long"] == "1s2 2s2 2p6 3s1"
    assert result["noble"] == "[Ne] 3s1"
    assert result["electrons"] == 11


def test_b_configuration():
    result = electron_configuration(5, 0)
    assert result["long"] == "1s2 2s2 2p1"


def test_o_2_minus_configuration():
    result = electron_configuration(8, -2)
    assert result["long"] == "1s2 2s2 2p6"
    assert result["noble"] == "[Ne]"


def test_cl_minus_configuration():
    result = electron_configuration(17, -1)
    assert result["long"] == "1s2 2s2 2p6 3s2 3p6"
    assert result["noble"] == "[Ar]"


def test_fe_2_plus_configuration():
    result = electron_configuration(26, 2)
    assert result["long"] == "1s2 2s2 2p6 3s2 3p6 3d6"
    assert result["noble"] == "[Ar] 3d6"


def test_fe_3_plus_configuration():
    result = electron_configuration(26, 3)
    assert result["long"] == "1s2 2s2 2p6 3s2 3p6 3d5"
    assert result["noble"] == "[Ar] 3d5"


def test_cr_exception_neutral_and_ion():
    neutral = electron_configuration(24, 0)
    assert neutral["long"] == "1s2 2s2 2p6 3s2 3p6 4s1 3d5"
    assert neutral["noble"] == "[Ar] 3d5 4s1"

    ion = electron_configuration(24, 2)
    assert ion["long"] == "1s2 2s2 2p6 3s2 3p6 3d4"
    assert ion["noble"] == "[Ar] 3d4"


def test_cu_exception_neutral_and_ion():
    neutral = electron_configuration(29, 0)
    assert neutral["long"] == "1s2 2s2 2p6 3s2 3p6 4s1 3d10"
    assert neutral["noble"] == "[Ar] 3d10 4s1"

    ion = electron_configuration(29, 1)
    assert ion["long"] == "1s2 2s2 2p6 3s2 3p6 3d10"
    assert ion["noble"] == "[Ar] 3d10"


def test_mo_ground_state_regression():
    result = electron_configuration(42, 0)
    assert result["noble"] == "[Kr] 4d5 5s1"
    assert result["long"] == "1s2 2s2 2p6 3s2 3p6 4s2 3d10 4p6 5s1 4d5"


def test_ru_ground_state_regression():
    result = electron_configuration(44, 0)
    assert result["long"] == "1s2 2s2 2p6 3s2 3p6 4s2 3d10 4p6 5s1 4d7"
    assert result["noble"] == "[Kr] 4d7 5s1"
    assert result["noble"] != "[Kr] 4d6 5s2"
    assert result["total_unpaired_electrons"] == 4
    assert result["d_electrons"] == 7
    assert result["d_unpaired_electrons"] == 3


def test_parse_supported_formats():
    parsed = parse_element_charge_input("O^2-")
    assert parsed.Z == 8
    assert parsed.symbol == "O"
    assert parsed.charge == -2

    parsed = parse_element_charge_input("O2-")
    assert parsed.Z == 8
    assert parsed.charge == -2

    parsed = parse_element_charge_input("Fe3+")
    assert parsed.Z == 26
    assert parsed.charge == 3

    parsed = parse_element_charge_input("26 2+")
    assert parsed.Z == 26
    assert parsed.symbol == "Fe"
    assert parsed.charge == 2

    parsed = parse_element_charge_input("Cl-")
    assert parsed.Z == 17
    assert parsed.charge == -1

    parsed = parse_element_charge_input("Br1-")
    assert parsed.Z == 35
    assert parsed.charge == -1

    parsed = parse_element_charge_input("Cu+")
    assert parsed.Z == 29
    assert parsed.charge == 1


def test_parse_invalid_formats():
    with pytest.raises(ValueError, match="Ugyldigt"):
        parse_element_charge_input("2- O")

    with pytest.raises(ValueError, match="Ukendt grundstofsymbol"):
        parse_element_charge_input("Xx2+")

    with pytest.raises(ValueError, match="Ladning"):
        parse_element_charge_input("Fe9+")


def test_negative_electron_count_rejected():
    with pytest.raises(ValueError, match="negativt antal elektroner"):
        electron_configuration(3, 5)


def test_radius_lookup_k_plus():
    r = resolve_radius(19, 1)
    assert r["kind"] == "ionic"
    assert r["value"] is not None
    assert r["unit"] == "pm"


def test_radius_lookup_ca_2_plus():
    r = resolve_radius(20, 2)
    assert r["kind"] == "ionic"
    assert r["value"] is not None


def test_radius_lookup_br_neutral():
    r = resolve_radius(35, 0)
    assert r["kind"] == "atomic"
    assert r["value"] is not None


def test_radius_lookup_y_neutral_not_unknown():
    r = resolve_radius(39, 0)
    assert r["kind"] == "atomic"
    assert r["value"] is not None


def test_radius_lookup_neutral_full_range_1_to_118():
    missing = [z for z in range(1, 119) if resolve_radius(z, 0)["value"] is None]
    assert missing == []


def test_radius_lookup_unusual_ca_2_minus_returns_unknown_not_crash():
    r = resolve_radius(20, -2)
    assert r["kind"] == "ionic"
    assert r["value"] is None
    assert "ingen ionradius-data" in r.get("note", "")


def test_wrapper_includes_radius_line_and_data():
    result, steps, metadata = calculate_electron_configuration_with_steps("K+")
    assert "radius" in result
    assert metadata["radius"]["kind"] == "ionic"
    assert any("Radius:" in step for step in steps)


def test_distribute_subshell_p3_hund_rule():
    assert distribute_subshell("p", 3) == ["↑", "↑", "↑"]


def test_distribute_subshell_p4_hund_then_pair():
    assert distribute_subshell("p", 4) == ["↑↓", "↑", "↑"]


def test_distribute_subshell_p6_full():
    assert distribute_subshell("p", 6) == ["↑↓", "↑↓", "↑↓"]


def test_distribute_subshell_s1():
    assert distribute_subshell("s", 1) == ["↑"]


def test_orbital_distribution_p_neutral():
    result, _steps, _metadata = calculate_electron_configuration_with_steps("P")
    lines = [row["text"] for row in result["orbital_distribution"]]
    target = [line for line in lines if line.startswith("3p:")]
    assert target
    assert "px [↑]" in target[0]
    assert "py [↑]" in target[0]
    assert "pz [↑]" in target[0]


def test_orbital_distribution_o_neutral_p4():
    result, _steps, _metadata = calculate_electron_configuration_with_steps("O")
    lines = [row["text"] for row in result["orbital_distribution"]]
    target = [line for line in lines if line.startswith("2p:")]
    assert target
    assert "px [↑↓]" in target[0]
    assert "py [↑]" in target[0]
    assert "pz [↑]" in target[0]


def test_orbital_distribution_o_show_all_false_keeps_current_behavior():
    result, _steps, _metadata = calculate_electron_configuration_with_steps("O", orbital_view="valence")
    labels = [row["subshell_label"] for row in result["orbital_distribution"]]
    assert labels == ["2s", "2p"]


def test_orbital_distribution_o_show_all_true_includes_core_shells():
    result, _steps, _metadata = calculate_electron_configuration_with_steps("O", orbital_view="all")
    labels = [row["subshell_label"] for row in result["orbital_distribution"]]
    assert labels == ["1s", "2s", "2p"]


def test_orbital_distribution_ne_full_p():
    result, _steps, _metadata = calculate_electron_configuration_with_steps("Ne")
    lines = [row["text"] for row in result["orbital_distribution"]]
    target = [line for line in lines if line.startswith("2p:")]
    assert target
    assert "px [↑↓]" in target[0]
    assert "py [↑↓]" in target[0]
    assert "pz [↑↓]" in target[0]


def test_orbital_distribution_ne_show_all_true_has_1s_2s_2p():
    result, _steps, _metadata = calculate_electron_configuration_with_steps("Ne", orbital_view="all")
    lines = [row["text"] for row in result["orbital_distribution"]]
    assert lines[0] == "1s: s [↑↓]"
    assert lines[1] == "2s: s [↑↓]"
    assert lines[2] == "2p: px [↑↓]  py [↑↓]  pz [↑↓]"


def test_orbital_distribution_na_3s1():
    result, _steps, _metadata = calculate_electron_configuration_with_steps("Na")
    lines = [row["text"] for row in result["orbital_distribution"]]
    target = [line for line in lines if line.startswith("3s:")]
    assert target
    assert "s [↑]" in target[0]


def test_orbital_distribution_na_show_all_true_has_1s_2s_2p_3s():
    result, _steps, _metadata = calculate_electron_configuration_with_steps("Na", orbital_view="all")
    labels = [row["subshell_label"] for row in result["orbital_distribution"]]
    assert labels == ["1s", "2s", "2p", "3s"]


def test_orbital_distribution_fe3_plus_d5():
    result, _steps, _metadata = calculate_electron_configuration_with_steps("Fe3+")
    lines = [row["text"] for row in result["orbital_distribution"]]
    target = [line for line in lines if line.startswith("3d:")]
    assert target
    assert target[0].count("[↑]") == 5


def test_orbital_distribution_fe2_plus_d6():
    result, _steps, _metadata = calculate_electron_configuration_with_steps("Fe2+")
    lines = [row["text"] for row in result["orbital_distribution"]]
    target = [line for line in lines if line.startswith("3d:")]
    assert target
    assert "dxy [↑↓]" in target[0]
    assert "dyz [↑]" in target[0]
    assert "dxz [↑]" in target[0]
    assert "dx2−y2 [↑]" in target[0]
    assert "dz2 [↑]" in target[0]


def test_orbital_distribution_fe2_plus_show_all_true_includes_core_and_d_shell():
    result, _steps, _metadata = calculate_electron_configuration_with_steps("Fe2+", orbital_view="all")
    labels = [row["subshell_label"] for row in result["orbital_distribution"]]
    assert labels == ["1s", "2s", "2p", "3s", "3p", "3d"]
    d_row = [row for row in result["orbital_distribution"] if row["subshell_label"] == "3d"][0]
    assert "dxy [↑↓]" in d_row["text"]
    assert "dyz [↑]" in d_row["text"]


def test_orbital_distribution_contains_quantum_numbers_for_2p():
    result, _steps, _metadata = calculate_electron_configuration_with_steps("O", orbital_view="all")
    p_row = [row for row in result["orbital_distribution"] if row["subshell_label"] == "2p"][0]

    assert p_row["n"] == 2
    assert p_row["l"] == 1
    assert p_row["m_values"] == [-1, 0, 1]

    orbitals = p_row["orbitals"]
    assert [orb["m"] for orb in orbitals] == [-1, 0, 1]
    assert all(orb["n"] == 2 for orb in orbitals)
    assert all(orb["l"] == 1 for orb in orbitals)


def test_configuration_orbitals_include_l_and_m_values():
    result = electron_configuration(8, 0)
    p_orbital = [orb for orb in result["orbitals"] if orb["label"] == "2p"][0]

    assert p_orbital["n"] == 2
    assert p_orbital["l"] == 1
    assert p_orbital["m_values"] == [-1, 0, 1]


def test_orbital_distribution_u_show_all_true_includes_all_occupied_subshells():
    result, _steps, _metadata = calculate_electron_configuration_with_steps("U", orbital_view="all")
    labels = [row["subshell_label"] for row in result["orbital_distribution"]]
    assert labels == [
        "1s", "2s", "2p", "3s", "3p", "4s", "3d", "4p", "5s", "4d",
        "5p", "6s", "4f", "5d", "6p", "7s", "5f",
    ]


def test_orbital_distribution_o2_minus_p6():
    result, _steps, _metadata = calculate_electron_configuration_with_steps("O2-")
    lines = [row["text"] for row in result["orbital_distribution"]]
    target = [line for line in lines if line.startswith("2p:")]
    assert target
    assert "px [↑↓]" in target[0]
    assert "py [↑↓]" in target[0]
    assert "pz [↑↓]" in target[0]


def test_parse_sort_render_helpers_simple():
    parsed = parse_electron_configuration("5p6 6s2 4f14 5d10")
    sorted_items = sort_by_shell_order(parsed)
    assert render_shell_sorted(sorted_items, grouped=False) == "4f14 5p6 5d10 6s2"


def test_na_aufbau_and_shell_sorted_are_same():
    res = electron_configuration(11, 0)
    assert res["aufbau"] == "1s2 2s2 2p6 3s1"
    assert res["shell_sorted"] == "1s2 2s2 2p6 3s1"


def test_br_shell_sorted_reorders_3d_and_4p_region():
    res = electron_configuration(35, 0)
    assert "4s2 3d10 4p5" in res["aufbau"]
    grouped_lines = res["shell_sorted_grouped"].splitlines()
    assert grouped_lines[3] == "4s2 4p5"
    assert grouped_lines[2] == "3s2 3p6 3d10"


def test_u_aufbau_and_shell_sorted_views_present():
    res = electron_configuration(92, 0)
    assert res["aufbau"] == "1s2 2s2 2p6 3s2 3p6 4s2 3d10 4p6 5s2 4d10 5p6 6s2 4f14 5d10 6p6 7s2 5f4"
    assert res["shell_sorted_grouped"] == "\n".join(
        [
            "1s2",
            "2s2 2p6",
            "3s2 3p6 3d10",
            "4s2 4p6 4d10 4f14",
            "5s2 5p6 5d10 5f4",
            "6s2 6p6",
            "7s2",
        ]
    )


def test_ion_shell_sorted_still_available():
    res = electron_configuration(8, -2)
    assert res["aufbau"] == "1s2 2s2 2p6"
    assert res["shell_sorted_grouped"] == "1s2\n2s2 2p6"


@pytest.mark.parametrize(
    "symbol,expected_noble,expected_unpaired,expected_d_electrons,expected_d_unpaired",
    [
        ("H", "1s1", 1, 0, 0),
        ("He", "[He]", 0, 0, 0),
        ("C", "[He] 2s2 2p2", 2, 0, 0),
        ("N", "[He] 2s2 2p3", 3, 0, 0),
        ("O", "[He] 2s2 2p4", 2, 0, 0),
        ("Ne", "[Ne]", 0, 0, 0),
        ("Na", "[Ne] 3s1", 1, 0, 0),
        ("Cl", "[Ne] 3s2 3p5", 1, 0, 0),
        ("Ar", "[Ar]", 0, 0, 0),
        ("K", "[Ar] 4s1", 1, 0, 0),
        ("Ca", "[Ar] 4s2", 0, 0, 0),
        ("Sc", "[Ar] 3d1 4s2", 1, 1, 1),
        ("Ti", "[Ar] 3d2 4s2", 2, 2, 2),
        ("V", "[Ar] 3d3 4s2", 3, 3, 3),
        ("Cr", "[Ar] 3d5 4s1", 6, 5, 5),
        ("Mn", "[Ar] 3d5 4s2", 5, 5, 5),
        ("Fe", "[Ar] 3d6 4s2", 4, 6, 4),
        ("Co", "[Ar] 3d7 4s2", 3, 7, 3),
        ("Ni", "[Ar] 3d8 4s2", 2, 8, 2),
        ("Cu", "[Ar] 3d10 4s1", 1, 10, 0),
        ("Zn", "[Ar] 3d10 4s2", 0, 10, 0),
        ("Kr", "[Kr]", 0, 10, 0),
        ("Rb", "[Kr] 5s1", 1, 10, 0),
        ("Sr", "[Kr] 5s2", 0, 10, 0),
        ("Y", "[Kr] 4d1 5s2", 1, 1, 1),
        ("Zr", "[Kr] 4d2 5s2", 2, 2, 2),
        ("Nb", "[Kr] 4d4 5s1", 5, 4, 4),
        ("Mo", "[Kr] 4d5 5s1", 6, 5, 5),
        ("Tc", "[Kr] 4d5 5s2", 5, 5, 5),
        ("Ru", "[Kr] 4d7 5s1", 4, 7, 3),
        ("Rh", "[Kr] 4d8 5s1", 3, 8, 2),
        ("Pd", "[Kr] 4d10", 0, 10, 0),
        ("Ag", "[Kr] 4d10 5s1", 1, 10, 0),
        ("Cd", "[Kr] 4d10 5s2", 0, 10, 0),
        ("La", "[Xe] 5d1 6s2", 1, 1, 1),
        ("Ce", "[Xe] 4f1 5d1 6s2", 2, 1, 1),
        ("Pt", "[Xe] 4f14 5d9 6s1", 2, 9, 1),
        ("Au", "[Xe] 4f14 5d10 6s1", 1, 10, 0),
        ("Hg", "[Xe] 4f14 5d10 6s2", 0, 10, 0),
    ],
)
def test_ground_state_reference_cases(
    symbol,
    expected_noble,
    expected_unpaired,
    expected_d_electrons,
    expected_d_unpaired,
):
    result, _steps, _metadata = calculate_electron_configuration_with_steps(symbol, orbital_view="all")
    assert result["noble"] == expected_noble
    assert result["total_unpaired_electrons"] == expected_unpaired
    assert result["d_electrons"] == expected_d_electrons
    assert result["d_unpaired_electrons"] == expected_d_unpaired


def test_basic_reference_long_forms():
    assert electron_configuration(1, 0)["long"] == "1s1"
    assert electron_configuration(2, 0)["long"] == "1s2"
    assert electron_configuration(6, 0)["long"] == "1s2 2s2 2p2"
    assert electron_configuration(7, 0)["long"] == "1s2 2s2 2p3"
    assert electron_configuration(8, 0)["long"] == "1s2 2s2 2p4"
    assert electron_configuration(10, 0)["long"] == "1s2 2s2 2p6"


def test_orbital_occupancy_examples_for_2p():
    assert subshell_orbital_occupancy("p", 2) == [1, 1, 0]
    assert subshell_orbital_occupancy("p", 3) == [1, 1, 1]
    assert sorted(subshell_orbital_occupancy("p", 4)) == [1, 1, 2]


def test_regressions_never_return_known_wrong_ground_states():
    mo = electron_configuration(42, 0)
    assert mo["noble"] != "[Kr] 5s2 4d4"
    assert mo["noble"] != "[Kr] 4d4 5s2"

    cu = electron_configuration(29, 0)
    assert cu["noble"] != "[Ar] 3d9 4s2"

    cr = electron_configuration(24, 0)
    assert cr["noble"] != "[Ar] 3d4 4s2"

    pd = electron_configuration(46, 0)
    assert pd["noble"] != "[Kr] 4d8 5s2"

    ag = electron_configuration(47, 0)
    assert ag["noble"] != "[Kr] 4d9 5s2"


def test_structured_configuration_and_formatters_round_trip_for_mo():
    structured = ground_state_configuration_structured(42)
    assert format_configuration_long(structured) == "1s2 2s2 2p6 3s2 3p6 4s2 3d10 4p6 5s1 4d5"
    assert format_configuration_noble(structured) == "[Kr] 4d5 5s1"

    total_unpaired = count_total_unpaired_electrons(structured)
    d_electrons = count_d_electrons(structured)
    d_unpaired = count_d_unpaired_electrons(structured)
    assert total_unpaired == 6
    assert d_electrons == 5
    assert d_unpaired == 5


@pytest.mark.parametrize(
    "subshell,electron_count,expected_unpaired",
    [
        ("s", 0, 0), ("s", 1, 1), ("s", 2, 0),
        ("p", 0, 0), ("p", 1, 1), ("p", 2, 2), ("p", 3, 3), ("p", 4, 2), ("p", 5, 1), ("p", 6, 0),
        ("d", 0, 0), ("d", 1, 1), ("d", 2, 2), ("d", 3, 3), ("d", 4, 4), ("d", 5, 5),
        ("d", 6, 4), ("d", 7, 3), ("d", 8, 2), ("d", 9, 1), ("d", 10, 0),
    ],
)
def test_subshell_unpaired_number_invariants(subshell, electron_count, expected_unpaired):
    boxes = distribute_subshell(subshell, electron_count)
    unpaired = sum(1 for box in boxes if box == "↑")
    assert unpaired == expected_unpaired


def _electron_count_from_config_text(config_text: str) -> int:
    if config_text.startswith("["):
        if " " in config_text:
            _prefix, rest = config_text.split(" ", 1)
            tokens = rest.split()
        else:
            tokens = []
    else:
        tokens = config_text.split()

    total = 0
    for token in tokens:
        match = re.fullmatch(r"(\d)([spdf])(\d+)", token)
        assert match is not None
        total += int(match.group(3))
    return total


def test_full_and_noble_notation_have_same_electron_total_for_neutral_atoms():
    noble_core_electrons = {
        "He": 2,
        "Ne": 10,
        "Ar": 18,
        "Kr": 36,
        "Xe": 54,
        "Rn": 86,
        "Og": 118,
    }
    for z_value in range(1, 119):
        result = electron_configuration(z_value, 0)
        long_total = sum(orb["electrons"] for orb in result["orbitals"])

        noble = result["noble"]
        if noble.startswith("["):
            symbol = noble.split("]", 1)[0].strip("[")
            core_total = noble_core_electrons[symbol]
            suffix_total = _electron_count_from_config_text(noble)
            assert core_total + suffix_total == long_total
        else:
            assert _electron_count_from_config_text(noble) == long_total


def test_neutral_atom_invariants_for_all_z_1_to_118():
    capacities = {"s": 2, "p": 6, "d": 10, "f": 14}
    for z_value in range(1, 119):
        result = electron_configuration(z_value, 0)
        orbitals = result["orbitals"]

        assert sum(int(orb["electrons"]) for orb in orbitals) == z_value
        for orb in orbitals:
            subshell = str(orb["subshell"])
            electrons = int(orb["electrons"])
            assert electrons <= capacities[subshell]

            boxes = distribute_subshell(subshell, electrons)
            assert all(len(box) <= 2 for box in boxes)


def test_mo_multiple_choice_logic_prefers_option_d_example():
    # Synthetic MCQ mapping for Mo: option d is (total unpaired=6, d-electrons=5).
    result = electron_configuration(42, 0)
    options = {
        "a": (4, 4),
        "b": (5, 4),
        "c": (5, 5),
        "d": (6, 5),
    }
    observed = (result["total_unpaired_electrons"], result["d_electrons"])
    selected = next(key for key, value in options.items() if value == observed)
    assert selected == "d"


@pytest.mark.parametrize(
    "symbol,expected_long,expected_noble,expected_unpaired,expected_d_electrons,expected_d_unpaired,forbidden_noble",
    [
        ("B", "1s2 2s2 2p1", "[He] 2s2 2p1", 1, 0, 0, None),
        ("F", "1s2 2s2 2p5", "[He] 2s2 2p5", 1, 0, 0, None),
        ("Mg", "1s2 2s2 2p6 3s2", "[Ne] 3s2", 0, 0, 0, None),
        ("Al", "1s2 2s2 2p6 3s2 3p1", "[Ne] 3s2 3p1", 1, 0, 0, None),
        ("Si", "1s2 2s2 2p6 3s2 3p2", "[Ne] 3s2 3p2", 2, 0, 0, None),
        ("P", "1s2 2s2 2p6 3s2 3p3", "[Ne] 3s2 3p3", 3, 0, 0, None),
        ("S", "1s2 2s2 2p6 3s2 3p4", "[Ne] 3s2 3p4", 2, 0, 0, None),
        ("Br", "1s2 2s2 2p6 3s2 3p6 4s2 3d10 4p5", "[Ar] 3d10 4s2 4p5", 1, 10, 0, None),
        ("I", "1s2 2s2 2p6 3s2 3p6 4s2 3d10 4p6 5s2 4d10 5p5", "[Kr] 4d10 5s2 5p5", 1, 10, 0, None),
        ("Xe", "1s2 2s2 2p6 3s2 3p6 4s2 3d10 4p6 5s2 4d10 5p6", ("[Kr] 4d10 5s2 5p6", "[Xe]"), 0, 10, 0, None),
        ("Ga", "1s2 2s2 2p6 3s2 3p6 4s2 3d10 4p1", "[Ar] 3d10 4s2 4p1", 1, 10, 0, None),
        ("Ge", "1s2 2s2 2p6 3s2 3p6 4s2 3d10 4p2", "[Ar] 3d10 4s2 4p2", 2, 10, 0, None),
        ("As", "1s2 2s2 2p6 3s2 3p6 4s2 3d10 4p3", "[Ar] 3d10 4s2 4p3", 3, 10, 0, None),
        ("Se", "1s2 2s2 2p6 3s2 3p6 4s2 3d10 4p4", "[Ar] 3d10 4s2 4p4", 2, 10, 0, None),
        ("W", None, "[Xe] 4f14 5d4 6s2", 4, 4, 4, "[Xe] 4f14 5d5 6s1"),
        ("Re", None, "[Xe] 4f14 5d5 6s2", 5, 5, 5, None),
        ("Os", None, "[Xe] 4f14 5d6 6s2", 4, 6, 4, None),
        ("Ir", None, "[Xe] 4f14 5d7 6s2", 3, 7, 3, None),
        ("Pb", None, "[Xe] 4f14 5d10 6s2 6p2", 2, 10, 0, None),
        ("Bi", None, "[Xe] 4f14 5d10 6s2 6p3", 3, 10, 0, None),
    ],
)
def test_user_requested_ground_state_examples(
    symbol,
    expected_long,
    expected_noble,
    expected_unpaired,
    expected_d_electrons,
    expected_d_unpaired,
    forbidden_noble,
):
    result, _steps, _metadata = calculate_electron_configuration_with_steps(symbol, orbital_view="all")

    if expected_long is not None:
        assert result["long"] == expected_long

    if isinstance(expected_noble, tuple):
        assert result["noble"] in expected_noble
    else:
        assert result["noble"] == expected_noble
    assert result["total_unpaired_electrons"] == expected_unpaired
    assert result["d_electrons"] == expected_d_electrons
    assert result["d_unpaired_electrons"] == expected_d_unpaired

    if forbidden_noble is not None:
        assert result["noble"] != forbidden_noble


@pytest.mark.parametrize(
    "raw_input,expected_outer_shell_electrons",
    [
        ("H", 1),
        ("He", 2),
        ("Li", 1),
        ("Be", 2),
        ("B", 3),
        ("C", 4),
        ("N", 5),
        ("O", 6),
        ("F", 7),
        ("Ne", 8),
        ("Na", 1),
        ("Mg", 2),
        ("Al", 3),
        ("Si", 4),
        ("P", 5),
        ("S", 6),
        ("Cl", 7),
        ("Ar", 8),
        ("K", 1),
        ("Ca", 2),
        ("Sc", 2),
        ("Ti", 2),
        ("Cr", 1),
        ("Cr2+", 12),
        ("Fe2+", 14),
        ("Fe3+", 13),
        ("Cu+", 18),
        ("Br-", 8),
        ("O2-", 8),
        ("Xe", 8),
    ],
)
def test_outer_shell_electron_count_is_rendered_for_30_examples(raw_input, expected_outer_shell_electrons):
    result, steps, metadata = calculate_electron_configuration_with_steps(raw_input, orbital_view="all")

    assert result["outer_shell_electrons"] == expected_outer_shell_electrons
    assert metadata["outer_shell_electrons"] == expected_outer_shell_electrons
    assert any(
        f"Elektroner i yderste skal: {expected_outer_shell_electrons}" in step
        for step in steps
    )
