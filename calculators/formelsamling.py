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
        "💡 Eksamenskoncepter (sandt/falsk)",
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

    elif active == "💡 Eksamenskoncepter (sandt/falsk)":
        st.markdown("## 💡 Eksamenskoncepter – sandt/falsk oversigt")
        st.markdown(
            "Oversigt over typiske **multiple choice-udsagn** og om de er ✅ korrekte eller ❌ forkerte. "
            "Særligt nyttigt til opgaver der spørger 'Hvilket udsagn er **ikke** korrekt?'"
        )
        st.markdown("---")

        with st.expander("⚗️ Katalysatorer", expanded=True):
            st.markdown("""
| Udsagn | ✅ / ❌ | Forklaring |
|--------|--------|-----------|
| Katalysatorer sænker aktiveringsenergi $E_a$ | ✅ | Tilbyder en alternativ reaktionsvej med lavere $E_a$ |
| Katalysatorer forøger reaktionshastigheden | ✅ | Lavere $E_a$ → flere kollisioner med tilstrækkelig energi |
| Katalysatorer påvirker **begge** retninger (frem og tilbage) ligeligt | ✅ | Derfor ændres $K$ ikke |
| Katalysatorer ændrer **ikke** ligevægtskonstanten $K$ | ✅ | $K$ bestemmes kun af $\\Delta G^\\circ$, ikke reaktionsvej |
| Katalysatorer forbruges **ikke** i reaktionen | ✅ | De gendannes til sidst (kan dog deaktiveres) |
| Katalysatorer kan være heterogene **eller** homogene | ✅ | Hetero: fast Pt + gas; homo: syre i opløsning |
| Katalysatorer ændrer **ikke** $\\Delta H$, $\\Delta G$ eller $\\Delta S$ | ✅ | Kun kinetik påvirkes, ikke termodynamik |
| **Katalysatorer virker kun ved høj temperatur** | ❌ | Enzymer er biologiske katalysatorer ved ~37 °C |
| **Katalysatorer ændrer ligevægtskonstanten** | ❌ | $K$ er uændret — ligevægtspositionen nås blot hurtigere |
| **En katalysator forskyder ligevægten mod produkterne** | ❌ | Den fremskynder reaktionen, men ændrer ikke $K$ |
""")

        with st.expander("⚗️ Ligevægt & Le Chatelier"):
            st.markdown("""
| Udsagn | ✅ / ❌ | Forklaring |
|--------|--------|-----------|
| Stigning i temperatur favoriserer den endoterme retning | ✅ | Le Chatelier: systemet modvirker ændringen |
| Stigning i tryk (ved konstant T) favoriserer siden med **færre** gasmol | ✅ | Le Chatelier |
| Tilsætning af inert gas ved konstant volumen ændrer **ikke** ligevægten | ✅ | Partialtrykke for reaktanterne uændrede |
| $K$ afhænger kun af temperaturen | ✅ | $K$ er konstant ved konstant T |
| Forøgelse af reaktantkoncentration forskyder ligevægt mod produkter | ✅ | $Q < K$ → reaktionen går fremad |
| **Tilsætning af katalysator forskyder ligevægten** | ❌ | Katalysator påvirker kun hastighed, ikke $K$ |
| **Fortynding ændrer $K$** | ❌ | $K$ er uafhængig af koncentration/tryk |
| **Inert gas ved konstant tryk ændrer ikke ligevægten** | ❌ | Det ændrer den faktisk — volumen øges, partialtryk falder |
""")

        with st.expander("🔥 Termokemi"):
            st.markdown("""
| Udsagn | ✅ / ❌ | Forklaring |
|--------|--------|-----------|
| Eksoterm reaktion: $\\Delta H < 0$ (energi frigives) | ✅ | Produkter er mere stabile end reaktanter |
| Endoterm reaktion: $\\Delta H > 0$ (energi optages) | ✅ | |
| Hess' lov: $\\Delta H_{rxn}$ er uafhængig af reaktionsvej | ✅ | Tilstandsfunktion |
| Standarddannelsesentalpien for et grundstof i standardtilstand = 0 | ✅ | Fx $\\Delta H_f^\\circ(O_2) = 0$ |
| En spontan reaktion kræver **ikke** nødvendigvis $\\Delta H < 0$ | ✅ | $\\Delta G = \\Delta H - T\\Delta S$ – entropi kan drive reaktionen |
| **Eksoterme reaktioner er altid spontane** | ❌ | Spontanitet bestemmes af $\\Delta G$, ikke kun $\\Delta H$ |
| **En reaktion med $\\Delta G < 0$ er hurtig** | ❌ | $\\Delta G$ siger noget om spontanitet, ikke hastighed |
""")

        with st.expander("⚡ Kinetik"):
            st.markdown("""
| Udsagn | ✅ / ❌ | Forklaring |
|--------|--------|-----------|
| Reaktionshastighed stiger med temperaturen | ✅ | Arrhenius: $k = Ae^{-E_a/RT}$ |
| Reaktionsordenen bestemmes **eksperimentelt** (ikke fra koefficienter) | ✅ | Gælder for det overordnede hastighedsudtryk |
| For elementarreaktioner kan orden aflæses fra koefficienter | ✅ | Kun for enkelttrins-mekanismer |
| 1. ordens reaktion: halvliv $t_{1/2} = \\ln2 / k$ er koncentrationsuafhængigt | ✅ | |
| Aktiveringsenergi $E_a$ sænkes af en katalysator | ✅ | |
| **Reaktionsordenen kan altid aflæses fra den afstemte reaktionsligning** | ❌ | Kun for elementarreaktioner |
| **En reaktion med stor $E_a$ er altid langsom** | ❌ | Hastighed afhænger også af frekvensfaktoren $A$ og T |
| **Halvliv for 2. orden er koncentrationsuafhængigt** | ❌ | $t_{1/2} = 1/(k[A]_0)$ – afhænger af $[A]_0$ |
""")

        with st.expander("🧪 Syrer & Baser"):
            st.markdown("""
| Udsagn | ✅ / ❌ | Forklaring |
|--------|--------|-----------|
| Stærke syrer dissocierer fuldstændigt i vand | ✅ | HCl, HBr, HI, $H_2SO_4$, $HNO_3$, $HClO_4$ |
| $pH + pOH = 14$ ved 25°C | ✅ | $K_w = 10^{-14}$ ved 25°C |
| En buffer modstår pH-ændring ved tilsætning af syre/base | ✅ | |
| Konjugerede base af stærk syre er en **svag** base | ✅ | Fx $Cl^-$ er en meget svag base |
| **Stærk syre har altid lavest pH** | ❌ | En fortyndet stærk syre kan have højere pH end en koncentreret svag syre |
| **En syre med lav $K_a$ er altid farlig/kraftig** | ❌ | $K_a$ siger noget om styrke, ikke om farlighed |
""")

        with st.expander("🌡️ Kolligative egenskaber"):
            st.markdown("""
| Udsagn | ✅ / ❌ | Forklaring |
|--------|--------|-----------|
| Frysepunktssænkning og kogepunktsstigning afhænger af **antal** opløste partikler | ✅ | Kolligativ egenskab — ikke partikeltype |
| Elektrolytter giver større effekt end ikke-elektrolytter ved samme masse | ✅ | Pga. van't Hoff-faktoren $i > 1$ |
| $\\Delta T_f = i \\cdot K_f \\cdot m$ | ✅ | $i=1$ for glucose, $i\\approx2$ for NaCl |
| Osmotisk tryk: $\\pi = iMRT$ | ✅ | |
| **Kogepunktssænkning opstår ved tilsætning af opløst stof** | ❌ | Opløst stof giver kogepunktS**STIGNING**, ikke sænkning |
| **Van't Hoff-faktoren $i$ er altid et helt tal** | ❌ | Ufuldstændig dissociation giver $1 < i < n_{ideal}$ |
""")

        with st.expander("🔋 Elektrokemi"):
            st.markdown("""
| Udsagn | ✅ / ❌ | Forklaring |
|--------|--------|-----------|
| Oxidation sker ved anoden | ✅ | "An-ox, Red-cat" |
| Reduktion sker ved katoden | ✅ | |
| I en galvanisk celle: $\\Delta G = -nFE_{celle}$ | ✅ | |
| Positiv $E^\\circ_{celle}$ → spontan reaktion ($\\Delta G < 0$) | ✅ | |
| **I en elektrolytisk celle produceres der energi** | ❌ | Elektrolyse **kræver** energi (tilført strøm) |
| **Anionen reduceres altid i en elektrolytisk celle** | ❌ | Anionen oxideres ved anoden |
""")

        with st.expander("🔷 Bindinger & IMF"):
            st.markdown("""
| Udsagn | ✅ / ❌ | Forklaring |
|--------|--------|-----------|
| Hydrogenbinding kræver N–H, O–H eller F–H | ✅ | Disse er tilstrækkeligt elektronegative |
| London-kræfter (dispersion) eksisterer i **alle** molekyler | ✅ | Selv i upolære |
| Et molekyle med polære bindinger kan godt være upolært | ✅ | Fx $CO_2$, $CCl_4$ (symmetri ophæver dipolerne) |
| Ionbindinger er generelt stærkere end kovalente bindinger | ✅ | Højere smeltepunkt, hårdere |
| **Et molekyle med frie elektronpar er altid polært** | ❌ | Fx $XeF_4$ (kvadratisk plan) er upolær pga. symmetri |
| **Stærkere IMF giver altid lavere kogepunkt** | ❌ | Stærkere IMF → **højere** kogepunkt |
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
