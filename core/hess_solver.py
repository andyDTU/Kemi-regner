"""
Hess' law solver using exact rational arithmetic.

Given a target reaction and a set of known reactions with ΔH°, this module
finds coefficients x such that A*x = b where each reaction is represented as
species stoichiometry vectors (reactants negative, products positive).
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math
import re
from typing import Any, Dict, List, Tuple

from core.reaction_enthalpy import parseReaction

_SPECIES_KEY_PATTERN = re.compile(r"^(.+)\((s|l|g|aq)\)$", re.IGNORECASE)


def _normalize_reaction_text(text: str) -> str:
    return text.strip().replace("→", "->").replace("½", "1/2")


def _fraction_to_str(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def _coeff_to_str(value: Fraction) -> str:
    if value == 1:
        return ""
    return f"{_fraction_to_str(value)} "


def _parse_energy(value_text: str) -> Fraction:
    raw = value_text.strip().replace(",", ".")
    if not raw:
        raise ValueError("Missing ΔH value")
    return Fraction(raw)


def _reaction_to_vector(ast: Dict[str, Any]) -> Dict[str, Fraction]:
    vector: Dict[str, Fraction] = {}

    for item in ast["reactants"]:
        key = item["species_key"]
        vector[key] = vector.get(key, Fraction(0, 1)) - Fraction(item["coefficient"])

    for item in ast["products"]:
        key = item["species_key"]
        vector[key] = vector.get(key, Fraction(0, 1)) + Fraction(item["coefficient"])

    return {k: v for k, v in vector.items() if v != 0}


def _format_species_term(species_key: str, abs_coeff: Fraction) -> str:
    return f"{_coeff_to_str(abs_coeff)}{species_key}"


def format_reaction_vector(vector: Dict[str, Fraction]) -> str:
    reactants: List[str] = []
    products: List[str] = []

    for species in sorted(vector.keys()):
        coeff = vector[species]
        if coeff < 0:
            reactants.append(_format_species_term(species, -coeff))
        elif coeff > 0:
            products.append(_format_species_term(species, coeff))

    left = " + ".join(reactants) if reactants else "0"
    right = " + ".join(products) if products else "0"
    return f"{left} -> {right}"


def parse_hess_reaction(reaction_text: str) -> Dict[str, Any]:
    normalized = _normalize_reaction_text(reaction_text)
    return parseReaction(normalized)


@dataclass
class KnownReaction:
    index: int
    reaction_text: str
    delta_h: Fraction
    ast: Dict[str, Any]
    vector: Dict[str, Fraction]


def parse_known_reaction_line(line_text: str, line_no: int) -> KnownReaction:
    if ";" not in line_text:
        raise ValueError(f"Line {line_no}: expected format 'reaction ; dH'")
    reaction_part, energy_part = line_text.split(";", 1)
    reaction_part = reaction_part.strip()
    if not reaction_part:
        raise ValueError(f"Line {line_no}: reaction is empty")

    try:
        ast = parse_hess_reaction(reaction_part)
    except Exception as exc:
        raise ValueError(f"Line {line_no}: could not parse reaction ({exc})") from exc

    try:
        delta_h = _parse_energy(energy_part)
    except Exception as exc:
        raise ValueError(f"Line {line_no}: could not parse ΔH value ({exc})") from exc

    return KnownReaction(
        index=line_no,
        reaction_text=ast["equation_str"],
        delta_h=delta_h,
        ast=ast,
        vector=_reaction_to_vector(ast),
    )


def parse_known_reactions_block(block_text: str) -> List[KnownReaction]:
    lines = block_text.splitlines()
    parsed: List[KnownReaction] = []

    for idx, raw in enumerate(lines, start=1):
        stripped = raw.strip()
        if not stripped:
            continue
        parsed.append(parse_known_reaction_line(stripped, idx))

    if not parsed:
        raise ValueError("Provide at least one known reaction line in format 'reaction ; dH'")

    return parsed


def _build_matrix(
    known: List[KnownReaction],
    target_vector: Dict[str, Fraction],
) -> Tuple[List[str], List[List[Fraction]], List[Fraction]]:
    species = sorted({s for s in target_vector.keys()} | {s for k in known for s in k.vector.keys()})
    rows: List[List[Fraction]] = []
    b: List[Fraction] = []

    for sp in species:
        rows.append([reaction.vector.get(sp, Fraction(0, 1)) for reaction in known])
        b.append(target_vector.get(sp, Fraction(0, 1)))

    return species, rows, b


def _rref_solve(
    matrix: List[List[Fraction]],
    rhs: List[Fraction],
) -> Dict[str, Any]:
    if not matrix:
        return {
            "consistent": all(v == 0 for v in rhs),
            "particular": [],
            "nullspace": [],
            "pivot_cols": [],
            "inconsistent_rows": [i for i, v in enumerate(rhs) if v != 0],
        }

    m = len(matrix)
    n = len(matrix[0])
    aug: List[List[Fraction]] = [list(matrix[r]) + [rhs[r]] for r in range(m)]
    pivot_cols: List[int] = []

    pivot_row = 0
    for col in range(n):
        pivot = None
        for r in range(pivot_row, m):
            if aug[r][col] != 0:
                pivot = r
                break
        if pivot is None:
            continue

        if pivot != pivot_row:
            aug[pivot_row], aug[pivot] = aug[pivot], aug[pivot_row]

        pivot_val = aug[pivot_row][col]
        aug[pivot_row] = [v / pivot_val for v in aug[pivot_row]]

        for r in range(m):
            if r == pivot_row:
                continue
            factor = aug[r][col]
            if factor == 0:
                continue
            aug[r] = [aug[r][c] - factor * aug[pivot_row][c] for c in range(n + 1)]

        pivot_cols.append(col)
        pivot_row += 1
        if pivot_row == m:
            break

    inconsistent_rows: List[int] = []
    for r in range(m):
        if all(aug[r][c] == 0 for c in range(n)) and aug[r][n] != 0:
            inconsistent_rows.append(r)

    if inconsistent_rows:
        return {
            "consistent": False,
            "particular": [],
            "nullspace": [],
            "pivot_cols": pivot_cols,
            "inconsistent_rows": inconsistent_rows,
        }

    particular = [Fraction(0, 1) for _ in range(n)]
    for row_idx, col_idx in enumerate(pivot_cols):
        particular[col_idx] = aug[row_idx][n]

    free_cols = [c for c in range(n) if c not in pivot_cols]
    nullspace: List[List[Fraction]] = []
    for free in free_cols:
        vec = [Fraction(0, 1) for _ in range(n)]
        vec[free] = Fraction(1, 1)
        for row_idx, pivot_col in enumerate(pivot_cols):
            vec[pivot_col] = -aug[row_idx][free]
        nullspace.append(vec)

    return {
        "consistent": True,
        "particular": particular,
        "nullspace": nullspace,
        "pivot_cols": pivot_cols,
        "inconsistent_rows": [],
    }


def _score_solution(solution: List[Fraction]) -> Tuple[int, Fraction]:
    nonzero = [v for v in solution if v != 0]
    l1 = sum(abs(v) for v in nonzero) if nonzero else Fraction(0, 1)
    return len(nonzero), l1


def _add_vec(a: List[Fraction], b: List[Fraction], scale: Fraction) -> List[Fraction]:
    return [av + scale * bv for av, bv in zip(a, b)]


def _refine_solution(particular: List[Fraction], nullspace: List[List[Fraction]]) -> List[Fraction]:
    if not nullspace:
        return particular

    current = list(particular)
    current_score = _score_solution(current)

    for basis_vec in nullspace:
        candidates = {Fraction(0, 1)}
        for idx, v in enumerate(basis_vec):
            if v != 0:
                candidates.add(-current[idx] / v)
        for k in range(-6, 7):
            candidates.add(Fraction(k, 1))

        best = current
        best_score = current_score
        for t in candidates:
            proposal = _add_vec(current, basis_vec, t)
            score = _score_solution(proposal)
            if score < best_score:
                best = proposal
                best_score = score

        current = best
        current_score = best_score

    return current


def _combine_vectors(
    known: List[KnownReaction],
    factors: List[Fraction],
) -> Dict[str, Fraction]:
    summed: Dict[str, Fraction] = {}
    for rxn, factor in zip(known, factors):
        if factor == 0:
            continue
        for species, coeff in rxn.vector.items():
            summed[species] = summed.get(species, Fraction(0, 1)) + factor * coeff
    return {k: v for k, v in summed.items() if v != 0}


def _residual(
    species: List[str],
    matrix: List[List[Fraction]],
    rhs: List[Fraction],
    factors: List[Fraction],
) -> Dict[str, Fraction]:
    out: Dict[str, Fraction] = {}
    for row_idx, sp in enumerate(species):
        lhs = sum(matrix[row_idx][col_idx] * factors[col_idx] for col_idx in range(len(factors)))
        delta = rhs[row_idx] - lhs
        if delta != 0:
            out[sp] = delta
    return out


def _scaled_integer_factors(factors: List[Fraction]) -> Dict[str, Any]:
    if not factors:
        return {"scale": 1, "factors": []}

    denoms = [f.denominator for f in factors if f != 0]
    if not denoms:
        return {"scale": 1, "factors": [0 for _ in factors]}

    lcm_den = denoms[0]
    for d in denoms[1:]:
        lcm_den = math.lcm(lcm_den, d)

    scaled = [int(f * lcm_den) for f in factors]
    nonzero = [abs(v) for v in scaled if v != 0]
    gcd_val = nonzero[0] if nonzero else 1
    for v in nonzero[1:]:
        gcd_val = math.gcd(gcd_val, v)

    reduced = [int(v // gcd_val) for v in scaled]
    scale = lcm_den // gcd_val
    return {"scale": scale, "factors": reduced}


def _species_reachability_diagnostics(
    species: List[str],
    matrix: List[List[Fraction]],
    rhs: List[Fraction],
) -> Dict[str, List[str]]:
    missing_target_species: List[str] = []
    known_only_species: List[str] = []
    for idx, sp in enumerate(species):
        row = matrix[idx]
        row_is_zero = all(v == 0 for v in row)
        if row_is_zero and rhs[idx] != 0:
            missing_target_species.append(sp)
        if row_is_zero and rhs[idx] == 0:
            known_only_species.append(sp)

    return {
        "missing_target_species": sorted(missing_target_species),
        "known_only_species": sorted(known_only_species),
    }


def _format_h_term(factor: Fraction, delta_h: Fraction) -> str:
    term = factor * delta_h
    sign = "+" if term >= 0 else "-"
    return f"{sign} ({_fraction_to_str(abs(factor))} × {_fraction_to_str(abs(delta_h))})"


def solve_hess_problem(target_reaction: str, known_lines_block: str) -> Dict[str, Any]:
    target_ast = parse_hess_reaction(target_reaction)
    known = parse_known_reactions_block(known_lines_block)
    target_vector = _reaction_to_vector(target_ast)
    species, matrix, rhs = _build_matrix(known, target_vector)
    linear = _rref_solve(matrix, rhs)

    if not linear["consistent"]:
        diagnostics = _species_reachability_diagnostics(species, matrix, rhs)
        return {
            "ok": False,
            "error": "Target reaction cannot be formed from provided known reactions.",
            "reason": "No exact solution to A*x=b (rank/consistency failure).",
            "inconsistent_species_rows": [species[i] for i in linear["inconsistent_rows"] if i < len(species)],
            "diagnostics": diagnostics,
        }

    factors = _refine_solution(linear["particular"], linear["nullspace"])
    residual = _residual(species, matrix, rhs, factors)
    if residual:
        return {
            "ok": False,
            "error": "Internal verification failed: non-zero residual after solving.",
            "reason": "Residual b - A*x is non-zero; refusing to report ΔH°.",
            "residual": {k: _fraction_to_str(v) for k, v in residual.items()},
        }

    used: List[Dict[str, Any]] = []
    for idx, (rxn, factor) in enumerate(zip(known, factors), start=1):
        if factor == 0:
            continue
        used.append(
            {
                "input_index": rxn.index,
                "solver_index": idx,
                "factor": factor,
                "factor_str": _fraction_to_str(factor),
                "is_reversed": factor < 0,
                "reaction": rxn.reaction_text,
                "delta_h": rxn.delta_h,
                "delta_h_str": _fraction_to_str(rxn.delta_h),
            }
        )

    combined_vector = _combine_vectors(known, factors)
    delta_h_terms = [_format_h_term(f, rxn.delta_h) for rxn, f in zip(known, factors) if f != 0]
    delta_h_total = sum((f * rxn.delta_h for rxn, f in zip(known, factors)), start=Fraction(0, 1))

    scaled = _scaled_integer_factors(factors)

    return {
        "ok": True,
        "target": {
            "equation": target_ast["equation_str"],
            "vector": {k: _fraction_to_str(v) for k, v in sorted(target_vector.items())},
        },
        "selected_combination": used,
        "factors": factors,
        "factors_str": [_fraction_to_str(v) for v in factors],
        "scaled_integer_presentation": scaled,
        "summed_reaction": format_reaction_vector(combined_vector),
        "summed_vector": {k: _fraction_to_str(v) for k, v in sorted(combined_vector.items())},
        "delta_h_total": delta_h_total,
        "delta_h_total_str": _fraction_to_str(delta_h_total),
        "delta_h_total_float": float(delta_h_total),
        "delta_h_terms": delta_h_terms,
        "validation": {
            "residual_zero": True,
            "residual": {},
            "matches_target_exactly": combined_vector == target_vector,
        },
    }
