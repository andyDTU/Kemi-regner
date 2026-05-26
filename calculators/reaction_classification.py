"""Reaction parser and reaction-type classification rule engine."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Dict, List, Optional

from core.formula import parse_chemical_formula


class ReactionParseError(ValueError):
    """Raised when a reaction string cannot be parsed safely."""


@dataclass(frozen=True)
class ReactionSpecies:
    coefficient: int
    formula: str
    state: Optional[str] = None


@dataclass(frozen=True)
class ParsedReaction:
    reactants: List[ReactionSpecies]
    products: List[ReactionSpecies]
    arrow: str


ARROW_PATTERN = re.compile(r"<->|⇌|→|->|=")
STATE_PATTERN = re.compile(r"\(\s*(aq|s|l|g)\s*\)\s*$", re.IGNORECASE)
COEFF_PATTERN = re.compile(r"^(\d+)\s*")
VALID_FORMULA_PATTERN = re.compile(r"^[A-Za-z0-9()\[\]{}^+\-_.·]+$")

COMMON_ACIDS = {
    "HCL",
    "HBR",
    "HI",
    "HNO3",
    "HCLO4",
    "H2SO4",
    "H2SO3",
    "H2CO3",
    "CH3COOH",
    "HF",
    "H3PO4",
}

COMMON_BASES = {
    "NAOH",
    "KOH",
    "LIOH",
    "CA(OH)2",
    "BA(OH)2",
    "MG(OH)2",
    "NH3",
}

TYPE_COMBUSTION = "Forbrændingsreaktion"
TYPE_ACID_BASE = "Syre-base-reaktion"
TYPE_PRECIPITATION = "Fældningsreaktion"
TYPE_REDOX = "Redoxreaktion"
TYPE_SINGLE = "Enkeltforskydning"
TYPE_DOUBLE = "Dobbeltforskydning"
TYPE_SYNTHESIS = "Syntese/foreningsreaktion"
TYPE_DECOMPOSITION = "Nedbrydningsreaktion"
TYPE_UNKNOWN = "Ukendt / kan ikke klassificeres sikkert"

PRIORITY = [
    TYPE_COMBUSTION,
    TYPE_ACID_BASE,
    TYPE_PRECIPITATION,
    TYPE_SINGLE,
    TYPE_DOUBLE,
    TYPE_SYNTHESIS,
    TYPE_DECOMPOSITION,
    TYPE_REDOX,
]


def parse_reaction_text(reaction_text: str) -> ParsedReaction:
    """Parse reaction text into a structured reaction model."""
    if not reaction_text or not reaction_text.strip():
        raise ReactionParseError("Reaktionen kan ikke være tom.")

    text = reaction_text.strip()
    arrow_matches = list(ARROW_PATTERN.finditer(text))
    if not arrow_matches:
        raise ReactionParseError("Reaktionen skal indeholde en pil (->, →, ⇌, <-> eller =).")
    if len(arrow_matches) != 1:
        raise ReactionParseError("Reaktionen skal indeholde præcis én pil.")

    m = arrow_matches[0]
    left = text[: m.start()].strip()
    right = text[m.end() :].strip()
    if not left or not right:
        raise ReactionParseError("Reaktionen skal have både reaktanter og produkter.")

    reactants = _parse_side(left)
    products = _parse_side(right)
    if not reactants:
        raise ReactionParseError("Ingen reaktanter fundet.")
    if not products:
        raise ReactionParseError("Ingen produkter fundet.")

    return ParsedReaction(reactants=reactants, products=products, arrow=m.group(0))


def classify_reaction(parsed: ParsedReaction) -> Dict[str, object]:
    """Classify parsed reaction with rule-based logic."""
    matches: Dict[str, Dict[str, str]] = {}

    reactants = parsed.reactants
    products = parsed.products

    aq_reactants = [s for s in reactants if (s.state or "").lower() == "aq"]
    solid_products = [s for s in products if (s.state or "").lower() == "s"]

    if _is_combustion(reactants, products):
        _add_match(
            matches,
            TYPE_COMBUSTION,
            "high",
            "O2 indgår som reaktant, og produkterne matcher et forbrændingsmønster.",
        )

    acid_base = _is_acid_base(reactants, products)
    if acid_base[0]:
        _add_match(matches, TYPE_ACID_BASE, acid_base[1], acid_base[2])

    is_double = _is_double_displacement(reactants, products)
    if is_double:
        _add_match(
            matches,
            TYPE_DOUBLE,
            "medium",
            "To forbindelser bytter sandsynligvis ionpartnere (dobbeltforskydning).",
        )

    if len(aq_reactants) >= 2 and solid_products and is_double:
        _add_match(
            matches,
            TYPE_PRECIPITATION,
            "high",
            "Mindst to vandige reaktanter danner et fast produkt (bundfald).",
        )

    is_single = _is_single_displacement(reactants, products)
    if is_single:
        _add_match(
            matches,
            TYPE_SINGLE,
            "high",
            "Et frit grundstof forskyder et andet fra en forbindelse.",
        )

    if len(reactants) >= 2 and len(products) == 1:
        _add_match(
            matches,
            TYPE_SYNTHESIS,
            "high",
            "Flere reaktanter danner ét hovedprodukt.",
        )

    if len(reactants) == 1 and len(products) >= 2:
        _add_match(
            matches,
            TYPE_DECOMPOSITION,
            "high",
            "Ét reaktantstof spaltes til flere produkter.",
        )

    redox = _is_redox_heuristic(reactants, products, TYPE_COMBUSTION in matches, is_single)
    if redox[0]:
        _add_match(matches, TYPE_REDOX, redox[1], redox[2])

    if not matches:
        return {
            "primaryType": TYPE_UNKNOWN,
            "secondaryTypes": [],
            "confidence": "low",
            "explanation": "Kan ikke klassificeres sikkert ud fra den indtastede reaktion.",
        }

    ordered = sorted(matches.keys(), key=lambda t: PRIORITY.index(t))
    primary = ordered[0]
    secondary = [t for t in ordered[1:]]
    return {
        "primaryType": primary,
        "secondaryTypes": secondary,
        "confidence": matches[primary]["confidence"],
        "explanation": matches[primary]["explanation"],
    }


def classify_reaction_text(reaction_text: str) -> Dict[str, object]:
    """Parse and classify reaction text."""
    parsed = parse_reaction_text(reaction_text)
    classification = classify_reaction(parsed)
    return {
        "parsed": {
            "reactants": [
                {"coefficient": s.coefficient, "formula": s.formula, "state": s.state}
                for s in parsed.reactants
            ],
            "products": [
                {"coefficient": s.coefficient, "formula": s.formula, "state": s.state}
                for s in parsed.products
            ],
            "arrow": parsed.arrow,
        },
        "classification": classification,
    }


def _parse_side(side: str) -> List[ReactionSpecies]:
    species_tokens = _split_species(side)
    if not species_tokens:
        raise ReactionParseError("Kunne ikke parse reaktionsside.")
    return [_parse_species_token(token) for token in species_tokens]


def _split_species(side: str) -> List[str]:
    parts: List[str] = []
    depth = 0
    start = 0

    for idx, ch in enumerate(side):
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth = max(0, depth - 1)
        elif ch == "+" and depth == 0 and _is_separator_plus(side, idx):
            token = side[start:idx].strip()
            if not token:
                raise ReactionParseError("Tomt stof fundet mellem '+'-tegn.")
            parts.append(token)
            start = idx + 1

    tail = side[start:].strip()
    if not tail:
        raise ReactionParseError("Ugyldig reaktionsside: mangler stof efter '+'.")
    parts.append(tail)
    return parts


def _is_separator_plus(text: str, idx: int) -> bool:
    prev = _prev_nonspace(text, idx)
    nxt = _next_nonspace(text, idx)
    if prev is None or nxt is None:
        return False

    prev_ok = prev.isalnum() or prev in ")] }"  # brace close or formula char
    next_ok = nxt.isalpha() or nxt.isdigit() or nxt in "([{" 

    if prev in "^+-" or nxt in "+>":
        return False
    return prev_ok and next_ok


def _prev_nonspace(text: str, idx: int) -> Optional[str]:
    i = idx - 1
    while i >= 0:
        if not text[i].isspace():
            return text[i]
        i -= 1
    return None


def _next_nonspace(text: str, idx: int) -> Optional[str]:
    i = idx + 1
    while i < len(text):
        if not text[i].isspace():
            return text[i]
        i += 1
    return None


def _parse_species_token(token: str) -> ReactionSpecies:
    raw = token.strip()
    if not raw:
        raise ReactionParseError("Ugyldigt tomt stof i reaktionen.")

    state = None
    state_match = STATE_PATTERN.search(raw)
    if state_match:
        state = state_match.group(1).lower()
        raw = raw[: state_match.start()].strip()

    coeff = 1
    coeff_match = COEFF_PATTERN.match(raw)
    if coeff_match:
        coeff = int(coeff_match.group(1))
        raw = raw[coeff_match.end() :].strip()

    formula = raw.replace(" ", "")
    if not formula:
        raise ReactionParseError(f"Kunne ikke finde formel i token: '{token}'")

    if not VALID_FORMULA_PATTERN.fullmatch(formula):
        raise ReactionParseError(f"Ugyldigt token i reaktionen: '{token}'")

    return ReactionSpecies(coefficient=coeff, formula=formula, state=state)


def _add_match(matches: Dict[str, Dict[str, str]], rtype: str, confidence: str, explanation: str) -> None:
    existing = matches.get(rtype)
    if existing is None:
        matches[rtype] = {"confidence": confidence, "explanation": explanation}
        return

    rank = {"low": 0, "medium": 1, "high": 2}
    if rank[confidence] > rank[existing["confidence"]]:
        matches[rtype] = {"confidence": confidence, "explanation": explanation}


def _canon(formula: str) -> str:
    return formula.replace(" ", "")


def _upper(formula: str) -> str:
    return _canon(formula).upper()


def _is_combustion(reactants: List[ReactionSpecies], products: List[ReactionSpecies]) -> bool:
    reactant_set = {_canon(s.formula) for s in reactants}
    if "O2" not in reactant_set:
        return False

    product_set = {_canon(s.formula) for s in products}
    if "CO2" in product_set and "H2O" in product_set:
        return True

    # Conservative fallback: require a likely carbon-based fuel.
    non_o2 = [s for s in reactants if _canon(s.formula) != "O2"]
    for s in non_o2:
        elems = _safe_element_set(s.formula)
        if "C" in elems and "H" in elems:
            return True

    # Metal combustion heuristic: elemental metal + O2 -> metal oxide.
    if len(non_o2) == 1 and _is_elemental(non_o2[0].formula):
        elem_set = _safe_element_set(non_o2[0].formula)
        if len(elem_set) == 1:
            symbol = next(iter(elem_set))
            if symbol not in {"H", "N", "O", "Cl", "Br", "I", "F"}:
                for p in products:
                    pe = _safe_element_set(p.formula)
                    if "O" in pe and symbol in pe:
                        return True

    return False


def _is_common_acid(formula: str) -> bool:
    f_up = _upper(formula)
    if f_up in COMMON_ACIDS:
        return True
    return f_up.startswith("H") and f_up not in {"H2O", "H2", "H2O2"}


def _is_common_base(formula: str) -> bool:
    f_up = _upper(formula)
    if f_up in COMMON_BASES:
        return True
    if f_up == "NH3":
        return True
    return bool(re.match(r"^[A-Z][A-Za-z0-9]*\(OH\)\d*$", _canon(formula))) or f_up.endswith("OH")


def _is_acid_base(reactants: List[ReactionSpecies], products: List[ReactionSpecies]) -> tuple[bool, str, str]:
    has_acid = any(_is_common_acid(s.formula) for s in reactants)
    has_base = any(_is_common_base(s.formula) for s in reactants)
    if not (has_acid and has_base):
        return (False, "low", "")

    product_formulas = {_canon(s.formula) for s in products}
    if "H2O" in product_formulas:
        return (
            True,
            "high",
            "Reaktanterne matcher syre + base, og vand dannes blandt produkterne.",
        )
    return (
        True,
        "medium",
        "Reaktanterne matcher et tydeligt syre/base-mønster, men uden fuld neutralisationssignatur.",
    )


def _safe_element_set(formula: str) -> set[str]:
    cleaned = re.sub(r"[\^+\-]", "", formula)
    try:
        parsed = parse_chemical_formula(cleaned)
        return set(parsed.keys())
    except Exception:
        return set(re.findall(r"[A-Z][a-z]?", cleaned))


def _is_elemental(formula: str) -> bool:
    if any(ch in formula for ch in "^+-"):
        return False
    elems = _safe_element_set(formula)
    return len(elems) == 1


def _is_single_displacement(reactants: List[ReactionSpecies], products: List[ReactionSpecies]) -> bool:
    if len(reactants) != 2 or len(products) != 2:
        return False

    reactant_elementals = [s for s in reactants if _is_elemental(s.formula)]
    product_elementals = [s for s in products if _is_elemental(s.formula)]
    reactant_compounds = [s for s in reactants if not _is_elemental(s.formula)]
    product_compounds = [s for s in products if not _is_elemental(s.formula)]

    return (
        len(reactant_elementals) == 1
        and len(product_elementals) == 1
        and len(reactant_compounds) == 1
        and len(product_compounds) == 1
    )


def _is_double_displacement(reactants: List[ReactionSpecies], products: List[ReactionSpecies]) -> bool:
    if len(reactants) != 2 or len(products) != 2:
        return False
    if any(_is_elemental(s.formula) for s in reactants + products):
        return False
    return True


def _is_redox_heuristic(
    reactants: List[ReactionSpecies],
    products: List[ReactionSpecies],
    combustion: bool,
    single_displacement: bool,
) -> tuple[bool, str, str]:
    if combustion:
        return (
            True,
            "high",
            "Forbrænding indebærer oxidation/reduktion og klassificeres derfor også som redox.",
        )
    if single_displacement:
        return (
            True,
            "high",
            "Enkeltforskydning med frit grundstof er typisk en redoxproces.",
        )

    reactant_elementals = [s for s in reactants if _is_elemental(s.formula)]
    product_compounds = [s for s in products if not _is_elemental(s.formula)]
    for elem_species in reactant_elementals:
        elem_set = _safe_element_set(elem_species.formula)
        if not elem_set:
            continue
        symbol = next(iter(elem_set))
        if any(symbol in _safe_element_set(p.formula) for p in product_compounds):
            return (
                True,
                "medium",
                "Et frit grundstof ses i en forbindelse på produktsiden, hvilket tyder på redox.",
            )

    product_elementals = [s for s in products if _is_elemental(s.formula)]
    reactant_compounds = [s for s in reactants if not _is_elemental(s.formula)]
    for elem_species in product_elementals:
        elem_set = _safe_element_set(elem_species.formula)
        if not elem_set:
            continue
        symbol = next(iter(elem_set))
        if any(symbol in _safe_element_set(r.formula) for r in reactant_compounds):
            return (
                True,
                "medium",
                "Et grundstof frigives fra en forbindelse, hvilket typisk indikerer redox.",
            )

    return (False, "low", "")
