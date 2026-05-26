"""
Le Chatelier's principle — predict equilibrium shift direction.

Rules implemented:
  Concentration: add/remove reactant or product
  Pressure:      increase/decrease (only affects gas-phase; shifts towards fewer/more moles gas)
  Temperature:   increase/decrease (shifts based on ΔH sign; changes K)
  Catalyst:      reaches equilibrium faster, no shift
  Inert gas:     constant volume → no shift; constant pressure → shifts towards more gas moles
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ShiftDirection(str, Enum):
    RIGHT   = "Højre (mod produkter)"
    LEFT    = "Venstre (mod reaktanter)"
    NONE    = "Ingen ændring"
    BOTH    = "Afhænger af Δn(gas)"


class Perturbation(str, Enum):
    ADD_REACTANT      = "Tilsæt reaktant"
    REMOVE_REACTANT   = "Fjern reaktant"
    ADD_PRODUCT       = "Tilsæt produkt"
    REMOVE_PRODUCT    = "Fjern produkt"
    INCREASE_PRESSURE = "Forøg tryk"
    DECREASE_PRESSURE = "Sænk tryk"
    INCREASE_TEMP     = "Forøg temperatur"
    DECREASE_TEMP     = "Sænk temperatur"
    ADD_CATALYST      = "Tilsæt katalysator"
    ADD_INERT_CONST_V = "Inert gas ved konstant volumen"
    ADD_INERT_CONST_P = "Inert gas ved konstant tryk"


@dataclass
class LeChatelierResult:
    perturbation: Perturbation
    shift: ShiftDirection
    k_changes: bool                 # Does K itself change?
    k_direction: Optional[str]      # "increases", "decreases", None
    explanation: str
    exam_tip: str
    steps: list[str] = field(default_factory=list)


class LeChatelierError(ValueError):
    pass


def predict_shift(
    perturbation: Perturbation,
    delta_h_kj: Optional[float] = None,     # sign of ΔH: <0 exothermic, >0 endothermic
    delta_n_gas: Optional[int] = None,       # Δn_gas = moles gas products − moles gas reactants
) -> LeChatelierResult:
    """
    Predict equilibrium shift from a perturbation.

    Args:
        perturbation:  The applied change (Perturbation enum).
        delta_h_kj:    ΔH of the forward reaction in kJ/mol. Required for temperature changes.
        delta_n_gas:   Change in moles of gas (products − reactants). Required for pressure changes.
    """
    steps: list[str] = []
    steps.append(f"**Forstyrrelse:** {perturbation.value}")

    # ── Concentration ────────────────────────────────────────────────────────
    if perturbation == Perturbation.ADD_REACTANT:
        shift = ShiftDirection.RIGHT
        k_changes = False
        explanation = (
            "Tilsætning af en reaktant øger dens koncentration. "
            "Q < K → ligevægten forskydes mod produkter for at genoprette Q = K."
        )
        exam_tip = "K er uændret. Kun retningen af ligevægt ændres."

    elif perturbation == Perturbation.REMOVE_REACTANT:
        shift = ShiftDirection.LEFT
        k_changes = False
        explanation = (
            "Fjernelse af en reaktant sænker dens koncentration. "
            "Q > K → ligevægten forskydes mod reaktanter."
        )
        exam_tip = "K er uændret."

    elif perturbation == Perturbation.ADD_PRODUCT:
        shift = ShiftDirection.LEFT
        k_changes = False
        explanation = (
            "Tilsætning af et produkt øger dets koncentration. "
            "Q > K → ligevægten forskydes mod reaktanter."
        )
        exam_tip = "K er uændret."

    elif perturbation == Perturbation.REMOVE_PRODUCT:
        shift = ShiftDirection.RIGHT
        k_changes = False
        explanation = (
            "Fjernelse af et produkt sænker dets koncentration. "
            "Q < K → ligevægten forskydes mod produkter."
        )
        exam_tip = "K er uændret. Bruges industrielt til at drive reaktioner fremad."

    # ── Pressure ─────────────────────────────────────────────────────────────
    elif perturbation == Perturbation.INCREASE_PRESSURE:
        k_changes = False
        if delta_n_gas is None:
            shift = ShiftDirection.NONE
            explanation = "Δn(gas) er ikke angivet. Angiv antal mol gas på hver side."
            exam_tip = ""
        elif delta_n_gas < 0:
            shift = ShiftDirection.RIGHT
            explanation = (
                f"Δn(gas) = {delta_n_gas} < 0: der er færre mol gas på produktsiden. "
                "Øget tryk forskydes mod færre mol gas → mod produkter."
            )
            exam_tip = "Øget tryk favoriserer siden med færrest mol gas."
        elif delta_n_gas > 0:
            shift = ShiftDirection.LEFT
            explanation = (
                f"Δn(gas) = {delta_n_gas} > 0: der er flere mol gas på produktsiden. "
                "Øget tryk forskydes mod færre mol gas → mod reaktanter."
            )
            exam_tip = "Øget tryk favoriserer siden med færrest mol gas."
        else:
            shift = ShiftDirection.NONE
            explanation = (
                "Δn(gas) = 0: ens antal mol gas på begge sider. "
                "Trykændring har ingen nettoeffekt på ligevægtspositionen."
            )
            exam_tip = "Kun gasrektioner med Δn(gas) ≠ 0 påvirkes af trykændringer."

    elif perturbation == Perturbation.DECREASE_PRESSURE:
        k_changes = False
        if delta_n_gas is None:
            shift = ShiftDirection.NONE
            explanation = "Δn(gas) er ikke angivet."
            exam_tip = ""
        elif delta_n_gas > 0:
            shift = ShiftDirection.RIGHT
            explanation = (
                f"Δn(gas) = {delta_n_gas} > 0: der er flere mol gas på produktsiden. "
                "Sænket tryk forskydes mod flere mol gas → mod produkter."
            )
            exam_tip = "Sænket tryk favoriserer siden med flest mol gas."
        elif delta_n_gas < 0:
            shift = ShiftDirection.LEFT
            explanation = (
                f"Δn(gas) = {delta_n_gas} < 0: der er færre mol gas på produktsiden. "
                "Sænket tryk forskydes mod flere mol gas → mod reaktanter."
            )
            exam_tip = "Sænket tryk favoriserer siden med flest mol gas."
        else:
            shift = ShiftDirection.NONE
            explanation = "Δn(gas) = 0: trykændring har ingen nettoeffekt."
            exam_tip = "Kun gasreaktioner med Δn(gas) ≠ 0 påvirkes."

    # ── Temperature ──────────────────────────────────────────────────────────
    elif perturbation == Perturbation.INCREASE_TEMP:
        k_changes = True
        if delta_h_kj is None:
            raise LeChatelierError("Angiv ΔH for temperaturændringer.")
        if delta_h_kj < 0:
            # Exothermic: treat heat as product; adding heat → shift left
            shift = ShiftDirection.LEFT
            k_direction = "decreases"
            explanation = (
                f"ΔH = {delta_h_kj} kJ/mol < 0 → **eksoterm** reaktion. "
                "Temperaturforøgelse svarer til at tilsætte 'varme' (et produkt i eksoterme reaktioner). "
                "Ligevægten forskydes mod reaktanter (venstre). "
                "**K falder.**"
            )
            exam_tip = "Eksoterm: ↑T → K falder, ligevægt forskydes mod reaktanter."
        else:
            shift = ShiftDirection.RIGHT
            k_direction = "increases"
            explanation = (
                f"ΔH = {delta_h_kj} kJ/mol > 0 → **endoterm** reaktion. "
                "Temperaturforøgelse favoriserer den endoterme (fremadgående) retning. "
                "Ligevægten forskydes mod produkter (højre). "
                "**K stiger.**"
            )
            exam_tip = "Endoterm: ↑T → K stiger, ligevægt forskydes mod produkter."
        result = LeChatelierResult(
            perturbation=perturbation,
            shift=shift,
            k_changes=k_changes,
            k_direction=k_direction,
            explanation=explanation,
            exam_tip=exam_tip,
            steps=steps,
        )
        _build_steps(result, delta_h_kj, delta_n_gas, steps)
        return result

    elif perturbation == Perturbation.DECREASE_TEMP:
        k_changes = True
        if delta_h_kj is None:
            raise LeChatelierError("Angiv ΔH for temperaturændringer.")
        if delta_h_kj < 0:
            shift = ShiftDirection.RIGHT
            k_direction = "increases"
            explanation = (
                f"ΔH = {delta_h_kj} kJ/mol < 0 → **eksoterm** reaktion. "
                "Temperaturfald fjerner 'varme', ligevægten producerer mere varme → forskydes mod produkter. "
                "**K stiger.**"
            )
            exam_tip = "Eksoterm: ↓T → K stiger, ligevægt forskydes mod produkter."
        else:
            shift = ShiftDirection.LEFT
            k_direction = "decreases"
            explanation = (
                f"ΔH = {delta_h_kj} kJ/mol > 0 → **endoterm** reaktion. "
                "Temperaturfald favoriserer den eksoterme (omvendte) retning. "
                "Ligevægten forskydes mod reaktanter. "
                "**K falder.**"
            )
            exam_tip = "Endoterm: ↓T → K falder, ligevægt forskydes mod reaktanter."
        result = LeChatelierResult(
            perturbation=perturbation,
            shift=shift,
            k_changes=k_changes,
            k_direction=k_direction,
            explanation=explanation,
            exam_tip=exam_tip,
            steps=steps,
        )
        _build_steps(result, delta_h_kj, delta_n_gas, steps)
        return result

    # ── Catalyst ─────────────────────────────────────────────────────────────
    elif perturbation == Perturbation.ADD_CATALYST:
        shift = ShiftDirection.NONE
        k_changes = False
        explanation = (
            "En katalysator sænker aktiveringsenergi for BEGGE retninger (frem og tilbage) ligeligt. "
            "Ligevægtssammensætningen ændres ikke — systemet når blot ligevægt hurtigere."
        )
        exam_tip = "Katalysator: ændrer ikke K, ændrer ikke ligevægtspositionen, kun hastighed."

    # ── Inert gas ─────────────────────────────────────────────────────────────
    elif perturbation == Perturbation.ADD_INERT_CONST_V:
        shift = ShiftDirection.NONE
        k_changes = False
        explanation = (
            "Ved konstant volumen øger en inert gas det totale tryk, "
            "men ændrer IKKE partialtrykket af reaktanterne/produkterne. "
            "Ligevægt uændret."
        )
        exam_tip = "Konstant volumen: inert gas påvirker ikke ligevægt."

    elif perturbation == Perturbation.ADD_INERT_CONST_P:
        k_changes = False
        if delta_n_gas is None or delta_n_gas == 0:
            shift = ShiftDirection.NONE
            explanation = (
                "Ved konstant tryk fortyndes alle gasser (volumen øges). "
                "Hvis Δn(gas) = 0, er der ingen nettoeffekt."
            )
            exam_tip = "Inert gas v. kons. P og Δn=0: ingen forskyding."
        elif delta_n_gas > 0:
            shift = ShiftDirection.RIGHT
            explanation = (
                f"Δn(gas) = {delta_n_gas} > 0. "
                "Inert gas ved konstant tryk øger volumen (fortynder gasserne). "
                "Svarer til trykfald → forskydes mod flest mol gas → mod produkter."
            )
            exam_tip = "Inert gas v. kons. P: svarer til trykfald."
        else:
            shift = ShiftDirection.LEFT
            explanation = (
                f"Δn(gas) = {delta_n_gas} < 0. "
                "Inert gas ved konstant tryk svarer til trykfald → forskydes mod færrest mol gas → mod reaktanter."
            )
            exam_tip = "Inert gas v. kons. P: svarer til trykfald."

    else:
        raise LeChatelierError(f"Ukendt forstyrrelse: {perturbation}")

    result = LeChatelierResult(
        perturbation=perturbation,
        shift=shift,
        k_changes=k_changes,
        k_direction=None,
        explanation=explanation,
        exam_tip=exam_tip,
        steps=steps,
    )
    _build_steps(result, delta_h_kj, delta_n_gas, steps)
    return result


def _build_steps(result: LeChatelierResult, delta_h, delta_n_gas, steps: list[str]):
    steps.append("")
    steps.append(f"**Forskydning:** {result.shift.value}")
    steps.append("")
    steps.append("**Forklaring:**")
    steps.append(result.explanation)
    steps.append("")
    steps.append(f"**Ændrer K sig?** {'Ja' if result.k_changes else 'Nej — kun koncentration/tryk/katalysator ændrer ikke K'}")
    if result.exam_tip:
        steps.append("")
        steps.append(f"📌 **Eksamenstip:** {result.exam_tip}")
