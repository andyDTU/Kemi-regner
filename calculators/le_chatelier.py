"""
Le Chatelier's principle — Streamlit UI tab.
"""

import streamlit as st
from core.le_chatelier import (
    predict_shift, Perturbation, ShiftDirection, LeChatelierError,
)

_SHIFT_ARROW = {
    ShiftDirection.RIGHT: "➡️ Højre (mod produkter)",
    ShiftDirection.LEFT:  "⬅️ Venstre (mod reaktanter)",
    ShiftDirection.NONE:  "⏸️ Ingen ændring",
    ShiftDirection.BOTH:  "↔️ Afhænger af Δn(gas)",
}

_SHIFT_COLOR = {
    ShiftDirection.RIGHT: "success",
    ShiftDirection.LEFT:  "warning",
    ShiftDirection.NONE:  "info",
    ShiftDirection.BOTH:  "info",
}

_PERTURBATION_OPTIONS = {
    "Tilsæt reaktant":                      Perturbation.ADD_REACTANT,
    "Fjern reaktant":                       Perturbation.REMOVE_REACTANT,
    "Tilsæt produkt":                       Perturbation.ADD_PRODUCT,
    "Fjern produkt":                        Perturbation.REMOVE_PRODUCT,
    "Forøg tryk":                           Perturbation.INCREASE_PRESSURE,
    "Sænk tryk":                            Perturbation.DECREASE_PRESSURE,
    "Forøg temperatur":                     Perturbation.INCREASE_TEMP,
    "Sænk temperatur":                      Perturbation.DECREASE_TEMP,
    "Tilsæt katalysator":                   Perturbation.ADD_CATALYST,
    "Inert gas (konstant volumen)":         Perturbation.ADD_INERT_CONST_V,
    "Inert gas (konstant tryk)":            Perturbation.ADD_INERT_CONST_P,
}

_NEEDS_DELTA_H = {
    Perturbation.INCREASE_TEMP,
    Perturbation.DECREASE_TEMP,
}
_NEEDS_DELTA_N = {
    Perturbation.INCREASE_PRESSURE,
    Perturbation.DECREASE_PRESSURE,
    Perturbation.ADD_INERT_CONST_P,
}


def render_le_chatelier_tab():
    """Render Le Chatelier's principle sub-tab."""
    st.markdown("## ⚖️ Le Chateliers princip")
    st.markdown(
        "Forudsig i hvilken retning en ligevægt forskydes, "
        "når der sker en ændring i systemet."
    )
    st.markdown("---")

    col_input, col_ref = st.columns([3, 2], gap="large")

    with col_input:
        st.markdown("### Vælg forstyrrelse")

        perturbation_label = st.selectbox(
            "Type af ændring:",
            list(_PERTURBATION_OPTIONS.keys()),
            key="lc_perturbation",
        )
        perturbation = _PERTURBATION_OPTIONS[perturbation_label]

        delta_h = None
        delta_n = None

        if perturbation in _NEEDS_DELTA_H:
            st.markdown("**ΔH for den fremadgående reaktion:**")
            rxn_type = st.radio(
                "Reaktionstype:",
                ["Eksoterm (ΔH < 0)", "Endoterm (ΔH > 0)"],
                key="lc_rxn_type",
                horizontal=True,
            )
            delta_h_abs = st.number_input(
                "|ΔH| (kJ/mol):",
                min_value=0.1, value=92.0, step=1.0,
                key="lc_dh_abs",
            )
            delta_h = -abs(delta_h_abs) if "Eksoterm" in rxn_type else abs(delta_h_abs)
            st.caption(f"ΔH = {delta_h:+.1f} kJ/mol")

        if perturbation in _NEEDS_DELTA_N:
            st.markdown("**Δn(gas) = mol gas (produkter) − mol gas (reaktanter):**")
            col_a, col_b = st.columns(2)
            with col_a:
                n_prod = st.number_input("Mol gas (produkter):", min_value=0, value=2, step=1, key="lc_n_prod")
            with col_b:
                n_react = st.number_input("Mol gas (reaktanter):", min_value=0, value=1, step=1, key="lc_n_react")
            delta_n = int(n_prod) - int(n_react)
            st.caption(f"Δn(gas) = {n_prod} − {n_react} = **{delta_n}**")

        run = st.button("Forudsig forskydning", type="primary", key="lc_run")

    with col_ref:
        st.markdown("### Hurtig reference")
        import pandas as pd
        ref = [
            ["Tilsæt reaktant",    "Højre",  "Nej"],
            ["Fjern reaktant",     "Venstre","Nej"],
            ["Tilsæt produkt",     "Venstre","Nej"],
            ["Fjern produkt",      "Højre",  "Nej"],
            ["↑ Tryk (Δn<0)",      "Højre",  "Nej"],
            ["↑ Tryk (Δn>0)",      "Venstre","Nej"],
            ["↑ Tryk (Δn=0)",      "Ingen",  "Nej"],
            ["↑ T (eksoterm)",     "Venstre","Ja (K ↓)"],
            ["↑ T (endoterm)",     "Højre",  "Ja (K ↑)"],
            ["↓ T (eksoterm)",     "Højre",  "Ja (K ↑)"],
            ["↓ T (endoterm)",     "Venstre","Ja (K ↓)"],
            ["Katalysator",        "Ingen",  "Nej"],
            ["Inert (kons. V)",    "Ingen",  "Nej"],
        ]
        df = pd.DataFrame(ref, columns=["Ændring", "Forskydning", "K ændres?"])
        st.dataframe(df, use_container_width=True, hide_index=True)

    if run:
        try:
            result = predict_shift(
                perturbation=perturbation,
                delta_h_kj=delta_h,
                delta_n_gas=delta_n,
            )
        except LeChatelierError as e:
            st.error(str(e))
            st.stop()

        st.markdown("---")
        st.markdown("## Resultat")

        # Big shift indicator
        shift_str = _SHIFT_ARROW[result.shift]
        color = _SHIFT_COLOR[result.shift]
        if color == "success":
            st.success(f"### {shift_str}")
        elif color == "warning":
            st.warning(f"### {shift_str}")
        else:
            st.info(f"### {shift_str}")

        # K changes?
        if result.k_changes:
            kdir = "stiger ↑" if result.k_direction == "increases" else "falder ↓"
            st.error(f"**K ændres:** K {kdir} (temperaturændring er den eneste faktor der ændrer K)")
        else:
            st.info("**K ændres ikke** — kun ligevægtspositionen forskydes.")

        # Explanation
        st.markdown("### Forklaring")
        st.markdown(result.explanation)

        if result.exam_tip:
            st.markdown("---")
            st.info(f"📌 **Eksamenstip:** {result.exam_tip}")

        with st.expander("📋 Vis trin for trin", expanded=False):
            for s in result.steps:
                st.markdown(s)

    # ── Haber-Bosch example ───────────────────────────────────────────────────
    st.markdown("---")
    with st.expander("💡 Eksempel: Haber-Bosch processen", expanded=False):
        st.markdown("""
**N₂(g) + 3H₂(g) ⇌ 2NH₃(g),  ΔH = −92 kJ/mol (eksoterm)**

Δn(gas) = 2 − (1+3) = **−2**

| Ændring | Forskydning | K |
|---------|-------------|---|
| Tilsæt N₂ | Højre → mere NH₃ | uændret |
| Fjern NH₃ | Højre → mere NH₃ | uændret |
| Øg tryk | Højre (Δn<0) | uændret |
| Sænk temp. | Højre (eksoterm) | stiger |
| Tilsæt katalysator | Ingen | uændret |

**Industriel kompromis:** Højt tryk (→ højre) + moderat temperatur
(lav T giver høj K men langsom reaktionshastighed → ~450°C er kompromis).
        """)
