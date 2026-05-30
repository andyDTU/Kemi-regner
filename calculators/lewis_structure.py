"""Lewis-structure parsing and generation utilities."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import itertools
import math
from math import comb
import re
from typing import Dict, List, Optional, Tuple

from core.formula import parse_chemical_formula
from core.periodic_table import get_element_by_symbol


# ---------------------------------------------------------------------------
# Predefined topologies for multi-center / chain molecules that cannot be
# auto-inferred from sum formula alone.
# Key: (normalised_formula, charge)  e.g. ("C2O4", -2)
# Value: (atom_symbols_in_order, list_of_(a,b) bond pairs)
# ---------------------------------------------------------------------------
_PREDEFINED_TOPOLOGIES: Dict[Tuple[str, int], Tuple[List[str], List[Tuple[int, int]]]] = {
    # Oxalate C2O4^2-  /  oxalic acid C2H2O4
    #   O    O
    #   ‖    ‖
    #   C0 - C1
    #   |    |
    #   O    O
    ("C2O4", -2): (
        ["C", "C", "O", "O", "O", "O"],
        [(0, 1), (0, 2), (0, 3), (1, 4), (1, 5)],
    ),
    ("C2H2O4", 0): (
        ["C", "C", "O", "O", "O", "O", "H", "H"],
        # HO-C(=O)-C(=O)-OH  → O2 and O4 carry the H
        [(0, 1), (0, 2), (0, 3), (1, 4), (1, 5), (2, 6), (4, 7)],
    ),
    # Hydrogen peroxide  H2O2
    ("H2O2", 0): (
        ["O", "O", "H", "H"],
        [(0, 1), (0, 2), (1, 3)],
    ),
    # Dinitrogen tetroxide  N2O4
    ("N2O4", 0): (
        ["N", "N", "O", "O", "O", "O"],
        [(0, 1), (0, 2), (0, 3), (1, 4), (1, 5)],
    ),
    # Hydrazine N2H4 (also handled by star, but explicit is cleaner)
    ("N2H4", 0): (
        ["N", "N", "H", "H", "H", "H"],
        [(0, 1), (0, 2), (0, 3), (1, 4), (1, 5)],
    ),
    # Dinitrogen N2
    ("N2", 0): (
        ["N", "N"],
        [(0, 1)],
    ),
    # Ethylene C2H4  (H2C=CH2)
    ("C2H4", 0): (
        ["C", "C", "H", "H", "H", "H"],
        [(0, 1), (0, 2), (0, 3), (1, 4), (1, 5)],
    ),
    # Acetylene C2H2  (HC≡CH)
    ("C2H2", 0): (
        ["C", "C", "H", "H"],
        [(0, 1), (0, 2), (1, 3)],
    ),
    # Ethane C2H6
    ("C2H6", 0): (
        ["C", "C", "H", "H", "H", "H", "H", "H"],
        [(0, 1), (0, 2), (0, 3), (0, 4), (1, 5), (1, 6), (1, 7)],
    ),
    # Acetaldehyde CH3CHO
    ("C2H4O", 0): (
        ["C", "C", "O", "H", "H", "H", "H"],
        # CH3-CHO: C0(H,H,H)-C1(=O,H)
        [(0, 1), (1, 2), (1, 6), (0, 3), (0, 4), (0, 5)],
    ),
    # Ethylene glycol C2H6O2
    ("C2H6O2", 0): (
        ["C", "C", "O", "O", "H", "H", "H", "H", "H", "H"],
        [(0, 1), (0, 2), (0, 4), (0, 5), (1, 3), (1, 6), (1, 7), (2, 8), (3, 9)],
    ),
    # Acetic acid (also reachable as CH3COOH)
    ("C2H4O2", 0): (
        ["C", "C", "O", "O", "H", "H", "H", "H"],
        # CH3-C(=O)-OH: C0(H,H,H)-C1(=O2,O3H)
        [(0, 1), (1, 2), (1, 3), (0, 4), (0, 5), (0, 6), (3, 7)],
    ),
    # Thiosulfate S2O3^2-
    ("S2O3", -2): (
        ["S", "S", "O", "O", "O"],
        # Central S0, terminal S1 and three O
        [(0, 1), (0, 2), (0, 3), (0, 4)],
    ),
    # Peroxodisulfate S2O8^2-
    ("S2O8", -2): (
        ["S", "S", "O", "O", "O", "O", "O", "O", "O", "O"],
        [(0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (1, 6), (1, 7), (1, 8), (1, 9)],
    ),
    # Dichromate Cr2O7^2-
    ("Cr2O7", -2): (
        ["Cr", "Cr", "O", "O", "O", "O", "O", "O", "O"],
        # Cr0-O2(bridge)-Cr1, each Cr has 3 more terminal O
        [(0, 2), (1, 2), (0, 3), (0, 4), (0, 5), (1, 6), (1, 7), (1, 8)],
    ),
}

HALOGENS = {"F", "Cl", "Br", "I", "At", "Ts"}
ELECTRONEGATIVITY = {
    "H": 2.20,
    "B": 2.04,
    "C": 2.55,
    "N": 3.04,
    "O": 3.44,
    "F": 3.98,
    "P": 2.19,
    "S": 2.58,
    "Cl": 3.16,
    "Br": 2.96,
    "I": 2.66,
    "Si": 1.90,
}


class LewisStructureError(ValueError):
    """Raised when a Lewis structure cannot be generated safely."""


@dataclass(frozen=True)
class ParsedSpecies:
    raw_input: str
    formula: str
    element_counts: Dict[str, int]
    ordered_symbols: List[str]
    charge: int


@dataclass
class AtomState:
    index: int
    symbol: str
    lone_pairs: int = 0
    formal_charge: int = 0


@dataclass
class BondState:
    a: int
    b: int
    order: int


@dataclass
class LewisStructure:
    parsed: ParsedSpecies
    atoms: List[AtomState]
    bonds: List[BondState]
    total_valence_electrons: int
    resonance_forms: int
    warnings: List[str]


def _valence_electrons_for_symbol(symbol: str) -> int:
    entry = get_element_by_symbol(symbol)
    if not entry:
        raise LewisStructureError(f"Ukendt grundstof: {symbol}")

    if symbol == "He":
        return 2

    shells = entry.get("shells") or []
    if shells:
        outer = int(shells[-1])
        return max(0, min(8, outer))

    group = entry.get("group")
    if isinstance(group, int):
        if 1 <= group <= 2:
            return group
        if 13 <= group <= 18:
            return group - 10
    raise LewisStructureError(f"Kan ikke bestemme valenselektroner for {symbol}")


def _period_for_symbol(symbol: str) -> int:
    entry = get_element_by_symbol(symbol)
    period = entry.get("period") if entry else None
    return int(period) if isinstance(period, int) else 2


def parse_species_input(raw: str) -> ParsedSpecies:
    text = (raw or "").strip()
    if not text:
        raise LewisStructureError("Input er tomt. Indtast en molekylformel.")

    formula, charge = _split_formula_and_charge(text)
    if not formula:
        raise LewisStructureError("Mangler kemisk formel før ladning.")

    if formula[0].isdigit():
        raise LewisStructureError("Ledende koefficienter understøttes ikke i Lewis-input (fx 2H2O).")

    if not re.fullmatch(r"[A-Za-z0-9()]+", formula):
        raise LewisStructureError("Formlen indeholder ugyldige tegn.")

    try:
        element_counts = parse_chemical_formula(formula)
    except ValueError as exc:
        raise LewisStructureError(f"Kunne ikke fortolke formel: {exc}") from exc

    ordered_symbols = re.findall(r"[A-Z][a-z]?", formula)
    if not ordered_symbols:
        raise LewisStructureError("Ingen gyldige atomsymboler fundet.")

    for symbol in element_counts:
        if not get_element_by_symbol(symbol):
            raise LewisStructureError(f"Ukendt grundstof: {symbol}")

    return ParsedSpecies(
        raw_input=text,
        formula=formula,
        element_counts=element_counts,
        ordered_symbols=ordered_symbols,
        charge=charge,
    )


def _split_formula_and_charge(text: str) -> Tuple[str, int]:
    # e.g. SO4^2-, NH4+, NO3-, Fe+2, Fe-3
    m = re.fullmatch(r"(.+?)\^(\d+)([+-])", text)
    if m:
        sign = 1 if m.group(3) == "+" else -1
        return m.group(1), sign * int(m.group(2))

    m = re.fullmatch(r"(.+?)([+-])(\d+)", text)
    if m:
        sign = 1 if m.group(2) == "+" else -1
        return m.group(1), sign * int(m.group(3))

    # Support monoatomic ion notation like Fe3+ or O2-.
    m = re.fullmatch(r"([A-Z][a-z]?)(\d+)([+-])", text)
    if m:
        sign = 1 if m.group(3) == "+" else -1
        return m.group(1), sign * int(m.group(2))

    m = re.fullmatch(r"(.+?)([+-])", text)
    if m:
        sign = 1 if m.group(2) == "+" else -1
        return m.group(1), sign

    return text, 0


def calculate_total_valence_electrons(parsed: ParsedSpecies) -> int:
    total = 0
    for symbol, count in parsed.element_counts.items():
        total += _valence_electrons_for_symbol(symbol) * count
    total -= parsed.charge
    return total


def _expanded_atom_symbols(parsed: ParsedSpecies) -> List[str]:
    symbols: List[str] = []
    for symbol, count in parsed.element_counts.items():
        symbols.extend([symbol] * int(count))
    return symbols


def _select_central_symbol(parsed: ParsedSpecies) -> Optional[str]:
    expanded = _expanded_atom_symbols(parsed)
    if len(expanded) <= 2:
        return None

    counts = parsed.element_counts
    non_h = [s for s in expanded if s != "H"]
    if not non_h:
        return None

    if counts.get("C", 0) == 1:
        return "C"

    order_rank = {s: i for i, s in enumerate(parsed.ordered_symbols)}

    unique_non_h = []
    for s in parsed.ordered_symbols:
        if s != "H" and s not in unique_non_h:
            unique_non_h.append(s)

    candidates = [s for s in unique_non_h if counts.get(s, 0) == 1 and s not in HALOGENS]
    if candidates:
        candidates.sort(key=lambda s: (ELECTRONEGATIVITY.get(s, 99.0), order_rank.get(s, 999)))
        return candidates[0]

    fallback = [s for s in unique_non_h if s not in HALOGENS]
    if fallback:
        return fallback[0]
    return unique_non_h[0]


def _target_electrons(symbol: str) -> int:
    return 2 if symbol == "H" else 8


def _find_bond(atom_a: int, atom_b: int, bonds: List[BondState]) -> BondState:
    for bond in bonds:
        if (bond.a == atom_a and bond.b == atom_b) or (bond.a == atom_b and bond.b == atom_a):
            return bond
    raise LewisStructureError("Intern fejl: binding ikke fundet")


def _bonding_electrons(index: int, bonds: List[BondState]) -> int:
    total = 0
    for bond in bonds:
        if bond.a == index or bond.b == index:
            total += 2 * bond.order
    return total


def _electrons_around(atom: AtomState, bonds: List[BondState]) -> int:
    return 2 * atom.lone_pairs + _bonding_electrons(atom.index, bonds)


def _compute_formal_charges(atoms: List[AtomState], bonds: List[BondState]) -> None:
    for atom in atoms:
        valence = _valence_electrons_for_symbol(atom.symbol)
        nonbonding = 2 * atom.lone_pairs
        bonding = _bonding_electrons(atom.index, bonds)
        atom.formal_charge = int(valence - (nonbonding + bonding / 2))


def _score_formal_charges(atoms: List[AtomState]) -> int:
    return sum(abs(atom.formal_charge) for atom in atoms)


def _formal_charge_preference_score(atoms: List[AtomState], bonds: List[BondState]) -> Tuple[int, int, int, int]:
    """Lexicographic score encoding formal-charge preference rules.

    Lower is better for each field in this order:
    1) number of atoms with nonzero formal charge
    2) total absolute formal charge
    3) adjacent like-sign formal charges (penalized)
    4) electronegativity-misaligned charge placement (penalized)
    """
    nonzero_count = sum(1 for atom in atoms if atom.formal_charge != 0)
    abs_sum = sum(abs(atom.formal_charge) for atom in atoms)

    by_index = {atom.index: atom for atom in atoms}
    adjacency_penalty = 0
    electroneg_penalty = 0

    for bond in bonds:
        a = by_index[bond.a]
        b = by_index[bond.b]
        qa = a.formal_charge
        qb = b.formal_charge

        if qa != 0 and qb != 0 and qa * qb > 0:
            adjacency_penalty += 1

        ena = ELECTRONEGATIVITY.get(a.symbol, 2.5)
        enb = ELECTRONEGATIVITY.get(b.symbol, 2.5)

        if qa < 0 and qb >= 0 and ena < enb:
            electroneg_penalty += 1
        if qb < 0 and qa >= 0 and enb < ena:
            electroneg_penalty += 1

        if qa > 0 and qb <= 0 and ena > enb:
            electroneg_penalty += 1
        if qb > 0 and qa <= 0 and enb > ena:
            electroneg_penalty += 1

    return (nonzero_count, abs_sum, adjacency_penalty, electroneg_penalty)


def _build_diatomic(parsed: ParsedSpecies) -> LewisStructure:
    expanded = _expanded_atom_symbols(parsed)
    if len(expanded) != 2:
        raise LewisStructureError("Diatomisk bygning kræver præcis 2 atomer")

    atoms = [AtomState(index=i, symbol=s) for i, s in enumerate(expanded)]
    total = calculate_total_valence_electrons(parsed)
    warnings: List[str] = []

    best: Optional[Tuple[Tuple[int, int, int, int, int, int], List[AtomState], List[BondState]]] = None

    for order in (1, 2, 3):
        used_bond = 2 * order
        remaining = total - used_bond
        if remaining < 0 or remaining % 2 != 0:
            continue

        candidate_atoms = [AtomState(index=atom.index, symbol=atom.symbol) for atom in atoms]
        candidate_bonds = [BondState(a=0, b=1, order=order)]

        # Fill octet/duet on atom 0 then atom 1
        ok = True
        for atom in candidate_atoms:
            need = _target_electrons(atom.symbol) - _electrons_around(atom, candidate_bonds)
            if need < 0 or need % 2 != 0:
                ok = False
                break
            assign = min(need, remaining)
            atom.lone_pairs += assign // 2
            remaining -= assign

        if not ok:
            continue

        if remaining:
            candidate_atoms[0].lone_pairs += remaining // 2
            remaining = 0

        _compute_formal_charges(candidate_atoms, candidate_bonds)
        score = _formal_charge_preference_score(candidate_atoms, candidate_bonds)
        penalty = 0 if all(_electrons_around(a, candidate_bonds) >= _target_electrons(a.symbol) for a in candidate_atoms if a.symbol != "H") else 10

        key = (penalty, *score, -order)
        if best is None or key < best[0]:
            best = (key, candidate_atoms, candidate_bonds)

    if best is None:
        raise LewisStructureError("Kunne ikke finde en kemisk rimelig diatomisk Lewis-struktur.")

    atoms_out = best[1]
    bonds_out = best[2]
    _compute_formal_charges(atoms_out, bonds_out)
    return LewisStructure(parsed=parsed, atoms=atoms_out, bonds=bonds_out, total_valence_electrons=total, resonance_forms=1, warnings=warnings)


def _build_star(parsed: ParsedSpecies) -> LewisStructure:
    expanded = _expanded_atom_symbols(parsed)
    central_symbol = _select_central_symbol(parsed)
    if not central_symbol:
        raise LewisStructureError("Kunne ikke identificere et centralt atom for strukturen.")

    atoms = [AtomState(index=i, symbol=s) for i, s in enumerate(expanded)]
    central_index = next((a.index for a in atoms if a.symbol == central_symbol), None)
    if central_index is None:
        raise LewisStructureError("Intern fejl: centralt atom findes ikke i atomlisten")

    terminal_indices = [a.index for a in atoms if a.index != central_index]
    bonds = [BondState(a=central_index, b=i, order=1) for i in terminal_indices]
    total = calculate_total_valence_electrons(parsed)
    remaining = total - 2 * len(bonds)
    warnings: List[str] = []

    if remaining < 0:
        raise LewisStructureError("For få valenselektroner til at oprette basisbindinger.")

    # Fill terminal atoms first.
    for idx in terminal_indices:
        atom = atoms[idx]
        need = _target_electrons(atom.symbol) - _electrons_around(atom, bonds)
        if need < 0:
            raise LewisStructureError("Ugyldig elektronfordeling ved terminalatom.")
        use = min(need, remaining)
        if use % 2 != 0:
            use -= 1
        atom.lone_pairs += max(0, use // 2)
        remaining -= max(0, use)

    if remaining % 2 != 0:
        warnings.append("Uparret elektron fundet; resultatet kan være usikkert.")

    atoms[central_index].lone_pairs += max(0, remaining // 2)

    # Enforce central octet where possible by promoting terminal lone pairs into multiple bonds.
    central = atoms[central_index]
    central_target = _target_electrons(central.symbol)
    deficit = central_target - _electrons_around(central, bonds)

    while deficit > 0:
        best_move: Optional[int] = None
        best_score: Optional[int] = None
        for tidx in terminal_indices:
            term = atoms[tidx]
            bond = _find_bond(central_index, tidx, bonds)
            if term.symbol == "H":
                continue
            if term.lone_pairs <= 0 or bond.order >= 3:
                continue

            # Simulate this promotion and keep the most charge-balanced option.
            term.lone_pairs -= 1
            bond.order += 1
            _compute_formal_charges(atoms, bonds)
            score = _formal_charge_preference_score(atoms, bonds)
            bond.order -= 1
            term.lone_pairs += 1

            if best_score is None or score < best_score:
                best_score = score
                best_move = tidx

        if best_move is None:
            warnings.append("Kunne ikke opfylde central oktet fuldt ud med rimelige bindinger.")
            break

        chosen_term = atoms[best_move]
        chosen_bond = _find_bond(central_index, best_move, bonds)
        chosen_term.lone_pairs -= 1
        chosen_bond.order += 1

        deficit = central_target - _electrons_around(central, bonds)

    _compute_formal_charges(atoms, bonds)

    # Optional formal-charge optimization with expanded octet for period >= 3 central atoms.
    central_period = _period_for_symbol(central.symbol)
    if central_period >= 3:
        improved = True
        while improved:
            improved = False
            baseline = _formal_charge_preference_score(atoms, bonds)
            best_move: Optional[int] = None
            best_score = baseline

            for tidx in terminal_indices:
                term = atoms[tidx]
                bond = _find_bond(central_index, tidx, bonds)
                if term.symbol == "H" or term.lone_pairs <= 0 or bond.order >= 3:
                    continue

                # Simulate one promotion.
                term.lone_pairs -= 1
                bond.order += 1
                _compute_formal_charges(atoms, bonds)
                score = _formal_charge_preference_score(atoms, bonds)

                if score < best_score:
                    best_score = score
                    best_move = tidx

                # Revert
                bond.order -= 1
                term.lone_pairs += 1
                _compute_formal_charges(atoms, bonds)

            if best_move is not None:
                term = atoms[best_move]
                bond = _find_bond(central_index, best_move, bonds)
                term.lone_pairs -= 1
                bond.order += 1
                _compute_formal_charges(atoms, bonds)
                improved = True

    resonance_forms = _estimate_resonance_forms(central_index, atoms, bonds)

    # Validate charge consistency.
    charge_sum = sum(atom.formal_charge for atom in atoms)
    if charge_sum != parsed.charge:
        warnings.append(
            f"Formelle ladninger summerer til {charge_sum:+d}, forventet {parsed.charge:+d}."
        )

    return LewisStructure(
        parsed=parsed,
        atoms=atoms,
        bonds=bonds,
        total_valence_electrons=total,
        resonance_forms=resonance_forms,
        warnings=warnings,
    )


def _build_from_topology(
    parsed: ParsedSpecies,
    atom_symbols: List[str],
    connectivity: List[Tuple[int, int]],
) -> LewisStructure:
    """Build a Lewis structure from an explicit atom list and bond connectivity."""
    atoms = [AtomState(index=i, symbol=s) for i, s in enumerate(atom_symbols)]
    bonds = [BondState(a=a, b=b, order=1) for a, b in connectivity]
    total = calculate_total_valence_electrons(parsed)
    remaining = total - 2 * len(bonds)
    warnings: List[str] = []

    if remaining < 0:
        warnings.append("For få valenselektroner til basisbindinger – tjek formel/ladning.")
        remaining = 0

    # Identify terminal vs internal atoms by degree
    degree: Counter = Counter()
    for a, b in connectivity:
        degree[a] += 1
        degree[b] += 1

    terminal_indices = [i for i in range(len(atoms)) if degree[i] == 1]
    internal_indices = [i for i in range(len(atoms)) if degree[i] > 1]

    # Fill terminals first (H doesn't need extra pairs)
    for idx in terminal_indices:
        atom = atoms[idx]
        need = _target_electrons(atom.symbol) - _electrons_around(atom, bonds)
        use = min(max(0, need), remaining)
        if use % 2 != 0:
            use -= 1
        atom.lone_pairs += use // 2
        remaining -= use

    # Distribute remainder to internal atoms
    for idx in internal_indices:
        atom = atoms[idx]
        need = _target_electrons(atom.symbol) - _electrons_around(atom, bonds)
        use = min(max(0, need), remaining)
        if use % 2 != 0:
            use -= 1
        atom.lone_pairs += use // 2
        remaining -= use

    # Promote lone pairs to multiple bonds to satisfy octets, iterating over
    # each internal (non-H) atom as the "central" atom in turn.
    for central_index in internal_indices:
        central = atoms[central_index]
        if central.symbol == "H":
            continue
        central_target = _target_electrons(central.symbol)
        neighbors = [b.b if b.a == central_index else b.a
                     for b in bonds if central_index in (b.a, b.b)]

        deficit = central_target - _electrons_around(central, bonds)
        iterations = 0
        while deficit > 0 and iterations < 20:
            iterations += 1
            best_move: Optional[int] = None
            best_score: Optional[tuple] = None
            for tidx in neighbors:
                term = atoms[tidx]
                bond = _find_bond(central_index, tidx, bonds)
                if term.symbol == "H" or term.lone_pairs <= 0 or bond.order >= 3:
                    continue
                term.lone_pairs -= 1
                bond.order += 1
                _compute_formal_charges(atoms, bonds)
                score = _formal_charge_preference_score(atoms, bonds)
                bond.order -= 1
                term.lone_pairs += 1
                _compute_formal_charges(atoms, bonds)
                if best_score is None or score < best_score:
                    best_score = score
                    best_move = tidx
            if best_move is None:
                break
            b = _find_bond(central_index, best_move, bonds)
            atoms[best_move].lone_pairs -= 1
            b.order += 1
            _compute_formal_charges(atoms, bonds)
            deficit = central_target - _electrons_around(central, bonds)

    _compute_formal_charges(atoms, bonds)

    charge_sum = sum(atom.formal_charge for atom in atoms)
    if charge_sum != parsed.charge:
        warnings.append(
            f"Formelle ladninger summerer til {charge_sum:+d}, forventet {parsed.charge:+d}."
        )

    # Simple resonance estimate for symmetric internal atoms
    resonance_forms = 1
    if len(internal_indices) == 1:
        resonance_forms = _estimate_resonance_forms(internal_indices[0], atoms, bonds)

    return LewisStructure(
        parsed=parsed,
        atoms=atoms,
        bonds=bonds,
        total_valence_electrons=total,
        resonance_forms=resonance_forms,
        warnings=warnings,
    )


def _estimate_resonance_forms(central_index: int, atoms: List[AtomState], bonds: List[BondState]) -> int:
    # Heuristic: equivalent terminal atoms with same symbol where k double bonds can be distributed.
    terminal_groups: Dict[str, List[BondState]] = {}
    for bond in bonds:
        if bond.a == central_index:
            tidx = bond.b
        elif bond.b == central_index:
            tidx = bond.a
        else:
            continue
        symbol = atoms[tidx].symbol
        terminal_groups.setdefault(symbol, []).append(bond)

    forms = 1
    for symbol, group_bonds in terminal_groups.items():
        if len(group_bonds) <= 1:
            continue
        k = sum(1 for bond in group_bonds if bond.order >= 2)
        n = len(group_bonds)
        if 0 < k < n:
            forms *= comb(n, k)

    return max(1, forms)


def _equivalent_terminal_groups(structure: LewisStructure) -> List[Tuple[int, str, List[int]]]:
    """Return groups as (center_idx, terminal_symbol, bond_indexes)."""
    bonds = structure.bonds
    atoms = structure.atoms

    degree = {atom.index: 0 for atom in atoms}
    for bond in bonds:
        degree[bond.a] += 1
        degree[bond.b] += 1
    center = max(degree.keys(), key=lambda idx: degree[idx])

    by_symbol: Dict[str, List[int]] = {}
    for i, bond in enumerate(bonds):
        if bond.a == center:
            terminal = bond.b
        elif bond.b == center:
            terminal = bond.a
        else:
            continue
        symbol = atoms[terminal].symbol
        by_symbol.setdefault(symbol, []).append(i)

    groups: List[Tuple[int, str, List[int]]] = []
    for symbol, indexes in by_symbol.items():
        if len(indexes) > 1:
            groups.append((center, symbol, indexes))
    return groups


def generate_resonance_structures(
    structure: LewisStructure,
    max_forms: int = 12,
) -> List[LewisStructure]:
    """Generate explicit resonance variants by permuting multiple-bond placement in equivalent terminal groups."""
    if structure.resonance_forms <= 1:
        return [structure]

    groups = _equivalent_terminal_groups(structure)
    if not groups:
        return [structure]

    # Build choices per group: all ways to place the same number of order>=2 bonds.
    group_choices: List[List[Tuple[int, ...]]] = []
    for _center, _symbol, bond_indexes in groups:
        k = sum(1 for bi in bond_indexes if structure.bonds[bi].order >= 2)
        n = len(bond_indexes)
        if k <= 0 or k >= n:
            group_choices.append([tuple(bond_indexes[:k])])
            continue
        combos = [tuple(choice) for choice in itertools.combinations(bond_indexes, k)]
        group_choices.append(combos)

    variants: List[LewisStructure] = []
    seen_signatures: set[str] = set()

    for selection in itertools.product(*group_choices):
        selected_by_group = {gi: set(sel) for gi, sel in enumerate(selection)}

        atoms = [
            AtomState(index=a.index, symbol=a.symbol, lone_pairs=a.lone_pairs, formal_charge=a.formal_charge)
            for a in structure.atoms
        ]
        bonds = [BondState(a=b.a, b=b.b, order=b.order) for b in structure.bonds]

        # Reset orders within resonance-active groups to 1/2 only based on selected set.
        for gi, (_center, _symbol, bond_indexes) in enumerate(groups):
            for bi in bond_indexes:
                bonds[bi].order = 2 if bi in selected_by_group[gi] else 1

        # Recompute lone pairs from valence + formal-charge relation with neutral assumptions.
        for atom in atoms:
            valence = _valence_electrons_for_symbol(atom.symbol)
            bonding = 0
            for bond in bonds:
                if bond.a == atom.index or bond.b == atom.index:
                    bonding += 2 * bond.order
            nonbonding = valence - bonding / 2
            atom.lone_pairs = max(0, int(round(nonbonding / 2)))

        _compute_formal_charges(atoms, bonds)

        signature = ",".join(
            f"{min(b.a,b.b)}-{max(b.a,b.b)}:{b.order}" for b in sorted(bonds, key=lambda x: (min(x.a, x.b), max(x.a, x.b)))
        )
        if signature in seen_signatures:
            continue
        seen_signatures.add(signature)

        variants.append(
            LewisStructure(
                parsed=structure.parsed,
                atoms=atoms,
                bonds=bonds,
                total_valence_electrons=structure.total_valence_electrons,
                resonance_forms=structure.resonance_forms,
                warnings=list(structure.warnings),
            )
        )

        if len(variants) >= max_forms:
            break

    return variants or [structure]


def _validate_supported_complexity(parsed: ParsedSpecies) -> None:
    """Reject ambiguous molecular formulas where connectivity cannot be inferred safely."""
    non_h = {symbol: count for symbol, count in parsed.element_counts.items() if symbol != "H"}
    repeated_non_h = [symbol for symbol, count in non_h.items() if count > 1]

    # Example: C6H12O6 has multiple repeated heavy-element groups and cannot be
    # mapped to one unique Lewis structure from sum formula alone.
    if len(non_h) >= 2 and len(repeated_non_h) >= 2:
        raise LewisStructureError(
            "Formlen er tvetydig for Lewis-struktur ud fra sumformel alene. "
            "Brug en enklere art (fx CO2, NO3-, NH4+) eller angiv struktur mere specifikt."
        )


def _build_atom_positions(structure: LewisStructure) -> Dict[int, Tuple[float, float]]:
    atoms = structure.atoms
    bonds = structure.bonds
    n_atoms = len(atoms)

    if n_atoms == 2:
        return {atoms[0].index: (130.0, 140.0), atoms[1].index: (290.0, 140.0)}

    degree: Dict[int, int] = {atom.index: 0 for atom in atoms}
    for bond in bonds:
        degree[bond.a] += 1
        degree[bond.b] += 1

    max_degree = max(degree.values())
    centers = [idx for idx, d in degree.items() if d == max_degree]

    # ── Two-center chain layout (e.g. C2O4^2-, H2O2, N2H4) ───────────────
    if len(centers) == 2:
        c0, c1 = centers[0], centers[1]
        positions: Dict[int, Tuple[float, float]] = {}
        positions[c0] = (155.0, 150.0)
        positions[c1] = (265.0, 150.0)

        terminals_c0 = [b.b if b.a == c0 else b.a
                        for b in bonds if c0 in (b.a, b.b) and (b.b if b.a == c0 else b.a) != c1]
        terminals_c1 = [b.b if b.a == c1 else b.a
                        for b in bonds if c1 in (b.a, b.b) and (b.b if b.a == c1 else b.a) != c0]

        radius = 90.0
        # Spread terminals of c0 to the LEFT, terminals of c1 to the RIGHT
        base_angle_c0 = math.pi           # pointing left
        base_angle_c1 = 0.0               # pointing right
        spread = math.pi * 0.65           # ~117° total spread

        for i, tidx in enumerate(terminals_c0):
            n = len(terminals_c0)
            angle = base_angle_c0 + spread * ((i / max(n - 1, 1)) - 0.5)
            positions[tidx] = (155.0 + radius * math.cos(angle),
                               150.0 + radius * math.sin(angle))
        for i, tidx in enumerate(terminals_c1):
            n = len(terminals_c1)
            angle = base_angle_c1 + spread * ((i / max(n - 1, 1)) - 0.5)
            positions[tidx] = (265.0 + radius * math.cos(angle),
                               150.0 + radius * math.sin(angle))
        return positions

    # ── Standard star layout ──────────────────────────────────────────────
    center_index = centers[0]
    positions = {}
    positions[center_index] = (210.0, 150.0)

    others = [atom.index for atom in atoms if atom.index != center_index]
    if not others:
        return positions

    radius = 120.0 if len(others) > 2 else 95.0
    for i, atom_index in enumerate(others):
        angle = (2.0 * math.pi * i) / len(others)
        x = 210.0 + radius * math.cos(angle)
        y = 150.0 + radius * math.sin(angle)
        positions[atom_index] = (x, y)

    return positions


def _bond_lines_svg(x1: float, y1: float, x2: float, y2: float, order: int) -> str:
    dx = x2 - x1
    dy = y2 - y1
    length = math.hypot(dx, dy)
    if length <= 1e-9:
        return ""

    # Trim lines so bonds end just outside atom labels.
    atom_pad = 18.0
    if length > 2.0 * atom_pad:
        ux = dx / length
        uy = dy / length
        x1 = x1 + ux * atom_pad
        y1 = y1 + uy * atom_pad
        x2 = x2 - ux * atom_pad
        y2 = y2 - uy * atom_pad
        dx = x2 - x1
        dy = y2 - y1
        length = math.hypot(dx, dy)
        if length <= 1e-9:
            return ""

    ox = -dy / length * 4.0
    oy = dx / length * 4.0

    offsets = [0.0]
    if order == 2:
        offsets = [-1.0, 1.0]
    elif order >= 3:
        offsets = [-1.0, 0.0, 1.0]

    parts: List[str] = []
    for offset in offsets:
        sx1 = x1 + ox * offset
        sy1 = y1 + oy * offset
        sx2 = x2 + ox * offset
        sy2 = y2 + oy * offset
        parts.append(
            f"<line x1='{sx1:.2f}' y1='{sy1:.2f}' x2='{sx2:.2f}' y2='{sy2:.2f}' "
            "stroke='#1f2937' stroke-width='2' stroke-linecap='round'/>"
        )

    return "".join(parts)


def _angular_distance(a: float, b: float) -> float:
    diff = abs(a - b) % (2.0 * math.pi)
    return min(diff, 2.0 * math.pi - diff)


def _lone_pair_angles(atom: AtomState, structure: LewisStructure, positions: Dict[int, Tuple[float, float]]) -> List[float]:
    if atom.lone_pairs <= 0:
        return []

    x, y = positions[atom.index]
    occupied: List[float] = []
    for bond in structure.bonds:
        if bond.a == atom.index:
            nx, ny = positions[bond.b]
            occupied.append(math.atan2(ny - y, nx - x))
        elif bond.b == atom.index:
            nx, ny = positions[bond.a]
            occupied.append(math.atan2(ny - y, nx - x))

    slot_angles = [
        0.0,
        math.pi / 2.0,
        math.pi,
        3.0 * math.pi / 2.0,
        math.pi / 4.0,
        3.0 * math.pi / 4.0,
        5.0 * math.pi / 4.0,
        7.0 * math.pi / 4.0,
    ]

    scored: List[Tuple[float, float]] = []
    for slot in slot_angles:
        if not occupied:
            score = math.pi
        else:
            score = min(_angular_distance(slot, occ) for occ in occupied)
        scored.append((score, slot))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [slot for _score, slot in scored[: atom.lone_pairs]]


def _lone_pairs_svg(atom: AtomState, structure: LewisStructure, positions: Dict[int, Tuple[float, float]]) -> str:
    x, y = positions[atom.index]
    parts: List[str] = []

    for angle in _lone_pair_angles(atom, structure, positions):
        cx = x + 22.0 * math.cos(angle)
        cy = y + 22.0 * math.sin(angle)
        px = -math.sin(angle)
        py = math.cos(angle)
        d = 3.0

        d1x = cx + px * d
        d1y = cy + py * d
        d2x = cx - px * d
        d2y = cy - py * d

        parts.append(f"<circle cx='{d1x:.2f}' cy='{d1y:.2f}' r='1.6' fill='#111827'/>")
        parts.append(f"<circle cx='{d2x:.2f}' cy='{d2y:.2f}' r='1.6' fill='#111827'/>")

    return "".join(parts)


def render_lewis_structure_svg(structure: LewisStructure) -> str:
    """Render a compact SVG drawing of the full Lewis structure."""
    positions = _build_atom_positions(structure)

    bond_parts: List[str] = []
    for bond in structure.bonds:
        x1, y1 = positions[bond.a]
        x2, y2 = positions[bond.b]
        bond_parts.append(_bond_lines_svg(x1, y1, x2, y2, bond.order))

    atom_parts: List[str] = []
    for atom in structure.atoms:
        x, y = positions[atom.index]
        atom_parts.append(_lone_pairs_svg(atom, structure, positions))
        atom_parts.append(
            f"<circle cx='{x:.2f}' cy='{y:.2f}' r='13.5' fill='#ffffff'/>"
        )
        atom_parts.append(
            f"<text x='{x:.2f}' y='{y:.2f}' text-anchor='middle' dominant-baseline='middle' "
            "font-size='20' font-weight='600' fill='#0f172a'>"
            f"{atom.symbol}</text>"
        )

        if atom.formal_charge != 0:
            fc = atom.formal_charge
            fc_text = f"{abs(fc)}+" if fc > 0 and abs(fc) > 1 else ("+" if fc > 0 else (f"{abs(fc)}-" if abs(fc) > 1 else "-"))
            atom_parts.append(
                f"<text x='{x + 12.0:.2f}' y='{y - 14.0:.2f}' text-anchor='start' "
                "font-size='12' font-weight='600' fill='#334155'>"
                f"{fc_text}</text>"
            )

    resonance_label = ""
    if structure.resonance_forms > 1:
        resonance_label = (
            f"<text x='12' y='292' text-anchor='start' font-size='12' fill='#334155'>"
            f"Resonansformer: {structure.resonance_forms}</text>"
        )

    return (
        "<div style='display:flex;justify-content:center;padding:0.25rem 0 0.5rem 0;'>"
        "<svg viewBox='0 0 420 300' width='100%' style='max-width:640px;background:#ffffff;border:1px solid #e2e8f0;border-radius:10px;'>"
        + "".join(bond_parts)
        + "".join(atom_parts)
        + resonance_label
        + "</svg></div>"
    )


def generate_lewis_structure(parsed: ParsedSpecies) -> LewisStructure:
    expanded = _expanded_atom_symbols(parsed)
    if len(expanded) < 2:
        raise LewisStructureError("Lewis-struktur kræver mindst to atomer.")

    # Check predefined topology table first
    key = (parsed.formula, parsed.charge)
    if key in _PREDEFINED_TOPOLOGIES:
        atom_symbols, connectivity = _PREDEFINED_TOPOLOGIES[key]
        return _build_from_topology(parsed, atom_symbols, connectivity)

    if len(expanded) == 2:
        return _build_diatomic(parsed)

    return _build_star(parsed)


def render_lewis_structure_text(structure: LewisStructure) -> str:
    parsed = structure.parsed
    lines: List[str] = []

    lines.append(f"Input: {parsed.raw_input}")
    lines.append(f"Fortolket formel: {parsed.formula}")
    lines.append(f"Samlet ladning: {parsed.charge:+d}")
    lines.append(f"Valenselektroner i alt: {structure.total_valence_electrons}")
    lines.append("")

    lines.append("Bindinger:")
    for bond in structure.bonds:
        a = structure.atoms[bond.a]
        b = structure.atoms[bond.b]
        label = {1: "enkelt", 2: "dobbelt", 3: "tripel"}.get(bond.order, str(bond.order))
        lines.append(f"- {a.symbol}{a.index + 1} - {b.symbol}{b.index + 1}: {label}")

    lines.append("")
    lines.append("Atomer:")
    lines.append("- symbol(index) | lone pairs | formel ladning")
    for atom in structure.atoms:
        lines.append(
            f"- {atom.symbol}({atom.index + 1}) | {atom.lone_pairs} | {atom.formal_charge:+d}"
        )

    if structure.resonance_forms > 1:
        lines.append("")
        lines.append(f"Resonans: {structure.resonance_forms} rimelige resonansformer fundet.")

    if structure.warnings:
        lines.append("")
        lines.append("Advarsler:")
        for warning in structure.warnings:
            lines.append(f"- {warning}")

    return "\n".join(lines)


def calculate_lewis_structure_with_steps(raw_input: str) -> Tuple[LewisStructure, List[str]]:
    steps: List[str] = []

    parsed = parse_species_input(raw_input)
    steps.append(f"Parsed input: formel={parsed.formula}, ladning={parsed.charge:+d}")

    # Skip complexity check for predefined topologies
    key = (parsed.formula, parsed.charge)
    if key not in _PREDEFINED_TOPOLOGIES:
        _validate_supported_complexity(parsed)
    steps.append("Input-kompleksitet valideret for entydig Lewis-struktur.")

    total_valence = calculate_total_valence_electrons(parsed)
    steps.append(f"Total valenselektroner: {total_valence}")

    structure = generate_lewis_structure(parsed)
    steps.append("Basisstruktur opbygget med enkeltbindinger og elektronfordeling.")
    steps.append("Formelle ladninger beregnet og struktur optimeret.")

    if structure.resonance_forms > 1:
        steps.append(f"Resonansdetektion: {structure.resonance_forms} mulige resonansformer.")

    if structure.warnings:
        for warning in structure.warnings:
            steps.append(f"Advarsel: {warning}")

    return structure, steps
