"""
Nuclear / radioactive decay calculations.

Key equations:
  N(t) = N₀ × (1/2)^(t / t½)         half-life form
  N(t) = N₀ × e^(-λt)                 decay constant form
  A(t) = A₀ × (1/2)^(t / t½)         same for activity
  t½   = ln(2) / λ ≈ 0.6931 / λ
  λ    = ln(2) / t½

Decay types and their properties are also catalogued.
"""

import math
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Decay types
# ---------------------------------------------------------------------------

DECAY_TYPES: dict[str, dict] = {
    "alpha": {
        "symbol": "α",
        "description": "Alfa-henfald: kerne udsender ⁴₂He (2 protoner + 2 neutroner)",
        "Z_change": -2,
        "A_change": -4,
        "penetration": "Lav (stoppes af papir/hud)",
        "example": "²³⁸U → ²³⁴Th + ⁴He",
    },
    "beta_minus": {
        "symbol": "β⁻",
        "description": "Beta-minus henfald: neutron → proton + elektron (β⁻) + antineutrino",
        "Z_change": +1,
        "A_change": 0,
        "penetration": "Moderat (stoppes af aluminium)",
        "example": "¹⁴C → ¹⁴N + β⁻",
    },
    "beta_plus": {
        "symbol": "β⁺",
        "description": "Beta-plus henfald (positronemission): proton → neutron + positron (β⁺) + neutrino",
        "Z_change": -1,
        "A_change": 0,
        "penetration": "Moderat",
        "example": "¹¹C → ¹¹B + β⁺",
    },
    "gamma": {
        "symbol": "γ",
        "description": "Gammastråling: kerne udsender foton (høj energi). Z og A uændret.",
        "Z_change": 0,
        "A_change": 0,
        "penetration": "Høj (kræver bly/beton)",
        "example": "⁶⁰Co* → ⁶⁰Co + γ",
    },
    "electron_capture": {
        "symbol": "EC",
        "description": "Elektronindfangning: proton + elektron (K-skal) → neutron + neutrino",
        "Z_change": -1,
        "A_change": 0,
        "penetration": "Lav (X-rays sekundært)",
        "example": "⁴⁰K + e⁻ → ⁴⁰Ar",
    },
}


# ---------------------------------------------------------------------------
# Time unit helpers
# ---------------------------------------------------------------------------

TIME_UNITS: dict[str, float] = {
    "sekunder (s)":    1.0,
    "minutter (min)":  60.0,
    "timer (h)":       3600.0,
    "dage (d)":        86400.0,
    "år (y)":          365.25 * 86400.0,
    "tusind år (ky)":  1e3 * 365.25 * 86400.0,
    "million år (My)": 1e6 * 365.25 * 86400.0,
}


def to_seconds(value: float, unit: str) -> float:
    factor = TIME_UNITS.get(unit)
    if factor is None:
        raise ValueError(f"Ukendt tidsenhed: {unit}")
    return value * factor


def from_seconds(value_s: float, unit: str) -> float:
    factor = TIME_UNITS.get(unit)
    if factor is None:
        raise ValueError(f"Ukendt tidsenhed: {unit}")
    return value_s / factor


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class DecayResult:
    N0: float
    Nt: float
    t: float
    t_half: float
    lambda_: float
    fraction_remaining: float
    fraction_decayed: float
    n_half_lives: float
    steps: list[str] = field(default_factory=list)


class NuclearDecayError(ValueError):
    pass


# ---------------------------------------------------------------------------
# Core calculation
# ---------------------------------------------------------------------------

def calculate_decay(
    N0: Optional[float],
    Nt: Optional[float],
    t: Optional[float],
    t_half: Optional[float],
    t_unit: str = "år (y)",
    half_unit: str = "år (y)",
) -> DecayResult:
    """
    Solve the radioactive decay equation for one unknown.

    N(t) = N₀ × (1/2)^(t/t½)

    Provide exactly three of the four: N0, Nt, t, t_half.
    All times must be in the same base unit (converted internally).
    """
    # Convert to seconds for consistent math
    t_s      = to_seconds(t, t_unit) if t is not None else None
    thalf_s  = to_seconds(t_half, half_unit) if t_half is not None else None

    provided = sum(x is not None for x in [N0, Nt, t_s, thalf_s])
    if provided < 3:
        raise NuclearDecayError(
            "Angiv 3 af de 4 størrelser: N₀, N(t), t og t½."
        )

    # Solve for the missing variable
    if t_half is None or thalf_s is None:
        # t½ = t × ln(2) / ln(N0/Nt)
        if N0 is None or Nt is None or t_s is None:
            raise NuclearDecayError("Kan ikke bestemme t½ — angiv N₀, N(t) og t.")
        if N0 <= 0 or Nt <= 0:
            raise NuclearDecayError("N₀ og N(t) skal være positive.")
        if Nt >= N0:
            raise NuclearDecayError("N(t) skal være mindre end N₀ for henfald.")
        thalf_s = t_s * math.log(2) / math.log(N0 / Nt)
        t_half = from_seconds(thalf_s, half_unit)

    elif t is None or t_s is None:
        # t = t½ × log2(N0/Nt)
        if N0 is None or Nt is None:
            raise NuclearDecayError("Kan ikke bestemme t — angiv N₀, N(t) og t½.")
        if N0 <= 0 or Nt <= 0:
            raise NuclearDecayError("N₀ og N(t) skal være positive.")
        if Nt >= N0:
            raise NuclearDecayError("N(t) skal være mindre end N₀.")
        t_s = thalf_s * math.log(N0 / Nt) / math.log(2)
        t = from_seconds(t_s, t_unit)

    elif N0 is None:
        # N0 = Nt / (1/2)^(t/t½)
        if Nt is None or t_s is None:
            raise NuclearDecayError("Kan ikke bestemme N₀ — angiv N(t), t og t½.")
        n_halves = t_s / thalf_s
        N0 = Nt / (0.5 ** n_halves)

    elif Nt is None:
        # Nt = N0 × (1/2)^(t/t½)
        if N0 is None or t_s is None:
            raise NuclearDecayError("Kan ikke bestemme N(t) — angiv N₀, t og t½.")
        n_halves = t_s / thalf_s
        Nt = N0 * (0.5 ** n_halves)

    lambda_ = math.log(2) / thalf_s
    n_halves = t_s / thalf_s
    fraction_remaining = Nt / N0
    fraction_decayed   = 1 - fraction_remaining

    steps = _build_steps(N0, Nt, t, t_unit, t_half, half_unit, lambda_, n_halves,
                         fraction_remaining, fraction_decayed, thalf_s)

    return DecayResult(
        N0=N0, Nt=Nt,
        t=t, t_half=t_half,
        lambda_=lambda_,
        fraction_remaining=fraction_remaining,
        fraction_decayed=fraction_decayed,
        n_half_lives=n_halves,
        steps=steps,
    )


def _build_steps(N0, Nt, t, t_unit, t_half, half_unit,
                 lambda_s, n_halves, frac_rem, frac_dec, thalf_s) -> list[str]:
    steps = []
    steps.append("### Radioaktivt henfald")
    steps.append("$$N(t) = N_0 \\cdot \\left(\\frac{1}{2}\\right)^{t/t_{1/2}}$$")
    steps.append("")
    steps.append(f"**N₀ = {N0:.6g}** (startmængde)")
    steps.append(f"**t½ = {t_half:.6g} {half_unit}**")
    steps.append(f"**t = {t:.6g} {t_unit}**")
    steps.append("")
    steps.append(f"**λ = ln(2) / t½ = 0.6931 / {t_half:.6g} {half_unit} = {lambda_s:.4e} s⁻¹**")
    steps.append("")
    steps.append(f"**Antal halveringstider:** n = t / t½ = {t:.6g} / {t_half:.6g} = **{n_halves:.4f}**")
    steps.append("")
    steps.append(
        f"**N(t) = {N0:.6g} × (½)^{n_halves:.4f} = {N0:.6g} × {0.5**n_halves:.6f} = **{Nt:.6g}****"
    )
    steps.append("")
    steps.append(f"**Fraktion tilbage:** {frac_rem*100:.3f}%")
    steps.append(f"**Fraktion henfaldet:** {frac_dec*100:.3f}%")
    return steps
