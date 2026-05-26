"""
Formelsamling — komplet eksamensreferenceside for DTU 26021.
"""

import streamlit as st


def render_formelsamling_page():
    st.title("📋 Formelsamling")
    st.markdown("Alle centrale formler fra DTU 26021 (OpenStax Chemistry 2e) på ét sted.")
    st.markdown("---")

    sections = [
        "⚖️ Støkiometri & Molarmasse",
        "📊 Gaslove",
        "🔥 Termokemi",
        "⚗️ Ligevægt",
        "🧪 Syrer & Baser",
        "🔋 Elektrokemi",
        "⚡ Kinetik",
        "🌡️ Kolligative egenskaber",
        "🔷 Geometri & Bindinger",
        "☢️ Nuklear kemi",
    ]

    active = st.radio(
        "Sektion:",
        sections,
        key="formel_section",
        horizontal=False,
    )

    st.markdown("---")

    if active == "⚖️ Støkiometri & Molarmasse":
        st.markdown(r"""
## ⚖️ Støkiometri & Molarmasse

| Formel | Beskrivelse |
|--------|-------------|
| $M = \sum n_i \cdot A_i$ | Molarmasse: sum af atommasser × antal |
| $n = m / M$ | Stofmængde (mol) = masse / molarmasse |
| $m = n \cdot M$ | Masse = stofmængde × molarmasse |
| $N = n \cdot N_A$ | Antal partikler, $N_A = 6.022 \times 10^{23}$ mol⁻¹ |
| $w_i = \frac{n_i M_i}{M_{total}} \times 100\%$ | Masseprocentkomposition |
| $\% \text{udbytte} = \frac{m_{faktisk}}{m_{teoretisk}} \times 100\%$ | Procentuelt udbytte |

**Afstemning:** Antal atomer af hvert grundstof er bevaret på begge sider af ligningen.

**Begrænsende reagent:** Det stof der løber tørt først — bestemmer det teoretiske udbytte.
        """)

    elif active == "📊 Gaslove":
        st.markdown(r"""
## 📊 Gaslove

| Formel | Navn | Betingelse |
|--------|------|------------|
| $PV = nRT$ | Idealgas | $R = 8.314\ \text{J mol}^{-1}\text{K}^{-1}$ |
| $\frac{P_1 V_1}{T_1} = \frac{P_2 V_2}{T_2}$ | Kombineret gaslov | n konstant |
| $P_1 V_1 = P_2 V_2$ | Boyles lov | T konstant |
| $\frac{V_1}{T_1} = \frac{V_2}{T_2}$ | Charles' lov | P konstant |
| $\frac{P_1}{T_1} = \frac{P_2}{T_2}$ | Gay-Lussacs lov | V konstant |
| $P_{total} = P_1 + P_2 + \cdots$ | Daltons lov | Blandinger |
| $P_i = \chi_i \cdot P_{total}$ | Partialtryk | $\chi_i$ = molfraktion |
| $\frac{r_1}{r_2} = \sqrt{\frac{M_2}{M_1}}$ | **Grahams lov** | Effusion |
| $\left(P + \frac{an^2}{V^2}\right)(V-nb) = nRT$ | van der Waals | Realgasser |

**Konstanter:** $R = 8.314$ J/mol·K = 0.08206 L·atm/mol·K · STP: 0°C, 1 atm → 22.4 L/mol
        """)

    elif active == "🔥 Termokemi":
        st.markdown(r"""
## 🔥 Termokemi

| Formel | Beskrivelse |
|--------|-------------|
| $\Delta H°_{rxn} = \sum \nu \Delta H°_f(\text{prod}) - \sum \nu \Delta H°_f(\text{react})$ | Hess' lov via dannelsesenthalpier |
| $\Delta H_{rxn} \approx \sum E(\text{bindinger brudt}) - \sum E(\text{bindinger dannet})$ | Bindingsenthalpier |
| $q = mc\Delta T$ | Kalorimetri; $c_{vand} = 4.184$ J/g·K |
| $\Delta G° = \Delta H° - T\Delta S°$ | Gibbs fri energi |
| $\Delta G° = -RT\ln K = -nFE°_{cell}$ | Sammenhæng G, K, E |
| $\Delta G = \Delta G° + RT\ln Q$ | Ikke-standardbetingelser |

**Spontanitet:**

| ΔH | ΔS | ΔG | Spontan? |
|----|----|----|----------|
| − | + | − altid | Ja |
| − | − | Afhænger af T | Lav T |
| + | + | Afhænger af T | Høj T |
| + | − | + altid | Nej |

**Opvarmningskurve (vand):** $q_{is} = mc\Delta T$ → $q_{smelt} = n\Delta H_{fus}$ → $q_{vand} = mc\Delta T$ → $q_{fordamp} = n\Delta H_{vap}$ → $q_{damp} = mc\Delta T$
        """)

    elif active == "⚗️ Ligevægt":
        st.markdown(r"""
## ⚗️ Ligevægt

| Formel | Beskrivelse |
|--------|-------------|
| $K_c = \frac{[\text{prod}]^\nu}{[\text{react}]^\nu}$ | Ligevægtskonstant (koncentration) |
| $K_p = K_c (RT)^{\Delta n_{gas}}$ | $K_p$ fra $K_c$; $\Delta n = \sum \nu_{prod} - \sum \nu_{react}$ |
| $Q < K$ → reaktion går fremad | Reaktionskvotient vs. K |
| $Q > K$ → reaktion går baglæns | |
| $K_{sp} = [\text{kation}]^m [\text{anion}]^n$ | Opløselighedsprodukt |
| $\Delta G° = -RT\ln K$ | G og ligevægt |

**ICE-tabel:** Initial → Change → Equilibrium

**Le Chateliers princip:**

| Ændring | Virkning | K? |
|---------|----------|----|
| Tilsæt reaktant | Forskydes mod produkter | Uændret |
| Fjern produkt | Forskydes mod produkter | Uændret |
| ↑ Tryk | Mod færrest mol gas | Uændret |
| ↑ T (eksoterm) | Mod reaktanter | K falder |
| ↑ T (endoterm) | Mod produkter | K stiger |
| Katalysator | Ingen | Uændret |
        """)

    elif active == "🧪 Syrer & Baser":
        st.markdown(r"""
## 🧪 Syrer & Baser

| Formel | Beskrivelse |
|--------|-------------|
| $\text{pH} = -\log[\text{H}^+]$ | Definition af pH |
| $\text{pOH} = -\log[\text{OH}^-]$ | Definition af pOH |
| $\text{pH} + \text{pOH} = 14$ | Ved 25°C |
| $K_w = [\text{H}^+][\text{OH}^-] = 1.0 \times 10^{-14}$ | Vandets ionprodukt (25°C) |
| $K_a \cdot K_b = K_w$ | Konjugeret par |
| $\text{pH} = \text{p}K_a + \log\frac{[\text{A}^-]}{[\text{HA}]}$ | **Henderson-Hasselbalch** |
| $[\text{H}^+] = \sqrt{K_a \cdot C_a}$ | Svag syre (approx) |
| $[\text{OH}^-] = \sqrt{K_b \cdot C_b}$ | Svag base (approx) |

**Stærke syrer:** HCl, HBr, HI, HNO₃, H₂SO₄, HClO₄ — $[\text{H}^+] = C_{syre}$

**Buffer:** Blanding af svag syre + konjugeret base. Modstår pH-ændring ved tilsætning af syre/base.

**Titration ækvivalenspunkt:** mol syre = mol base → brug for stærk/stærk: pH = 7; svag syre + stærk base: pH > 7.
        """)

    elif active == "🔋 Elektrokemi":
        st.markdown(r"""
## 🔋 Elektrokemi

| Formel | Beskrivelse |
|--------|-------------|
| $E°_{cell} = E°_{cathode} - E°_{anode}$ | Standard cellespænding |
| $\Delta G° = -nFE°_{cell}$ | G og cellespænding; $F = 96485$ C/mol |
| $E = E° - \frac{RT}{nF}\ln Q$ | **Nernst-ligningen** |
| $E = E° - \frac{0.0592}{n}\log Q$ | Nernst ved 25°C |
| $\ln K = \frac{nFE°}{RT} = \frac{nE°}{0.0257}$ | K fra E° (25°C) |
| $m = \frac{M \cdot I \cdot t}{n \cdot F}$ | **Faradays lov** (elektrolyse) |
| $Q = I \cdot t$ | Ladning (coulomb) |

**Galvanisk celle:** Spontan ($E° > 0$, $\Delta G° < 0$)

**Elektrolytisk celle:** Ikke-spontan — drives af ekstern spænding

**Oxidation ved anode, reduktion ved katode** (i begge celletyper)

**Oxid.tal:** Stiger ved oxidation (afgiver e⁻), falder ved reduktion (optager e⁻)
        """)

    elif active == "⚡ Kinetik":
        st.markdown(r"""
## ⚡ Kinetik

| Formel | Orden | Enhed for k |
|--------|-------|-------------|
| $[\text{A}]_t = [\text{A}]_0 - kt$ | 0. orden | M/s |
| $\ln[\text{A}]_t = \ln[\text{A}]_0 - kt$ | 1. orden | s⁻¹ |
| $\frac{1}{[\text{A}]_t} = \frac{1}{[\text{A}]_0} + kt$ | 2. orden | M⁻¹s⁻¹ |

**Halveringstider:**

| Orden | $t_{1/2}$ |
|-------|-----------|
| 0 | $[\text{A}]_0 / 2k$ |
| 1 | $\ln 2 / k = 0.693/k$ |
| 2 | $1/(k[\text{A}]_0)$ |

**Arrhenius:** $k = A e^{-E_a/RT}$ → $\ln\frac{k_2}{k_1} = \frac{E_a}{R}\left(\frac{1}{T_1} - \frac{1}{T_2}\right)$

**Reaktionsorden bestemmes eksperimentelt** — ikke fra den kemiske ligning alene.
        """)

    elif active == "🌡️ Kolligative egenskaber":
        st.markdown(r"""
## 🌡️ Kolligative egenskaber

Afhænger kun af antal opløste partikler, ikke hvad de er.

| Formel | Navn | Beskrivelse |
|--------|------|-------------|
| $\Delta T_b = i \cdot K_b \cdot m$ | Kogepunktsstigning | $K_b(\text{vand}) = 0.512$ °C·kg/mol |
| $\Delta T_f = i \cdot K_f \cdot m$ | Frysepunktssænkning | $K_f(\text{vand}) = 1.86$ °C·kg/mol |
| $\pi = i \cdot MRT$ | Osmotisk tryk | $M$ = molaritet, $R = 0.08206$ L·atm/mol·K |
| $P_{sol} = \chi_{solvent} \cdot P°_{solvent}$ | **Raoults lov** | Damptrykssænkning |

**Van't Hoff faktor $i$:** Antal partikler pr. formelenhed

| Stof | $i$ (ideal) |
|------|------------|
| Glucose, saccharose | 1 |
| NaCl, KBr, MgO | 2 |
| MgCl₂, CaCl₂, Na₂SO₄ | 3 |
| AlCl₃, FeCl₃ | 4 |

**Molalitet:** $m = n_{solut} / \text{kg}_{solvent}$ (ikke liter!)
        """)

    elif active == "🔷 Geometri & Bindinger":
        st.markdown(r"""
## 🔷 Geometri & Bindinger

**VSEPR + Hybridisering:**

| SN | LP | Geometri | Hybr. | Vinkler | Polær? |
|----|----|----------|-------|---------|--------|
| 2 | 0 | Lineær | sp | 180° | Nej* |
| 3 | 0 | Trig. plan | sp² | 120° | Nej* |
| 3 | 1 | Vinklet | sp² | ~120° | Ja |
| 4 | 0 | Tetraedrisk | sp³ | 109.5° | Nej* |
| 4 | 1 | Trig. pyramidal | sp³ | ~107° | Ja |
| 4 | 2 | Vinklet | sp³ | ~104.5° | Ja |
| 5 | 0 | Trig. bipyramidal | sp³d | 90°/120° | Nej* |
| 6 | 0 | Oktaedrisk | sp³d² | 90° | Nej* |
| 6 | 2 | Kvadratisk plan | sp³d² | 90° | Nej* |

\* Upolær kun hvis alle terminale atomer er identiske.

**IMF styrke:** Ion-ion > H-bond > Dipol-dipol > London (van der Waals)

**H-bond kræver:** donor (N–H, O–H, F–H) + acceptor (frit par på N, O, F)

**Bindingsenthalpier:** $\Delta H \approx \sum E(\text{brudt}) - \sum E(\text{dannet})$

**Eksamenstip:** Upolær + højere M → lavere damptryk, højere kogepunkt (London). H-bond >> London.
        """)

    elif active == "☢️ Nuklear kemi":
        st.markdown(r"""
## ☢️ Nuklear kemi

| Formel | Beskrivelse |
|--------|-------------|
| $N(t) = N_0 \cdot \left(\frac{1}{2}\right)^{t/t_{1/2}}$ | Radioaktivt henfald |
| $t_{1/2} = \frac{\ln 2}{\lambda} \approx \frac{0.693}{\lambda}$ | Halveringstid |
| $\lambda = \frac{\ln 2}{t_{1/2}}$ | Henfaldskonstant |
| $A = \lambda N$ | Aktivitet (henfald/s = Becquerel) |

**Henfaldstyperne:**

| Type | Symbol | ΔZ | ΔA | Penetration |
|------|--------|----|----|-------------|
| Alfa | α (⁴He) | −2 | −4 | Lav (papir) |
| Beta⁻ | β⁻ (e⁻) | +1 | 0 | Moderat (Al) |
| Beta⁺ | β⁺ (e⁺) | −1 | 0 | Moderat |
| Gamma | γ | 0 | 0 | Høj (bly) |
| Elektronindfangning | EC | −1 | 0 | — |

**Huskeregel:** Efter $n$ halveringstider er $(1/2)^n$ tilbage.
3 halveringstider → $12.5\%$ → $87.5\%$ henfaldet.
        """)

    # Always show constants footer
    st.markdown("---")
    with st.expander("🔢 Vigtige konstanter og enheder", expanded=False):
        st.markdown(r"""
| Konstant | Værdi |
|----------|-------|
| $N_A$ (Avogadros tal) | $6.022 \times 10^{23}$ mol⁻¹ |
| $R$ (gaskonstant) | 8.314 J/mol·K = 0.08206 L·atm/mol·K |
| $F$ (Faradays konstant) | 96485 C/mol |
| $K_w$ (25°C) | $1.0 \times 10^{-14}$ |
| $c_{vand}$ | 4.184 J/g·K |
| $\Delta H_{fus}(vand)$ | 6.01 kJ/mol |
| $\Delta H_{vap}(vand)$ | 40.7 kJ/mol |
| 0°C | 273.15 K |
| 1 atm | 101325 Pa = 760 mmHg |
| STP | 0°C, 1 atm → 22.4 L/mol (idealgas) |
        """)
