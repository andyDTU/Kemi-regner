"""
Intermolecular forces (IMF) classifier.

Given molecule properties, identifies the dominant IMF types and
provides exam-style reasoning about vapor pressure, boiling point,
and relative volatility.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class IMFType(str, Enum):
    ION_ION          = "Ion–ion (ionbinding)"
    ION_DIPOLE       = "Ion–dipol"
    HYDROGEN_BOND    = "Hydrogenbinding (H-bond)"
    DIPOLE_DIPOLE    = "Dipol–dipol"
    VAN_DER_WAALS    = "London dispersionskraft (van der Waals)"


IMF_STRENGTH_RANK = {
    IMFType.ION_ION:       5,
    IMFType.ION_DIPOLE:    4,
    IMFType.HYDROGEN_BOND: 3,
    IMFType.DIPOLE_DIPOLE: 2,
    IMFType.VAN_DER_WAALS: 1,
}

IMF_STRENGTH_LABEL = {
    IMFType.ION_ION:       "Meget stærk (~100–1000 kJ/mol)",
    IMFType.ION_DIPOLE:    "Stærk (~40–600 kJ/mol)",
    IMFType.HYDROGEN_BOND: "Moderat–stærk (~10–40 kJ/mol)",
    IMFType.DIPOLE_DIPOLE: "Moderat (~5–25 kJ/mol)",
    IMFType.VAN_DER_WAALS: "Svag (<5 kJ/mol, skalerer med M_r)",
}


@dataclass
class IMFResult:
    formula: str
    imf_types: list[IMFType]
    dominant_imf: IMFType
    is_polar: bool
    has_hbond_donor: bool
    molar_mass_approx: Optional[float]
    boiling_point_trend: str       # "høj", "moderat", "lav"
    vapor_pressure_trend: str      # "lav", "moderat", "høj"
    steps: list[str] = field(default_factory=list)


@dataclass
class MoleculeIMFEntry:
    is_ion: bool
    is_polar: bool
    hbond_donor: bool      # has N–H, O–H, or F–H
    hbond_acceptor: bool   # has lone pairs on N, O, F
    approx_molar_mass: float
    note: str = ""


MOLECULE_IMF_DB: dict[str, MoleculeIMFEntry] = {
    # Noble gases
    "He":    MoleculeIMFEntry(False, False, False, False, 4.0,   "monatomisk, kun LDF"),
    "Ne":    MoleculeIMFEntry(False, False, False, False, 20.2,  "monatomisk, kun LDF"),
    "Ar":    MoleculeIMFEntry(False, False, False, False, 39.9,  "monatomisk, kun LDF"),
    "Kr":    MoleculeIMFEntry(False, False, False, False, 83.8,  "monatomisk, kun LDF"),
    "Xe":    MoleculeIMFEntry(False, False, False, False, 131.3, "monatomisk, kun LDF"),
    # Small nonpolar
    "H2":    MoleculeIMFEntry(False, False, False, False, 2.0,   ""),
    "N2":    MoleculeIMFEntry(False, False, False, False, 28.0,  ""),
    "O2":    MoleculeIMFEntry(False, False, False, False, 32.0,  ""),
    "F2":    MoleculeIMFEntry(False, False, False, False, 38.0,  ""),
    "Cl2":   MoleculeIMFEntry(False, False, False, False, 70.9,  ""),
    "Br2":   MoleculeIMFEntry(False, False, False, False, 160.0, ""),
    "I2":    MoleculeIMFEntry(False, False, False, False, 254.0, ""),
    "CH4":   MoleculeIMFEntry(False, False, False, False, 16.0,  ""),
    "C2H6":  MoleculeIMFEntry(False, False, False, False, 30.1,  ""),
    "C3H8":  MoleculeIMFEntry(False, False, False, False, 44.1,  ""),
    "C4H10": MoleculeIMFEntry(False, False, False, False, 58.1,  ""),
    "C6H6":  MoleculeIMFEntry(False, False, False, False, 78.1,  "benzen, LDF + svag dipol"),
    "CCl4":  MoleculeIMFEntry(False, False, False, False, 153.8, "symmetrisk → kun LDF"),
    "CO2":   MoleculeIMFEntry(False, False, False, False, 44.0,  "lineær → kun LDF"),
    "CS2":   MoleculeIMFEntry(False, False, False, False, 76.1,  "lineær → kun LDF"),
    "SF6":   MoleculeIMFEntry(False, False, False, False, 146.1, ""),
    # Polar, no H-bond donor
    "CO":    MoleculeIMFEntry(False, True,  False, True,  28.0,  "svag dipol"),
    "SO2":   MoleculeIMFEntry(False, True,  False, True,  64.1,  ""),
    "SO3":   MoleculeIMFEntry(False, False, False, True,  80.1,  "symmetrisk → kun LDF"),
    "H2S":   MoleculeIMFEntry(False, True,  False, True,  34.1,  "S er ikke elektronegativ nok til H-bond"),
    "HCl":   MoleculeIMFEntry(False, True,  False, True,  36.5,  "polar, dipol-dipol"),
    "HBr":   MoleculeIMFEntry(False, True,  False, True,  80.9,  "polar, dipol-dipol"),
    "HI":    MoleculeIMFEntry(False, True,  False, True,  127.9, "polar, dipol-dipol"),
    "NO":    MoleculeIMFEntry(False, True,  False, True,  30.0,  ""),
    "NO2":   MoleculeIMFEntry(False, True,  False, True,  46.0,  ""),
    "NH3":   MoleculeIMFEntry(False, True,  True,  True,  17.0,  "H-bond donor og acceptor"),
    "PH3":   MoleculeIMFEntry(False, True,  False, True,  34.0,  "P er ikke elektronegativ nok til H-bond"),
    # H-bond formers
    "HF":    MoleculeIMFEntry(False, True,  True,  True,  20.0,  "stærk H-bond"),
    "H2O":   MoleculeIMFEntry(False, True,  True,  True,  18.0,  "stærk H-bond"),
    "CH3OH": MoleculeIMFEntry(False, True,  True,  True,  32.0,  "methanol, H-bond"),
    "C2H5OH":MoleculeIMFEntry(False, True,  True,  True,  46.1,  "ethanol, H-bond"),
    "CH3COOH":MoleculeIMFEntry(False,True,  True,  True,  60.1,  "eddikesyre, stærk H-bond"),
    "HCOOH": MoleculeIMFEntry(False, True,  True,  True,  46.0,  "myresyre, stærk H-bond"),
    "CH3NH2":MoleculeIMFEntry(False, True,  True,  True,  31.1,  "methylamin, H-bond"),
    "N2H4":  MoleculeIMFEntry(False, True,  True,  True,  32.0,  "hydrazin, H-bond"),
    "C6H5OH":MoleculeIMFEntry(False, True,  True,  True,  94.1,  "phenol, H-bond"),
    "HCHO":  MoleculeIMFEntry(False, True,  False, True,  30.0,  "formaldehyd, dipol-dipol (ingen donor)"),
    "CH3CHO":MoleculeIMFEntry(False, True,  False, True,  44.1,  "acetaldehyd, dipol-dipol (ingen donor)"),
    "CH3COCH3":MoleculeIMFEntry(False,True, False, True,  58.1,  "acetone, dipol-dipol (acceptor, ingen donor)"),
    "CHCl3": MoleculeIMFEntry(False, True,  False, False, 119.4, "kloroform, dipol-dipol"),
    "CH2Cl2":MoleculeIMFEntry(False, True,  False, False, 84.9,  "dichlormethan, dipol-dipol"),
    "CH3Cl": MoleculeIMFEntry(False, True,  False, False, 50.5,  "chlormethan, dipol-dipol"),
    "CH3F":  MoleculeIMFEntry(False, True,  False, False, 34.0,  "fluormethan, dipol-dipol"),
    "CH3Br": MoleculeIMFEntry(False, True,  False, False, 94.9,  "brommethan, dipol-dipol"),
    "CCl4":  MoleculeIMFEntry(False, False, False, False, 153.8, "tetrachlormethan, upolær, London"),
    "CF4":   MoleculeIMFEntry(False, False, False, False, 88.0,  "tetrafluormethan, upolær, London"),
    "CBr4":  MoleculeIMFEntry(False, False, False, False, 331.6, "tetrabromethan, upolær, London"),
    # Alkaner
    "C2H6":  MoleculeIMFEntry(False, False, False, False, 30.1,  "ethan, London"),
    "C3H8":  MoleculeIMFEntry(False, False, False, False, 44.1,  "propan, London"),
    "C4H10": MoleculeIMFEntry(False, False, False, False, 58.1,  "butan, London"),
    "C5H12": MoleculeIMFEntry(False, False, False, False, 72.2,  "pentan, London"),
    "C6H14": MoleculeIMFEntry(False, False, False, False, 86.2,  "hexan, London"),
    "C8H18": MoleculeIMFEntry(False, False, False, False, 114.2, "oktan, London"),
    # Alkener/alkiner
    "C2H4":  MoleculeIMFEntry(False, False, False, False, 28.1,  "ethylen, London"),
    "C3H6":  MoleculeIMFEntry(False, False, False, False, 42.1,  "propen, London"),
    "C2H2":  MoleculeIMFEntry(False, False, False, False, 26.0,  "acetylen, London"),
    # Aromater
    "C6H6":  MoleculeIMFEntry(False, False, False, False, 78.1,  "benzen, London"),
    "C7H8":  MoleculeIMFEntry(False, False, False, False, 92.1,  "toluen, svagt polær, London"),
    # Alkoholer
    "C3H7OH":MoleculeIMFEntry(False, True,  True,  True,  60.1,  "1-propanol, H-bond"),
    "C4H9OH":MoleculeIMFEntry(False, True,  True,  True,  74.1,  "1-butanol, H-bond"),
    "C2H4OH2":MoleculeIMFEntry(False,True,  True,  True,  62.1,  "ethylenglykol, stærk H-bond (2 OH)"),
    "C3H5OH3":MoleculeIMFEntry(False,True,  True,  True,  92.1,  "glycerol, meget stærk H-bond (3 OH)"),
    # Ethere (acceptor men ingen donor)
    "C2H5OC2H5":MoleculeIMFEntry(False,True,False, True,  74.1,  "diethylether, dipol-dipol (acceptor, ingen donor)"),
    "CH3OCH3":MoleculeIMFEntry(False,True, False, True,  46.1,  "dimethylether, dipol-dipol (acceptor, ingen donor)"),
    # Estere
    "CH3COOC2H5":MoleculeIMFEntry(False,True,False,True,  88.1,  "ethylacetat, dipol-dipol (acceptor, ingen donor)"),
    "CH3COOCH3":MoleculeIMFEntry(False,True,False,True,   74.1,  "methylacetat, dipol-dipol"),
    # Aminer
    "CH3NH2":MoleculeIMFEntry(False, True,  True,  True,  31.1,  "methylamin, H-bond"),
    "(CH3)2NH":MoleculeIMFEntry(False,True, True,  True,  45.1,  "dimethylamin, H-bond (svagere end primær)"),
    "(CH3)3N":MoleculeIMFEntry(False, True, False, True,  59.1,  "trimethylamin, dipol-dipol (ingen donor)"),
    # Syrer
    "C2H5COOH":MoleculeIMFEntry(False,True, True,  True,  74.1,  "propansyre, H-bond"),
    "C3H7COOH":MoleculeIMFEntry(False,True, True,  True,  88.1,  "butansyre, H-bond"),
    # Nitriler
    "CH3CN": MoleculeIMFEntry(False, True,  False, True,  41.1,  "acetonitril, stærk dipol-dipol"),
    "HCN":   MoleculeIMFEntry(False, True,  False, True,  27.0,  "hydrogencyanid, dipol-dipol"),
    # Uorganiske
    "BF3":   MoleculeIMFEntry(False, False, False, False, 67.8,  "bortrifluorid, upolær (trigonal plan), London"),
    "BCl3":  MoleculeIMFEntry(False, False, False, False, 117.2, "bortrichlorid, upolær (trigonal plan), London"),
    "PCl3":  MoleculeIMFEntry(False, True,  False, True,  137.3, "phosphortrichlorid, dipol-dipol"),
    "PCl5":  MoleculeIMFEntry(False, False, False, False, 208.2, "phosphorpentachlorid, upolær, London"),
    "SiH4":  MoleculeIMFEntry(False, False, False, False, 32.1,  "silan, London"),
    "GeH4":  MoleculeIMFEntry(False, False, False, False, 76.6,  "german, London"),
    "H2Se":  MoleculeIMFEntry(False, True,  False, True,  81.0,  "hydrogenselend, svag dipol (ingen H-bond)"),
    "H2Te":  MoleculeIMFEntry(False, True,  False, True,  129.6, "hydrogentellurd, svag dipol"),
    "OF2":   MoleculeIMFEntry(False, True,  False, False, 54.0,  "oxydifluorid, dipol-dipol"),
    "NF3":   MoleculeIMFEntry(False, True,  False, False, 71.0,  "nitrogentrifluorid, dipol-dipol"),
    "ClF":   MoleculeIMFEntry(False, True,  False, False, 54.5,  "chlorfluorid, dipol-dipol"),
    "ICl":   MoleculeIMFEntry(False, True,  False, False, 162.4, "iodchlorid, dipol-dipol"),
    # Ions
    "NaCl":  MoleculeIMFEntry(True,  False, False, False, 58.4,  "ionbinding"),
    "KCl":   MoleculeIMFEntry(True,  False, False, False, 74.6,  "ionbinding"),
    "NaOH":  MoleculeIMFEntry(True,  False, False, False, 40.0,  "ionbinding"),
    "HNO3":  MoleculeIMFEntry(False, True,  True,  True,  63.0,  "stærk syre, H-bond + dipol"),
    "H2SO4": MoleculeIMFEntry(False, True,  True,  True,  98.1,  "stærk syre, H-bond"),
    "H3PO4": MoleculeIMFEntry(False, True,  True,  True,  98.0,  "H-bond"),
}


class IMFError(ValueError):
    pass


def classify_imf(
    formula: str,
    is_ion: Optional[bool] = None,
    is_polar: Optional[bool] = None,
    has_hbond_donor: Optional[bool] = None,
    has_hbond_acceptor: Optional[bool] = None,
    molar_mass: Optional[float] = None,
) -> IMFResult:
    """
    Classify the dominant intermolecular forces for a molecule.

    Manual overrides take precedence over the database lookup.
    """
    formula = formula.strip()
    steps: list[str] = []

    entry = MOLECULE_IMF_DB.get(formula)
    if entry is None:
        import re
        clean = re.sub(r"[\+\-]\d*$|\d*[\+\-]$", "", formula)
        entry = MOLECULE_IMF_DB.get(clean)

    # Merge DB data with any manual overrides
    if entry is not None:
        _is_ion          = is_ion          if is_ion          is not None else entry.is_ion
        _is_polar        = is_polar        if is_polar        is not None else entry.is_polar
        _hbond_donor     = has_hbond_donor if has_hbond_donor is not None else entry.hbond_donor
        _hbond_acceptor  = has_hbond_acceptor if has_hbond_acceptor is not None else entry.hbond_acceptor
        _molar_mass      = molar_mass      if molar_mass      is not None else entry.approx_molar_mass
        note             = entry.note
    elif is_polar is not None:
        _is_ion         = is_ion          or False
        _is_polar       = is_polar
        _hbond_donor    = has_hbond_donor or False
        _hbond_acceptor = has_hbond_acceptor or False
        _molar_mass     = molar_mass
        note            = ""
    else:
        raise IMFError(
            f"'{formula}' er ikke i IMF-databasen. "
            "Angiv egenskaberne manuelt (polær, H-bond donor/acceptor)."
        )

    steps.append(f"**Molekyle:** {formula}")
    if note:
        steps.append(f"*{note}*")
    steps.append("")

    # Build IMF list
    imf_types: list[IMFType] = []

    if _is_ion:
        imf_types.append(IMFType.ION_ION)
        steps.append("✅ **Ion–ion:** Molekylet er et ionisk stof (ladede partikler tiltrækker hinanden stærkt).")
    else:
        if _hbond_donor and _hbond_acceptor:
            imf_types.append(IMFType.HYDROGEN_BOND)
            steps.append(
                "✅ **Hydrogenbinding:** Molekylet har H bundet til N, O eller F (donor) "
                "OG et frit elektronpar på N, O eller F (acceptor) → hydrogenbindinger dannes."
            )
        if _is_polar:
            imf_types.append(IMFType.DIPOLE_DIPOLE)
            steps.append("✅ **Dipol–dipol:** Molekylet er polært → permanente dipoler tiltrækker hinanden.")
        imf_types.append(IMFType.VAN_DER_WAALS)
        steps.append(
            "✅ **London dispersionskraft (van der Waals):** Alle molekyler har disse. "
            f"Styrken stiger med molarmassen ({'~' + str(_molar_mass) + ' g/mol' if _molar_mass else 'ukendt'})."
        )

    dominant = max(imf_types, key=lambda t: IMF_STRENGTH_RANK[t])

    steps.append("")
    steps.append(f"**Dominerende kraft:** {dominant.value}")
    steps.append(f"**Styrke:** {IMF_STRENGTH_LABEL[dominant]}")

    # Boiling point / vapor pressure trend
    rank = IMF_STRENGTH_RANK[dominant]
    if rank >= 3:
        bp_trend = "høj"
        vp_trend = "lav"
    elif rank == 2:
        bp_trend = "moderat"
        vp_trend = "moderat"
    else:
        bp_trend = "lav"
        vp_trend = "høj"

    steps.append("")
    steps.append("**Kogepunkt & damptryk:**")
    steps.append(
        f"Stærkere IMF → højere kogepunkt, lavere damptryk (ved fast temperatur)."
    )
    steps.append(
        f"For {formula}: kogepunkt **{bp_trend}**, damptryk **{vp_trend}** sammenlignet med "
        "stoffer med kun London-kræfter og tilsvarende molarmasse."
    )

    return IMFResult(
        formula=formula,
        imf_types=imf_types,
        dominant_imf=dominant,
        is_polar=_is_polar,
        has_hbond_donor=_hbond_donor,
        molar_mass_approx=_molar_mass,
        boiling_point_trend=bp_trend,
        vapor_pressure_trend=vp_trend,
        steps=steps,
    )


def compare_imf(formulas: list[str]) -> list[tuple[str, IMFResult]]:
    """
    Classify multiple molecules and return them sorted from lowest to highest boiling point
    (weakest to strongest IMF).
    """
    results = []
    for f in formulas:
        try:
            r = classify_imf(f)
            results.append((f, r))
        except IMFError:
            pass
    results.sort(key=lambda x: (
        IMF_STRENGTH_RANK[x[1].dominant_imf],
        x[1].molar_mass_approx or 0,
    ))
    return results


def list_known_molecules() -> list[str]:
    return sorted(MOLECULE_IMF_DB.keys())
