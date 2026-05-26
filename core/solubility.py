from __future__ import annotations

"""Solubility parsing and rule engine for ionic salts in water.

Implemented model:
- parser: identifies cation/anion from a known ion database
- rule engine: explicit prioritized solubility rules

Internal statuses:
- soluble
- insoluble
- slightly_soluble
- unknown
"""

from dataclasses import dataclass
from math import gcd
from typing import Any, Dict, List, Tuple

from core.formula import parse_chemical_formula


@dataclass(frozen=True)
class Ion:
    symbol: str
    formula: str
    charge: int
    kind: str  # cation | anion


KNOWN_CATIONS: List[Ion] = [
    Ion("Li+", "Li", 1, "cation"),
    Ion("Na+", "Na", 1, "cation"),
    Ion("K+", "K", 1, "cation"),
    Ion("NH4+", "NH4", 1, "cation"),
    Ion("Mg2+", "Mg", 2, "cation"),
    Ion("Ca2+", "Ca", 2, "cation"),
    Ion("Sr2+", "Sr", 2, "cation"),
    Ion("Ba2+", "Ba", 2, "cation"),
    Ion("Ag+", "Ag", 1, "cation"),
    Ion("Pb2+", "Pb", 2, "cation"),
    Ion("Zn2+", "Zn", 2, "cation"),
    Ion("Cu2+", "Cu", 2, "cation"),
    Ion("Fe2+", "Fe", 2, "cation"),
    Ion("Fe3+", "Fe", 3, "cation"),
    Ion("Al3+", "Al", 3, "cation"),
]


KNOWN_ANIONS: List[Ion] = [
    Ion("NO3-", "NO3", -1, "anion"),
    Ion("C2H3O2-", "C2H3O2", -1, "anion"),
    Ion("Cl-", "Cl", -1, "anion"),
    Ion("Br-", "Br", -1, "anion"),
    Ion("I-", "I", -1, "anion"),
    Ion("SO4^2-", "SO4", -2, "anion"),
    Ion("OH-", "OH", -1, "anion"),
    Ion("S^2-", "S", -2, "anion"),
    Ion("CO3^2-", "CO3", -2, "anion"),
    Ion("PO4^3-", "PO4", -3, "anion"),
]


STATUS_DA = {
    "soluble": "let opløseligt",
    "insoluble": "tungt opløseligt",
    "slightly_soluble": "svagt opløseligt",
    "unknown": "ukendt / kan ikke afgøres sikkert",
}


STATUS_EN = {
    "soluble": "soluble",
    "insoluble": "insoluble",
    "slightly_soluble": "slightly soluble",
    "unknown": "unknown / cannot determine",
}


ALWAYS_SOLUBLE_CATIONS = {"Li+", "Na+", "K+", "NH4+"}
ALWAYS_SOLUBLE_ANIONS = {"NO3-", "C2H3O2-"}


def _ion_composition(ion: Ion) -> Dict[str, int]:
    return parse_chemical_formula(ion.formula)


def _scaled_composition(parts: List[Tuple[Dict[str, int], int]]) -> Dict[str, int]:
    total: Dict[str, int] = {}
    for comp, factor in parts:
        for element, count in comp.items():
            total[element] = total.get(element, 0) + count * factor
    return total


def _integer_scale_if_multiple(target: Dict[str, int], base: Dict[str, int]) -> int | None:
    if set(target.keys()) != set(base.keys()):
        return None

    scale = None
    for element, base_count in base.items():
        if base_count <= 0:
            return None
        t_count = target[element]
        if t_count % base_count != 0:
            return None
        ratio = t_count // base_count
        if ratio <= 0:
            return None
        if scale is None:
            scale = ratio
        elif scale != ratio:
            return None
    return scale


def _normalize_formula_input(formula: str) -> str:
    if formula is None:
        raise ValueError("Input mangler. Indtast et salt, fx NaCl eller BaSO4.")
    normalized = "".join(str(formula).split())
    if not normalized:
        raise ValueError("Input er tomt. Indtast et salt, fx NaCl eller BaSO4.")
    return normalized


def parse_ionic_salt(formula: str) -> Dict[str, Any]:
    """Parse a salt formula and identify cation/anion from known ion database.

    Raises ValueError if parsing fails or if the formula cannot be safely interpreted
    as a supported ionic salt in this model.
    """
    normalized = _normalize_formula_input(formula)
    try:
        total_composition = parse_chemical_formula(normalized)
    except ValueError as exc:
        raise ValueError(f"Kunne ikke parse salt-formlen: {exc}") from exc

    matches: List[Dict[str, Any]] = []
    cation_comps = {ion.symbol: _ion_composition(ion) for ion in KNOWN_CATIONS}
    anion_comps = {ion.symbol: _ion_composition(ion) for ion in KNOWN_ANIONS}

    for cation in KNOWN_CATIONS:
        for anion in KNOWN_ANIONS:
            g = gcd(cation.charge, abs(anion.charge))
            cat_units = abs(anion.charge) // g
            an_units = cation.charge // g

            base_comp = _scaled_composition([
                (cation_comps[cation.symbol], cat_units),
                (anion_comps[anion.symbol], an_units),
            ])
            scale = _integer_scale_if_multiple(total_composition, base_comp)
            if scale is None:
                continue

            matches.append(
                {
                    "cation": cation,
                    "anion": anion,
                    "cation_units": cat_units * scale,
                    "anion_units": an_units * scale,
                    "scale": scale,
                }
            )

    if not matches:
        raise ValueError(
            "Formlen kunne ikke fortolkes sikkert som et understøttet ionisk salt i regelmodellen."
        )

    if len(matches) > 1:
        options = ", ".join(f"{m['cation'].symbol}+{m['anion'].symbol}" for m in matches[:3])
        raise ValueError(
            "Formlen er tvetydig i den nuværende iondatabase "
            f"({options}). Skriv et mere specifikt salt."
        )

    match = matches[0]
    return {
        "input": formula,
        "normalized_formula": normalized,
        "composition": total_composition,
        "cation": {
            "symbol": match["cation"].symbol,
            "formula": match["cation"].formula,
            "charge": match["cation"].charge,
            "units": match["cation_units"],
        },
        "anion": {
            "symbol": match["anion"].symbol,
            "formula": match["anion"].formula,
            "charge": match["anion"].charge,
            "units": match["anion_units"],
        },
    }


def classify_solubility(parsed_salt: Dict[str, Any]) -> Dict[str, Any]:
    """Classify solubility using explicit prioritized rules."""
    cation = parsed_salt["cation"]["symbol"]
    anion = parsed_salt["anion"]["symbol"]

    # Rule 1: alkali metal + ammonium salts are soluble
    if cation in ALWAYS_SOLUBLE_CATIONS:
        return {
            "status": "soluble",
            "rule_id": "R1_ALWAYS_SOLUBLE_CATIONS",
            "rule": "Alkalimetal- og ammoniumsalte er let opløselige.",
            "reason": f"Kation {cation} matcher altid-opløselig gruppe.",
        }

    # Rule 2: nitrates and acetates are soluble
    if anion in ALWAYS_SOLUBLE_ANIONS:
        return {
            "status": "soluble",
            "rule_id": "R2_NITRATE_ACETATE",
            "rule": "Nitrater og acetater er let opløselige.",
            "reason": f"Anion {anion} matcher altid-opløselig gruppe.",
        }

    # Rule 3: halides with explicit exceptions
    if anion in {"Cl-", "Br-", "I-"}:
        if cation in {"Ag+", "Pb2+"}:
            return {
                "status": "insoluble",
                "rule_id": "R3_HALIDES_EXCEPTION",
                "rule": "Halider er normalt opløselige, men Ag+ og Pb2+ er undtagelser.",
                "reason": f"{cation} med {anion} matcher halid-undtagelse.",
            }
        return {
            "status": "soluble",
            "rule_id": "R3_HALIDES_GENERAL",
            "rule": "Halider er generelt let opløselige.",
            "reason": f"{anion} uden undtagelses-kation.",
        }

    # Rule 4: sulfates with explicit exceptions
    if anion == "SO4^2-":
        if cation in {"Ba2+", "Sr2+", "Pb2+"}:
            return {
                "status": "insoluble",
                "rule_id": "R4_SULFATES_EXCEPTION",
                "rule": "Sulfater er generelt opløselige, men Ba2+, Sr2+ og Pb2+ er undtagelser.",
                "reason": f"{cation} med sulfat matcher undtagelseslisten.",
            }
        if cation == "Ca2+":
            return {
                "status": "slightly_soluble",
                "rule_id": "R4_SULFATES_CA_SPECIAL",
                "rule": "Calciumsulfat behandles som svagt opløseligt i denne regelmodel.",
                "reason": "Ca2+ med sulfat har særstatus.",
            }
        return {
            "status": "soluble",
            "rule_id": "R4_SULFATES_GENERAL",
            "rule": "Sulfater er generelt let opløselige.",
            "reason": "Ingen undtagelses-kation fundet.",
        }

    # Rule 5: hydroxides
    if anion == "OH-":
        if cation in ALWAYS_SOLUBLE_CATIONS:
            return {
                "status": "soluble",
                "rule_id": "R5_HYDROXIDES_ALKALI",
                "rule": "Hydroxider af alkalimetaller og ammonium er opløselige.",
                "reason": f"{cation} matcher opløselig undtagelse for hydroxider.",
            }
        if cation in {"Ca2+", "Sr2+", "Ba2+"}:
            return {
                "status": "slightly_soluble",
                "rule_id": "R5_HYDROXIDES_ALKALINE_EARTH",
                "rule": "Ca(OH)2, Sr(OH)2 og Ba(OH)2 behandles som svagt opløselige i denne model.",
                "reason": f"{cation} med hydroxid har særstatus.",
            }
        return {
            "status": "insoluble",
            "rule_id": "R5_HYDROXIDES_GENERAL",
            "rule": "Hydroxider er generelt tungt opløselige.",
            "reason": "Ingen opløselig undtagelse fundet.",
        }

    # Rule 6: sulfides
    if anion == "S^2-":
        if cation in ALWAYS_SOLUBLE_CATIONS:
            return {
                "status": "soluble",
                "rule_id": "R6_SULFIDES_ALKALI",
                "rule": "Sulfider af alkalimetaller og ammonium er opløselige.",
                "reason": f"{cation} matcher opløselig undtagelse for sulfider.",
            }
        if cation in {"Ca2+", "Sr2+", "Ba2+"}:
            return {
                "status": "slightly_soluble",
                "rule_id": "R6_SULFIDES_ALKALINE_EARTH",
                "rule": "Sulfider af Ca2+, Sr2+ og Ba2+ behandles som svagt opløselige i denne model.",
                "reason": f"{cation} med sulfid har særstatus.",
            }
        return {
            "status": "insoluble",
            "rule_id": "R6_SULFIDES_GENERAL",
            "rule": "Sulfider er generelt tungt opløselige.",
            "reason": "Ingen opløselig undtagelse fundet.",
        }

    # Rule 7: carbonates and phosphates
    if anion in {"CO3^2-", "PO4^3-"}:
        if cation in ALWAYS_SOLUBLE_CATIONS:
            return {
                "status": "soluble",
                "rule_id": "R7_CARBONATE_PHOSPHATE_EXCEPTION",
                "rule": "Carbonater/fosfater er normalt tungt opløselige, men alkalimetaller og ammonium er undtagelser.",
                "reason": f"{cation} matcher undtagelse.",
            }
        return {
            "status": "insoluble",
            "rule_id": "R7_CARBONATE_PHOSPHATE_GENERAL",
            "rule": "Carbonater og fosfater er generelt tungt opløselige.",
            "reason": "Ingen opløselig undtagelse fundet.",
        }

    return {
        "status": "unknown",
        "rule_id": "R0_UNKNOWN",
        "rule": "Ingen implementeret regel matcher sikkert denne kombination.",
        "reason": "Kan ikke afgøres sikkert ud fra de implementerede opløselighedsregler.",
    }


def evaluate_salt_solubility(formula: str) -> Dict[str, Any]:
    """Parse and classify a salt formula.

    Returns combined parsed and classification result.
    """
    parsed = parse_ionic_salt(formula)
    classification = classify_solubility(parsed)
    status = classification["status"]
    return {
        "salt": parsed["normalized_formula"],
        "cation": parsed["cation"],
        "anion": parsed["anion"],
        "status": status,
        "classification_da": STATUS_DA[status],
        "classification_en": STATUS_EN[status],
        "rule_id": classification["rule_id"],
        "rule": classification["rule"],
        "reason": classification["reason"],
    }
