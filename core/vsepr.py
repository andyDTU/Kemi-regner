"""
VSEPR geometry prediction and molecular polarity.

Given a molecule formula or (bonding_pairs, lone_pairs) directly, returns:
- geometry name (English + Danish)
- bond angles
- polar / nonpolar classification
- planar / non-planar classification
"""

from dataclasses import dataclass, field
from typing import Optional

# ---------------------------------------------------------------------------
# Data tables
# ---------------------------------------------------------------------------

@dataclass
class GeometryInfo:
    name_en: str
    name_da: str
    bond_angles: str          # e.g. "109.5°"
    is_planar: bool
    is_polar_if_diff_groups: bool  # True if geometry CAN be polar with unequal substituents
    description: str          # short exam-style explanation


# (steric_number, lone_pairs) → GeometryInfo
GEOMETRY_TABLE: dict[tuple[int, int], GeometryInfo] = {
    # steric 2
    (2, 0): GeometryInfo("linear",                "lineær",              "180°",        True,  False, "2 bindingspar, 0 frie elektroner → lineær, 180°"),
    # steric 3
    (3, 0): GeometryInfo("trigonal planar",        "trigonal plan",       "120°",        True,  True,  "3 bindingspar, 0 frie elektroner → trigonal plan, 120°"),
    (3, 1): GeometryInfo("bent",                   "vinklet (120°)",      "~120°",       True,  True,  "2 bindingspar, 1 frit elektronpar → vinklet, ~120°"),
    # steric 4
    (4, 0): GeometryInfo("tetrahedral",            "tetraedrisk",         "109.5°",      False, True,  "4 bindingspar, 0 frie elektroner → tetraedrisk, 109.5°"),
    (4, 1): GeometryInfo("trigonal pyramidal",     "trigonal pyramidal",  "~107°",       False, True,  "3 bindingspar, 1 frit elektronpar → trigonal pyramidal, ~107°"),
    (4, 2): GeometryInfo("bent",                   "vinklet (sp³)",       "~109.5°",     False, True,  "2 bindingspar, 2 frie elektroner → vinklet, ~109.5° (ideal sp³; frie elektroner reducerer til ~104.5° i H₂O)"),
    (4, 3): GeometryInfo("linear",                 "lineær",              "180°",        True,  False, "1 bindingspar, 3 frie elektroner → lineær, 180°"),
    # steric 5
    (5, 0): GeometryInfo("trigonal bipyramidal",   "trigonal bipyramidal","90°, 120°",   False, True,  "5 bindingspar, 0 frie elektroner → trigonal bipyramidal"),
    (5, 1): GeometryInfo("see-saw",                "vippestol (see-saw)", "~90°, ~120°", False, True,  "4 bindingspar, 1 frit elektronpar → vippestol"),
    (5, 2): GeometryInfo("T-shaped",               "T-formet",            "~90°",        True,  True,  "3 bindingspar, 2 frie elektroner → T-formet"),
    (5, 3): GeometryInfo("linear",                 "lineær",              "180°",        True,  False, "2 bindingspar, 3 frie elektroner → lineær"),
    # steric 6
    (6, 0): GeometryInfo("octahedral",             "oktaedrisk",          "90°",         False, False, "6 bindingspar, 0 frie elektroner → oktaedrisk, 90°"),
    (6, 1): GeometryInfo("square pyramidal",       "kvadratisk pyramidal","~90°",        False, True,  "5 bindingspar, 1 frit elektronpar → kvadratisk pyramidal"),
    (6, 2): GeometryInfo("square planar",          "kvadratisk plan",     "90°",         True,  False, "4 bindingspar, 2 frie elektroner → kvadratisk plan"),
}

# ---------------------------------------------------------------------------
# Known molecules (formula → bonding_pairs, lone_pairs, all_same_substituents)
# ---------------------------------------------------------------------------

@dataclass
class MoleculeEntry:
    bonding_pairs: int
    lone_pairs: int
    all_same_substituents: bool   # True if all terminal atoms identical (→ symmetric)
    example_note: str = ""


MOLECULE_DB: dict[str, MoleculeEntry] = {
    # Diatomics / linear
    "HF":    MoleculeEntry(1, 3, True,  ""),
    "HCl":   MoleculeEntry(1, 3, True,  ""),
    "HBr":   MoleculeEntry(1, 3, True,  ""),
    "HI":    MoleculeEntry(1, 3, True,  ""),
    "H2":    MoleculeEntry(1, 0, True,  ""),
    "N2":    MoleculeEntry(1, 2, True,  ""),
    "O2":    MoleculeEntry(1, 2, True,  ""),
    "F2":    MoleculeEntry(1, 3, True,  ""),
    "Cl2":   MoleculeEntry(1, 3, True,  ""),
    "Br2":   MoleculeEntry(1, 3, True,  ""),
    "I2":    MoleculeEntry(1, 3, True,  ""),
    "CO":    MoleculeEntry(1, 2, True,  ""),
    # Linear (triatomic)
    "CO2":   MoleculeEntry(2, 0, True,  "2 dobbeltbindinger, ingen frie par → lineær, upolar"),
    "CS2":   MoleculeEntry(2, 0, True,  "lineær, upolar"),
    "HCN":   MoleculeEntry(2, 0, False, "lineær, polær (C–N trippelbinding)"),
    "BeH2":  MoleculeEntry(2, 0, True,  "lineær, upolar"),
    "BeCl2": MoleculeEntry(2, 0, True,  "lineær, upolar"),
    "NO2":   MoleculeEntry(2, 1, False, "vinklet ~134°, polær"),
    # Trigonal planar
    "BF3":   MoleculeEntry(3, 0, True,  "trigonal plan, upolar"),
    "BCl3":  MoleculeEntry(3, 0, True,  "trigonal plan, upolar"),
    "SO3":   MoleculeEntry(3, 0, True,  "trigonal plan, upolar"),
    "AlCl3": MoleculeEntry(3, 0, True,  "trigonal plan, upolar"),
    # Bent ~120°
    "SO2":   MoleculeEntry(2, 1, False, "vinklet ~119°, polær"),
    "O3":    MoleculeEntry(2, 1, False, "vinklet ~117°, polær"),
    # Tetrahedral
    "CH4":   MoleculeEntry(4, 0, True,  "tetraedrisk, upolar"),
    "CCl4":  MoleculeEntry(4, 0, True,  "tetraedrisk, upolar"),
    "CBr4":  MoleculeEntry(4, 0, True,  "tetraedrisk, upolar"),
    "CF4":   MoleculeEntry(4, 0, True,  "tetraedrisk, upolar"),
    "SiH4":  MoleculeEntry(4, 0, True,  "tetraedrisk, upolar"),
    "SiCl4": MoleculeEntry(4, 0, True,  "tetraedrisk, upolar"),
    "NH4":   MoleculeEntry(4, 0, True,  "tetraedrisk, upolar (ion)"),
    "SO4":   MoleculeEntry(4, 0, True,  "tetraedrisk, upolar (ion)"),
    "PO4":   MoleculeEntry(4, 0, True,  "tetraedrisk (ion)"),
    "BF4":   MoleculeEntry(4, 0, True,  "tetraedrisk (ion)"),
    "CH3Cl": MoleculeEntry(4, 0, False, "tetraedrisk, polær"),
    "CH3F":  MoleculeEntry(4, 0, False, "tetraedrisk, polær"),
    "CHCl3": MoleculeEntry(4, 0, False, "tetraedrisk, polær"),
    "CH2Cl2":MoleculeEntry(4, 0, False, "tetraedrisk, polær"),
    # Trigonal pyramidal
    "NH3":   MoleculeEntry(3, 1, True,  "trigonal pyramidal, polær"),
    "NF3":   MoleculeEntry(3, 1, True,  "trigonal pyramidal, polær"),
    "NCl3":  MoleculeEntry(3, 1, True,  "trigonal pyramidal, polær"),
    "PH3":   MoleculeEntry(3, 1, True,  "trigonal pyramidal, polær"),
    "PCl3":  MoleculeEntry(3, 1, True,  "trigonal pyramidal, polær"),
    "PF3":   MoleculeEntry(3, 1, True,  "trigonal pyramidal, polær"),
    "AsCl3": MoleculeEntry(3, 1, True,  "trigonal pyramidal, polær"),
    # Bent ~104.5°
    "H2O":   MoleculeEntry(2, 2, True,  "vinklet ~104.5°, polær"),
    "H2S":   MoleculeEntry(2, 2, True,  "vinklet ~92°, polær"),
    "H2Se":  MoleculeEntry(2, 2, True,  "vinklet, polær"),
    "OF2":   MoleculeEntry(2, 2, True,  "vinklet, polær"),
    "SCl2":  MoleculeEntry(2, 2, True,  "vinklet, polær"),
    # Trigonal bipyramidal
    "PF5":   MoleculeEntry(5, 0, True,  "trigonal bipyramidal, upolar"),
    "PCl5":  MoleculeEntry(5, 0, True,  "trigonal bipyramidal, upolar"),
    "AsF5":  MoleculeEntry(5, 0, True,  "trigonal bipyramidal, upolar"),
    # See-saw
    "SF4":   MoleculeEntry(4, 1, False, "vippestol, polær"),
    "TeCl4": MoleculeEntry(4, 1, False, "vippestol, polær"),
    # T-shaped
    "ClF3":  MoleculeEntry(3, 2, False, "T-formet, polær"),
    "BrF3":  MoleculeEntry(3, 2, False, "T-formet, polær"),
    # Octahedral
    "SF6":   MoleculeEntry(6, 0, True,  "oktaedrisk, upolar"),
    "SeF6":  MoleculeEntry(6, 0, True,  "oktaedrisk, upolar"),
    # Square pyramidal
    "BrF5":  MoleculeEntry(5, 1, False, "kvadratisk pyramidal, polær"),
    "IF5":   MoleculeEntry(5, 1, False, "kvadratisk pyramidal, polær"),
    # Square planar
    "XeF4":  MoleculeEntry(4, 2, True,  "kvadratisk plan, upolar"),
    "ICl4":  MoleculeEntry(4, 2, True,  "kvadratisk plan (ion), upolar"),
    # Polyatomics
    "XeF2":  MoleculeEntry(2, 3, True,  "lineær, upolar"),
}


# ---------------------------------------------------------------------------
# Hybridization lookup (function of steric number only)
# ---------------------------------------------------------------------------

HYBRIDIZATION: dict[int, str] = {
    2: "sp",
    3: "sp²",
    4: "sp³",
    5: "sp³d",
    6: "sp³d²",
}

HYBRIDIZATION_DESCRIPTION: dict[int, str] = {
    2: "sp — 2 hybride orbitaler, lineær arrangement, 180°",
    3: "sp² — 3 hybride orbitaler, trigonal plan arrangement, 120°",
    4: "sp³ — 4 hybride orbitaler, tetraedrisk arrangement, 109.5°",
    5: "sp³d — 5 hybride orbitaler, trigonal bipyramidal arrangement",
    6: "sp³d² — 6 hybride orbitaler, oktaedrisk arrangement, 90°",
}


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class VSEPRResult:
    formula: str
    bonding_pairs: int
    lone_pairs: int
    steric_number: int
    geometry: GeometryInfo
    hybridization: str
    is_polar: bool
    polarity_reason: str
    steps: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class VSEPRError(ValueError):
    pass


def predict_vsepr(
    formula: str,
    bonding_pairs: Optional[int] = None,
    lone_pairs: Optional[int] = None,
    all_same_substituents: Optional[bool] = None,
) -> VSEPRResult:
    """
    Predict VSEPR geometry for a molecule.

    If bonding_pairs/lone_pairs are given, use them directly.
    Otherwise look up the formula in the database.
    """
    formula = formula.strip()
    steps: list[str] = []

    if bonding_pairs is not None and lone_pairs is not None:
        bp = bonding_pairs
        lp = lone_pairs
        same = all_same_substituents if all_same_substituents is not None else True
        note = ""
    else:
        # Normalise: try exact, then without charges like 2+/2-
        key = formula
        entry = MOLECULE_DB.get(key)
        if entry is None:
            # Try stripping trailing charge notation (e.g. NH4+, SO42-)
            import re
            clean = re.sub(r"[\+\-]\d*$|\d*[\+\-]$", "", formula)
            entry = MOLECULE_DB.get(clean)
        if entry is None:
            raise VSEPRError(
                f"'{formula}' er ikke i VSEPR-databasen. "
                "Indtast antallet af bindingspar og frie elektronpar manuelt."
            )
        bp = entry.bonding_pairs
        lp = entry.lone_pairs
        same = entry.all_same_substituents
        note = entry.example_note

    sn = bp + lp

    steps.append(f"**Formel:** {formula}")
    steps.append(f"**Bindingspar (BP):** {bp}   |   **Frie elektronpar (LP):** {lp}")
    steps.append(f"**Sterisk tal (SN) = BP + LP = {bp} + {lp} = {sn}**")

    geom = GEOMETRY_TABLE.get((sn, lp))
    if geom is None:
        raise VSEPRError(
            f"Ingen geometri i tabellen for SN={sn}, LP={lp}. "
            "Kombinationen er usædvanlig; kontrollér inputtet."
        )

    hybridization = HYBRIDIZATION.get(sn, f"sp³d{sn-4}" if sn > 6 else "?")

    steps.append(f"**Hybridisering:** SN={sn} → **{hybridization}**")
    steps.append(f"  {HYBRIDIZATION_DESCRIPTION.get(sn, '')}")
    steps.append(f"**Elektrongeometri baseret på SN={sn}, LP={lp}:**")
    steps.append(f"→ **{geom.name_en}** ({geom.name_da})")
    steps.append(f"→ Bindingsvinkler: **{geom.bond_angles}**")
    steps.append(f"→ Plan: {'Ja' if geom.is_planar else 'Nej'}")

    # Polarity logic
    # Geometries where all bond dipoles cancel regardless of lone pairs
    # (lone pairs are in symmetric axial positions):
    #   square planar (6,2), linear with lone pairs (4,3), (5,3)
    always_nonpolar = not geom.is_polar_if_diff_groups

    if always_nonpolar and same:
        is_polar = False
        polarity_reason = (
            f"Geometri '{geom.name_en}' har symmetrisk arrangement af bindingspar og frie par "
            "→ alle dipoler nulstilles → **upolært**, selv med frie elektronpar."
        )
    elif not same:
        is_polar = True
        polarity_reason = (
            "Terminale atomer er ikke alle ens (forskellige elektronegativiteter) "
            "→ dipolerne nulstilles ikke → **polært**."
        )
    elif lp > 0:
        is_polar = True
        polarity_reason = (
            f"Molekylet har {lp} frit/frie elektronpar, som forskyver ladningsfordelingen "
            "→ resulterende dipol ≠ 0 → **polært**."
        )
    else:
        is_polar = False
        polarity_reason = (
            f"Symmetrisk geometri ({geom.name_en}) med identiske terminale atomer "
            "→ dipolerne nulstilles → **upolært**."
        )

    steps.append("")
    steps.append("**Polaritet:**")
    steps.append(polarity_reason)

    if note:
        steps.append(f"*Note: {note}*")

    return VSEPRResult(
        formula=formula,
        bonding_pairs=bp,
        lone_pairs=lp,
        steric_number=sn,
        geometry=geom,
        hybridization=hybridization,
        is_polar=is_polar,
        polarity_reason=polarity_reason,
        steps=steps,
    )


def list_known_molecules() -> list[str]:
    return sorted(MOLECULE_DB.keys())
