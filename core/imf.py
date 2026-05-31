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
    bp_celsius: Optional[float] = None  # actual BP for accurate comparison sorting


MOLECULE_IMF_DB: dict[str, MoleculeIMFEntry] = {
    # Noble gases
    "He":    MoleculeIMFEntry(False, False, False, False, 4.0,   "monatomisk, kun LDF",                           bp_celsius=-269.0),
    "Ne":    MoleculeIMFEntry(False, False, False, False, 20.2,  "monatomisk, kun LDF",                           bp_celsius=-246.0),
    "Ar":    MoleculeIMFEntry(False, False, False, False, 39.9,  "monatomisk, kun LDF",                           bp_celsius=-186.0),
    "Kr":    MoleculeIMFEntry(False, False, False, False, 83.8,  "monatomisk, kun LDF",                           bp_celsius=-153.0),
    "Xe":    MoleculeIMFEntry(False, False, False, False, 131.3, "monatomisk, kun LDF",                           bp_celsius=-108.0),
    # Small nonpolar
    "H2":    MoleculeIMFEntry(False, False, False, False, 2.0,   "",                                              bp_celsius=-253.0),
    "N2":    MoleculeIMFEntry(False, False, False, False, 28.0,  "",                                              bp_celsius=-196.0),
    "O2":    MoleculeIMFEntry(False, False, False, False, 32.0,  "",                                              bp_celsius=-183.0),
    "F2":    MoleculeIMFEntry(False, False, False, False, 38.0,  "",                                              bp_celsius=-188.0),
    "Cl2":   MoleculeIMFEntry(False, False, False, False, 70.9,  "",                                              bp_celsius=-34.0),
    "Br2":   MoleculeIMFEntry(False, False, False, False, 160.0, "",                                              bp_celsius=59.0),
    "I2":    MoleculeIMFEntry(False, False, False, False, 254.0, "",                                              bp_celsius=184.0),
    "CH4":   MoleculeIMFEntry(False, False, False, False, 16.0,  "",                                              bp_celsius=-161.0),
    "C2H6":  MoleculeIMFEntry(False, False, False, False, 30.1,  "ethan, London",                                 bp_celsius=-89.0),
    "C3H8":  MoleculeIMFEntry(False, False, False, False, 44.1,  "propan, London",                                bp_celsius=-42.0),
    "C4H10": MoleculeIMFEntry(False, False, False, False, 58.1,  "butan, London",                                 bp_celsius=-1.0),
    "C5H12": MoleculeIMFEntry(False, False, False, False, 72.2,  "pentan, London",                                bp_celsius=36.0),
    "C6H14": MoleculeIMFEntry(False, False, False, False, 86.2,  "hexan, London",                                 bp_celsius=69.0),
    "C8H18": MoleculeIMFEntry(False, False, False, False, 114.2, "oktan, London",                                 bp_celsius=126.0),
    "C6H6":  MoleculeIMFEntry(False, False, False, False, 78.1,  "benzen, LDF + svag dipol",                      bp_celsius=80.0),
    "C7H8":  MoleculeIMFEntry(False, False, False, False, 92.1,  "toluen, svagt polær, London",                   bp_celsius=111.0),
    "CCl4":  MoleculeIMFEntry(False, False, False, False, 153.8, "symmetrisk → kun LDF",                          bp_celsius=77.0),
    "CO2":   MoleculeIMFEntry(False, False, False, False, 44.0,  "lineær → kun LDF",                              bp_celsius=-78.0),
    "CS2":   MoleculeIMFEntry(False, False, False, False, 76.1,  "lineær → kun LDF",                              bp_celsius=46.0),
    "SF6":   MoleculeIMFEntry(False, False, False, False, 146.1, "",                                              bp_celsius=-64.0),
    "CF4":   MoleculeIMFEntry(False, False, False, False, 88.0,  "tetrafluormethan, upolær, London",               bp_celsius=-128.0),
    "CBr4":  MoleculeIMFEntry(False, False, False, False, 331.6, "tetrabromethan, upolær, London",                 bp_celsius=190.0),
    # Alkener/alkiner
    "C2H4":  MoleculeIMFEntry(False, False, False, False, 28.1,  "ethylen, London",                               bp_celsius=-104.0),
    "C3H6":  MoleculeIMFEntry(False, False, False, False, 42.1,  "propen, London",                                bp_celsius=-47.0),
    "C2H2":  MoleculeIMFEntry(False, False, False, False, 26.0,  "acetylen, London",                              bp_celsius=-84.0),
    # Polar, no H-bond donor
    "CO":    MoleculeIMFEntry(False, True,  False, True,  28.0,  "svag dipol",                                    bp_celsius=-191.0),
    "SO2":   MoleculeIMFEntry(False, True,  False, True,  64.1,  "",                                              bp_celsius=-10.0),
    "SO3":   MoleculeIMFEntry(False, False, False, True,  80.1,  "symmetrisk → kun LDF",                          bp_celsius=45.0),
    "H2S":   MoleculeIMFEntry(False, True,  False, True,  34.1,  "S er ikke elektronegativ nok til H-bond",       bp_celsius=-60.0),
    "HCl":   MoleculeIMFEntry(False, True,  False, True,  36.5,  "polar, dipol-dipol",                            bp_celsius=-85.0),
    "HBr":   MoleculeIMFEntry(False, True,  False, True,  80.9,  "polar, dipol-dipol",                            bp_celsius=-67.0),
    "HI":    MoleculeIMFEntry(False, True,  False, True,  127.9, "polar, dipol-dipol",                            bp_celsius=-35.0),
    "NO":    MoleculeIMFEntry(False, True,  False, True,  30.0,  "",                                              bp_celsius=-152.0),
    "NO2":   MoleculeIMFEntry(False, True,  False, True,  46.0,  "",                                              bp_celsius=21.0),
    "PH3":   MoleculeIMFEntry(False, True,  False, True,  34.0,  "P er ikke elektronegativ nok til H-bond",       bp_celsius=-88.0),
    "H2Se":  MoleculeIMFEntry(False, True,  False, True,  81.0,  "hydrogenselend, svag dipol (ingen H-bond)",     bp_celsius=-42.0),
    "H2Te":  MoleculeIMFEntry(False, True,  False, True,  129.6, "hydrogentellurd, svag dipol",                   bp_celsius=-2.0),
    "OF2":   MoleculeIMFEntry(False, True,  False, False, 54.0,  "oxydifluorid, dipol-dipol",                     bp_celsius=-145.0),
    "NF3":   MoleculeIMFEntry(False, True,  False, False, 71.0,  "nitrogentrifluorid, dipol-dipol",               bp_celsius=-129.0),
    "ClF":   MoleculeIMFEntry(False, True,  False, False, 54.5,  "chlorfluorid, dipol-dipol",                     bp_celsius=-101.0),
    "ICl":   MoleculeIMFEntry(False, True,  False, False, 162.4, "iodchlorid, dipol-dipol",                       bp_celsius=97.0),
    "PCl3":  MoleculeIMFEntry(False, True,  False, True,  137.3, "phosphortrichlorid, dipol-dipol",               bp_celsius=76.0),
    "PCl5":  MoleculeIMFEntry(False, False, False, False, 208.2, "phosphorpentachlorid, upolær, London",           bp_celsius=160.0),
    "HCN":   MoleculeIMFEntry(False, True,  False, True,  27.0,  "hydrogencyanid, dipol-dipol",                   bp_celsius=26.0),
    "CH3CN": MoleculeIMFEntry(False, True,  False, True,  41.1,  "acetonitril, stærk dipol-dipol",                bp_celsius=82.0),
    "CHCl3": MoleculeIMFEntry(False, True,  False, False, 119.4, "kloroform, dipol-dipol",                        bp_celsius=61.0),
    "CH2Cl2":MoleculeIMFEntry(False, True,  False, False, 84.9,  "dichlormethan, dipol-dipol",                    bp_celsius=40.0),
    "CH3Cl": MoleculeIMFEntry(False, True,  False, False, 50.5,  "chlormethan, dipol-dipol",                      bp_celsius=-24.0),
    "CH3F":  MoleculeIMFEntry(False, True,  False, False, 34.0,  "fluormethan, dipol-dipol",                      bp_celsius=-78.0),
    "CH3Br": MoleculeIMFEntry(False, True,  False, False, 94.9,  "brommethan, dipol-dipol",                       bp_celsius=4.0),
    "HCHO":  MoleculeIMFEntry(False, True,  False, True,  30.0,  "formaldehyd, dipol-dipol (ingen donor)",         bp_celsius=-19.0),
    "CH3CHO":MoleculeIMFEntry(False, True,  False, True,  44.1,  "acetaldehyd, dipol-dipol (ingen donor)",         bp_celsius=20.0),
    "CH3COCH3":MoleculeIMFEntry(False,True, False, True,  58.1,  "acetone, dipol-dipol (acceptor, ingen donor)",   bp_celsius=56.0),
    "C2H5OC2H5":MoleculeIMFEntry(False,True,False, True,  74.1,  "diethylether, dipol-dipol (acceptor, ingen donor)", bp_celsius=34.0),
    "CH3OCH3":MoleculeIMFEntry(False,True, False, True,   46.1,  "dimethylether, dipol-dipol (acceptor, ingen donor)", bp_celsius=-24.0),
    "CH3COOC2H5":MoleculeIMFEntry(False,True,False,True,  88.1,  "ethylacetat, dipol-dipol (acceptor, ingen donor)", bp_celsius=77.0),
    "CH3COOCH3":MoleculeIMFEntry(False,True,False,True,   74.1,  "methylacetat, dipol-dipol",                      bp_celsius=57.0),
    "(CH3)3N":MoleculeIMFEntry(False, True, False, True,  59.1,  "trimethylamin, dipol-dipol (ingen donor)",       bp_celsius=3.0),
    "BF3":   MoleculeIMFEntry(False, False, False, False, 67.8,  "bortrifluorid, upolær (trigonal plan), London",  bp_celsius=-100.0),
    "BCl3":  MoleculeIMFEntry(False, False, False, False, 117.2, "bortrichlorid, upolær (trigonal plan), London",  bp_celsius=12.5),
    "SiH4":  MoleculeIMFEntry(False, False, False, False, 32.1,  "silan, London",                                  bp_celsius=-112.0),
    "GeH4":  MoleculeIMFEntry(False, False, False, False, 76.6,  "german, London",                                 bp_celsius=-88.0),
    # H-bond formers
    "HF":    MoleculeIMFEntry(False, True,  True,  True,  20.0,  "stærk H-bond",                                   bp_celsius=19.5),
    "H2O":   MoleculeIMFEntry(False, True,  True,  True,  18.0,  "stærk H-bond, 4 H-bonds pr. molekyle",           bp_celsius=100.0),
    "NH3":   MoleculeIMFEntry(False, True,  True,  True,  17.0,  "H-bond donor og acceptor",                       bp_celsius=-33.0),
    "CH3OH": MoleculeIMFEntry(False, True,  True,  True,  32.0,  "methanol, H-bond",                               bp_celsius=65.0),
    "C2H5OH":MoleculeIMFEntry(False, True,  True,  True,  46.1,  "ethanol, H-bond",                                bp_celsius=78.0),
    "C3H7OH":MoleculeIMFEntry(False, True,  True,  True,  60.1,  "1-propanol, H-bond",                             bp_celsius=97.0),
    "C4H9OH":MoleculeIMFEntry(False, True,  True,  True,  74.1,  "1-butanol, H-bond",                              bp_celsius=118.0),
    "C2H4OH2":MoleculeIMFEntry(False,True,  True,  True,  62.1,  "ethylenglykol, stærk H-bond (2 OH)",             bp_celsius=197.0),
    "C3H5OH3":MoleculeIMFEntry(False,True,  True,  True,  92.1,  "glycerol, meget stærk H-bond (3 OH)",            bp_celsius=290.0),
    "CH3NH2":MoleculeIMFEntry(False, True,  True,  True,  31.1,  "methylamin, H-bond",                             bp_celsius=-6.0),
    "(CH3)2NH":MoleculeIMFEntry(False,True, True,  True,  45.1,  "dimethylamin, H-bond (svagere end primær)",       bp_celsius=7.0),
    "N2H4":  MoleculeIMFEntry(False, True,  True,  True,  32.0,  "hydrazin, H-bond",                               bp_celsius=114.0),
    "C6H5OH":MoleculeIMFEntry(False, True,  True,  True,  94.1,  "phenol, H-bond",                                 bp_celsius=182.0),
    "HCOOH": MoleculeIMFEntry(False, True,  True,  True,  46.0,  "myresyre, stærk H-bond",                         bp_celsius=101.0),
    "CH3COOH":MoleculeIMFEntry(False,True,  True,  True,  60.1,  "eddikesyre, stærk H-bond",                       bp_celsius=118.0),
    "C2H5COOH":MoleculeIMFEntry(False,True, True,  True,  74.1,  "propansyre, H-bond",                             bp_celsius=141.0),
    "C3H7COOH":MoleculeIMFEntry(False,True, True,  True,  88.1,  "butansyre, H-bond",                              bp_celsius=164.0),
    "HNO3":  MoleculeIMFEntry(False, True,  True,  True,  63.0,  "stærk syre, H-bond + dipol",                     bp_celsius=83.0),
    "H2SO4": MoleculeIMFEntry(False, True,  True,  True,  98.1,  "stærk syre, H-bond",                             bp_celsius=337.0),
    "H3PO4": MoleculeIMFEntry(False, True,  True,  True,  98.0,  "H-bond",                                         bp_celsius=158.0),
    # Ions / salts
    "NaCl":  MoleculeIMFEntry(True,  False, False, False, 58.4,  "ionbinding",                                     bp_celsius=1413.0),
    "KCl":   MoleculeIMFEntry(True,  False, False, False, 74.6,  "ionbinding",                                     bp_celsius=1420.0),
    "NaOH":  MoleculeIMFEntry(True,  False, False, False, 40.0,  "ionbinding",                                     bp_celsius=1388.0),
    "CaCl2": MoleculeIMFEntry(True,  False, False, False, 111.0, "ionbinding",                                     bp_celsius=1935.0),
    "MgCl2": MoleculeIMFEntry(True,  False, False, False, 95.2,  "ionbinding",                                     bp_celsius=1412.0),
    "Na2SO4":MoleculeIMFEntry(True,  False, False, False, 142.0, "ionbinding",                                     bp_celsius=1429.0),
    "K2SO4": MoleculeIMFEntry(True,  False, False, False, 174.3, "ionbinding",                                     bp_celsius=1689.0),
    "NH4Cl": MoleculeIMFEntry(True,  False, False, False, 53.5,  "ionbinding",                                     bp_celsius=520.0),
    "AgNO3": MoleculeIMFEntry(True,  False, False, False, 170.0, "ionbinding",                                     bp_celsius=440.0),
    "Ca(OH)2":MoleculeIMFEntry(True, False, False, False, 74.1,  "ionbinding",                                     bp_celsius=2500.0),
    "Al2(SO4)3":MoleculeIMFEntry(True,False, False, False, 342.2,"ionbinding",                                     bp_celsius=1000.0),
    # Sugars / biomolecules (no real BP — use pseudo-high value for sorting)
    "C6H12O6":  MoleculeIMFEntry(False, True, True, True, 180.2, "glukose – 5 OH-grupper, meget stærk H-bond, fast stof ved stuetemperatur", bp_celsius=500.0),
    "C12H22O11":MoleculeIMFEntry(False, True, True, True, 342.3, "saccharose – 8 OH-grupper, meget stærk H-bond, fast stof",                 bp_celsius=800.0),
    "C3H8O3":   MoleculeIMFEntry(False, True, True, True, 92.1,  "glycerol – 3 OH-grupper, stærk H-bond",                                    bp_celsius=290.0),
    # Halogens (molecular)
    "Cl2":   MoleculeIMFEntry(False, False, False, False, 70.9,  "upolær, London",                                 bp_celsius=-34.0),
    "Br2":   MoleculeIMFEntry(False, False, False, False, 159.8, "upolær, London (flydende pga. stor M)",          bp_celsius=59.0),
    "I2":    MoleculeIMFEntry(False, False, False, False, 253.8, "upolær, London (fast pga. stor M)",              bp_celsius=184.0),
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
    (weakest to strongest IMF). Uses actual BP data when available, otherwise falls back
    to IMF rank + molar mass heuristic.
    """
    results = []
    for f in formulas:
        try:
            r = classify_imf(f)
            results.append((f, r))
        except IMFError:
            pass

    def _sort_key(item: tuple[str, IMFResult]) -> float:
        f, r = item
        entry = MOLECULE_IMF_DB.get(f)
        if entry is not None and entry.bp_celsius is not None:
            return entry.bp_celsius
        # Fallback: IMF rank dominates, molar mass breaks ties within same class
        return IMF_STRENGTH_RANK[r.dominant_imf] * 10_000 + (r.molar_mass_approx or 0)

    results.sort(key=_sort_key)
    return results


def list_known_molecules() -> list[str]:
    return sorted(MOLECULE_IMF_DB.keys())
