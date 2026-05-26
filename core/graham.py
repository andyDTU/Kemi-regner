"""
Graham's law of effusion / diffusion.

  r₁/r₂ = √(M₂/M₁)

where r = effusion rate (or average speed) and M = molar mass.
Also: t₁/t₂ = √(M₁/M₂)   (time is inversely proportional to rate)
"""

import math
from dataclasses import dataclass, field
from typing import Optional


COMMON_GAS_MASSES: dict[str, float] = {
    "H2":   2.016,
    "He":   4.003,
    "CH4":  16.04,
    "NH3":  17.03,
    "H2O":  18.02,
    "Ne":   20.18,
    "N2":   28.01,
    "CO":   28.01,
    "C2H6": 30.07,
    "O2":   32.00,
    "H2S":  34.08,
    "Ar":   39.95,
    "CO2":  44.01,
    "C3H8": 44.10,
    "NO2":  46.01,
    "SO2":  64.06,
    "Cl2":  70.90,
    "Kr":   83.80,
    "HBr":  80.91,
    "SO3":  80.06,
    "Br2":  159.8,
    "Xe":   131.3,
    "I2":   253.8,
    "UF6":  352.0,
    "SF6":  146.1,
    "N2O":  44.01,
    "F2":   38.00,
    "HCl":  36.46,
    "HF":   20.01,
    "HI":   127.9,
}


class GrahamError(ValueError):
    pass


@dataclass
class GrahamResult:
    gas1: str
    gas2: str
    M1: float
    M2: float
    rate_ratio: float        # r1/r2
    time_ratio: float        # t1/t2
    faster_gas: str
    steps: list[str] = field(default_factory=list)


def calculate_graham(
    gas1: str,
    gas2: str,
    M1: Optional[float] = None,
    M2: Optional[float] = None,
) -> GrahamResult:
    """
    Apply Graham's law between two gases.

    gas1/gas2: label (used for display)
    M1/M2:     molar mass in g/mol. If None, look up from COMMON_GAS_MASSES.
    """
    m1 = M1 if M1 is not None else COMMON_GAS_MASSES.get(gas1)
    m2 = M2 if M2 is not None else COMMON_GAS_MASSES.get(gas2)

    if m1 is None:
        raise GrahamError(
            f"Molarmasse for '{gas1}' er ikke i databasen. Angiv den manuelt."
        )
    if m2 is None:
        raise GrahamError(
            f"Molarmasse for '{gas2}' er ikke i databasen. Angiv den manuelt."
        )
    if m1 <= 0 or m2 <= 0:
        raise GrahamError("Molarmasse skal være positiv.")

    rate_ratio = math.sqrt(m2 / m1)    # r1/r2 = √(M2/M1)
    time_ratio = math.sqrt(m1 / m2)    # t1/t2 = √(M1/M2) = 1/rate_ratio

    faster = gas1 if rate_ratio > 1 else (gas2 if rate_ratio < 1 else "Ens")

    steps: list[str] = []
    steps.append("### Graham's lov for effusion")
    steps.append("$$\\frac{r_1}{r_2} = \\sqrt{\\frac{M_2}{M_1}}$$")
    steps.append("")
    steps.append(f"**Gas 1:** {gas1}, M₁ = {m1:.3f} g/mol")
    steps.append(f"**Gas 2:** {gas2}, M₂ = {m2:.3f} g/mol")
    steps.append("")
    steps.append(
        f"$$\\frac{{r_1}}{{r_2}} = \\sqrt{{\\frac{{{m2:.3f}}}{{{m1:.3f}}}}} "
        f"= \\sqrt{{{m2/m1:.4f}}} = {rate_ratio:.4f}$$"
    )
    steps.append("")
    steps.append(f"**r₁/r₂ = {rate_ratio:.4f}**")
    steps.append(
        f"→ {gas1} effunderer **{rate_ratio:.2f}× {'hurtigere' if rate_ratio > 1 else 'langsommere'}** end {gas2}"
    )
    steps.append("")
    steps.append(
        f"**Tid:** t₁/t₂ = √(M₁/M₂) = {time_ratio:.4f} "
        f"→ {gas1} bruger **{time_ratio:.2f}× {'kortere' if time_ratio < 1 else 'længere'}** tid end {gas2}"
    )
    steps.append("")
    steps.append("**Huskeregel:** Lettere gas → højere effusionshastighed → kortere tid")

    return GrahamResult(
        gas1=gas1, gas2=gas2,
        M1=m1, M2=m2,
        rate_ratio=rate_ratio,
        time_ratio=time_ratio,
        faster_gas=faster,
        steps=steps,
    )


def calculate_graham_unknown_mass(
    known_gas: str,
    M_known: Optional[float],
    rate_ratio: Optional[float] = None,
    time_ratio: Optional[float] = None,
) -> tuple[float, list[str]]:
    """
    Find the molar mass of an unknown gas from a measured rate or time ratio.

    rate_ratio = r_known / r_unknown
    time_ratio = t_unknown / t_known   (= rate_known/rate_unknown also)
    """
    m_k = M_known if M_known is not None else COMMON_GAS_MASSES.get(known_gas)
    if m_k is None:
        raise GrahamError(f"Molarmasse for '{known_gas}' ukendt.")
    if m_k <= 0:
        raise GrahamError("Molarmasse skal være positiv.")

    if rate_ratio is not None and rate_ratio > 0:
        # r_known/r_unknown = √(M_unknown/M_known)
        # M_unknown = M_known × (r_known/r_unknown)²
        m_unknown = m_k * rate_ratio ** 2
        steps = [
            f"**Beregn molarmasse af ukendt gas:**",
            f"r_{known_gas}/r_ukendt = {rate_ratio:.4f}",
            f"M_ukendt = M_{known_gas} × (r_{known_gas}/r_ukendt)² = {m_k:.3f} × {rate_ratio:.4f}² = **{m_unknown:.3f} g/mol**",
        ]
    elif time_ratio is not None and time_ratio > 0:
        # t_unknown/t_known = √(M_unknown/M_known)
        m_unknown = m_k * time_ratio ** 2
        steps = [
            f"**Beregn molarmasse af ukendt gas:**",
            f"t_ukendt/t_{known_gas} = {time_ratio:.4f}",
            f"M_ukendt = M_{known_gas} × (t_ukendt/t_{known_gas})² = {m_k:.3f} × {time_ratio:.4f}² = **{m_unknown:.3f} g/mol**",
        ]
    else:
        raise GrahamError("Angiv enten hastighedsforhold eller tidsforhold.")

    return m_unknown, steps
