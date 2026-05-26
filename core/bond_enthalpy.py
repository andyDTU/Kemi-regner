"""
Bond enthalpy estimation of ΔH_rxn.

ΔH_rxn ≈ Σ(bonds broken) - Σ(bonds formed)

All values in kJ/mol. Data from standard undergraduate tables (Atkins / OpenStax).
"""

from dataclasses import dataclass, field
from typing import Optional

# ---------------------------------------------------------------------------
# Bond enthalpy table (kJ/mol, average values)
# ---------------------------------------------------------------------------

BOND_ENTHALPIES: dict[str, float] = {
    # H–X
    "H–H":   436,
    "H-H":   436,
    "H–F":   570,
    "H-F":   570,
    "H–Cl":  432,
    "H-Cl":  432,
    "H–Br":  366,
    "H-Br":  366,
    "H–I":   298,
    "H-I":   298,
    "H–O":   460,
    "H-O":   460,
    "H–N":   391,
    "H-N":   391,
    "H–C":   413,
    "H-C":   413,
    "H–S":   363,
    "H-S":   363,
    # C–X single bonds
    "C–C":   347,
    "C-C":   347,
    "C=C":   614,
    "C≡C":   839,
    "C–N":   305,
    "C-N":   305,
    "C=N":   615,
    "C≡N":   891,
    "C–O":   358,
    "C-O":   358,
    "C=O":   799,
    "C–F":   485,
    "C-F":   485,
    "C–Cl":  339,
    "C-Cl":  339,
    "C–Br":  285,
    "C-Br":  285,
    "C–I":   240,
    "C-I":   240,
    "C–S":   259,
    "C-S":   259,
    # N–X
    "N–N":   163,
    "N-N":   163,
    "N=N":   418,
    "N≡N":   945,
    "N–O":   201,
    "N-O":   201,
    "N=O":   607,
    "N–F":   272,
    "N-F":   272,
    "N–Cl":  200,
    "N-Cl":  200,
    # O–X
    "O–O":   146,
    "O-O":   146,
    "O=O":   498,
    "O–F":   190,
    "O-F":   190,
    "O–Cl":  203,
    "O-Cl":  203,
    # Halogens
    "F–F":   159,
    "F-F":   159,
    "Cl–Cl": 243,
    "Cl-Cl": 243,
    "Br–Br": 193,
    "Br-Br": 193,
    "I–I":   151,
    "I-I":   151,
    "Cl–Br": 218,
    "Cl-Br": 218,
    "Cl–I":  208,
    "Cl-I":  208,
    "Br–F":  237,
    "Br-F":  237,
    "Br–Cl": 218,
    "Br-Cl": 218,
    "Br–I":  175,
    "Br-I":  175,
    "I–Cl":  208,
    "I-Cl":  208,
    "I–Br":  175,
    "I-Br":  175,
    # S–X
    "S–S":   266,
    "S-S":   266,
    "S=S":   425,
    "S=O":   522,
    "S–F":   327,
    "S-F":   327,
    "S–Cl":  253,
    "S-Cl":  253,
    # Si–X
    "Si–Si": 222,
    "Si-Si": 222,
    "Si–O":  452,
    "Si-O":  452,
    "Si–H":  318,
    "Si-H":  318,
    "Si–F":  597,
    "Si-F":  597,
    "Si–Cl": 381,
    "Si-Cl": 381,
    # P–X
    "P–H":   322,
    "P-H":   322,
    "P–F":   490,
    "P-F":   490,
    "P–Cl":  326,
    "P-Cl":  326,
    "P=O":   544,
    "P–O":   335,
    "P-O":   335,
    "P–P":   201,
    "P-P":   201,
}


def lookup_bond(bond_str: str) -> Optional[float]:
    """
    Look up bond enthalpy. Tries the key as-is, then swapped order.
    E.g. 'Br–F' and 'F–Br' both work.
    """
    val = BOND_ENTHALPIES.get(bond_str)
    if val is not None:
        return val
    # Try reversed: split on – or -
    for sep in ["–", "-"]:
        if sep in bond_str:
            parts = bond_str.split(sep, 1)
            if len(parts) == 2:
                reversed_key = f"{parts[1]}{sep}{parts[0]}"
                val = BOND_ENTHALPIES.get(reversed_key)
                if val is not None:
                    return val
    return None


def list_available_bonds() -> list[str]:
    seen = set()
    result = []
    for key in BOND_ENTHALPIES:
        canonical = key.replace("-", "–")
        if canonical not in seen:
            seen.add(canonical)
            result.append(canonical)
    return sorted(result)


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class BondEnthalpyEntry:
    bond: str
    count: int
    enthalpy_per_bond: float
    total: float


@dataclass
class BondEnthalpyResult:
    broken: list[BondEnthalpyEntry]
    formed: list[BondEnthalpyEntry]
    sum_broken: float
    sum_formed: float
    delta_h: float
    steps: list[str] = field(default_factory=list)


class BondEnthalpyError(ValueError):
    pass


# ---------------------------------------------------------------------------
# Calculator
# ---------------------------------------------------------------------------

def calculate_bond_enthalpy(
    bonds_broken: list[tuple[str, int]],
    bonds_formed: list[tuple[str, int]],
) -> BondEnthalpyResult:
    """
    Calculate ΔH_rxn from bond enthalpies.

    Args:
        bonds_broken: list of (bond_label, count), e.g. [("H–H", 1), ("F–F", 1)]
        bonds_formed:  list of (bond_label, count), e.g. [("H–F", 2)]

    Returns:
        BondEnthalpyResult with ΔH and step-by-step reasoning.
    """
    steps: list[str] = []
    broken_entries: list[BondEnthalpyEntry] = []
    formed_entries: list[BondEnthalpyEntry] = []

    steps.append("### Beregning af ΔH via bindingsenthalpier")
    steps.append("**ΔH_rxn ≈ Σ(bindingsenthalpier brudt) − Σ(bindingsenthalpier dannet)**")
    steps.append("")
    steps.append("#### Bindinger brudt (reaktanter → energi *tilføres*)")

    sum_broken = 0.0
    for bond, count in bonds_broken:
        val = lookup_bond(bond)
        if val is None:
            raise BondEnthalpyError(
                f"Ukendt binding: '{bond}'. "
                "Brug format som 'H–H', 'C=O', 'Br–Br'. "
                f"Tilgængelige bindinger: {', '.join(list_available_bonds()[:20])} …"
            )
        total = val * count
        sum_broken += total
        broken_entries.append(BondEnthalpyEntry(bond, count, val, total))
        steps.append(f"  {count} × {bond}: {count} × {val:.0f} = **+{total:.0f} kJ**")

    steps.append(f"  **Σ(brudt) = +{sum_broken:.0f} kJ**")
    steps.append("")
    steps.append("#### Bindinger dannet (produkter → energi *frigives*)")

    sum_formed = 0.0
    for bond, count in bonds_formed:
        val = lookup_bond(bond)
        if val is None:
            raise BondEnthalpyError(
                f"Ukendt binding: '{bond}'. "
                "Brug format som 'H–F', 'C=O'. "
                f"Tilgængelige bindinger: {', '.join(list_available_bonds()[:20])} …"
            )
        total = val * count
        sum_formed += total
        formed_entries.append(BondEnthalpyEntry(bond, count, val, total))
        steps.append(f"  {count} × {bond}: {count} × {val:.0f} = **−{total:.0f} kJ**")

    steps.append(f"  **Σ(dannet) = −{sum_formed:.0f} kJ**")
    steps.append("")

    delta_h = sum_broken - sum_formed
    sign = "+" if delta_h > 0 else ""
    steps.append(f"#### Resultat")
    steps.append(
        f"ΔH_rxn = +{sum_broken:.0f} − {sum_formed:.0f} = **{sign}{delta_h:.0f} kJ/mol**"
    )
    if delta_h > 0:
        steps.append("→ ΔH > 0: **Endoterm** reaktion (kræver energi)")
    elif delta_h < 0:
        steps.append("→ ΔH < 0: **Eksoterm** reaktion (frigiver energi)")
    else:
        steps.append("→ ΔH = 0: Neutral reaktion")

    return BondEnthalpyResult(
        broken=broken_entries,
        formed=formed_entries,
        sum_broken=sum_broken,
        sum_formed=sum_formed,
        delta_h=delta_h,
        steps=steps,
    )
