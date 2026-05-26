"""
Opløselighedsregler og Beer-Lambert lov — Streamlit UI.
"""

import streamlit as st
import pandas as pd


# ---------------------------------------------------------------------------
# Solubility rules data
# ---------------------------------------------------------------------------

SOLUBILITY_RULES = [
    # (regel_nr, ion, undtagelse, opløselig)
    (1,  "NO₃⁻ (nitrat)",                  "Ingen — alle nitrater er opløselige",              True),
    (2,  "CH₃COO⁻ (acetat)",               "Ingen — alle acetater er opløselige",              True),
    (3,  "Cl⁻, Br⁻, I⁻ (halogenider)",     "AgX, PbX₂, Hg₂X₂ er uopløselige",               True),
    (4,  "SO₄²⁻ (sulfat)",                  "BaSO₄, PbSO₄, CaSO₄ er uopløselige (sparsomt)", True),
    (5,  "OH⁻ (hydroxid)",                  "Gruppe 1 + Ca²⁺, Ba²⁺, Sr²⁺ er opløselige",     False),
    (6,  "S²⁻ (sulfid)",                    "Gruppe 1 + 2 er opløselige",                       False),
    (7,  "CO₃²⁻ (carbonat)",               "Gruppe 1 + NH₄⁺ er opløselige",                  False),
    (8,  "PO₄³⁻ (phosphat)",              "Gruppe 1 + NH₄⁺ er opløselige",                  False),
    (9,  "Gruppe 1 + NH₄⁺ salte",         "Ingen — altid opløselige",                         True),
]

# Common salt solubility lookup
SALT_SOLUBILITY = {
    # Nitrates — all soluble
    "NaNO3": ("NaNO₃", True, "Alle nitrater er opløselige"),
    "KNO3":  ("KNO₃",  True, "Alle nitrater er opløselige"),
    "AgNO3": ("AgNO₃", True, "Alle nitrater er opløselige"),
    "Ca(NO3)2": ("Ca(NO₃)₂", True, "Alle nitrater er opløselige"),
    "Pb(NO3)2": ("Pb(NO₃)₂", True, "Alle nitrater er opløselige"),
    # Chlorides
    "NaCl":  ("NaCl",  True,  "Chlorider er opløselige (Gruppe 1)"),
    "KCl":   ("KCl",   True,  "Chlorider er opløselige (Gruppe 1)"),
    "MgCl2": ("MgCl₂", True,  "Chlorider er opløselige"),
    "CaCl2": ("CaCl₂", True,  "Chlorider er opløselige"),
    "BaCl2": ("BaCl₂", True,  "Chlorider er opløselige"),
    "FeCl3": ("FeCl₃", True,  "Chlorider er opløselige"),
    "CuCl2": ("CuCl₂", True,  "Chlorider er opløselige"),
    "AgCl":  ("AgCl",  False, "AgCl er uopløseligt (undtagelse for halogenider)"),
    "PbCl2": ("PbCl₂", False, "PbCl₂ er uopløseligt"),
    "Hg2Cl2":("Hg₂Cl₂", False,"Hg₂Cl₂ er uopløseligt"),
    # Sulfates
    "Na2SO4": ("Na₂SO₄", True,  "Sulfater er opløselige (Gruppe 1)"),
    "K2SO4":  ("K₂SO₄",  True,  "Sulfater er opløselige (Gruppe 1)"),
    "MgSO4":  ("MgSO₄",  True,  "Sulfater er opløselige"),
    "CuSO4":  ("CuSO₄",  True,  "Sulfater er opløselige"),
    "FeSO4":  ("FeSO₄",  True,  "Sulfater er opløselige"),
    "BaSO4":  ("BaSO₄",  False, "BaSO₄ er uopløseligt"),
    "PbSO4":  ("PbSO₄",  False, "PbSO₄ er uopløseligt"),
    "CaSO4":  ("CaSO₄",  False, "CaSO₄ er sparsomt opløseligt"),
    "Ag2SO4": ("Ag₂SO₄", False, "Ag₂SO₄ er sparsomt opløseligt"),
    # Hydroxides
    "NaOH":  ("NaOH",  True,  "Gruppe 1 hydroxider er opløselige"),
    "KOH":   ("KOH",   True,  "Gruppe 1 hydroxider er opløselige"),
    "LiOH":  ("LiOH",  True,  "Gruppe 1 hydroxider er opløselige"),
    "Ba(OH)2":("Ba(OH)₂", True, "Ba(OH)₂ er opløseligt"),
    "Ca(OH)2":("Ca(OH)₂", False,"Ca(OH)₂ er sparsomt opløseligt (kalk)"),
    "Mg(OH)2":("Mg(OH)₂", False,"Mg(OH)₂ er uopløseligt"),
    "Fe(OH)3":("Fe(OH)₃", False,"Overgangsmetalhydroxider er uopløselige"),
    "Cu(OH)2":("Cu(OH)₂", False,"Overgangsmetalhydroxider er uopløselige"),
    "Al(OH)3":("Al(OH)₃", False,"Al(OH)₃ er uopløseligt"),
    "Zn(OH)2":("Zn(OH)₂", False,"Zn(OH)₂ er uopløseligt"),
    # Carbonates
    "Na2CO3": ("Na₂CO₃", True,  "Gruppe 1 carbonater er opløselige"),
    "K2CO3":  ("K₂CO₃",  True,  "Gruppe 1 carbonater er opløselige"),
    "(NH4)2CO3":("(NH₄)₂CO₃",True,"NH₄⁺ salte er opløselige"),
    "CaCO3":  ("CaCO₃",  False, "CaCO₃ er uopløseligt (kalksten)"),
    "BaCO3":  ("BaCO₃",  False, "BaCO₃ er uopløseligt"),
    "MgCO3":  ("MgCO₃",  False, "MgCO₃ er uopløseligt"),
    "FeCO3":  ("FeCO₃",  False, "Overgangsmetalcarbonater er uopløselige"),
    "PbCO3":  ("PbCO₃",  False, "PbCO₃ er uopløseligt"),
    # Sulfides
    "Na2S":   ("Na₂S",   True,  "Gruppe 1 sulfider er opløselige"),
    "K2S":    ("K₂S",    True,  "Gruppe 1 sulfider er opløselige"),
    "(NH4)2S":("(NH₄)₂S",True,  "NH₄⁺ sulfid er opløseligt"),
    "FeS":    ("FeS",    False, "Overgangsmetalsulfider er uopløselige"),
    "CuS":    ("CuS",    False, "CuS er uopløseligt"),
    "ZnS":    ("ZnS",    False, "ZnS er uopløseligt"),
    "PbS":    ("PbS",    False, "PbS er uopløseligt"),
    "Ag2S":   ("Ag₂S",   False, "Ag₂S er uopløseligt"),
    # Phosphates
    "Na3PO4": ("Na₃PO₄", True,  "Gruppe 1 phosphater er opløselige"),
    "K3PO4":  ("K₃PO₄",  True,  "Gruppe 1 phosphater er opløselige"),
    "Ca3(PO4)2":("Ca₃(PO₄)₂",False,"Calciumphosphat er uopløseligt"),
    "Ag3PO4": ("Ag₃PO₄", False, "Ag₃PO₄ er uopløseligt"),
}

VANT_HOFF_TABLE = [
    ("Glucose (C₆H₁₂O₆)", 1, "Molekylær forbindelse"),
    ("Saccharose (sukker)", 1, "Molekylær forbindelse"),
    ("Ethanol (C₂H₅OH)", 1, "Molekylær forbindelse"),
    ("Urea (CO(NH₂)₂)", 1, "Molekylær forbindelse"),
    ("NaCl (natriumklorid)", 2, "Na⁺ + Cl⁻"),
    ("KCl (kaliumklorid)", 2, "K⁺ + Cl⁻"),
    ("KBr", 2, "K⁺ + Br⁻"),
    ("NaOH", 2, "Na⁺ + OH⁻"),
    ("HCl (stærk syre)", 2, "H⁺ + Cl⁻"),
    ("MgCl₂", 3, "Mg²⁺ + 2 Cl⁻"),
    ("CaCl₂", 3, "Ca²⁺ + 2 Cl⁻"),
    ("Na₂SO₄", 3, "2 Na⁺ + SO₄²⁻"),
    ("K₂SO₄", 3, "2 K⁺ + SO₄²⁻"),
    ("AlCl₃", 4, "Al³⁺ + 3 Cl⁻"),
    ("FeCl₃", 4, "Fe³⁺ + 3 Cl⁻"),
    ("Na₃PO₄", 4, "3 Na⁺ + PO₄³⁻"),
    ("Al₂(SO₄)₃", 5, "2 Al³⁺ + 3 SO₄²⁻"),
]


def render_oploselighedsregler_page():
    st.title("💧 Opløselighedsregler & Van't Hoff faktor")
    st.markdown("---")

    subtabs = st.tabs([
        "📏 Opløselighedsregler",
        "🔍 Opslag på salt",
        "⚗️ Van't Hoff faktor (i)",
        "🌈 Beer-Lamberts lov",
    ])

    # ── Regler ────────────────────────────────────────────────────────────────
    with subtabs[0]:
        st.markdown("## 📏 Opløselighedsregler")
        st.markdown("Disse regler gælder for salte i vand ved stuetemperatur.")

        rows = []
        for nr, ion, undtagelse, oploselig in SOLUBILITY_RULES:
            rows.append({
                "#": nr,
                "Ion": ion,
                "Generelt": "✅ Opløseligt" if oploselig else "❌ Uopløseligt",
                "Undtagelser / bemærkninger": undtagelse,
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("### Mnemoteknik")
        st.info(
            "**Altid opløselige:** Gruppe 1 (Li, Na, K, Rb, Cs), NH₄⁺, NO₃⁻, acetat\n\n"
            "**Næsten altid opløselige:** Cl⁻, Br⁻, I⁻ (undtagen Ag, Pb, Hg₂), SO₄²⁻ (undtagen Ba, Pb, Ca)\n\n"
            "**Næsten altid uopløselige:** OH⁻, S²⁻, CO₃²⁻, PO₄³⁻ (undtagen Gruppe 1 og NH₄⁺)"
        )

        st.markdown("### Fuldstændig ionligning vs. nettoligning")
        st.markdown(r"""
Når to opløselige salte blandes, skriv:
1. **Molekylær ligning:** AgNO₃(aq) + NaCl(aq) → AgCl(s) + NaNO₃(aq)
2. **Fuldstændig ionligning:** Ag⁺ + NO₃⁻ + Na⁺ + Cl⁻ → AgCl(s) + Na⁺ + NO₃⁻
3. **Nettoligning (fjern tilskuere):** Ag⁺(aq) + Cl⁻(aq) → AgCl(s)
        """)

    # ── Salt lookup ───────────────────────────────────────────────────────────
    with subtabs[1]:
        st.markdown("## 🔍 Opslag på salt")
        query = st.text_input(
            "Formel (fx NaCl, BaSO4, Ca(OH)2):",
            placeholder="Skriv formel...",
            key="sol_query",
        )

        # Normalize: remove spaces, lowercase for matching
        def normalize(s):
            return s.replace(" ", "").replace("(", "").replace(")", "").lower()

        if query.strip():
            match = None
            for key, val in SALT_SOLUBILITY.items():
                if normalize(key) == normalize(query):
                    match = val
                    break
            # Fuzzy: try partial match
            if match is None:
                for key, val in SALT_SOLUBILITY.items():
                    if normalize(query) in normalize(key) or normalize(key) in normalize(query):
                        match = val
                        break

            if match:
                name, soluble, reason = match
                if soluble:
                    st.success(f"### ✅ {name} — **OPLØSELIGT**")
                else:
                    st.error(f"### ❌ {name} — **UOPLØSELIGT**")
                st.info(reason)
            else:
                st.warning(
                    f"'{query}' er ikke i databasen. "
                    "Anvend de generelle opløselighedsregler i fanen til venstre."
                )

        st.markdown("---")
        st.markdown("### Alle stoffer i databasen")
        rows = [
            {"Formel": v[0], "Opløselig": "✅" if v[1] else "❌", "Forklaring": v[2]}
            for v in SALT_SOLUBILITY.values()
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # ── Van't Hoff ────────────────────────────────────────────────────────────
    with subtabs[2]:
        st.markdown("## ⚗️ Van't Hoff faktor (i)")
        st.markdown(
            "Van't Hoff faktoren **i** angiver det effektive antal partikler pr. formelenhed. "
            "Bruges i kolligative egenskaber: $\\Delta T_b = i K_b m$, $\\Delta T_f = i K_f m$, $\\pi = iMRT$"
        )

        df_vh = pd.DataFrame(
            VANT_HOFF_TABLE,
            columns=["Stof", "i (ideal)", "Ioner"],
        )
        st.dataframe(df_vh, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("### Beregn i fra formel")
        st.markdown(
            "I er antallet af ioner forbindelsen dissocierer til i vandig opløsning.\n\n"
            "**Fremgangsmåde:** Find kation + anion, tæl antal ioner.\n\n"
            "Eksempel: Al₂(SO₄)₃ → 2 Al³⁺ + 3 SO₄²⁻ → **i = 5**"
        )

        col1, col2 = st.columns(2)
        with col1:
            n_cations = st.number_input("Antal kationer pr. formelenhed:", min_value=0, value=1, step=1, key="vh_cat")
            n_anions = st.number_input("Antal anioner pr. formelenhed:", min_value=0, value=1, step=1, key="vh_an")
        with col2:
            i_result = int(n_cations) + int(n_anions)
            st.metric("i =", i_result)
            if i_result == 1:
                st.info("Molekylær forbindelse — ingen dissociation.")
            elif i_result == 2:
                st.info("1:1-salt (fx NaCl, KBr)")
            elif i_result == 3:
                st.info("1:2 eller 2:1 salt (fx MgCl₂, Na₂SO₄)")

    # ── Beer-Lambert ──────────────────────────────────────────────────────────
    with subtabs[3]:
        st.markdown("## 🌈 Beer-Lamberts lov")
        st.markdown(
            r"$$A = \varepsilon \cdot l \cdot c$$"
        )
        st.markdown(
            "**A** = absorbans (ingen enhed)  ·  **ε** = molar absorptionskoefficient (M⁻¹cm⁻¹)  "
            "·  **l** = lysvejlængde (cm)  ·  **c** = koncentration (M)"
        )
        st.markdown(
            r"$$A = \log_{10}\frac{I_0}{I} = -\log_{10}T$$  ·  $T = I/I_0$ = transmittans"
        )
        st.markdown("---")

        unknown = st.radio(
            "Find:",
            ["A (absorbans)", "c (koncentration)", "ε (koefficient)", "l (vejlængde)"],
            key="bl_unknown",
            horizontal=True,
        )

        col1, col2 = st.columns(2)
        with col1:
            if "A" not in unknown:
                A = st.number_input("A (absorbans):", value=0.500, min_value=0.0, key="bl_A")
            else:
                A = None
            if "ε" not in unknown:
                eps = st.number_input("ε (M⁻¹cm⁻¹):", value=1000.0, min_value=0.001, key="bl_eps")
            else:
                eps = None
        with col2:
            if "l" not in unknown:
                l = st.number_input("l (cm):", value=1.0, min_value=0.001, key="bl_l")
            else:
                l = None
            if "c" not in unknown:
                c = st.number_input("c (M):", value=0.001, min_value=0.0, format="%.6f", key="bl_c")
            else:
                c = None

        if st.button("Beregn", type="primary", key="bl_run"):
            try:
                if A is None:
                    result = eps * l * c
                    st.success(f"### A = {result:.4f}")
                    t = 10 ** (-result)
                    st.info(f"Transmittans T = {t*100:.2f}%")
                elif c is None:
                    result = A / (eps * l)
                    st.success(f"### c = {result:.6g} M")
                elif eps is None:
                    result = A / (l * c)
                    st.success(f"### ε = {result:.4g} M⁻¹cm⁻¹")
                else:
                    result = A / (eps * c)
                    st.success(f"### l = {result:.4g} cm")
            except ZeroDivisionError:
                st.error("Division med nul — tjek at ingen værdier er 0.")

        st.markdown("---")
        with st.expander("📚 Eksamenseksempel", expanded=False):
            st.markdown("""
En opløsning af KMnO₄ har ε = 2350 M⁻¹cm⁻¹ ved 525 nm og måles i en 1.00 cm kuvette.
Absorbansen aflæses til A = 0.470.

**Find koncentrationen:**

c = A / (ε × l) = 0.470 / (2350 × 1.00) = **2.0 × 10⁻⁴ M**

Transmittans: T = 10⁻⁰·⁴⁷⁰ = 0.339 = **33.9%**
            """)
