"""
Graham's law of effusion — Streamlit UI tab.
"""

import streamlit as st
import pandas as pd
from core.graham import (
    calculate_graham, calculate_graham_unknown_mass,
    GrahamError, COMMON_GAS_MASSES,
)


def render_graham_tab():
    """Render Graham's law of effusion sub-tab."""
    st.markdown("## 💨 Grahams lov – Effusion og diffusion")
    st.markdown(
        "Sammenlign effusionshastigheder af to gasser eller find en ukendt molarmasse."
    )
    st.markdown(
        r"$$\frac{r_1}{r_2} = \sqrt{\frac{M_2}{M_1}}$$"
        r"  ·  "
        r"$$\frac{t_1}{t_2} = \sqrt{\frac{M_1}{M_2}}$$"
    )
    st.markdown("---")

    mode = st.radio(
        "Opgavetype:",
        [
            "⚡ Sammenlign to gassers effusionshastighed",
            "🔍 Find molarmasse af ukendt gas",
        ],
        key="graham_mode",
        horizontal=True,
    )

    known_gases = sorted(COMMON_GAS_MASSES.keys())

    # ── Compare two gases ─────────────────────────────────────────────────────
    if mode == "⚡ Sammenlign to gassers effusionshastighed":
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Gas 1**")
            g1_mode = st.radio("Input:", ["Vælg fra liste", "Manuel M"], key="g1_mode", horizontal=True)
            if g1_mode == "Vælg fra liste":
                gas1 = st.selectbox("Gas 1:", known_gases, index=known_gases.index("H2"), key="g1_select")
                M1 = None
            else:
                gas1 = st.text_input("Navn/label:", value="Gas A", key="g1_name")
                M1 = st.number_input("M₁ (g/mol):", min_value=0.1, value=2.016, key="g1_M")

        with col2:
            st.markdown("**Gas 2**")
            g2_mode = st.radio("Input:", ["Vælg fra liste", "Manuel M"], key="g2_mode", horizontal=True)
            if g2_mode == "Vælg fra liste":
                gas2 = st.selectbox("Gas 2:", known_gases, index=known_gases.index("O2"), key="g2_select")
                M2 = None
            else:
                gas2 = st.text_input("Navn/label:", value="Gas B", key="g2_name")
                M2 = st.number_input("M₂ (g/mol):", min_value=0.1, value=32.00, key="g2_M")

        if st.button("Beregn", type="primary", key="graham_compare_run"):
            try:
                result = calculate_graham(gas1, gas2, M1, M2)

                st.markdown("---")
                c1, c2, c3 = st.columns(3)
                c1.metric(f"r({result.gas1}) / r({result.gas2})", f"{result.rate_ratio:.4f}")
                c2.metric(f"t({result.gas1}) / t({result.gas2})", f"{result.time_ratio:.4f}")
                c3.metric("Hurtigste gas", result.faster_gas)

                if result.rate_ratio > 1:
                    st.success(
                        f"**{result.gas1}** effunderer **{result.rate_ratio:.2f}×** hurtigere end **{result.gas2}** "
                        f"(lettere gas, M = {result.M1:.3f} vs {result.M2:.3f} g/mol)"
                    )
                elif result.rate_ratio < 1:
                    st.warning(
                        f"**{result.gas2}** effunderer **{1/result.rate_ratio:.2f}×** hurtigere end **{result.gas1}** "
                        f"(lettere gas, M = {result.M2:.3f} vs {result.M1:.3f} g/mol)"
                    )
                else:
                    st.info("Begge gasser effunderer med samme hastighed.")

                with st.expander("📋 Vis udledning", expanded=False):
                    for s in result.steps:
                        st.markdown(s)

            except GrahamError as e:
                st.error(str(e))

    # ── Unknown molar mass ────────────────────────────────────────────────────
    else:
        st.markdown(
            "Brug en målt hastighedsforhold eller tidsforhold til at bestemme "
            "molarmassen af en ukendt gas."
        )
        col1, col2 = st.columns(2)
        with col1:
            k_mode = st.radio("Kendte gas:", ["Vælg fra liste", "Manuel M"], key="unk_kmode", horizontal=True)
            if k_mode == "Vælg fra liste":
                known_gas = st.selectbox("Kendt gas:", known_gases, index=known_gases.index("H2"), key="unk_kgas")
                M_known = None
            else:
                known_gas = st.text_input("Navn/label:", value="H2", key="unk_kname")
                M_known = st.number_input("M_kendt (g/mol):", min_value=0.1, value=2.016, key="unk_kM")

        with col2:
            ratio_type = st.radio(
                "Givet forholdet:",
                ["r_kendt/r_ukendt (hastighedsforhold)", "t_ukendt/t_kendt (tidsforhold)"],
                key="unk_rtype",
            )
            ratio_val = st.number_input("Forholdet:", min_value=0.001, value=4.0, step=0.01, key="unk_ratio")

        if st.button("Find molarmasse", type="primary", key="graham_unk_run"):
            try:
                if "hastighed" in ratio_type:
                    m_unk, steps = calculate_graham_unknown_mass(known_gas, M_known, rate_ratio=ratio_val)
                else:
                    m_unk, steps = calculate_graham_unknown_mass(known_gas, M_known, time_ratio=ratio_val)

                st.markdown("---")
                st.metric("Molarmasse af ukendt gas", f"{m_unk:.3f} g/mol")

                # Guess identity
                closest = min(COMMON_GAS_MASSES.items(), key=lambda x: abs(x[1] - m_unk))
                if abs(closest[1] - m_unk) < 2:
                    st.info(f"Ligner: **{closest[0]}** (M = {closest[1]:.3f} g/mol)")

                with st.expander("📋 Vis udledning", expanded=False):
                    for s in steps:
                        st.markdown(s)
            except GrahamError as e:
                st.error(str(e))

    # ── Reference table ───────────────────────────────────────────────────────
    st.markdown("---")
    with st.expander("📚 Molarmasser for almindelige gasser", expanded=False):
        rows = [{"Gas": k, "M (g/mol)": v} for k, v in sorted(COMMON_GAS_MASSES.items(), key=lambda x: x[1])]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    with st.expander("💡 Eksamenseksempler", expanded=False):
        st.markdown("""
**Eksempel 1:** Hvad er forholdet mellem effusionshastighederne af H₂ og O₂?

r(H₂)/r(O₂) = √(M(O₂)/M(H₂)) = √(32.00/2.016) = √15.87 = **3.98**

→ H₂ effunderer **~4 gange** hurtigere end O₂.

---

**Eksempel 2:** En ukendt gas effunderer 3.16× langsommere end H₂. Find molarmassen.

r(H₂)/r(X) = 3.16  →  M(X) = M(H₂) × 3.16² = 2.016 × 9.99 = **~20 g/mol** → He ikke, **Ne (20.18)**

---

**Eksempel 3 (tidsforhold):** En ukendt gas bruger 2× så lang tid som CH₄.

t(X)/t(CH₄) = 2  →  M(X) = M(CH₄) × 2² = 16.04 × 4 = **~64 g/mol** → SO₂ (64.06)
        """)
