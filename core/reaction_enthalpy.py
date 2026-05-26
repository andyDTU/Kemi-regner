"""
Reaction enthalpy utilities built around Hess' law.

Public API:
- parseReaction(input_text) -> AST
- computeRxnEnthalpy(ast, dhfDb, overrides) -> details
- balanceReaction(ast) -> balanced AST/details
"""

from __future__ import annotations

import math
import re
from typing import Any, Dict, List, Tuple

import sympy as sp

from core.formula import parse_chemical_formula
from core.dhf_database import getDhf

_PHASE_PATTERN = re.compile(r"\((s|l|g|aq)\)\s*$", re.IGNORECASE)
_COEFF_PATTERN = re.compile(r"^\s*([0-9]+(?:/[0-9]+)?|[0-9]*\.[0-9]+)\s*(.+)$")


def _to_rational(value: str | int | float | sp.Rational) -> sp.Rational:
    if isinstance(value, sp.Rational):
        return value
    if isinstance(value, int):
        return sp.Rational(value, 1)
    if isinstance(value, float):
        return sp.Rational(str(value))
    return sp.Rational(value)


def _format_coeff(coeff: sp.Rational) -> str:
    if coeff == 1:
        return ""
    if coeff.q == 1:
        return str(int(coeff))
    return f"{coeff.p}/{coeff.q}"


def _phase_key(formula: str, phase: str) -> str:
    return f"{formula}({phase})"


def _split_reaction_arrow(input_text: str) -> Tuple[str, str]:
    normalized = input_text.strip().replace("=>", "->")
    if "->" in normalized:
        left, right = normalized.split("->", 1)
        return left, right
    if "=" in normalized:
        left, right = normalized.split("=", 1)
        return left, right
    raise ValueError("Reaction must contain an arrow: '->', '=>', or '='")


def _parse_term(term_text: str) -> Tuple[sp.Rational, str, str, bool]:
    term = term_text.strip()
    if not term:
        raise ValueError("Empty species term in reaction")

    phase_match = _PHASE_PATTERN.search(term)
    used_default_phase = False
    if phase_match:
        phase = phase_match.group(1).lower()
        core = term[: phase_match.start()].strip()
    else:
        phase = "g"
        core = term
        used_default_phase = True

    coeff = sp.Rational(1, 1)
    coeff_match = _COEFF_PATTERN.match(core)
    if coeff_match:
        try:
            coeff = _to_rational(coeff_match.group(1))
        except Exception as exc:
            raise ValueError(f"Invalid stoichiometric coefficient in '{term_text}'") from exc
        formula = coeff_match.group(2).strip()
    else:
        formula = core.strip()

    if coeff <= 0:
        raise ValueError(f"Coefficient must be positive in '{term_text}'")

    if not formula:
        raise ValueError(f"Missing chemical formula in '{term_text}'")

    parse_chemical_formula(formula)

    return coeff, formula, phase, used_default_phase


def _parse_side(side_text: str, side_name: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    terms = [part.strip() for part in side_text.split("+")]
    items: List[Dict[str, Any]] = []
    warnings: List[str] = []

    for term in terms:
        if not term:
            continue
        coeff, formula, phase, used_default_phase = _parse_term(term)
        entry = {
            "side": side_name,
            "coefficient": coeff,
            "formula": formula,
            "phase": phase,
            "species_key": _phase_key(formula, phase),
            "lookup_key_raw": formula if used_default_phase else _phase_key(formula, phase),
            "phase_was_default": used_default_phase,
            "raw": term,
        }
        items.append(entry)
        if used_default_phase:
            warnings.append(f"Phase missing for {formula}; defaulted to (g).")

    return items, warnings


def parseReaction(input_text: str) -> Dict[str, Any]:
    """
    Parse a reaction string into AST containing reactants/products with
    coefficient, formula, and phase.
    """
    if not input_text or not input_text.strip():
        raise ValueError("Reaction input cannot be empty")

    left_text, right_text = _split_reaction_arrow(input_text)
    reactants, warnings_left = _parse_side(left_text, "reactant")
    products, warnings_right = _parse_side(right_text, "product")

    if not reactants:
        raise ValueError("No reactants found")
    if not products:
        raise ValueError("No products found")

    ast = {
        "raw_input": input_text,
        "reactants": reactants,
        "products": products,
        "warnings": warnings_left + warnings_right,
    }
    ast["species_order"] = reactants + products
    ast["equation_str"] = formatReaction(ast)
    return ast


def formatReaction(ast: Dict[str, Any]) -> str:
    def fmt_side(items: List[Dict[str, Any]]) -> str:
        parts: List[str] = []
        for item in items:
            coeff = _format_coeff(_to_rational(item["coefficient"]))
            species = f"{item['formula']}({item['phase']})"
            parts.append(f"{coeff}{species}" if coeff else species)
        return " + ".join(parts)

    return f"{fmt_side(ast['reactants'])} -> {fmt_side(ast['products'])}"


def _element_balance(ast: Dict[str, Any]) -> Dict[str, sp.Rational]:
    balance: Dict[str, sp.Rational] = {}
    for item in ast["reactants"]:
        coeff = _to_rational(item["coefficient"])
        formula_counts = parse_chemical_formula(item["formula"])
        for element, count in formula_counts.items():
            balance[element] = balance.get(element, sp.Rational(0, 1)) + coeff * count

    for item in ast["products"]:
        coeff = _to_rational(item["coefficient"])
        formula_counts = parse_chemical_formula(item["formula"])
        for element, count in formula_counts.items():
            balance[element] = balance.get(element, sp.Rational(0, 1)) - coeff * count

    return balance


def isReactionBalanced(ast: Dict[str, Any]) -> Tuple[bool, Dict[str, float]]:
    raw = _element_balance(ast)
    imbalance = {
        element: float(delta)
        for element, delta in raw.items()
        if delta != 0
    }
    return len(imbalance) == 0, imbalance


def computeRxnEnthalpy(
    ast: Dict[str, Any],
    dhfDb: Dict[str, Dict[str, Any]],
    overrides: Dict[str, float] | None = None,
) -> Dict[str, Any]:
    """
    Compute reaction enthalpy using Hess' law.
    Returns detailed row-wise contributions and totals.
    """
    overrides = overrides or {}
    rows: List[Dict[str, Any]] = []
    missing_species: List[str] = []

    sum_products = 0.0
    sum_reactants = 0.0

    for item in ast["reactants"] + ast["products"]:
        side = item["side"]
        coeff_rat = _to_rational(item["coefficient"])
        coeff_val = float(coeff_rat)
        species_key = item["species_key"]
        lookup_key_raw = item.get("lookup_key_raw", species_key)

        lookup = getDhf(lookup_key_raw, overrides=overrides, db=dhfDb)
        dhf_value = lookup["value"]
        source = lookup["source"]
        resolved_key = lookup["key"]

        subtotal = None if dhf_value is None else coeff_val * dhf_value

        if dhf_value is None:
            missing_species.append(species_key)
        else:
            if side == "product":
                sum_products += subtotal
            else:
                sum_reactants += subtotal

        rows.append(
            {
                "side": side,
                "species": resolved_key if lookup["found"] else species_key,
                "formula": item["formula"],
                "phase": item["phase"],
                "coefficient": coeff_val,
                "dhf_kj_per_mol": dhf_value,
                "source": source,
                "subtotal_kj_per_mol": subtotal,
                "missing": not lookup["found"],
            }
        )

    total = None if missing_species else (sum_products - sum_reactants)
    balanced, imbalance = isReactionBalanced(ast)

    return {
        "rows": rows,
        "sum_products_kj_per_mol": sum_products,
        "sum_reactants_kj_per_mol": sum_reactants,
        "delta_h_rxn_kj_per_mol": total,
        "missing_species": sorted(set(missing_species)),
        "warnings": ast.get("warnings", []),
        "is_balanced": balanced,
        "imbalance": imbalance,
    }


def _scale_vector_to_integers(vec: List[sp.Rational]) -> List[int]:
    denominators = [v.q for v in vec if v != 0]
    if not denominators:
        raise ValueError("Balancing failed: nullspace produced zero vector")

    lcm_den = denominators[0]
    for d in denominators[1:]:
        lcm_den = sp.ilcm(lcm_den, d)

    scaled = [int(v * lcm_den) for v in vec]
    nonzero = [abs(v) for v in scaled if v != 0]
    gcd_val = nonzero[0]
    for n in nonzero[1:]:
        gcd_val = math.gcd(gcd_val, n)

    reduced = [int(v // gcd_val) for v in scaled]

    if all(v <= 0 for v in reduced):
        reduced = [-v for v in reduced]
    if any(v < 0 for v in reduced):
        reduced = [abs(v) for v in reduced]

    return reduced


def balanceReaction(ast: Dict[str, Any]) -> Dict[str, Any]:
    """
    Balance reaction AST using linear algebra and return a new AST with
    integer stoichiometric coefficients.
    """
    species = ast["reactants"] + ast["products"]
    if len(species) < 2:
        raise ValueError("Balancing failed: reaction must contain at least two species")

    element_set = set()
    species_element_counts: List[Dict[str, int]] = []
    for item in species:
        counts = parse_chemical_formula(item["formula"])
        species_element_counts.append(counts)
        element_set.update(counts.keys())

    elements = sorted(element_set)
    matrix_rows: List[List[int]] = []

    reactant_count = len(ast["reactants"])
    for element in elements:
        row: List[int] = []
        for idx, counts in enumerate(species_element_counts):
            sign = 1 if idx < reactant_count else -1
            row.append(sign * counts.get(element, 0))
        matrix_rows.append(row)

    matrix = sp.Matrix(matrix_rows)
    nullspace = matrix.nullspace()
    if not nullspace:
        raise ValueError("Balancing failed: no algebraic solution found")

    basis = [sp.nsimplify(v) for v in list(nullspace[0])]
    coeffs_int = _scale_vector_to_integers(basis)

    if any(c == 0 for c in coeffs_int):
        raise ValueError("Balancing failed: degenerate coefficient set produced")

    new_reactants: List[Dict[str, Any]] = []
    new_products: List[Dict[str, Any]] = []

    for idx, item in enumerate(ast["reactants"]):
        copy_item = dict(item)
        copy_item["coefficient"] = sp.Rational(coeffs_int[idx], 1)
        new_reactants.append(copy_item)

    for idx, item in enumerate(ast["products"]):
        copy_item = dict(item)
        copy_item["coefficient"] = sp.Rational(coeffs_int[idx + reactant_count], 1)
        new_products.append(copy_item)

    out = {
        "raw_input": ast.get("raw_input", ""),
        "reactants": new_reactants,
        "products": new_products,
        "warnings": ast.get("warnings", []),
    }
    out["species_order"] = out["reactants"] + out["products"]
    out["equation_str"] = formatReaction(out)

    balanced, imbalance = isReactionBalanced(out)
    if not balanced:
        raise ValueError(f"Balancing failed verification: {imbalance}")

    return {
        "ast": out,
        "equation_str": out["equation_str"],
        "coefficients": coeffs_int,
        "elements": elements,
    }
