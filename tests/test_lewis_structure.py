"""Tests for Lewis-structure parsing and generation."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from calculators.lewis_structure import (
    LewisStructureError,
    calculate_total_valence_electrons,
    generate_resonance_structures,
    generate_lewis_structure,
    parse_species_input,
    render_lewis_structure_svg,
)


def _bond_orders_by_pair(structure):
    out = {}
    for bond in structure.bonds:
        a = structure.atoms[bond.a].symbol
        b = structure.atoms[bond.b].symbol
        key = tuple(sorted((a, b)))
        out.setdefault(key, []).append(bond.order)
    for key in out:
        out[key].sort()
    return out


def _atom_stats(structure, symbol):
    return [a for a in structure.atoms if a.symbol == symbol]


def test_parser_valid_inputs():
    parsed = parse_species_input("H2O")
    assert parsed.formula == "H2O"
    assert parsed.charge == 0
    assert parsed.element_counts == {"H": 2, "O": 1}

    parsed = parse_species_input("NO3-")
    assert parsed.formula == "NO3"
    assert parsed.charge == -1
    assert parsed.element_counts == {"N": 1, "O": 3}

    parsed = parse_species_input("NH4+")
    assert parsed.formula == "NH4"
    assert parsed.charge == 1
    assert parsed.element_counts == {"N": 1, "H": 4}

    parsed = parse_species_input("Fe3+")
    assert parsed.formula == "Fe"
    assert parsed.charge == 3
    assert parsed.element_counts == {"Fe": 1}


@pytest.mark.parametrize(
    "bad_input",
    [
        "",
        "   ",
        "H2O@",
        "2H2O",
        "^2-",
        "(())",
    ],
)
def test_parser_invalid_inputs(bad_input):
    with pytest.raises(LewisStructureError):
        parse_species_input(bad_input)


@pytest.mark.parametrize(
    "species, expected",
    [
        ("H2", 2),
        ("Cl2", 14),
        ("HCl", 8),
        ("H2O", 8),
        ("NH3", 8),
        ("CH4", 8),
        ("CO2", 16),
        ("HCN", 10),
        ("O2", 12),
        ("N2", 10),
        ("SO2", 18),
        ("NH4+", 8),
        ("NO3-", 24),
    ],
)
def test_total_valence_electrons(species, expected):
    parsed = parse_species_input(species)
    assert calculate_total_valence_electrons(parsed) == expected


@pytest.mark.parametrize(
    "species, pair_key, expected_orders",
    [
        ("H2", ("H", "H"), [1]),
        ("Cl2", ("Cl", "Cl"), [1]),
        ("HCl", ("Cl", "H"), [1]),
        ("H2O", ("H", "O"), [1, 1]),
        ("NH3", ("H", "N"), [1, 1, 1]),
        ("CH4", ("C", "H"), [1, 1, 1, 1]),
        ("CO2", ("C", "O"), [2, 2]),
        ("HCN", ("C", "H"), [1]),
        ("O2", ("O", "O"), [2]),
        ("N2", ("N", "N"), [3]),
        ("SO2", ("O", "S"), [2, 2]),
        ("NH4+", ("H", "N"), [1, 1, 1, 1]),
        ("NO3-", ("N", "O"), [1, 1, 2]),
    ],
)
def test_expected_bond_orders(species, pair_key, expected_orders):
    parsed = parse_species_input(species)
    structure = generate_lewis_structure(parsed)
    pairs = _bond_orders_by_pair(structure)
    assert pairs[pair_key] == expected_orders


@pytest.mark.parametrize(
    "species, symbol, expected_lone_pairs",
    [
        ("H2O", "O", [2]),
        ("NH3", "N", [1]),
        ("CH4", "C", [0]),
        ("CO2", "O", [2, 2]),
        ("HCN", "N", [1]),
        ("O2", "O", [2, 2]),
        ("N2", "N", [1, 1]),
        ("SO2", "S", [1]),
        ("NH4+", "N", [0]),
        ("NO3-", "O", [2, 3, 3]),
    ],
)
def test_expected_lone_pairs(species, symbol, expected_lone_pairs):
    parsed = parse_species_input(species)
    structure = generate_lewis_structure(parsed)
    lone_pairs = sorted(atom.lone_pairs for atom in _atom_stats(structure, symbol))
    assert lone_pairs == sorted(expected_lone_pairs)


@pytest.mark.parametrize(
    "species, expected_charge",
    [
        ("H2", 0),
        ("Cl2", 0),
        ("HCl", 0),
        ("H2O", 0),
        ("NH3", 0),
        ("CH4", 0),
        ("CO2", 0),
        ("HCN", 0),
        ("O2", 0),
        ("N2", 0),
        ("SO2", 0),
        ("NH4+", 1),
        ("NO3-", -1),
    ],
)
def test_formal_charge_sum_matches_species_charge(species, expected_charge):
    parsed = parse_species_input(species)
    structure = generate_lewis_structure(parsed)
    total_formal = sum(atom.formal_charge for atom in structure.atoms)
    assert total_formal == expected_charge


def test_resonance_detected_for_nitrate():
    parsed = parse_species_input("NO3-")
    structure = generate_lewis_structure(parsed)
    assert structure.resonance_forms == 3


def test_generate_resonance_structures_for_nitrate():
    parsed = parse_species_input("NO3-")
    structure = generate_lewis_structure(parsed)
    variants = generate_resonance_structures(structure, max_forms=12)
    assert len(variants) == 3


def test_svg_renderer_returns_svg_markup():
    parsed = parse_species_input("H2O")
    structure = generate_lewis_structure(parsed)
    svg = render_lewis_structure_svg(structure)
    assert "<svg" in svg
    assert "</svg>" in svg
