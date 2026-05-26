"""
Bond enthalpy ΔH_rxn calculator — Streamlit UI.
"""

import streamlit as st
import pandas as pd
from core.bond_enthalpy import (
    calculate_bond_enthalpy, BondEnthalpyError,
    list_available_bonds, lookup_bond,
)


def render_bond_enthalpy_tab():
    """Render the bond enthalpy ΔH calculator sub-tab."""
    st.markdown("## ⚡ Bindingsenthalpier — Beregn ΔH_rxn")
    st.markdown(
        "Estimer reaktionsenthalpien ud fra gennemsnitlige bindingsenthalpier:\n\n"
        "**ΔH_rxn ≈ Σ(bindinger brudt) − Σ(bindinger dannet)**"
    )
    st.markdown("---")

    col_input, col_ref = st.columns([3, 2], gap="large")

    with col_input:
        st.markdown("### Bindinger brudt (i reaktanter)")
        st.caption("Angiv binding og antal. Brug f.eks. H–H, Cl–Cl, H–Cl, C=O, O=O …")

        if "bond_broken_rows" not in st.session_state:
            st.session_state["bond_broken_rows"] = [{"bond": "", "count": 1}]
        if "bond_formed_rows" not in st.session_state:
            st.session_state["bond_formed_rows"] = [{"bond": "", "count": 1}]

        broken_rows = st.session_state["bond_broken_rows"]
        formed_rows = st.session_state["bond_formed_rows"]

        broken_inputs = _render_bond_rows("brudt", broken_rows)

        col_add_b, _ = st.columns([1, 3])
        with col_add_b:
            if st.button("＋ Tilføj binding", key="bond_add_broken"):
                st.session_state["bond_broken_rows"].append({"bond": "", "count": 1})
                st.rerun()

        st.markdown("### Bindinger dannet (i produkter)")
        formed_inputs = _render_bond_rows("dannet", formed_rows)

        col_add_f, _ = st.columns([1, 3])
        with col_add_f:
            if st.button("＋ Tilføj binding", key="bond_add_formed"):
                st.session_state["bond_formed_rows"].append({"bond": "", "count": 1})
                st.rerun()

        st.markdown("")
        run = st.button("Beregn ΔH", type="primary", key="bond_run")

    with col_ref:
        st.markdown("### Bindingsentalpier (udvalg)")
        ref_bonds = [
            "H–H", "H–F", "H–Cl", "H–Br", "H–I", "H–O", "H–N", "H–C",
            "F–F", "Cl–Cl", "Br–Br", "I–I",
            "C–C", "C=C", "C≡C", "C–O", "C=O", "C–N", "C≡N",
            "N–N", "N≡N", "O=O", "O–O",
            "Br–F", "Cl–Br",
        ]
        ref_rows = []
        for b in ref_bonds:
            val = lookup_bond(b)
            if val:
                ref_rows.append({"Binding": b, "ΔH (kJ/mol)": int(val)})
        st.dataframe(
            pd.DataFrame(ref_rows),
            use_container_width=True,
            hide_index=True,
            height=400,
        )
        st.caption("Gennemsnitsværdier fra OpenStax Chemistry 2e / Atkins.")

    # ── Result ───────────────────────────────────────────────────────────────
    if run:
        parsed_broken = _parse_rows(broken_inputs)
        parsed_formed = _parse_rows(formed_inputs)

        if not parsed_broken and not parsed_formed:
            st.error("Angiv mindst én binding.")
            st.stop()

        try:
            result = calculate_bond_enthalpy(parsed_broken, parsed_formed)
        except BondEnthalpyError as e:
            st.error(str(e))
            st.stop()

        st.markdown("---")
        st.markdown("## Resultat")

        # Summary metrics
        c1, c2, c3 = st.columns(3)
        c1.metric("Σ bindinger brudt", f"+{result.sum_broken:.0f} kJ")
        c2.metric("Σ bindinger dannet", f"−{result.sum_formed:.0f} kJ")
        sign = "+" if result.delta_h >= 0 else ""
        c3.metric("ΔH_rxn", f"{sign}{result.delta_h:.0f} kJ/mol")

        if result.delta_h > 0:
            st.info("🔵 **Endoterm** reaktion — reaktionen absorberer energi fra omgivelserne.")
        elif result.delta_h < 0:
            st.success("🟢 **Eksoterm** reaktion — reaktionen frigiver energi til omgivelserne.")
        else:
            st.info("⚪ Neutral reaktion — ingen netto energiudveksling.")

        # Detail tables
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.markdown("**Bindinger brudt:**")
            if result.broken:
                df_b = pd.DataFrame([
                    {"Binding": e.bond, "Antal": e.count,
                     "Per binding (kJ)": e.enthalpy_per_bond,
                     "Total (kJ)": f"+{e.total:.0f}"}
                    for e in result.broken
                ])
                st.dataframe(df_b, use_container_width=True, hide_index=True)
        with col_t2:
            st.markdown("**Bindinger dannet:**")
            if result.formed:
                df_f = pd.DataFrame([
                    {"Binding": e.bond, "Antal": e.count,
                     "Per binding (kJ)": e.enthalpy_per_bond,
                     "Total (kJ)": f"−{e.total:.0f}"}
                    for e in result.formed
                ])
                st.dataframe(df_f, use_container_width=True, hide_index=True)

        with st.expander("📋 Vis udledning trin for trin", expanded=False):
            for s in result.steps:
                st.markdown(s)

    # ── Example reactions ───────────────────────────────────────────────────
    st.markdown("---")
    with st.expander("💡 Eksempler fra eksamensopgaver", expanded=False):
        st.markdown("""
**Eksempel 1: H₂ + F₂ → 2 HF**
- Brudt: 1 × H–H (436), 1 × F–F (159)
- Dannet: 2 × H–F (570)
- ΔH = (436 + 159) − 2×570 = 595 − 1140 = **−545 kJ/mol**

**Eksempel 2: H₂ + Br₂ → 2 HBr**
- Brudt: 1 × H–H (436), 1 × Br–Br (193)
- Dannet: 2 × H–Br (366)
- ΔH = (436 + 193) − 2×366 = 629 − 732 = **−103 kJ/mol**

**Eksempel 3: N₂ + 3H₂ → 2 NH₃**
- Brudt: 1 × N≡N (945), 3 × H–H (436)
- Dannet: 6 × N–H (391)
- ΔH = (945 + 1308) − 2346 = 2253 − 2346 = **−93 kJ/mol**
        """)


def _render_bond_rows(label: str, rows: list) -> list[dict]:
    """Render editable bond input rows and return current values."""
    result = []
    to_delete = None
    known = list_available_bonds()

    for i, row in enumerate(rows):
        c1, c2, c3 = st.columns([3, 1, 0.5])
        with c1:
            bond_val = st.selectbox(
                f"Binding {i+1}",
                options=[""] + known,
                index=(known.index(row["bond"]) + 1) if row["bond"] in known else 0,
                key=f"bond_{label}_{i}_select",
                label_visibility="collapsed",
            )
        with c2:
            count_val = st.number_input(
                "Antal",
                min_value=1, max_value=20,
                value=row.get("count", 1),
                step=1,
                key=f"bond_{label}_{i}_count",
                label_visibility="collapsed",
            )
        with c3:
            if len(rows) > 1:
                if st.button("✕", key=f"bond_{label}_{i}_del", help="Fjern"):
                    to_delete = i

        result.append({"bond": bond_val, "count": int(count_val)})

    if to_delete is not None:
        rows.pop(to_delete)
        st.rerun()

    return result


def _parse_rows(rows: list[dict]) -> list[tuple[str, int]]:
    """Filter out empty rows and return (bond, count) pairs."""
    return [(r["bond"], r["count"]) for r in rows if r["bond"]]
