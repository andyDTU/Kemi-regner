"""
VSEPR geometry and molecular polarity calculator — Streamlit UI.
"""

import streamlit as st
from core.vsepr import (
    predict_vsepr, VSEPRError, list_known_molecules,
    GEOMETRY_TABLE, HYBRIDIZATION, HYBRIDIZATION_DESCRIPTION,
)


def render_vsepr_tab():
    """Render the VSEPR geometry + polarity sub-tab."""
    st.markdown("## 🔷 VSEPR – Molekylgeometri og polaritet")
    st.markdown(
        "Forudsig molekylgeometri og polaritet ud fra Lewis-strukturen. "
        "Find dit molekyle i databasen, eller angiv bindingspar og frie elektronpar manuelt."
    )
    st.markdown("---")

    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.markdown("### Input")
        input_mode = st.radio(
            "Inputmetode:",
            ["🔍 Søg molekyle i database", "✏️ Manuel input (BP og LP)"],
            key="vsepr_mode",
            horizontal=True,
        )

        formula = ""
        bonding_pairs = None
        lone_pairs = None
        all_same = None

        if input_mode == "🔍 Søg molekyle i database":
            formula = st.text_input(
                "Kemisk formel:",
                placeholder="fx H2O, NH3, CO2, CH4, SF6",
                key="vsepr_formula",
            )
            st.caption(
                "Understøtter: " +
                ", ".join(list_known_molecules()[:18]) + " og flere …"
            )
        else:
            formula = st.text_input(
                "Molekyle (til visning):",
                placeholder="fx 'AX3E1' eller 'mit molekyle'",
                value="",
                key="vsepr_formula_manual",
            )
            bonding_pairs = st.number_input(
                "Antal bindingspar (BP) – bindinger til centrale atom:",
                min_value=1, max_value=6, value=4, step=1,
                key="vsepr_bp",
            )
            lone_pairs = st.number_input(
                "Antal frie elektronpar (LP) på centrale atom:",
                min_value=0, max_value=5, value=0, step=1,
                key="vsepr_lp",
            )
            all_same = st.checkbox(
                "Alle terminale atomer er identiske (symmetrisk molekyle)",
                value=True,
                key="vsepr_same",
            )

            with st.expander("❓ Hvordan finder jeg BP og LP?", expanded=False):
                st.markdown(
                    "**Trin 1 – Find det centrale atom**  \n"
                    "Det atom med **lavest elektronegativity** er typisk centralt (H er aldrig centralt).  \n"
                    "_Eksempel: I XeF₂ er Xe centralt, i ClO₃⁻ er Cl centralt._\n\n"
                    "---\n"
                    "**Trin 2 – Tæl BP (bindende par)**  \n"
                    "BP = **antal terminale atomer** bondet til det centrale atom.  \n"
                    "Dobbelt- og tripelbindinger tæller stadig som **ét** par i VSEPR.  \n"
                    "_XeF₂ → 2 F → BP = 2 | SOF₄ → 4 F + 1 O → BP = 5 | ClO₃⁻ → 3 O → BP = 3_\n\n"
                    "---\n"
                    "**Trin 3 – Find LP (frie elektronpar på centrale atom)**  \n"
                    "Brug denne fremgangsmåde:\n\n"
                    "1. **V** = valenselektroner i det centrale atom _(H=1, C=4, N=5, O=6, F/Cl/Br=7, S=6, P=5, Xe=8)_\n"
                    "2. Juster for ladning: **+1 per negativ ladning**, −1 per positiv\n"
                    "3. Træk elektroner brugt i bindinger: **V_justeret − 2 × BP**\n"
                    "4. **LP = resultat ÷ 2**\n\n"
                    "| Molekyle | V | Ladning | V_just. | BP | V_just − 2×BP | LP |\n"
                    "|---------|---|---------|---------|----|--------------|----|  \n"
                    "| XeF₂    | 8 | 0       | 8       | 2  | 8 − 4 = 4    | **2** → men OBS: brug Lewisstruktur |\n"
                    "| NH₃     | 5 | 0       | 5       | 3  | 5 − 6 = −1?  | Brug Lewisstruktur → **1** |\n"
                    "| H₂O     | 6 | 0       | 6       | 2  | 6 − 4 = 2    | **1**? → Lewis → **2** |\n\n"
                    "> **Vigtig note:** Formlen `LP = (V − 2×BP) / 2` virker for enkeltbindinger, men ved "
                    "dobbeltbindinger (O, S) og expanderet oktet (Xe, S, Cl, P) er **Lewisstrukturen sikrere**.  \n\n"
                    "---\n"
                    "**Lewisstruktur-metoden (mest pålidelig)**\n\n"
                    "1. Tæl **alle** valenselektroner (inkl. ladning)\n"
                    "2. Tegn bindinger til alle terminale atomer\n"
                    "3. Fyld terminale atomer med lone pairs til oktet\n"
                    "4. Resterende elektroner på centrale atom = LP × 2\n\n"
                    "_Eksempel ClO₃⁻:_ Total = 7+3×6+1 = 26 e⁻. "
                    "3 bindinger = 6 e⁻. Resterende = 20. "
                    "3 O med 3 lone pairs = 18 e⁻. Tilbage til Cl = 2 e⁻ = **1 lone pair** → AB₃E → trigonal pyramidal.\n\n"
                    "---\n"
                    "**Valenselektroner – hurtig reference:**\n\n"
                    "| Gruppe | Grundstoffer | V |\n"
                    "|--------|-------------|---|\n"
                    "| 1 | H, Li, Na, K | 1 |\n"
                    "| 2 | Be, Mg, Ca | 2 |\n"
                    "| 13 | B, Al | 3 |\n"
                    "| 14 | C, Si | 4 |\n"
                    "| 15 | N, P | 5 |\n"
                    "| 16 | O, S, Se | 6 |\n"
                    "| 17 | F, Cl, Br, I | 7 |\n"
                    "| 18 | Xe, Kr | 8 |\n"
                )

        run = st.button("Beregn geometri", type="primary", key="vsepr_run")

    with col_right:
        st.markdown("### Hurtig reference – VSEPR + Hybridisering")
        ref_data = [
            ("2", "0", "2", "sp",    "Lineær",           "180°",     "Upolær*"),
            ("3", "0", "3", "sp²",   "Trigonal plan",    "120°",     "Upolær*"),
            ("3", "1", "2", "sp²",   "Vinklet",          "~120°",    "Polær"),
            ("4", "0", "4", "sp³",   "Tetraedrisk",      "109.5°",   "Upolær*"),
            ("4", "1", "3", "sp³",   "Trig. pyramidal",  "~107°",    "Polær"),
            ("4", "2", "2", "sp³",   "Vinklet",          "~104.5°",  "Polær"),
            ("5", "0", "5", "sp³d",  "Trig. bipyramidal","90°/120°", "Upolær*"),
            ("5", "1", "4", "sp³d",  "Vippestol",        "~90°/120°","Polær"),
            ("5", "2", "3", "sp³d",  "T-formet",         "~90°",     "Polær"),
            ("6", "0", "6", "sp³d²", "Oktaedrisk",       "90°",      "Upolær*"),
            ("6", "1", "5", "sp³d²", "Kv. pyramidal",    "~90°",     "Polær"),
            ("6", "2", "4", "sp³d²", "Kvadratisk plan",  "90°",      "Upolær*"),
        ]
        import pandas as pd
        df = pd.DataFrame(ref_data, columns=["SN", "LP", "BP", "Hybr.", "Geometri", "Vinkler", "Polaritet"])
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.caption("* Upolær kun hvis alle terminale atomer er identiske.")

    if run:
        f = formula.strip() if formula else "?"
        try:
            if input_mode == "🔍 Søg molekyle i database":
                if not f or f == "?":
                    st.error("Angiv en kemisk formel.")
                    st.stop()
                result = predict_vsepr(f)
            else:
                result = predict_vsepr(
                    f or "AX",
                    bonding_pairs=int(bonding_pairs),
                    lone_pairs=int(lone_pairs),
                    all_same_substituents=all_same,
                )

            st.markdown("---")
            st.markdown(f"## Resultat for {result.formula}")

            # Key metrics — now 5 columns including hybridization
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Geometri", result.geometry.name_da)
            c2.metric("Hybridisering", result.hybridization)
            c3.metric("Bindingsvinkler", result.geometry.bond_angles)
            c4.metric("Plan", "Ja" if result.geometry.is_planar else "Nej")
            c5.metric("Polaritet", "Polær 🔴" if result.is_polar else "Upolær ⚪")

            st.markdown("---")

            # Polarity detail
            polarity_color = "🔴" if result.is_polar else "⚪"
            st.markdown(f"### {polarity_color} Polaritet")
            st.info(result.polarity_reason)

            # Geometry + hybridization card
            st.markdown("### 🔷 Geometri & Hybridisering")
            geom = result.geometry
            cols = st.columns([1, 1])
            with cols[0]:
                st.markdown(f"**Engelsk navn:** {geom.name_en}")
                st.markdown(f"**Dansk navn:** {geom.name_da}")
                st.markdown(f"**Sterisk tal (SN):** {result.steric_number}")
                st.markdown(f"**Hybridisering:** {result.hybridization}")
            with cols[1]:
                st.markdown(f"**Bindingspar (BP):** {result.bonding_pairs}")
                st.markdown(f"**Frie elektronpar (LP):** {result.lone_pairs}")
                st.markdown(f"**Bindingsvinkler:** {geom.bond_angles}")
                st.info(HYBRIDIZATION_DESCRIPTION.get(result.steric_number, ""))

            # Steps
            with st.expander("📋 Vis udledning trin for trin", expanded=False):
                for s in result.steps:
                    st.markdown(s)

        except VSEPRError as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"Uventet fejl: {e}")

    # Geometry overview table (always visible)
    st.markdown("---")
    with st.expander("📚 Komplet geometrioversigt (alle geometrier)", expanded=False):
        rows = []
        for (sn, lp), g in sorted(GEOMETRY_TABLE.items()):
            rows.append({
                "SN": sn,
                "LP": lp,
                "BP": sn - lp,
                "Hybridisering": HYBRIDIZATION.get(sn, "?"),
                "Geometri (EN)": g.name_en,
                "Geometri (DA)": g.name_da,
                "Vinkler": g.bond_angles,
                "Plan": "Ja" if g.is_planar else "Nej",
            })
        import pandas as pd
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
