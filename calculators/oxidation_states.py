"""
Dedicated oxidation state assignment tool — Streamlit UI tab.
"""

import streamlit as st
import pandas as pd
import re
from typing import Optional


# ---------------------------------------------------------------------------
# Core logic: assign oxidation states using standard rules
# ---------------------------------------------------------------------------

ELECTRONEGATIVITIES = {
    "F": 3.98, "O": 3.44, "N": 3.04, "Cl": 3.16, "Br": 2.96,
    "I": 2.66, "S": 2.58, "C": 2.55, "H": 2.20, "P": 2.19,
    "Si": 1.90, "B": 2.04, "Al": 1.61,
}

# Fixed oxidation states by element in most compounds
FIXED_STATES: dict[str, int] = {
    "F":  -1,    # always -1
    "H":  +1,    # +1 (except metal hydrides: -1)
    "O":  -2,    # -2 (except peroxides: -1, OF2: +2)
    "Na": +1, "K": +1, "Li": +1, "Rb": +1, "Cs": +1,   # group 1
    "Ca": +2, "Mg": +2, "Ba": +2, "Sr": +2, "Be": +2,  # group 2
    "Al": +3, "Zn": +2, "Ag": +1,
}

SPECIAL_CASES: dict[str, dict[str, int]] = {
    "H2O2": {"H": +1, "O": -1},
    "Na2O2": {"Na": +1, "O": -1},
    "BaO2": {"Ba": +2, "O": -1},
    "KO2": {"K": +1, "O": -1/2},
    "OF2": {"O": +2, "F": -1},
    "NaH": {"Na": +1, "H": -1},
    "CaH2": {"Ca": +2, "H": -1},
    "LiH": {"Li": +1, "H": -1},
}

COMMON_IONS: dict[str, dict[str, int]] = {
    "SO4":   {"S": +6, "O": -2},
    "SO3":   {"S": +4, "O": -2},
    "NO3":   {"N": +5, "O": -2},
    "NO2":   {"N": +3, "O": -2},
    "PO4":   {"P": +5, "O": -2},
    "ClO4":  {"Cl": +7, "O": -2},
    "ClO3":  {"Cl": +5, "O": -2},
    "ClO2":  {"Cl": +3, "O": -2},
    "ClO":   {"Cl": +1, "O": -2},
    "MnO4":  {"Mn": +7, "O": -2},
    "CrO4":  {"Cr": +6, "O": -2},
    "Cr2O7": {"Cr": +6, "O": -2},
    "CO3":   {"C": +4, "O": -2},
    "HCO3":  {"H": +1, "C": +4, "O": -2},
    "NH4":   {"N": -3, "H": +1},
    "OH":    {"O": -2, "H": +1},
    "CN":    {"C": +2, "N": -3},
    "SCN":   {"S": -1, "C": +4, "N": -3},
}


def parse_formula(formula: str) -> dict[str, int]:
    """Parse chemical formula into {element: count} dict."""
    formula = formula.strip()
    # Remove charge notation
    formula = re.sub(r"[\d]*[+-]+$|[+-]+[\d]*$", "", formula)
    # Expand parentheses iteratively
    while "(" in formula:
        formula = re.sub(
            r"\(([^()]+)\)(\d*)",
            lambda m: _expand_group(m.group(1), int(m.group(2)) if m.group(2) else 1),
            formula,
        )
    tokens = re.findall(r"([A-Z][a-z]?)(\d*)", formula)
    counts: dict[str, int] = {}
    for elem, cnt in tokens:
        if elem:
            counts[elem] = counts.get(elem, 0) + (int(cnt) if cnt else 1)
    return counts


def _expand_group(inner: str, multiplier: int) -> str:
    tokens = re.findall(r"([A-Z][a-z]?)(\d*)", inner)
    result = ""
    for elem, cnt in tokens:
        n = (int(cnt) if cnt else 1) * multiplier
        result += f"{elem}{n}"
    return result


def assign_oxidation_states(formula: str, charge: int = 0) -> dict[str, float]:
    """
    Assign oxidation states for each element in formula.
    Returns {element: ox_state}.
    Raises ValueError if indeterminate.
    """
    formula_clean = formula.strip()

    # Check special cases first
    for key, states in SPECIAL_CASES.items():
        if formula_clean.upper() == key.upper():
            return states

    # Check common ions / polyatomics
    for key, states in COMMON_IONS.items():
        if formula_clean.upper() == key.upper():
            return states

    counts = parse_formula(formula_clean)
    if not counts:
        raise ValueError("Kunne ikke parse formel.")

    elements = list(counts.keys())

    # Pure element
    if len(elements) == 1:
        return {elements[0]: 0}

    known: dict[str, float] = {}
    unknown_elems: list[str] = []

    for elem in elements:
        if elem in FIXED_STATES:
            # Special: H is -1 in metal hydrides (check later)
            known[elem] = float(FIXED_STATES[elem])
        else:
            unknown_elems.append(elem)

    # Sum of known contributions
    known_sum = sum(known[e] * counts[e] for e in known)
    unknown_total = charge - known_sum

    if len(unknown_elems) == 0:
        # Verify
        total = sum(known[e] * counts[e] for e in known)
        if abs(total - charge) > 0.01:
            raise ValueError(
                f"Inkonsistente oxidationstrin: sum={total:.1f}, forventet={charge}. "
                "Tjek specialtilfælde (peroxid, metalhydrid etc.)."
            )
        return known

    elif len(unknown_elems) == 1:
        elem = unknown_elems[0]
        ox = unknown_total / counts[elem]
        known[elem] = ox
        return known
    else:
        raise ValueError(
            f"Kan ikke entydigt bestemme oxidationstrin for {', '.join(unknown_elems)}. "
            "Der er mere end ét ukendt element. Angiv oxidationstrin manuelt."
        )


def format_ox(val: float) -> str:
    if val == int(val):
        n = int(val)
        return f"+{n}" if n >= 0 else str(n)
    return f"+{val:.2f}" if val > 0 else f"{val:.2f}"


# ---------------------------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------------------------

def render_oxidation_states_tab():
    """Render the dedicated oxidation state assignment tab."""
    st.markdown("## 🔢 Oxidationstrin")
    st.markdown(
        "Bestem oxidationstrin for hvert grundstof i en kemisk forbindelse. "
        "Bruges til at identificere oxidation/reduktion i redoxreaktioner."
    )
    st.markdown("---")

    col_input, col_rules = st.columns([3, 2], gap="large")

    with col_input:
        st.markdown("### Input")
        formula = st.text_input(
            "Kemisk formel eller forbindelsesbetegnelse:",
            placeholder="fx KMnO4, Cr2O7, Fe2O3, H2SO4, NH4Cl",
            key="ox_formula",
        )
        charge = st.number_input(
            "Ladning på ion (0 for neutral forbindelse):",
            min_value=-6, max_value=6, value=0, step=1,
            key="ox_charge",
        )

        run = st.button("Bestem oxidationstrin", type="primary", key="ox_run")

        # Multi-species comparison
        st.markdown("---")
        st.markdown("### Sammenlign oxidationstrin i reaktion")
        st.markdown("Angiv reaktant- og produktformler for at se ændringer:")
        col_r, col_p = st.columns(2)
        with col_r:
            reactant_str = st.text_area("Reaktanter (én pr. linje):", height=90, key="ox_reactants",
                                        placeholder="Fe\nFe2O3")
        with col_p:
            product_str = st.text_area("Produkter (én pr. linje):", height=90, key="ox_products",
                                       placeholder="Fe2O3\nFe")
        compare_run = st.button("Sammenlign", key="ox_compare_run")

    with col_rules:
        st.markdown("### Regler for oxidationstrin")
        rules = [
            ["1", "Rent grundstof", "0", "Fe, O₂, H₂"],
            ["2", "Monoatomisk ion", "= ladning", "Na⁺ = +1, Cl⁻ = −1"],
            ["3", "F i forbindelser", "−1", "altid"],
            ["4", "O i forbindelser", "−2", "undtagen peroxid (−1), OF₂ (+2)"],
            ["5", "H med ikke-metal", "+1", "HCl, H₂O"],
            ["6", "H med metal", "−1", "NaH, CaH₂"],
            ["7", "Gruppe 1 metaller", "+1", "Na, K, Li"],
            ["8", "Gruppe 2 metaller", "+2", "Ca, Mg, Ba"],
            ["9", "Sum i neutral", "= 0", "alle atomer"],
            ["10", "Sum i ion", "= ladning", "SO₄²⁻: sum = −2"],
        ]
        df = pd.DataFrame(rules, columns=["#", "Regel", "Oxidationstrin", "Eksempel"])
        st.dataframe(df, use_container_width=True, hide_index=True)

    # ── Single compound result ────────────────────────────────────────────────
    if run:
        if not formula.strip():
            st.error("Angiv en kemisk formel.")
        else:
            _show_single_result(formula.strip(), int(charge))

    # ── Comparison result ─────────────────────────────────────────────────────
    if compare_run:
        reactants = [f.strip() for f in reactant_str.splitlines() if f.strip()]
        products  = [f.strip() for f in product_str.splitlines()  if f.strip()]
        if not reactants and not products:
            st.error("Angiv mindst én reaktant eller produkt.")
        else:
            _show_comparison(reactants, products)

    # ── Common examples ───────────────────────────────────────────────────────
    st.markdown("---")
    with st.expander("💡 Hyppige eksempler fra eksamen", expanded=False):
        examples = [
            ("KMnO4",  0, "Mn i permanganat"),
            ("K2Cr2O7",0, "Cr i dichromat"),
            ("H2SO4",  0, "S i svovlsyre"),
            ("HNO3",   0, "N i salpetersyre"),
            ("Fe2O3",  0, "Fe i jernoxid"),
            ("Na2O2",  0, "O i natriumperoxid (−1)"),
            ("NH4",    1, "N i ammoniumion"),
            ("SO4",   -2, "S i sulfation"),
            ("MnO4",  -1, "Mn i permanganation"),
            ("Cr2O7", -2, "Cr i dichromation"),
        ]
        for f, q, note in examples:
            try:
                states = assign_oxidation_states(f, q)
                counts = parse_formula(f)
                parts = [f"{el}: **{format_ox(ox)}**" for el, ox in states.items()]
                lbl = f"{f}" + (f"^{q:+d}" if q != 0 else "")
                st.markdown(f"- **{lbl}** ({note}): {', '.join(parts)}")
            except ValueError:
                pass


def _show_single_result(formula: str, charge: int):
    st.markdown("---")
    try:
        states = assign_oxidation_states(formula, charge)
        counts = parse_formula(formula)
    except ValueError as e:
        st.error(str(e))
        return

    st.markdown(f"## Oxidationstrin i {formula}" + (f" (ladning {charge:+d})" if charge != 0 else ""))

    rows = []
    total = 0.0
    for elem, ox in states.items():
        cnt = counts.get(elem, 1)
        contrib = ox * cnt
        total += contrib
        rows.append({
            "Grundstof": elem,
            "Antal atomer": cnt,
            "Oxidationstrin": format_ox(ox),
            "Bidrag (× antal)": f"{format_ox(contrib)}",
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.markdown(f"**Sum = {total:+.1f}** (forventet = {charge:+d})")

    # Metrics
    cols = st.columns(len(states))
    for i, (elem, ox) in enumerate(states.items()):
        cols[i].metric(elem, format_ox(ox))

    # Rules applied
    with st.expander("📋 Regler anvendt", expanded=False):
        for elem, ox in states.items():
            cnt = counts.get(elem, 1)
            if ox == 0:
                rule = "Rent grundstof → 0"
            elif elem == "F":
                rule = "F er altid −1"
            elif elem == "O":
                if ox == -2:
                    rule = "O er normalt −2"
                elif ox == -1:
                    rule = "O = −1 i peroxid"
                else:
                    rule = f"O = {format_ox(ox)} (specialtilfælde)"
            elif elem == "H":
                rule = f"H = {format_ox(ox)} ({'metalhydrid' if ox == -1 else 'normal'})"
            elif elem in ("Na","K","Li","Rb","Cs"):
                rule = f"Gruppe 1 metal = {format_ox(ox)}"
            elif elem in ("Ca","Mg","Ba","Sr","Be"):
                rule = f"Gruppe 2 metal = {format_ox(ox)}"
            else:
                rule = f"Beregnet fra: sum = {charge}, kendte bidrag"
            st.markdown(f"- **{elem}** ({cnt}×): {format_ox(ox)} — {rule}")


def _show_comparison(reactants: list[str], products: list[str]):
    st.markdown("---")
    st.markdown("## Sammenligning — ændringer i oxidationstrin")

    all_data: dict[str, dict[str, Optional[float]]] = {}

    for formula in reactants + products:
        try:
            states = assign_oxidation_states(formula, 0)
            for elem, ox in states.items():
                if elem not in all_data:
                    all_data[elem] = {}
                # Use formula as key for source
                all_data[elem][formula] = ox
        except ValueError:
            st.warning(f"Kunne ikke bestemme oxidationstrin for {formula}.")

    if not all_data:
        return

    # Build change table
    changes = []
    for elem, source_map in all_data.items():
        react_vals = [source_map.get(f) for f in reactants if f in source_map]
        prod_vals  = [source_map.get(f) for f in products  if f in source_map]
        react_ox = react_vals[0] if react_vals else None
        prod_ox  = prod_vals[0]  if prod_vals  else None
        if react_ox is not None and prod_ox is not None and react_ox != prod_ox:
            diff = prod_ox - react_ox
            if diff > 0:
                role = "🔴 Oxideret"
            else:
                role = "🔵 Reduceret"
            changes.append({
                "Grundstof": elem,
                "Ox. reaktant": format_ox(react_ox),
                "Ox. produkt":  format_ox(prod_ox),
                "Ændring": f"{diff:+.0f}",
                "Rolle": role,
            })

    if changes:
        st.markdown("### Grundstoffer der ændrer oxidationstrin:")
        st.dataframe(pd.DataFrame(changes), use_container_width=True, hide_index=True)
        st.markdown(
            "🔴 **Oxideret** = øget oxidationstrin (afgiver elektroner) — er **reduktionsmidlet**\n\n"
            "🔵 **Reduceret** = sænket oxidationstrin (optager elektroner) — er **oxidationsmidlet**"
        )
    else:
        st.info("Ingen grundstoffer ændrer oxidationstrin — ikke en redoxreaktion.")
