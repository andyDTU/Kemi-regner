"""Faststofkemi – Krystalstrukturer og enhedsceller."""

import math
import streamlit as st

AVOGADRO = 6.02214076e23

# Crystal type definitions
CRYSTAL_TYPES = {
    "Simpelt kubisk (SC)": {
        "z": 1,
        "coord_num": 6,
        "packing": 0.5236,
        "r_formula": "r = a / 2",
        "r_from_a": lambda a: a / 2,
        "a_from_r": lambda r: 2 * r,
        "desc": "1 atom pr. enhedscelle (8 × 1/8 hjørneatomer)",
    },
    "Rumcentreret kubisk (BCC)": {
        "z": 2,
        "coord_num": 8,
        "packing": 0.6802,
        "r_formula": "r = a√3 / 4",
        "r_from_a": lambda a: a * math.sqrt(3) / 4,
        "a_from_r": lambda r: 4 * r / math.sqrt(3),
        "desc": "2 atomer pr. enhedscelle (8 × 1/8 hjørner + 1 center)",
    },
    "Fladecentreret kubisk (FCC)": {
        "z": 4,
        "coord_num": 12,
        "packing": 0.7405,
        "r_formula": "r = a√2 / 4",
        "r_from_a": lambda a: a * math.sqrt(2) / 4,
        "a_from_r": lambda r: 4 * r / math.sqrt(2),
        "desc": "4 atomer pr. enhedscelle (8 × 1/8 hjørner + 6 × 1/2 flader)",
    },
}


def _fmt(val: float, sig: int = 4) -> str:
    """Format value in scientific notation with sig significant figures."""
    if val == 0:
        return "0"
    exp = math.floor(math.log10(abs(val)))
    coeff = val / 10**exp
    return f"{coeff:.{sig-1}f} × 10^{exp}"


def _render_unit_cell_volume_tab():
    st.subheader("📦 Volumen af enhedscelle")
    st.markdown("Givet densitet og molarmasse — find volumen af enhedscellen.")
    st.latex(r"V = \frac{Z \cdot M}{N_A \cdot \rho}")

    col1, col2 = st.columns(2)
    with col1:
        crystal = st.selectbox(
            "Krystalstruktur",
            list(CRYSTAL_TYPES.keys()),
            index=1,
            key="fss_vol_crystal",
        )
        rho_unit = st.selectbox(
            "Densitetsenhed",
            ["g/cm³", "kg/m³", "g/mL"],
            index=0,
            key="fss_vol_rho_unit",
        )
        # Default values in selected unit
        default_rho = {"g/cm³": 7.874, "kg/m³": 7874.0, "g/mL": 7.874}[rho_unit]
        rho_input = st.number_input(
            f"Densitet ρ ({rho_unit})",
            value=default_rho,
            min_value=1e-6,
            format="%.4g",
            key="fss_vol_rho",
        )
    with col2:
        M_gmol = st.number_input(
            "Molarmasse M (g/mol)",
            value=55.85,
            min_value=0.001,
            step=0.01,
            key="fss_vol_M",
        )
        st.info(CRYSTAL_TYPES[crystal]["desc"])

    if st.button("Beregn volumen", type="primary", key="fss_vol_calc"):
        ct = CRYSTAL_TYPES[crystal]
        Z = ct["z"]
        # Konvertér til kg/m³ for beregning
        to_kg_m3 = {"g/cm³": 1000.0, "kg/m³": 1.0, "g/mL": 1000.0}[rho_unit]
        rho_kg = rho_input * to_kg_m3
        M_kg = M_gmol / 1000  # kg/mol
        V = (Z * M_kg) / (AVOGADRO * rho_kg)
        a = V ** (1 / 3)
        r = ct["r_from_a"](a)

        st.markdown("---")
        st.markdown("### Trin-for-trin løsning")

        st.markdown(f"**Givet:**")
        st.markdown(f"- Krystalstruktur: **{crystal}** → Z = {Z}")
        st.markdown(f"- Densitet: ρ = {rho_input} {rho_unit} = {rho_kg:.2f} kg/m³")
        st.markdown(f"- Molarmasse: M = {M_gmol} g/mol = {M_kg} kg/mol")

        st.markdown("**Trin 1 – Indsæt i formlen:**")
        st.latex(
            r"V = \frac{Z \cdot M}{N_A \cdot \rho} = "
            rf"\frac{{{Z} \times {M_kg:.5f}\,\text{{kg/mol}}}}"
            rf"{{{AVOGADRO:.4e} \times {rho_kg:.2f}\,\text{{kg/m}}^3}}"
        )

        numerator = Z * M_kg
        denominator = AVOGADRO * rho_kg
        st.latex(
            rf"V = \frac{{{numerator:.5e}}}{{{denominator:.4e}}} = {V:.4e}\,\text{{m}}^3"
        )

        st.markdown("**Trin 2 – Gitterparameter (kantlængde):**")
        st.latex(rf"a = V^{{1/3}} = ({V:.4e})^{{1/3}} = {a:.4e}\,\text{{m}} = {a*1e12:.4f}\,\text{{pm}}")

        st.markdown(f"**Trin 3 – Atomradius ({ct['r_formula']}):**")
        st.latex(rf"r = {r:.4e}\,\text{{m}} = {r*1e12:.1f}\,\text{{pm}}")

        st.markdown("---")
        col_r1, col_r2, col_r3 = st.columns(3)
        col_r1.metric("Enhedscellevolumen V", f"{V:.3e} m³")
        col_r2.metric("Kantlængde a", f"{a*1e12:.2f} pm")
        col_r3.metric("Pakningsgrad", f"{ct['packing']*100:.1f}%")


def _render_density_tab():
    st.subheader("⚖️ Densitet fra enhedscelle")
    st.markdown("Givet kantlængde og molarmasse — find densitet.")
    st.latex(r"\rho = \frac{Z \cdot M}{N_A \cdot V} = \frac{Z \cdot M}{N_A \cdot a^3}")

    col1, col2 = st.columns(2)
    with col1:
        crystal = st.selectbox(
            "Krystalstruktur",
            list(CRYSTAL_TYPES.keys()),
            index=1,
            key="fss_rho_crystal",
        )
        a_pm = st.number_input(
            "Kantlængde a (pm)",
            value=286.7,
            min_value=1.0,
            step=0.1,
            key="fss_rho_a",
        )
    with col2:
        M_gmol = st.number_input(
            "Molarmasse M (g/mol)",
            value=55.85,
            min_value=0.001,
            step=0.01,
            key="fss_rho_M",
        )
        st.info(CRYSTAL_TYPES[crystal]["desc"])

    if st.button("Beregn densitet", type="primary", key="fss_rho_calc"):
        ct = CRYSTAL_TYPES[crystal]
        Z = ct["z"]
        M_kg = M_gmol / 1000
        a_m = a_pm * 1e-12
        V = a_m ** 3
        rho = (Z * M_kg) / (AVOGADRO * V)

        st.markdown("---")
        st.markdown("### Trin-for-trin løsning")
        st.markdown(f"**Givet:** {crystal} (Z = {Z}), a = {a_pm} pm = {a_m:.4e} m, M = {M_gmol} g/mol")

        st.markdown("**Trin 1 – Volumen af enhedscelle:**")
        st.latex(rf"V = a^3 = ({a_m:.4e})^3 = {V:.4e}\,\text{{m}}^3")

        st.markdown("**Trin 2 – Densitet:**")
        st.latex(
            rf"\rho = \frac{{{Z} \times {M_kg:.5f}}}{{{AVOGADRO:.4e} \times {V:.4e}}} = {rho:.2f}\,\text{{kg/m}}^3"
        )

        rho_gcm3 = rho / 1000.0
        r = ct["r_from_a"](a_m)
        st.markdown("---")
        col_r1, col_r2, col_r3, col_r4 = st.columns(4)
        col_r1.metric("Densitet ρ", f"{rho:.2f} kg/m³")
        col_r2.metric("Densitet ρ", f"{rho_gcm3:.4f} g/cm³")
        col_r3.metric("Atomradius r", f"{r*1e12:.1f} pm")
        col_r4.metric("Koordinationstal", str(ct["coord_num"]))


def _render_lattice_param_tab():
    st.subheader("📐 Gitterparameter fra atomradius")
    st.markdown("Givet atomradius — find kantlængde og enhedscellevolumen.")

    col1, col2 = st.columns(2)
    with col1:
        crystal = st.selectbox(
            "Krystalstruktur",
            list(CRYSTAL_TYPES.keys()),
            index=1,
            key="fss_lat_crystal",
        )
    with col2:
        r_pm = st.number_input(
            "Atomradius r (pm)",
            value=126.0,
            min_value=1.0,
            step=0.5,
            key="fss_lat_r",
        )

    if st.button("Beregn gitterparameter", type="primary", key="fss_lat_calc"):
        ct = CRYSTAL_TYPES[crystal]
        r_m = r_pm * 1e-12
        a_m = ct["a_from_r"](r_m)
        V = a_m ** 3

        st.markdown("---")
        st.markdown(f"**Formel:** {ct['r_formula']} → inverter til a")
        formula_inv = ct['r_formula'].replace("r = ", "a = ").replace("a", "r·const")

        st.markdown("**Kantlængde:**")
        if crystal == "Simpelt kubisk (SC)":
            st.latex(rf"a = 2r = 2 \times {r_pm}\,\text{{pm}} = {a_m*1e12:.2f}\,\text{{pm}}")
        elif crystal == "Rumcentreret kubisk (BCC)":
            st.latex(rf"a = \frac{{4r}}{{\sqrt{{3}}}} = \frac{{4 \times {r_pm}}}{{\sqrt{{3}}}} = {a_m*1e12:.2f}\,\text{{pm}}")
        else:
            st.latex(rf"a = \frac{{4r}}{{\sqrt{{2}}}} = \frac{{4 \times {r_pm}}}{{\sqrt{{2}}}} = {a_m*1e12:.2f}\,\text{{pm}}")

        st.markdown("**Enhedscellevolumen:**")
        st.latex(rf"V = a^3 = ({a_m:.4e})^3 = {V:.4e}\,\text{{m}}^3")

        st.markdown("---")
        col_r1, col_r2, col_r3 = st.columns(3)
        col_r1.metric("Kantlængde a", f"{a_m*1e12:.2f} pm")
        col_r2.metric("Volumen V", f"{V:.3e} m³")
        col_r3.metric("Atomer pr. celle Z", str(ct["z"]))


def _render_overview_tab():
    st.subheader("📊 Oversigt over kubiske krystaltyper")

    st.markdown("""
| Egenskab | Simpelt kubisk (SC) | BCC | FCC |
|---|---|---|---|
| **Atomer pr. celle Z** | 1 | 2 | 4 |
| **Koordinationstal** | 6 | 8 | 12 |
| **Pakningsgrad** | 52.4% | 68.0% | 74.0% |
| **Atomradius** | r = a/2 | r = a√3/4 | r = a√2/4 |
| **Eksempler** | Po | Fe, W, Cr, Mo | Cu, Al, Au, Ag, Ni |
""")

    st.markdown("---")
    st.markdown("### Vigtige formler")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Densitet ↔ Volumen:**")
        st.latex(r"\rho = \frac{Z \cdot M}{N_A \cdot V} \qquad V = \frac{Z \cdot M}{N_A \cdot \rho}")
        st.markdown("**Volumen fra kantlængde:**")
        st.latex(r"V = a^3 \quad \Rightarrow \quad a = V^{1/3}")
    with col2:
        st.markdown("**Koordinationstal = antal nærmeste naboer**")
        st.markdown("**Pakningsgrad:**")
        st.latex(r"\text{Pakningsgrad} = \frac{Z \cdot \frac{4}{3}\pi r^3}{a^3}")
        st.markdown("**Nernst – antal atomer i prøve:**")
        st.latex(r"N = \frac{\rho \cdot V_{\text{prøve}} \cdot N_A}{M}")


def render_faststofkemi_page():
    st.title("🔩 Faststofkemi – Krystalstrukturer")
    st.markdown("Beregn enhedscellevolumen, densitet og gitterparametre for kubiske krystaller.")

    tab_vol, tab_rho, tab_lat, tab_overview = st.tabs([
        "📦 Find volumen",
        "⚖️ Find densitet",
        "📐 Find gitterparameter",
        "📊 Oversigt",
    ])

    with tab_vol:
        _render_unit_cell_volume_tab()
    with tab_rho:
        _render_density_tab()
    with tab_lat:
        _render_lattice_param_tab()
    with tab_overview:
        _render_overview_tab()
