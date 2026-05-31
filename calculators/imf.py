"""
Intermolecular forces (IMF) classifier — Streamlit UI.
"""

import streamlit as st
import pandas as pd
from core.imf import (
    classify_imf, compare_imf, IMFError, IMFType,
    IMF_STRENGTH_RANK, IMF_STRENGTH_LABEL, list_known_molecules,
)


_IMF_COLORS = {
    IMFType.ION_ION:          "#e74c3c",
    IMFType.ION_DIPOLE:       "#e67e22",
    IMFType.HYDROGEN_BOND:    "#2980b9",
    IMFType.DIPOLE_DIPOLE:    "#8e44ad",
    IMFType.VAN_DER_WAALS:    "#27ae60",
}


def render_imf_tab():
    """Render the IMF classifier sub-tab."""
    st.markdown("## 🔗 Intermolekylære kræfter (IMF)")
    st.markdown(
        "Identificér de dominerende kræfter mellem molekyler og forstå forskelle i "
        "kogepunkt og damptryk."
    )
    st.markdown("---")

    mode = st.radio(
        "Tilstand:",
        ["🔍 Enkelt molekyle", "⚖️ Sammenlign molekyler (bp/damptryk rækkefølge)", "✏️ Manuel klassificering"],
        key="imf_mode",
        horizontal=True,
    )

    st.markdown("---")

    # ── Single molecule ──────────────────────────────────────────────────────
    if mode == "🔍 Enkelt molekyle":
        col1, col2 = st.columns([2, 1])
        with col1:
            formula = st.text_input(
                "Kemisk formel:",
                placeholder="fx H2O, NH3, CH4, HCl, C2H5OH",
                key="imf_single_formula",
            )
        with col2:
            st.caption("Understøttede molekyler:")
            st.caption(", ".join(list_known_molecules()[:20]) + " …")

        if st.button("Klassificér IMF", type="primary", key="imf_single_run"):
            if not formula.strip():
                st.error("Angiv en kemisk formel.")
            else:
                try:
                    result = classify_imf(formula.strip())
                    _render_imf_result(result)
                except IMFError as e:
                    st.error(str(e))

    # ── Compare molecules ────────────────────────────────────────────────────
    elif mode == "⚖️ Sammenlign molekyler (bp/damptryk rækkefølge)":
        st.markdown("Indtast 2–6 molekyler (ét pr. linje eller komma-separeret):")
        raw = st.text_area(
            "Molekyler:",
            placeholder="H2O\nHCl\nCH4\nNH3",
            height=130,
            key="imf_compare_input",
        )
        if st.button("Sammenlign", type="primary", key="imf_compare_run"):
            formulas = [f.strip() for f in raw.replace(",", "\n").splitlines() if f.strip()]
            if len(formulas) < 2:
                st.error("Angiv mindst 2 molekyler.")
            else:
                results = compare_imf(formulas)
                missing = [f for f in formulas if f not in [r[0] for r in results]]
                if missing:
                    st.warning(f"Ikke genkendt (ignoreret): {', '.join(missing)}")
                if results:
                    n = len(results)

                    # ── Visual rank cards ────────────────────────────────────
                    st.markdown("### Rangering (svageste → stærkeste IMF)")

                    # Vapor pressure: rank 1 (weakest IMF) = highest VP
                    st.markdown("#### 💨 Damptryk (højest → lavest)")
                    vp_cols = st.columns(n)
                    for i, (f, r) in enumerate(results):
                        with vp_cols[i]:
                            if i == 0:
                                st.success(f"**#{i+1} HØJEST**\n\n### {f}")
                            elif i == n - 1:
                                st.error(f"**#{i+1} lavest**\n\n{f}")
                            else:
                                st.info(f"**#{i+1}**\n\n{f}")
                            st.caption(r.dominant_imf.value)

                    st.markdown("#### 🌡️ Kogepunkt (lavest → højest)")
                    bp_cols = st.columns(n)
                    for i, (f, r) in enumerate(results):
                        with bp_cols[i]:
                            if i == 0:
                                st.success(f"**#{i+1} LAVEST**\n\n### {f}")
                            elif i == n - 1:
                                st.error(f"**#{i+1} højest**\n\n{f}")
                            else:
                                st.info(f"**#{i+1}**\n\n{f}")
                            st.caption(r.dominant_imf.value)

                    # ── Detail table ─────────────────────────────────────────
                    st.markdown("---")
                    rows = []
                    for rank, (f, r) in enumerate(results, 1):
                        rows.append({
                            "IMF-rang": rank,
                            "Molekyle": f,
                            "Dominerende IMF": r.dominant_imf.value,
                            "Polær": "Ja" if r.is_polar else "Nej",
                            "H-bond donor": "Ja" if r.has_hbond_donor else "Nej",
                            "Damptryk-rang (1=højest)": rank,
                            "Kogepunkt-rang (1=lavest)": rank,
                        })
                    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

                    st.markdown("### Forklaring pr. molekyle")
                    for f, r in results:
                        with st.expander(f"{f} — {r.dominant_imf.value}", expanded=False):
                            for s in r.steps:
                                st.markdown(s)

    # ── Manual ──────────────────────────────────────────────────────────────
    else:
        st.markdown("Angiv molekyleegenskaber manuelt:")
        formula = st.text_input("Navn / formel (til visning):", value="mit molekyle", key="imf_manual_formula")
        col1, col2 = st.columns(2)
        with col1:
            is_ion     = st.checkbox("Er det et ion/ionisk forbindelse?",   key="imf_is_ion")
            is_polar   = st.checkbox("Er molekylet polært?",                key="imf_is_polar")
        with col2:
            hb_donor   = st.checkbox("H-bond donor (H bundet til N/O/F)?", key="imf_hb_donor")
            hb_accept  = st.checkbox("H-bond acceptor (N/O/F med frie par)?", key="imf_hb_accept")
        molar_mass = st.number_input("Approx. molarmasse (g/mol):", min_value=1.0, value=18.0, step=1.0, key="imf_mm")

        if st.button("Klassificér", type="primary", key="imf_manual_run"):
            try:
                result = classify_imf(
                    formula,
                    is_ion=is_ion,
                    is_polar=is_polar,
                    has_hbond_donor=hb_donor,
                    has_hbond_acceptor=hb_accept,
                    molar_mass=molar_mass,
                )
                _render_imf_result(result)
            except IMFError as e:
                st.error(str(e))

    # ── Always: IMF reference table ─────────────────────────────────────────
    st.markdown("---")
    with st.expander("📚 IMF-referencetabel", expanded=False):
        ref_rows = [
            ["Ion–ion", "Salte, ioniske forbindelser", "~100–1000 kJ/mol", "Meget høj", "Meget lav"],
            ["Hydrogenbinding", "H bundet til N, O eller F; acceptor: N, O, F", "~10–40 kJ/mol", "Høj", "Lav"],
            ["Dipol–dipol", "Polære molekyler (ingen H-bond donor)", "~5–25 kJ/mol", "Moderat", "Moderat"],
            ["London (van der Waals)", "Alle molekyler; stiger med molarmasse", "<5 kJ/mol", "Lav", "Høj"],
        ]
        df_ref = pd.DataFrame(
            ref_rows,
            columns=["Kraft", "Krav", "Styrke", "Kogepunkt", "Damptryk"],
        )
        st.dataframe(df_ref, use_container_width=True, hide_index=True)

        st.markdown(
            "**Huskeregel:** H-bond kræver **donor** (N–H, O–H, F–H) *og* **acceptor** "
            "(frit elektronpar på N, O eller F). S og Cl er *ikke* elektronegative nok."
        )


def _render_imf_result(result):
    """Render a single IMFResult."""
    st.markdown("---")
    st.markdown(f"## Resultat for {result.formula}")

    # Metrics row
    cols = st.columns(4)
    cols[0].metric("Dominerende IMF", result.dominant_imf.value.split("(")[0].strip())
    cols[1].metric("Polær", "Ja" if result.is_polar else "Nej")
    cols[2].metric("Kogepunkt (trend)", result.boiling_point_trend)
    cols[3].metric("Damptryk (trend)", result.vapor_pressure_trend)

    # IMF type badges
    st.markdown("### Aktive kræfter (svageste → stærkeste):")
    sorted_imf = sorted(result.imf_types, key=lambda t: IMF_STRENGTH_RANK[t])
    for imf in sorted_imf:
        color = _IMF_COLORS.get(imf, "#555")
        strength = IMF_STRENGTH_LABEL[imf]
        st.markdown(
            f"<span style='background:{color};color:white;padding:4px 10px;"
            f"border-radius:12px;margin-right:6px;font-weight:600'>"
            f"{imf.value}</span>  {strength}",
            unsafe_allow_html=True,
        )

    # Detailed steps
    with st.expander("📋 Vis udledning trin for trin", expanded=True):
        for s in result.steps:
            st.markdown(s)
