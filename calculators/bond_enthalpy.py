"""
Bond enthalpy ΔH_rxn calculator — Streamlit UI.
"""

from __future__ import annotations

import re
import streamlit as st
import pandas as pd
from core.bond_enthalpy import (
    calculate_bond_enthalpy, BondEnthalpyError,
    list_available_bonds, lookup_bond,
)


# ── Molecule bond database (bonds per molecule) ───────────────────────────────
_MOL_BONDS: dict[str, dict[str, int]] = {
    # Diatomics
    "H2": {"H–H": 1}, "F2": {"F–F": 1}, "Cl2": {"Cl–Cl": 1},
    "Br2": {"Br–Br": 1}, "I2": {"I–I": 1}, "N2": {"N≡N": 1},
    "O2": {"O=O": 1}, "HF": {"H–F": 1}, "HCl": {"H–Cl": 1},
    "HBr": {"H–Br": 1}, "HI": {"H–I": 1}, "CO": {"C≡O": 1},
    "NO": {"N–O": 1},
    # Inorganic
    "H2O": {"H–O": 2}, "H2S": {"H–S": 2}, "H2O2": {"O–O": 1, "H–O": 2},
    "NH3": {"H–N": 3}, "N2H4": {"N–N": 1, "H–N": 4},
    "SO2": {"S=O": 2}, "SO3": {"S=O": 3},
    "CO2": {"C=O": 2}, "NO2": {"N=O": 2},
    "PCl3": {"P–Cl": 3}, "PCl5": {"P–Cl": 5},
    "BrF": {"Br–F": 1}, "BrF3": {"Br–F": 3}, "BrF5": {"Br–F": 5},
    "ClF": {"Cl–F": 1}, "ClF3": {"Cl–F": 3}, "IF5": {"I–F": 5},
    "NF3": {"N–F": 3}, "OF2": {"O–F": 2},
    "HNO3": {"N=O": 1, "N–O": 2, "H–O": 1},
    # Organic — hydrocarbons
    "CH4": {"H–C": 4}, "C2H6": {"C–C": 1, "H–C": 6},
    "C3H8": {"C–C": 2, "H–C": 8}, "C4H10": {"C–C": 3, "H–C": 10},
    "C2H4": {"C=C": 1, "H–C": 4}, "C3H6": {"C=C": 1, "H–C": 6},
    "C2H2": {"C≡C": 1, "H–C": 2},
    "C6H6": {"C=C": 3, "C–C": 3, "H–C": 6},
    # Organic — oxygen
    "CH3OH": {"C–O": 1, "H–O": 1, "H–C": 3},
    "C2H5OH": {"C–C": 1, "C–O": 1, "H–O": 1, "H–C": 5},
    "CH2O": {"C=O": 1, "H–C": 2},
    "CH3CHO": {"C–C": 1, "C=O": 1, "H–C": 4},
    "CH3COOH": {"C–C": 1, "C=O": 1, "C–O": 1, "H–O": 1, "H–C": 3},
    "HCOOH": {"C=O": 1, "C–O": 1, "H–O": 1, "H–C": 1},
    # Nitrogen
    "CH3NH2": {"C–N": 1, "H–N": 2, "H–C": 3},
}

# Normalise keys (users may write BrF3, BRF3, brf3 etc.)
_MOL_BONDS_NORM = {k.upper(): v for k, v in _MOL_BONDS.items()}


def _get_mol_bonds(formula: str) -> dict[str, int] | None:
    return _MOL_BONDS_NORM.get(formula.strip().upper())


def _parse_reaction(eq: str):
    """Return (reactants, products) as lists of (formula, coeff) or (None, error_msg)."""
    parts = re.split(r"->|=>|→|=", eq)
    if len(parts) != 2:
        return None, "Brug → eller -> som pil (fx Br2 + 3F2 -> 2BrF3)"

    def _side(s):
        result = []
        for term in s.split("+"):
            term = term.strip()
            if not term:
                continue
            m = re.match(r"^(\d+(?:\.\d+)?)\s*(.+)$", term)
            if m:
                result.append((m.group(2).strip(), float(m.group(1))))
            else:
                result.append((term, 1.0))
        return result

    return _side(parts[0]), _side(parts[1])


def render_bond_enthalpy_tab():
    """Render the bond enthalpy ΔH calculator sub-tab."""
    st.markdown("## ⚡ Bindingsenthalpier — Beregn ΔH_rxn")
    st.markdown(
        "**ΔH_rxn ≈ Σ(bindinger brudt) − Σ(bindinger dannet)**"
    )
    st.markdown("---")

    mode = st.radio(
        "Tilstand:",
        ["⚗️ Fra reaktionsligning", "🔧 Manuel (binding for binding)"],
        key="be_mode",
        horizontal=True,
    )

    st.markdown("---")

    if mode == "⚗️ Fra reaktionsligning":
        _render_from_equation()
    else:
        _render_manual()


# ── Mode 1: Fra reaktionsligning ──────────────────────────────────────────────

def _render_from_equation():
    st.markdown("### Reaktionsligning")
    st.caption("Skriv den afstemte reaktion. Koefficienter og bindinger beregnes automatisk.")

    eq = st.text_input(
        "Reaktion:",
        value="Br2 + 3F2 -> 2BrF3",
        placeholder="fx H2 + Cl2 -> 2HCl  |  N2 + 3H2 -> 2NH3",
        key="be_eq",
    )

    reactants, products = _parse_reaction(eq) if eq.strip() else (None, "")
    if reactants is None:
        if products:
            st.error(products)
        return

    # ── Collect bonds per molecule ────────────────────────────────────────────
    st.markdown("---")
    all_bond_types: set[str] = set()
    species_data = []  # [{formula, coeff, side, bonds_per_mol}]

    def _species_section(title: str, species_list):
        st.markdown(f"#### {title}")
        for formula, coeff in species_list:
            known = _get_mol_bonds(formula)
            coeff_int = int(coeff) if coeff == int(coeff) else coeff
            st.markdown(f"**{formula}** (koefficient: {coeff_int})")

            if known:
                st.caption(f"Bindinger pr. molekyle (auto-detekteret):")
                bonds_per_mol = {}
                for bond, cnt in known.items():
                    c1, c2 = st.columns([2, 1])
                    with c1:
                        st.write(f"{bond}")
                    with c2:
                        n = st.number_input(
                            "antal",
                            value=cnt, min_value=0, max_value=20,
                            key=f"be_{title[:3]}_{formula}_{bond}",
                            label_visibility="collapsed",
                        )
                    bonds_per_mol[bond] = n
                    all_bond_types.add(bond)
            else:
                st.caption(f"Ikke i database — angiv bindinger manuelt:")
                # Let user add bonds for unknown molecules
                row_key = f"be_custom_{title[:3]}_{formula}"
                if row_key not in st.session_state:
                    st.session_state[row_key] = [{"bond": "", "count": 1}]
                known_bonds = list_available_bonds()
                bonds_per_mol = {}
                to_del = None
                for i, row in enumerate(st.session_state[row_key]):
                    c1, c2, c3 = st.columns([3, 1, 0.5])
                    with c1:
                        bv = st.selectbox(
                            "binding", [""] + known_bonds,
                            index=(known_bonds.index(row["bond"]) + 1) if row["bond"] in known_bonds else 0,
                            key=f"{row_key}_{i}_b",
                            label_visibility="collapsed",
                        )
                    with c2:
                        cv = st.number_input(
                            "antal", value=row["count"], min_value=1, max_value=20,
                            key=f"{row_key}_{i}_c",
                            label_visibility="collapsed",
                        )
                    with c3:
                        if st.button("✕", key=f"{row_key}_{i}_d") and len(st.session_state[row_key]) > 1:
                            to_del = i
                    if bv:
                        bonds_per_mol[bv] = int(cv)
                        all_bond_types.add(bv)
                if to_del is not None:
                    st.session_state[row_key].pop(to_del)
                    st.rerun()
                if st.button("＋ Tilføj binding", key=f"{row_key}_add"):
                    st.session_state[row_key].append({"bond": "", "count": 1})
                    st.rerun()

            species_data.append({
                "formula": formula, "coeff": coeff,
                "side": title[:3], "bonds_per_mol": bonds_per_mol,
            })
            st.markdown("")

    col_r, col_p = st.columns(2)
    with col_r:
        _species_section("Reaktanter (brudte bindinger)", reactants)
    with col_p:
        _species_section("Produkter (dannede bindinger)", products)

    # ── Bond enthalpy overrides ───────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### Bindingsentalpier")
    st.caption(
        "App-databasens standardværdier vises. Overskriv med opgavens egne værdier hvis angivet."
    )

    override_vals: dict[str, float] = {}
    if all_bond_types:
        cols = st.columns(min(len(all_bond_types), 4))
        for i, bond in enumerate(sorted(all_bond_types)):
            db_val = lookup_bond(bond)
            with cols[i % 4]:
                default = float(db_val) if db_val else 0.0
                hint = f"(db: {int(db_val)})" if db_val else "(ikke i db)"
                v = st.number_input(
                    f"{bond} kJ/mol {hint}",
                    value=default, min_value=0.0, step=1.0,
                    key=f"be_ov_{bond}",
                )
                override_vals[bond] = v

    # ── Calculate ─────────────────────────────────────────────────────────────
    st.markdown("")
    if st.button("Beregn ΔH", type="primary", key="be_eq_run"):
        # Build broken/formed lists with coeff × bonds_per_mol
        broken_map: dict[str, float] = {}
        formed_map: dict[str, float] = {}
        breakdown_broken = []
        breakdown_formed = []

        for sp in species_data:
            coeff = sp["coeff"]
            is_reactant = sp["side"] == "Rea"
            target = broken_map if is_reactant else formed_map
            bdown = breakdown_broken if is_reactant else breakdown_formed
            for bond, n_per_mol in sp["bonds_per_mol"].items():
                total_n = coeff * n_per_mol
                target[bond] = target.get(bond, 0) + total_n
                bdown.append({
                    "Molekyle": f"{sp['coeff']:g} × {sp['formula']}",
                    "Binding": bond,
                    "pr. mol.": n_per_mol,
                    "Total": f"{total_n:g}",
                })

        # Compute ΔH
        sum_broken = 0.0
        sum_formed = 0.0
        broken_rows, formed_rows = [], []

        for bond, total_n in broken_map.items():
            dh = override_vals.get(bond, lookup_bond(bond) or 0)
            contrib = total_n * dh
            sum_broken += contrib
            broken_rows.append({"Binding": bond, "Antal": f"{total_n:g}", "ΔH/binding": f"{dh:.0f}", "Total (kJ)": f"+{contrib:.0f}"})

        for bond, total_n in formed_map.items():
            dh = override_vals.get(bond, lookup_bond(bond) or 0)
            contrib = total_n * dh
            sum_formed += contrib
            formed_rows.append({"Binding": bond, "Antal": f"{total_n:g}", "ΔH/binding": f"{dh:.0f}", "Total (kJ)": f"−{contrib:.0f}"})

        delta_h = sum_broken - sum_formed

        # Display results
        st.markdown("---")
        st.markdown("## Resultat")
        c1, c2, c3 = st.columns(3)
        c1.metric("Σ bindinger brudt", f"+{sum_broken:.0f} kJ")
        c2.metric("Σ bindinger dannet", f"−{sum_formed:.0f} kJ")
        sign = "+" if delta_h >= 0 else ""
        c3.metric("ΔH_rxn", f"{sign}{delta_h:.0f} kJ/mol",
                  delta=("Endoterm 🔵" if delta_h > 0 else "Eksoterm 🟢"))

        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.markdown("**Bindinger brudt:**")
            if broken_rows:
                st.dataframe(pd.DataFrame(broken_rows), use_container_width=True, hide_index=True)
        with col_t2:
            st.markdown("**Bindinger dannet:**")
            if formed_rows:
                st.dataframe(pd.DataFrame(formed_rows), use_container_width=True, hide_index=True)

        with st.expander("📋 Bindingsopgørelse pr. molekyle", expanded=False):
            if breakdown_broken:
                st.markdown("**Brudt (reaktanter):**")
                st.dataframe(pd.DataFrame(breakdown_broken), use_container_width=True, hide_index=True)
            if breakdown_formed:
                st.markdown("**Dannet (produkter):**")
                st.dataframe(pd.DataFrame(breakdown_formed), use_container_width=True, hide_index=True)

    # ── Reference table ───────────────────────────────────────────────────────
    _render_ref_table()


# ── Mode 2: Manuel ────────────────────────────────────────────────────────────

def _render_manual():
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
        _render_ref_table()

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

        c1, c2, c3 = st.columns(3)
        c1.metric("Σ bindinger brudt", f"+{result.sum_broken:.0f} kJ")
        c2.metric("Σ bindinger dannet", f"−{result.sum_formed:.0f} kJ")
        sign = "+" if result.delta_h >= 0 else ""
        c3.metric("ΔH_rxn", f"{sign}{result.delta_h:.0f} kJ/mol")

        if result.delta_h > 0:
            st.info("🔵 **Endoterm** reaktion.")
        elif result.delta_h < 0:
            st.success("🟢 **Eksoterm** reaktion.")

        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.markdown("**Bindinger brudt:**")
            if result.broken:
                st.dataframe(pd.DataFrame([
                    {"Binding": e.bond, "Antal": e.count,
                     "Per binding (kJ)": e.enthalpy_per_bond,
                     "Total (kJ)": f"+{e.total:.0f}"}
                    for e in result.broken
                ]), use_container_width=True, hide_index=True)
        with col_t2:
            st.markdown("**Bindinger dannet:**")
            if result.formed:
                st.dataframe(pd.DataFrame([
                    {"Binding": e.bond, "Antal": e.count,
                     "Per binding (kJ)": e.enthalpy_per_bond,
                     "Total (kJ)": f"−{e.total:.0f}"}
                    for e in result.formed
                ]), use_container_width=True, hide_index=True)

        with st.expander("📋 Vis udledning trin for trin", expanded=False):
            for s in result.steps:
                st.markdown(s)


# ── Shared helpers ────────────────────────────────────────────────────────────

def _render_ref_table():
    st.markdown("---")
    with st.expander("📚 Bindingsentalpier (reference)", expanded=False):
        ref_bonds = [
            "H–H", "H–F", "H–Cl", "H–Br", "H–I", "H–O", "H–N", "H–C",
            "F–F", "Cl–Cl", "Br–Br", "I–I",
            "C–C", "C=C", "C≡C", "C–O", "C=O", "C–N", "C≡N",
            "N–N", "N≡N", "O=O", "O–O",
            "Br–F", "Cl–F", "S=O",
        ]
        ref_rows = []
        for b in ref_bonds:
            val = lookup_bond(b)
            if val:
                ref_rows.append({"Binding": b, "ΔH (kJ/mol)": int(val)})
        st.dataframe(pd.DataFrame(ref_rows), use_container_width=True, hide_index=True)
        st.caption("Gennemsnitsværdier fra OpenStax Chemistry 2e / Atkins.")


def _render_bond_rows(label: str, rows: list) -> list[dict]:
    result = []
    to_delete = None
    known = list_available_bonds()

    for i, row in enumerate(rows):
        c1, c2, c3 = st.columns([3, 1, 0.5])
        with c1:
            bond_val = st.selectbox(
                f"Binding {i+1}", options=[""] + known,
                index=(known.index(row["bond"]) + 1) if row["bond"] in known else 0,
                key=f"bond_{label}_{i}_select",
                label_visibility="collapsed",
            )
        with c2:
            count_val = st.number_input(
                "Antal", min_value=1, max_value=20,
                value=row.get("count", 1), step=1,
                key=f"bond_{label}_{i}_count",
                label_visibility="collapsed",
            )
        with c3:
            if len(rows) > 1:
                if st.button("✕", key=f"bond_{label}_{i}_del"):
                    to_delete = i

        result.append({"bond": bond_val, "count": int(count_val)})

    if to_delete is not None:
        rows.pop(to_delete)
        st.rerun()

    return result


def _parse_rows(rows: list[dict]) -> list[tuple[str, int]]:
    return [(r["bond"], r["count"]) for r in rows if r["bond"]]
