"""
Radioactive decay calculator — Streamlit UI.
"""

import streamlit as st
import pandas as pd
import math
from core.nuclear_decay import (
    calculate_decay, NuclearDecayError, DECAY_TYPES, TIME_UNITS,
)


def render_nuclear_decay_page():
    """Render the nuclear decay calculator page."""
    st.title("☢️ Nuklear kemi – Radioaktivt henfald")
    st.markdown(
        "Beregn resterende mængde, aktivitet og halveringstid for radioaktive isotoper."
    )
    st.markdown("---")

    subpage_labels = [
        "🔢 Henfaldskalkulator",
        "⚛️ Henfaldstyperne",
        "📚 Kendte isotoper",
        "💡 Foton energi",
    ]

    subpage_to_query = {
        "🔢 Henfaldskalkulator": "decay-calc",
        "⚛️ Henfaldstyperne":    "decay-types",
        "📚 Kendte isotoper":    "isotopes",
        "💡 Foton energi":       "photon",
    }
    query_to_subpage = {v: k for k, v in subpage_to_query.items()}

    query_sub_raw = st.query_params.get("nuc_tab")
    if isinstance(query_sub_raw, list):
        query_sub_raw = query_sub_raw[0] if query_sub_raw else None
    query_sub = str(query_sub_raw).strip() if query_sub_raw else ""
    if "nuc_subpage" not in st.session_state and query_sub in query_to_subpage:
        st.session_state["nuc_subpage"] = query_to_subpage[query_sub]

    st.markdown(
        """
<style>
.st-key-nuc_subpage label[data-testid="stWidgetLabel"] {
    position: absolute; width: 1px; height: 1px; padding: 0;
    margin: -1px; overflow: hidden; clip: rect(0,0,0,0); border: 0;
}
.st-key-nuc_subpage [data-testid="stRadio"] div[role="radiogroup"] {
    display: flex; flex-wrap: wrap; gap: 0.35rem;
    border-bottom: 1px solid #e2e8f0; margin-bottom: 0.8rem;
}
.st-key-nuc_subpage [data-testid="stRadio"] label[data-baseweb="radio"] {
    margin: 0; padding: 0.35rem 0.05rem 0.55rem 0.05rem;
    border-bottom: 2px solid transparent; background: transparent; min-height: 0;
}
.st-key-nuc_subpage [data-testid="stRadio"] label[data-baseweb="radio"] > div:first-child {
    display: none !important;
}
.st-key-nuc_subpage [data-testid="stRadio"] label[data-baseweb="radio"] p {
    margin: 0; font-size: 1.02rem; color: #0f172a;
}
.st-key-nuc_subpage [data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) {
    border-bottom-color: #ff4b4b;
}
.st-key-nuc_subpage [data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) p {
    color: #ff4b4b; font-weight: 600;
}
</style>
        """,
        unsafe_allow_html=True,
    )

    active = st.radio(
        "NucSubpage",
        subpage_labels,
        key="nuc_subpage",
        horizontal=True,
        label_visibility="collapsed",
    )
    sel_q = subpage_to_query[active]
    if st.query_params.get("nuc_tab") != sel_q:
        st.query_params["nuc_tab"] = sel_q

    if active == "🔢 Henfaldskalkulator":
        _render_decay_calc()
    elif active == "⚛️ Henfaldstyperne":
        _render_decay_types()
    elif active == "📚 Kendte isotoper":
        _render_isotopes()
    elif active == "💡 Foton energi":
        _render_photon_energy()


def _render_decay_calc():
    st.markdown("## Henfaldskalkulator")
    st.markdown(
        r"$$N(t) = N_0 \cdot \left(\frac{1}{2}\right)^{t/t_{1/2}}$$"
    )
    st.markdown("Angiv **3 af 4** størrelser. Den fjerde beregnes automatisk.")

    time_unit_opts = list(TIME_UNITS.keys())
    half_unit_opts = list(TIME_UNITS.keys())

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Størrelse og tidsenheder")
        N0_enabled = st.checkbox("Angiv N₀ (startmængde/aktivitet)", value=True, key="nuc_N0_en")
        N0 = st.number_input("N₀:", min_value=0.0, value=1000.0, key="nuc_N0") if N0_enabled else None

        Nt_enabled = st.checkbox("Angiv N(t) (rest efter tid t)", value=True, key="nuc_Nt_en")
        Nt = st.number_input("N(t):", min_value=0.0, value=125.0, key="nuc_Nt") if Nt_enabled else None

        t_enabled = st.checkbox("Angiv t (forløbet tid)", value=True, key="nuc_t_en")
        col_t1, col_t2 = st.columns([2, 1])
        with col_t1:
            t = st.number_input("t:", min_value=0.0, value=30.0, key="nuc_t") if t_enabled else None
        with col_t2:
            t_unit = st.selectbox("Enhed:", time_unit_opts, index=3, key="nuc_t_unit") if t_enabled else "dage (d)"

        thalf_enabled = st.checkbox("Angiv t½ (halveringstid)", value=False, key="nuc_th_en")
        col_h1, col_h2 = st.columns([2, 1])
        with col_h1:
            t_half = st.number_input("t½:", min_value=0.001, value=10.0, key="nuc_thalf") if thalf_enabled else None
        with col_h2:
            half_unit = st.selectbox("Enhed:", half_unit_opts, index=3, key="nuc_h_unit") if thalf_enabled else "dage (d)"

    with col2:
        st.markdown("#### Formelark")
        st.markdown(r"""
| Ubekendt | Formel |
|----------|--------|
| N(t) | $N_0 \cdot (½)^{t/t_{½}}$ |
| N₀ | $N(t) / (½)^{t/t_{½}}$ |
| t½ | $t \cdot \ln 2 / \ln(N_0/N_t)$ |
| t | $t_{½} \cdot \log_2(N_0/N_t)$ |
| λ | $\ln 2 / t_{½}$ |

**Procent tilbage:** $100\% \times (½)^n$, hvor $n$ = antal halveringstider.

**Eksempel:** 3 halveringstider → $(½)^3 = 12.5\%$ tilbage
        """)

    run = st.button("Beregn", type="primary", key="nuc_run")

    if run:
        provided = sum(x is not None for x in [N0, Nt, t, t_half])
        if provided < 3:
            st.error("Angiv mindst 3 af de 4 størrelser (sæt kryds for dem du kender).")
            st.stop()
        if provided == 4:
            st.warning("Alle 4 er angivet — beregner alligevel (ignorerer N(t) hvis inkonsistent).")
            Nt = None

        t_u   = t_unit   if t_enabled   else "dage (d)"
        h_u   = half_unit if thalf_enabled else "dage (d)"
        if not t_enabled:
            t_u = h_u

        try:
            result = calculate_decay(N0, Nt, t, t_half, t_unit=t_u, half_unit=h_u)
        except NuclearDecayError as e:
            st.error(str(e))
            st.stop()

        st.markdown("---")
        st.markdown("## Resultat")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("N₀", f"{result.N0:.6g}")
        c2.metric("N(t)", f"{result.Nt:.6g}")
        c3.metric("t½", f"{result.t_half:.4g} {h_u}")
        c4.metric("t", f"{result.t:.4g} {t_u}")

        c5, c6, c7 = st.columns(3)
        c5.metric("Antal halveringstider", f"{result.n_half_lives:.3f}")
        c6.metric("Tilbage", f"{result.fraction_remaining*100:.3f}%")
        c7.metric("Henfaldet", f"{result.fraction_decayed*100:.3f}%")

        # Visual fraction bar
        pct = result.fraction_remaining
        bar_filled = int(pct * 20)
        bar = "█" * bar_filled + "░" * (20 - bar_filled)
        st.markdown(f"**Tilbageværende:** `[{bar}]` {pct*100:.1f}%")

        with st.expander("📋 Vis udledning", expanded=False):
            for s in result.steps:
                st.markdown(s)


def _render_decay_types():
    st.markdown("## ⚛️ Henfaldstyperne")

    rows = []
    for key, d in DECAY_TYPES.items():
        rows.append({
            "Type": d["symbol"],
            "Navn": key.replace("_", "-"),
            "ΔZ": f"{d['Z_change']:+d}",
            "ΔA": f"{d['A_change']:+d}",
            "Penetration": d["penetration"],
            "Beskrivelse": d["description"],
            "Eksempel": d["example"],
        })
    df = pd.DataFrame(rows)
    st.dataframe(df[["Type", "Navn", "ΔZ", "ΔA", "Penetration", "Eksempel"]],
                 use_container_width=True, hide_index=True)

    st.markdown("---")
    for key, d in DECAY_TYPES.items():
        with st.expander(f"{d['symbol']} — {d['description'].split(':')[0]}", expanded=False):
            st.markdown(d["description"])
            st.markdown(f"**ΔZ = {d['Z_change']:+d}, ΔA = {d['A_change']:+d}**")
            st.markdown(f"**Penetration:** {d['penetration']}")
            st.markdown(f"**Eksempel:** {d['example']}")

    st.markdown("---")
    st.markdown("### Beregn datterisotop efter alfa- eller betahenfald")
    col1, col2, col3 = st.columns(3)
    with col1:
        A_in = st.number_input("Masseantal A:", min_value=1, value=238, step=1, key="dt_A")
    with col2:
        Z_in = st.number_input("Protontal Z:", min_value=1, value=92, step=1, key="dt_Z")
    with col3:
        dtype = st.selectbox("Henfald:", ["alpha", "beta_minus", "beta_plus", "electron_capture"], key="dt_type")

    if st.button("Find datter", key="dt_run"):
        d = DECAY_TYPES[dtype]
        A_out = int(A_in) + d["A_change"]
        Z_out = int(Z_in) + d["Z_change"]

        # Try to name the daughter element
        ELEMENT_SYMBOLS = {
            1:"H",2:"He",3:"Li",4:"Be",5:"B",6:"C",7:"N",8:"O",9:"F",10:"Ne",
            11:"Na",12:"Mg",13:"Al",14:"Si",15:"P",16:"S",17:"Cl",18:"Ar",
            19:"K",20:"Ca",21:"Sc",22:"Ti",23:"V",24:"Cr",25:"Mn",26:"Fe",
            27:"Co",28:"Ni",29:"Cu",30:"Zn",31:"Ga",32:"Ge",33:"As",34:"Se",
            35:"Br",36:"Kr",37:"Rb",38:"Sr",39:"Y",40:"Zr",41:"Nb",42:"Mo",
            43:"Tc",44:"Ru",45:"Rh",46:"Pd",47:"Ag",48:"Cd",49:"In",50:"Sn",
            51:"Sb",52:"Te",53:"I",54:"Xe",55:"Cs",56:"Ba",57:"La",58:"Ce",
            59:"Pr",60:"Nd",61:"Pm",62:"Sm",63:"Eu",64:"Gd",65:"Tb",66:"Dy",
            67:"Ho",68:"Er",69:"Tm",70:"Yb",71:"Lu",72:"Hf",73:"Ta",74:"W",
            75:"Re",76:"Os",77:"Ir",78:"Pt",79:"Au",80:"Hg",81:"Tl",82:"Pb",
            83:"Bi",84:"Po",85:"At",86:"Rn",87:"Fr",88:"Ra",89:"Ac",90:"Th",
            91:"Pa",92:"U",93:"Np",94:"Pu",95:"Am",96:"Cm",97:"Bk",98:"Cf",
        }
        parent_sym = ELEMENT_SYMBOLS.get(int(Z_in), f"Z={Z_in}")
        daughter_sym = ELEMENT_SYMBOLS.get(Z_out, f"Z={Z_out}")
        particle = {"alpha":"⁴₂He", "beta_minus":"β⁻", "beta_plus":"β⁺", "electron_capture":"+ e⁻"}.get(dtype, "")

        st.success(
            f"**{A_in}{parent_sym}** → **{A_out}{daughter_sym}** + {particle}  "
            f"(Z: {Z_in} → {Z_out}, A: {A_in} → {A_out})"
        )


def _render_isotopes():
    st.markdown("## 📚 Kendte radioaktive isotoper")

    isotopes = [
        ("¹⁴C (karbon-14)",     5730,     "år (y)",   "beta_minus", "Kulstof-datering"),
        ("²²⁶Ra (radium-226)",  1600,     "år (y)",   "alpha",      "Marie Curies forskning"),
        ("²³⁸U (uran-238)",     4.47e9,   "år (y)",   "alpha",      "Geologisk datering"),
        ("²³⁵U (uran-235)",     7.04e8,   "år (y)",   "alpha",      "Kernebrændsel"),
        ("²³⁹Pu (plutonium)",   2.41e4,   "år (y)",   "alpha",      "Kernevåben / reaktor"),
        ("⁶⁰Co (kobolt-60)",    5.27,     "år (y)",   "beta_minus", "Strålebehandling"),
        ("¹³¹I (iod-131)",      8.02,     "dage (d)", "beta_minus", "Skjoldbruskkirtel"),
        ("⁹⁰Sr (strontium-90)",29.1,     "år (y)",   "beta_minus", "Fallout fra atomprøver"),
        ("¹³⁷Cs (cæsium-137)", 30.2,     "år (y)",   "beta_minus", "Kernekraftulykker"),
        ("²²²Rn (radon-222)",   3.82,     "dage (d)", "alpha",      "Indeklimaproblem"),
        ("³H (tritium)",        12.3,     "år (y)",   "beta_minus", "Fusionsreaktor"),
        ("³²P (phosphor-32)",   14.3,     "dage (d)", "beta_minus", "Biologisk forskning"),
        ("²¹⁰Po (polonium-210)",138.4,    "dage (d)", "alpha",      "Poloniumforgiftning"),
        ("¹⁸F (fluor-18)",      109.8,    "minutter (min)", "beta_plus", "PET-scanning"),
        ("⁹⁹ᵐTc (technetium)", 6.01,     "timer (h)","gamma",      "Medicinsk diagnostik"),
    ]

    rows = []
    for name, t_half, unit, decay_type, note in isotopes:
        rows.append({
            "Isotop": name,
            "t½": f"{t_half:g} {unit}",
            "Henfald": DECAY_TYPES[decay_type]["symbol"],
            "Anvendelse": note,
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("### Beregn hurtigt for en isotop")
    iso_names = [r[0] for r in isotopes]
    selected = st.selectbox("Vælg isotop:", iso_names, key="iso_select")
    iso_data = dict(zip(iso_names, isotopes))
    _, t_half_v, t_half_u, _, _ = iso_data[selected]

    pct = st.slider("Procent tilbageværende:", 1, 99, 50, key="iso_pct")
    if pct < 100:
        from core.nuclear_decay import to_seconds, from_seconds
        thalf_s = to_seconds(t_half_v, t_half_u)
        frac = pct / 100
        t_s = thalf_s * math.log(1 / frac) / math.log(2)
        t_val = from_seconds(t_s, t_half_u)
        st.info(
            f"For at **{100-pct}%** af {selected} henfalder: **t = {t_val:.3g} {t_half_u}**  "
            f"({t_val / t_half_v:.2f} halveringstider)"
        )


def _render_photon_energy():
    H = 6.62607015e-34   # J·s
    C = 2.99792458e8     # m/s
    EV = 1.602176634e-19 # J per eV

    st.markdown("## 💡 Foton energi")
    st.latex(r"E = \frac{hc}{\lambda}")
    st.markdown(
        f"h = 6.626×10⁻³⁴ J·s &nbsp;|&nbsp; c = 2.998×10⁸ m/s &nbsp;|&nbsp; 1 eV = 1.602×10⁻¹⁹ J",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    mode = st.radio(
        "Beregningsretning:",
        ["λ → E  (bølgelængde til energi)", "E → λ  (energi til bølgelængde)"],
        key="photon_mode",
        horizontal=True,
    )

    if mode.startswith("λ"):
        st.markdown("#### Indtast bølgelængde")
        col1, col2 = st.columns([2, 1])
        with col1:
            lam_nm = st.number_input("Bølgelængde (nm):", min_value=0.001, value=500.0,
                                     format="%.3f", key="photon_lam")
        with col2:
            st.markdown("")
            st.markdown("")
            lam_unit = st.selectbox("Enhed:", ["nm", "μm", "pm", "Å"], key="photon_lam_unit")

        unit_to_m = {"nm": 1e-9, "μm": 1e-6, "pm": 1e-12, "Å": 1e-10}
        lam_m = lam_nm * unit_to_m[lam_unit]

        if lam_m > 0:
            E_J = H * C / lam_m
            E_eV = E_J / EV
            E_kJ_mol = E_J * 6.02214076e23 / 1000

            st.markdown("---")
            st.markdown("#### Resultat")
            r1, r2, r3 = st.columns(3)
            with r1:
                st.metric("Energi (J)", f"{E_J:.4e}")
            with r2:
                st.metric("Energi (eV)", f"{E_eV:.4f}")
            with r3:
                st.metric("Energi (kJ/mol)", f"{E_kJ_mol:.2f}")

            # Show LaTeX with numbers
            lam_val = lam_nm * unit_to_m[lam_unit]
            st.latex(
                rf"E = \frac{{hc}}{{\lambda}} = "
                rf"\frac{{6.626 \times 10^{{-34}} \times 2.998 \times 10^8}}"
                rf"{{{lam_nm:.3g}\ \text{{{lam_unit}}} \times 10^{{{int(math.log10(unit_to_m[lam_unit]))}}}}} "
                rf"= {E_J:.4e}\ \text{{J}} = {E_eV:.4f}\ \text{{eV}}"
            )

            # Spectrum reference
            st.markdown("---")
            st.markdown("#### Elektromagnetisk spektrum (reference)")
            lam_nm_val = lam_nm if lam_unit == "nm" else lam_m / 1e-9
            spectrum = [
                ("Gamma (γ)", 0, 0.01, "☢️"),
                ("Røntgen", 0.01, 10, "🩻"),
                ("Ultraviolet (UV)", 10, 400, "🔆"),
                ("Synligt lys", 400, 700, "🌈"),
                ("Infrarød (IR)", 700, 1e6, "🌡️"),
                ("Mikrobølger", 1e6, 1e11, "📡"),
                ("Radiobølger", 1e11, 1e15, "📻"),
            ]
            region = "Ukendt"
            for name, lo, hi, icon in spectrum:
                if lo <= lam_nm_val < hi:
                    region = f"{icon} {name}"
                    break
            st.info(f"λ = {lam_nm:.3g} {lam_unit} svarer til: **{region}**")

            if 400 <= lam_nm_val <= 700:
                if lam_nm_val < 450:
                    color = "violet"
                elif lam_nm_val < 495:
                    color = "blå"
                elif lam_nm_val < 570:
                    color = "grøn"
                elif lam_nm_val < 590:
                    color = "gul"
                elif lam_nm_val < 620:
                    color = "orange"
                else:
                    color = "rød"
                st.success(f"Synlig farve: **{color}** (~{lam_nm_val:.0f} nm)")

    else:
        st.markdown("#### Indtast energi")
        col1, col2 = st.columns([2, 1])
        with col1:
            E_val = st.number_input("Energi:", min_value=1e-30, value=2.5,
                                    format="%.4f", key="photon_E_val")
        with col2:
            st.markdown("")
            st.markdown("")
            E_unit = st.selectbox("Enhed:", ["eV", "J", "kJ/mol"], key="photon_E_unit")

        if E_unit == "eV":
            E_J = E_val * EV
        elif E_unit == "J":
            E_J = E_val
        else:  # kJ/mol
            E_J = E_val * 1000 / 6.02214076e23

        if E_J > 0:
            lam_m = H * C / E_J
            lam_nm_out = lam_m / 1e-9

            st.markdown("---")
            st.markdown("#### Resultat")
            r1, r2, r3 = st.columns(3)
            with r1:
                st.metric("λ (nm)", f"{lam_nm_out:.4f}")
            with r2:
                st.metric("λ (m)", f"{lam_m:.4e}")
            with r3:
                freq = C / lam_m
                st.metric("Frekvens (Hz)", f"{freq:.4e}")

            st.latex(
                rf"\lambda = \frac{{hc}}{{E}} = "
                rf"\frac{{6.626 \times 10^{{-34}} \times 2.998 \times 10^8}}{{{E_J:.4e}}} "
                rf"= {lam_m:.4e}\ \text{{m}} = {lam_nm_out:.4f}\ \text{{nm}}"
            )

            spectrum = [
                ("Gamma (γ)", 0, 0.01, "☢️"),
                ("Røntgen", 0.01, 10, "🩻"),
                ("Ultraviolet (UV)", 10, 400, "🔆"),
                ("Synligt lys", 400, 700, "🌈"),
                ("Infrarød (IR)", 700, 1e6, "🌡️"),
                ("Mikrobølger", 1e6, 1e11, "📡"),
                ("Radiobølger", 1e11, 1e15, "📻"),
            ]
            region = "Ukendt"
            for name, lo, hi, icon in spectrum:
                if lo <= lam_nm_out < hi:
                    region = f"{icon} {name}"
                    break
            st.info(f"λ = {lam_nm_out:.4f} nm svarer til: **{region}**")
