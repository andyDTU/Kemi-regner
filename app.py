from __future__ import annotations

"""
Chemistry Calculator - Streamlit App
A comprehensive chemistry calculator for high school and introductory university students.
"""

import streamlit as st
import pandas as pd
import math
from pathlib import Path
from urllib.parse import quote

import requests

# Import calculators
from calculators.molar_mass import calculate_molar_mass_with_steps, format_composition_table
from calculators.electron_configuration import calculate_electron_configuration_with_steps
from calculators.gibbs import (
    calculate_gibbs_free_energy_with_steps,
    analyze_gibbs_temperature_dependence,
    calculate_reaction_gibbs_with_steps,
)
from calculators.stoichiometry import calculate_limiting_reagent_with_steps, calculate_dilution_with_steps
from calculators.solubility import analyze_salt_solubility_with_steps
from calculators.redox_balance import (
    balance_redox_with_steps,
    analyze_oxidation_numbers,
    _oxidation_states_for_species,
    _normalize_ox_number,
)
from calculators.reaction_classification import classify_reaction_text, ReactionParseError
from calculators.damptryk import render_damptryk_page
from calculators.kogepunkt_frysepunkt import render_kogepunkt_frysepunkt_page
from calculators.acids_bases import (
    calculate_strong_acid_ph, calculate_strong_base_ph, calculate_strong_acid_base_mixture,
    calculate_weak_acid_ph, calculate_weak_base_ph, calculate_buffer_ph,
    calculate_buffer_mixing_ph, calculate_target_buffer_ratio,
    calculate_titration_strong_acid_strong_base, calculate_titration_weak_acid_strong_base
)
from calculators.equilibrium import (
    solve_ice_table_with_steps, convert_equilibrium_constants_with_steps,
    calculate_reaction_quotient_with_steps, calculate_solubility_with_steps,
    calculate_solubility_product_with_steps
)
from calculators.periodic_table import render_periodic_table_tab
from calculators.ionization_energy import render_ionization_energy_tab
from calculators.lewis_structure import (
    LewisStructureError,
    calculate_lewis_structure_with_steps,
    parse_species_input,
    generate_resonance_structures,
    render_lewis_structure_svg,
    render_lewis_structure_text,
)
from calculators.vsepr import render_vsepr_tab
from calculators.imf import render_imf_tab
from calculators.bond_enthalpy import render_bond_enthalpy_tab
from calculators.le_chatelier import render_le_chatelier_tab
from calculators.oxidation_states import render_oxidation_states_tab
from calculators.graham import render_graham_tab
from calculators.nuclear_decay import render_nuclear_decay_page
from calculators.formelsamling import render_formelsamling_page
from calculators.oploselighedsregler import render_oploselighedsregler_page
from core.reaction import balance_equation
from core.molecule_db import (
    search_substances,
    get_substance_by_id,
    get_vsepr_description,
    get_vsepr_distortion_label,
    SUBSTANCES,
    Substance,
)

# Page configuration
st.set_page_config(
    page_title="Chemistry Calculator",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

NAVIGATION_OPTIONS = [
    "🏠 Fundamentals",
    "📝 Eksamensguide",
    "⚖️ Atoms & Molar Mass",
    "🧮 Balancering og stofmængde",
    "📊 Gases",
    "🔥 Thermochemistry",
    "🌫️ Damptryk",
    "🌡️ Koge- og frysepunkt (colligative properties)",
    "🧪 Acids & Bases",
    "⚗️ Solutions",
    "⚡ Kinetics",
    "🔋 Electrochemistry",
    "🔷 Geometri & Bindinger",
    "⚗️ Ligevægt",
    "☢️ Nuklear kemi",
    "💧 Opløselighed & Beer-Lambert",
    "🧬 Organisk kemi",
    "📋 Formelsamling",
    "🔬 Molekyle database",
]

PAGE_LABEL_TO_QUERY = {
    "🏠 Fundamentals": "fundamentals",
    "📝 Eksamensguide": "eksamensguide",
    "⚖️ Atoms & Molar Mass": "atoms-molar",
    "🧮 Balancering og stofmængde": "stoichiometry",
    "📊 Gases": "gases",
    "🌫️ Damptryk": "damptryk",
    "🌡️ Koge- og frysepunkt (colligative properties)": "koge-fryse",
    "🔥 Thermochemistry": "thermochemistry",
    "🧪 Acids & Bases": "acids-bases",
    "🧪 Colligative Properties": "colligatives",
    "⚗️ Solutions": "solutions",
    "⚡ Kinetics": "kinetics",
    "🔋 Electrochemistry": "electrochemistry",
    "🔷 Geometri & Bindinger": "geometri",
    "⚗️ Ligevægt": "ligevaegt",
    "☢️ Nuklear kemi": "nuklear",
    "💧 Opløselighed & Beer-Lambert": "oploselig",
    "🧬 Organisk kemi": "organisk",
    "📋 Formelsamling": "formelsamling",
    "🔬 Molekyle database": "molecule-db",
}

PAGE_QUERY_TO_LABEL = {value: key for key, value in PAGE_LABEL_TO_QUERY.items()}

# Search index: maps user queries to specific calculators
SEARCH_INDEX = [
    {"title": "pH af stærk syre", "keywords": ["ph", "stærk syre", "saltsyre", "hcl", "hno3", "salpetersyre", "svovlsyre", "h2so4", "stærk", "syre"], "page": "acids-bases", "tab": "Stærk syre/base", "description": "Bruges til HCl, HNO₃, H₂SO₄ og andre syrer der ioniserer 100%"},
    {"title": "pH af stærk base", "keywords": ["ph", "stærk base", "naoh", "koh", "base", "hydroxid"], "page": "acids-bases", "tab": "Stærk syre/base", "description": "Bruges til NaOH, KOH og andre baser der ioniserer 100%"},
    {"title": "pH af svag syre", "keywords": ["ph", "svag syre", "ka", "eddikesyre", "ch3cooh", "hac", "svag", "syre", "acetic"], "page": "acids-bases", "tab": "Svag syre/base", "description": "Bruges til eddikesyre, citronsyre og andre syrer med Ka-værdi"},
    {"title": "pH af svag base", "keywords": ["ph", "svag base", "kb", "ammoniak", "nh3", "svag", "base", "amin"], "page": "acids-bases", "tab": "Svag syre/base", "description": "Bruges til NH₃, aminer og andre baser med Kb-værdi"},
    {"title": "Buffer pH (Henderson-Hasselbalch)", "keywords": ["buffer", "ph", "henderson", "hasselbalch", "bufferløsning", "acetat", "konjugeret"], "page": "acids-bases", "tab": "Buffer", "description": "Blanding af svag syre og dens konjugerede base"},
    {"title": "Titrering", "keywords": ["titrering", "ækvivalenspunkt", "neutralisation", "titration", "halvækvivalenspunkt"], "page": "acids-bases", "tab": "Titrering", "description": "Beregn pH ved titrering af syre med base"},
    {"title": "Molarmasse", "keywords": ["molarmasse", "molar masse", "g/mol", "molekylvægt", "h2o", "nacl", "formel", "sammensætning"], "page": "atoms-molar", "tab": None, "description": "Find molarmassen for en kemisk forbindelse"},
    {"title": "Elektronkonfiguration", "keywords": ["elektron", "konfiguration", "orbital", "atom", "ion", "aufbau", "periodisk", "elektroner"], "page": "atoms-molar", "tab": None, "description": "Find elektronkonfiguration for atomer og ioner"},
    {"title": "Balancer kemisk reaktion", "keywords": ["balancer", "reaktion", "ligning", "balance", "koefficient", "afstemning"], "page": "stoichiometry", "tab": "⚖️ Balancer reaktion", "description": "Balancer en kemisk reaktionsligning"},
    {"title": "Begrænsende reaktant", "keywords": ["begrænsende", "limiting reagent", "reaktant", "udbytte", "yield", "overskud", "stofmængde"], "page": "stoichiometry", "tab": "🔬 Begrænsende reaktant", "description": "Find den begrænsende reaktant og det teoretiske udbytte"},
    {"title": "Fortynding", "keywords": ["fortynding", "dilution", "koncentration", "c1v1", "c2v2", "molær"], "page": "stoichiometry", "tab": "💧 Fortynding", "description": "Beregn koncentration efter fortynding (C₁V₁ = C₂V₂)"},
    {"title": "Redoxafstemning", "keywords": ["redox", "oxidation", "reduktion", "halv-reaktion", "oxidationstal", "afstemning"], "page": "stoichiometry", "tab": "Redoxafstemning", "description": "Afstem redoxreaktioner med halvreaktionsmetoden"},
    {"title": "Ideal gaslov (PV=nRT)", "keywords": ["ideal gas", "pv=nrt", "tryk", "volumen", "temperatur", "mol", "gaslov", "p", "v", "n", "t"], "page": "gases", "tab": "Ideel gaslov", "description": "Beregn P, V, n eller T med idealgasloven"},
    {"title": "Daltons lov (partialtryk)", "keywords": ["dalton", "partialtryk", "gasblanding", "molfraktion", "partial"], "page": "gases", "tab": None, "description": "Find partialtryk i en gasblanding"},
    {"title": "Van der Waals ligning", "keywords": ["van der waals", "reel gas", "real gas", "a", "b", "korrektionsfaktorer"], "page": "gases", "tab": None, "description": "Gaslov for reelle gasser med korrektionsfaktorer"},
    {"title": "Enthalpi (ΔH)", "keywords": ["enthalpi", "δh", "varme", "reaktionsvarme", "eksoterm", "endoterm", "hess", "dannelsesenthalpi"], "page": "thermochemistry", "tab": None, "description": "Beregn reaktionsenthalpi for en kemisk reaktion"},
    {"title": "Gibbs fri energi (ΔG)", "keywords": ["gibbs", "δg", "spontan", "fri energi", "δh", "δs", "temperaturafhængig", "ligevægtskonstant"], "page": "thermochemistry", "tab": None, "description": "Beregn ΔG og find ud af om reaktionen er spontan"},
    {"title": "Kalorimetri (q = mcΔT)", "keywords": ["kalorimeter", "kalorimetri", "varmekapacitet", "q=mcδt", "specifik varme", "temperaturstigning", "flammekalorimeter"], "page": "thermochemistry", "tab": None, "description": "Beregn varmeoverførsel med q = mcΔT"},
    {"title": "Opvarmnings-/afkølingskurve", "keywords": ["opvarmning", "afkøling", "faseskift", "smelteenthalpi", "kogepunkt", "kurve", "plateau"], "page": "thermochemistry", "tab": None, "description": "Beregn energi til opvarmning med faseovergange"},
    {"title": "ICE-tabel (ligevægt)", "keywords": ["ice", "ligevægt", "kc", "kp", "equilibrium", "koncentration", "ice-tabel", "balance"], "page": "ligevaegt", "tab": None, "description": "Opsæt ICE-tabel og beregn ligevægtskoncentrationer"},
    {"title": "Reaktionskvotient (Q)", "keywords": ["q", "reaktionskvotient", "ligevægt", "shift", "le chatelier", "kc vs q"], "page": "ligevaegt", "tab": None, "description": "Find Q og afgør hvilken retning reaktionen går"},
    {"title": "Kc/Kp konvertering", "keywords": ["kc", "kp", "konvertering", "delta n", "gasreaktioner", "ligevægt"], "page": "ligevaegt", "tab": None, "description": "Konverter mellem Kc og Kp"},
    {"title": "Cellespænding (E°)", "keywords": ["elektrokemi", "celle", "spænding", "e°", "emf", "oxidation", "reduktion", "batteri", "galvanisk"], "page": "electrochemistry", "tab": None, "description": "Beregn standardcellespænding og spontanitet"},
    {"title": "Nernst ligning", "keywords": ["nernst", "cellespænding", "ikke-standard", "koncentration", "e"], "page": "electrochemistry", "tab": None, "description": "Beregn cellespænding under ikke-standardbetingelser"},
    {"title": "Reaktionshastighed & kinetik", "keywords": ["kinetik", "hastighed", "rate", "orden", "halvliv", "half-life", "k", "arrhenius", "aktiveringsenergy"], "page": "kinetics", "tab": None, "description": "Beregn reaktionshastigheder og halveringstider"},
    {"title": "Damptryk (Raoults lov)", "keywords": ["damptryk", "vapor pressure", "raoult", "fordampning", "molfraktion"], "page": "damptryk", "tab": None, "description": "Beregn damptryk med Raoults lov"},
    {"title": "Kogepunktselevering / Frysepunktssænkning", "keywords": ["kogepunkt", "frysepunkt", "kolligative", "molalitet", "kb", "kf", "δtb", "δtf", "elevering", "sænkning"], "page": "koge-fryse", "tab": None, "description": "Beregn kogepunktselevering og frysepunktssænkning"},
    {"title": "VSEPR geometri", "keywords": ["vsepr", "geometri", "molekyleform", "form", "molekyle", "vinkel", "lineær", "tetrahedral", "trigonal", "bent", "pyramidal", "hybridisering", "sp3", "sp2"], "page": "geometri", "tab": "🔷 VSEPR – Molekylgeometri", "description": "Find molekylegeometri og bindingsvinkler ud fra BP og LP"},
    {"title": "Lewis-struktur", "keywords": ["lewis", "lewis-struktur", "lewis struktur", "lewis structure", "tegn lewis", "lone pair", "oktett", "resonans", "binding", "elektronstruktur", "valenselektroner tegn", "punktstruktur"], "page": "atoms-molar", "tab": "🧷 Lewis-struktur", "description": "Tegn Lewis-struktur for et molekyle eller ion"},
    {"title": "Opløselighed og Ksp", "keywords": ["opløselighed", "ksp", "solubility", "fælding", "precipitation", "mættet"], "page": "oploselig", "tab": None, "description": "Beregn opløselighed og Ksp for svagt opløselige salte"},
    {"title": "Nuklear henfald", "keywords": ["nuklear", "radioaktivitet", "henfald", "alpha", "beta", "gamma", "halvliv", "radioaktiv"], "page": "nuklear", "tab": None, "description": "Beregn radioaktivt henfald og halveringstid"},
    {"title": "Formelsamling", "keywords": ["formel", "samling", "tabel", "oversigt", "konstanter", "alle formler"], "page": "formelsamling", "tab": None, "description": "Oversigt over alle kemiformler og konstanter"},
    {"title": "Osmotisk tryk", "keywords": ["osmose", "osmotisk", "tryk", "van't hoff", "kolligativ", "membran"], "page": "koge-fryse", "tab": None, "description": "Beregn osmotisk tryk med van't Hoffs lov"},
    # Eksamens-sprog
    {"title": "pH af stærk syre", "keywords": ["beregn ph", "find ph", "hcl", "h2so4", "hno3", "stærk syre opgave"], "page": "acids-bases", "tab": "Stærk syre/base", "description": "HCl, HNO₃, H₂SO₄ – ioniserer 100%"},
    {"title": "pH af svag syre", "keywords": ["beregn ph", "find ph", "ka", "eddikesyre", "svag syre opgave", "procentvis ionisering"], "page": "acids-bases", "tab": "Svag syre/base", "description": "Ka-opgave – eddikesyre, citronsyre m.fl."},
    {"title": "Buffer pH", "keywords": ["buffer", "henderson", "beregn ph buffer", "ha og a-", "konjugeret base"], "page": "acids-bases", "tab": "Buffer", "description": "pH af buffer med svag syre + konjugeret base"},
    {"title": "Titrering", "keywords": ["titrering", "ækvivalenspunkt", "titrer", "neutraliser", "halvækvivalens", "beregn ph ved titrering"], "page": "acids-bases", "tab": "Titrering", "description": "pH ved titrering"},
    {"title": "Er reaktionen spontan?", "keywords": ["spontan", "er reaktionen spontan", "δg", "gibbs", "spontanitet", "negativ δg"], "page": "thermochemistry", "tab": "Gibbs (ΔG)", "description": "ΔG = ΔH − TΔS – find fortegnet"},
    {"title": "Beregn ΔH° for reaktion", "keywords": ["beregn δh", "find δh", "reaktionsvarme", "hess", "eksoterm", "endoterm", "dannelsesenthalpi"], "page": "thermochemistry", "tab": "Enthalpi (ΔH°)", "description": "Hess' lov med dannelsesentalpier"},
    {"title": "Kalorimetri – temperaturstigning", "keywords": ["kalorimeter", "temperaturstigning", "q=mcδt", "specifik varme", "registrerer", "afgivet varme"], "page": "thermochemistry", "tab": "Kalorimetri (q = mcΔT)", "description": "q = mcΔT – varme fra temperaturændring"},
    {"title": "Afstem reaktion", "keywords": ["afstem", "balancer ligning", "koefficienter", "afstemning", "balance reaktion"], "page": "stoichiometry", "tab": "⚖️ Balancer reaktion", "description": "Afstemt kemisk ligning"},
    {"title": "Begrænsende reaktant / udbytte", "keywords": ["begrænsende", "theoretical yield", "udbytte", "hvad er den begrænsende", "overskud", "limiting"], "page": "stoichiometry", "tab": "🔬 Begrænsende reaktant", "description": "Find limiting reagent og teoretisk udbytte"},
    {"title": "Fortynding af opløsning", "keywords": ["fortynding", "fortyndes", "ny koncentration", "c1v1=c2v2", "fortynder", "tilsæt vand"], "page": "stoichiometry", "tab": "💧 Fortynding", "description": "C₁V₁ = C₂V₂"},
    {"title": "Ideel gaslov – find ubekendt", "keywords": ["pv=nrt", "gaslov", "find tryk", "find volumen", "find temperature", "find mol gas", "beregn gas"], "page": "gases", "tab": "Ideel gaslov", "description": "PV = nRT – beregn P, V, n eller T"},
    {"title": "Molarmasse fra densitet", "keywords": ["densitet", "molarmasse fra densitet", "m fra densitet", "rho", "ρ", "g/l", "molar masse densitet", "identificer gas", "ukendt gas", "nitrogen oxid", "kvælstofoxid"], "page": "gases", "tab": "🔬 M fra densitet", "description": "M = ρRT/P – find molarmassen fra densitet, tryk og temperatur"},
    {"title": "Empirisk formel", "keywords": ["empirisk formel", "empirisk", "procentsammensætning", "procent sammensætning", "masseandel", "elementaranalyse", "forbrændingsanalyse", "%c", "%h", "%o", "hvad er formlen", "find formel fra procent", "molekylær formel", "molecular formula"], "page": "atoms-molar", "tab": "🔬 Empirisk formel", "description": "Find empirisk/molekylær formel fra procentvis sammensætning – klassisk elementaranalyse"},
    {"title": "Formel ladning", "keywords": ["formel ladning", "formal charge", "fc", "lewis struktur rangering", "sandsynlig struktur", "lone pair", "bindende elektroner", "valenselektroner", "rang struktur", "oktett", "resonans formal", "sammenlign strukturer", "v minus l minus b"], "page": "atoms-molar", "tab": "⚗️ Formel ladning", "description": "Beregn FC = V − L − ½B for hvert atom og rangér Lewis-strukturer efter sandsynlighed"},
    {"title": "Funktionelle grupper", "keywords": ["funktionel gruppe", "organisk", "keton", "aldehyd", "alkohol", "ester", "carboxylsyre", "amin", "alken", "alkyn", "alkan", "CH3CO", "CHO", "COOH", "COO", "identify group", "find gruppe", "kondenseret formel", "organisk formel"], "page": "organisk", "tab": None, "description": "Identificér funktionelle grupper fra kondenseret formel eller IUPAC-navn"},
    {"title": "Organisk reaktion", "keywords": ["organisk reaktion", "hydrering", "halogenering", "oxidation alkohol", "reduktion keton", "esterifikation", "hydrolyse ester", "markovnikov", "additionsreaktion", "eliminering", "saponifikation", "hvad dannes", "reaktionsprodukt", "alken reaktion", "br2 alken"], "page": "organisk", "tab": None, "description": "Forudsig produkt af organiske reaktioner: hydrering, halogenering, oxidation, esterifikation m.fl."},
    {"title": "Salthydrolyse / pH af salt", "keywords": ["salthydrolyse", "hydrolyse", "ph af salt", "natriumacetat", "ammoniumchlorid", "konjugeret base", "konjugeret syre", "kh", "salt opløsning ph", "basisk salt", "sur salt", "ch3coona", "nh4cl"], "page": "acids-bases", "tab": "⚗️ Salthydrolyse", "description": "pH af saltopløsninger via hydrolyse – Kh = Kw/Ka eller Kw/Kb"},
    {"title": "Ioniseringsgrad α", "keywords": ["ioniseringsgrad", "ionisering", "alpha", "α", "procentvis ioniseret", "5%regel", "5 procent regel", "svag syre ioniseret", "andel ioniseret", "degree of ionization"], "page": "acids-bases", "tab": "Svag syre/base", "description": "Beregn ioniseringsgrad α og procentvis ionisering for svag syre/base"},
    {"title": "Van't Hoff-plot", "keywords": ["van't hoff", "vant hoff", "lnk vs 1/t", "delta h fra k", "delta s fra k", "k ved to temperaturer", "hældning lnk", "reaktionsentalpi fra k", "temperaturafhængig k", "van hoff plot"], "page": "thermochemistry", "tab": None, "description": "Find ΔH° og ΔS° fra K-værdier ved to temperaturer – hældning og skæringspunkt i lnK vs. 1/T"},
    {"title": "Kirchhoffs lov", "keywords": ["kirchhoff", "kirchhoffs lov", "delta h ved anden temperatur", "temperaturkorrektions", "delta cp", "varmekaps", "delta h 500k", "reaktionsenthalpi ved t"], "page": "thermochemistry", "tab": None, "description": "ΔH°(T₂) = ΔH°(T₁) + ΔCp×ΔT – korriger entalpien til anden temperatur"},
    {"title": "Molarmasse fra kolligative egenskaber", "keywords": ["molarmasse fra deltaT", "molarmasse fra osmose", "ukendt molarmasse", "find M fra frysepunkt", "find M fra kogepunkt", "baglæns kolligativ", "osmotisk tryk molarmasse", "protein molarmasse"], "page": "koge-fryse", "tab": None, "description": "Find molarmasse fra ΔTf, ΔTb eller osmotisk tryk – klassisk analyseopgave"},
    {"title": "Bufferkapacitet β", "keywords": ["bufferkapacitet", "buffer kapacitet", "beta buffer", "van slyke", "β buffer", "maksimal buffer", "modstandsevne syre base", "buffer robusthed"], "page": "acids-bases", "tab": "Buffer", "description": "β = 2,303×C×Ka×[H⁺]/(Ka+[H⁺])² – bufferens modstandsevne mod pH-ændring"},
    {"title": "Debye-Hückel aktivitetskoefficent", "keywords": ["debye huckel", "debye-hückel", "aktivitetskoefficent", "gamma", "γ±", "ionsstyrke", "ionisk styrke", "aktivitet", "log gamma", "nicht-ideale opløsning", "koncentration vs aktivitet"], "page": "acids-bases", "tab": "🧮 Debye-Hückel", "description": "log γ± = −A|z+z−|√I – aktivitetskorrektion for ionopløsninger"},
    {"title": "Born-Haber cyklus / Gitterenthalpi", "keywords": ["born haber", "born-haber", "gitterenthalpi", "lattice energy", "ionisk bindingsenergi", "sublimation", "ioniseringsenergi", "elektronaffinitet", "hess ionisk", "dannnelsesenthalpi ionisk", "salt krystal enthalpi"], "page": "thermochemistry", "tab": "🔷 Born-Haber", "description": "Beregn gitterenthalpi via Born-Haber cyklus – Hess' lov for ioniske salte"},
    {"title": "Stofmænge fra reaktionsligning", "keywords": ["stofmænge", "molforhold", "koefficient", "beregn mol fra ligning", "stoichiometrisk beregning", "omregn mol", "mole ratio", "reaktantmol til produktmol", "n fra reaktion"], "page": "stoichiometry", "tab": "🔢 Stofmænge fra ligning", "description": "n_B = n_A × (ν_B/ν_A) – koefficient-baseret stofmængeomregning fra afstemt ligning"},
    {"title": "Halvliv – 0., 1., 2. orden", "keywords": ["halvliv", "half life", "t½", "1. orden halvliv", "2. orden halvliv", "ln2 over k", "t½ = 1/k[A]", "halveringstid reaktion"], "page": "kinetics", "tab": "📊 Halvliv", "description": "t½ for 0., 1. og 2. ordens reaktioner – se forskel og beregn"},
    {"title": "Initial rates – reaktionsorden fra tabel", "keywords": ["initial rates", "initialhastighedsmetode", "reaktionsorden fra eksperiment", "bestem m og n", "method of initial rates", "eksperimentel orden", "rate tabel"], "page": "kinetics", "tab": "📋 Initial rates", "description": "Find reaktionsorden og k fra tabel med eksperimentelle initialhastigheder"},
    {"title": "Ksp fælding – dannes bundfald?", "keywords": ["fældning", "bundfald", "precipitate", "q vs ksp", "ionprodukt", "overmættet", "precipitation check", "dannes der bundfald"], "page": "ligevaegt", "tab": "💧 Opløselighed (Ksp)", "description": "Q vs. Ksp – beregn om bundfald dannes ved blanding af to opløsninger"},
    {"title": "ICE-tabel / ligevægt", "keywords": ["ice tabel", "ice-tabel", "opstil ice", "opsæt ice", "ligevægtskoncentration", "beregn kc", "beregn kp"], "page": "ligevaegt", "tab": "🧊 ICE Table", "description": "ICE-tabel og ligevægtskoncentrationer"},
    {"title": "Q vs K – reaktionsretning", "keywords": ["reaktionskvotient", "q vs k", "hvilken retning", "går reaktionen frem", "går reaktionen tilbage", "forskydning"], "page": "ligevaegt", "tab": "📊 Reaktionskvotient Q", "description": "Beregn Q og sammenlign med K"},
    {"title": "Eksamensguide", "keywords": ["eksamensguide", "eksamen", "guide", "hjælp", "opgave", "hvilken beregner", "hvad skal jeg bruge"], "page": "eksamensguide", "tab": None, "description": "Oversigt over opgavetyper og hvilken beregner de kræver"},
]


def _search_calculators(query: str) -> list:
    """Return ranked search results for a query string."""
    q = query.lower().strip()
    if len(q) < 2:
        return []
    results = []
    for entry in SEARCH_INDEX:
        score = 0
        if q in entry["title"].lower():
            score += 4
        for kw in entry["keywords"]:
            if q == kw:
                score += 3
            elif q in kw or kw in q:
                score += 1
        if score > 0:
            results.append((score, entry))
    results.sort(key=lambda x: -x[0])
    return [e for _, e in results[:6]]


_TAB_NAV_CSS = """
<style>
.st-key-{key} label[data-testid="stWidgetLabel"] {{
    position: absolute; width: 1px; height: 1px; padding: 0;
    margin: -1px; overflow: hidden; clip: rect(0,0,0,0); border: 0;
}}
.st-key-{key} [data-testid="stRadio"] div[role="radiogroup"] {{
    display: flex; flex-wrap: wrap; gap: 0;
    border-bottom: 2px solid #e2e8f0; margin-bottom: 1rem;
}}
.st-key-{key} [data-testid="stRadio"] label[data-baseweb="radio"] {{
    margin: 0; padding: 0.45rem 1.1rem 0.55rem 1.1rem;
    border-bottom: 3px solid transparent; margin-bottom: -2px;
    background: transparent; min-height: 0; cursor: pointer;
}}
.st-key-{key} [data-testid="stRadio"] label[data-baseweb="radio"] > div:first-child {{
    display: none !important;
}}
.st-key-{key} [data-testid="stRadio"] label[data-baseweb="radio"] p {{
    margin: 0; font-size: 0.97rem; color: #4a5568;
}}
.st-key-{key} [data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) {{
    border-bottom-color: #ff4b4b;
}}
.st-key-{key} [data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) p {{
    color: #ff4b4b; font-weight: 600;
}}
</style>
"""


def _render_styled_tab_nav(options: list, key: str, nav_key: str | None = None) -> str:
    """Render CSS-styled tab navigation from a radio widget. Supports deep-linking via nav_key."""
    if nav_key and nav_key in st.session_state:
        target = st.session_state.pop(nav_key)
        if target in options:
            st.session_state[key] = target
    st.markdown(_TAB_NAV_CSS.format(key=key), unsafe_allow_html=True)
    return st.radio("Tab:", options, key=key, horizontal=True)


def _quick_links(links: list[tuple[str, str, str | None]], ctx: str = "") -> None:
    """Render a 'Se også' shortcut bar with links to related calculators.

    Each entry is (label, page, tab_or_None). Pass ctx= when multiple
    _quick_links calls share the same page/tab combos (e.g. inside st.tabs()).
    """
    st.markdown("---")
    st.caption("📎 **Se også:**")
    cols = st.columns(len(links))
    for col, (label, page, tab) in zip(cols, links):
        tab_safe = (tab or "").replace(" ", "_").replace("/", "_")
        label_safe = label[:12].replace(" ", "_").replace("/", "_")
        key = f"ql_{ctx}_{label_safe}_{page}_{tab_safe}"
        with col:
            if st.button(label, key=key, use_container_width=True):
                page_label = PAGE_QUERY_TO_LABEL.get(page, "🏠 Fundamentals")
                st.session_state["_pending_page"] = page_label
                st.query_params["page"] = page
                if tab:
                    st.session_state[f"nav_{page.replace('-', '_')}"] = tab
                st.rerun()


def render_search_sidebar():
    """Render a search bar in the sidebar and show navigation results."""
    if st.session_state.pop("_clear_search", False):
        st.session_state["sidebar_search_query"] = ""

    query = st.sidebar.text_input(
        "🔍 Søg efter beregner",
        key="sidebar_search_query",
        placeholder="fx 'pH', 'buffer', 'gaslov'...",
    )
    if query:
        hits = _search_calculators(query)
        if hits:
            for i, entry in enumerate(hits):
                tab_hint = f"  ›  *{entry['tab']}*" if entry["tab"] else ""
                label = f"{entry['title']}{tab_hint}"
                if st.sidebar.button(label, key=f"search_nav_{i}_{entry['title']}", help=entry["description"]):
                    page_label = PAGE_QUERY_TO_LABEL.get(entry["page"], "🏠 Fundamentals")
                    st.session_state["_pending_page"] = page_label
                    st.query_params["page"] = entry["page"]
                    if entry.get("tab"):
                        nav_key = f"nav_{entry['page'].replace('-', '_')}"
                        st.session_state[nav_key] = entry["tab"]
                    st.session_state["_clear_search"] = True
                    st.rerun()
        else:
            st.sidebar.caption("Ingen resultater – prøv et andet søgeord.")



def main():
    """Main application function."""
    
    # Sidebar navigation
    st.sidebar.title("🧪 Chemistry Calculator")
    st.sidebar.markdown("---")
    render_search_sidebar()

    # Cards/buttons set _pending_page to force radio to follow programmatic navigation.
    # Sidebar clicks don't set it, so their own session state is preserved unchanged.
    pending = st.session_state.pop("_pending_page", None)
    if pending and pending in NAVIGATION_OPTIONS:
        st.session_state["main_page"] = pending

    # On first load (no session state yet), sync from URL query params for deep links.
    query_page_raw = st.query_params.get("page")
    if isinstance(query_page_raw, list):
        query_page_raw = query_page_raw[0] if query_page_raw else None
    query_page = str(query_page_raw).strip().lower() if query_page_raw else ""

    if "main_page" not in st.session_state:
        initial = PAGE_QUERY_TO_LABEL.get(query_page, "🏠 Fundamentals")
        if initial not in NAVIGATION_OPTIONS:
            initial = "🏠 Fundamentals"
        st.session_state["main_page"] = initial

    page = st.sidebar.radio(
        "Select Calculator:",
        NAVIGATION_OPTIONS,
        key="main_page",
    )

    selected_page_query = PAGE_LABEL_TO_QUERY.get(page)
    if selected_page_query and st.query_params.get("page") != selected_page_query:
        st.query_params["page"] = selected_page_query
    
    # Main content area
    if page == "🏠 Fundamentals":
        show_fundamentals_page()
    elif page == "📝 Eksamensguide":
        show_exam_guide_page()
    elif page == "⚖️ Atoms & Molar Mass":
        show_molar_mass_page()
    elif page == "🧮 Balancering og stofmængde":
        show_stoichiometry_page()
    elif page == "🧪 Acids & Bases":
        show_acids_bases_page()
    elif page == "📊 Gases":
        show_gas_laws_page()
    elif page == "🌫️ Damptryk":
        render_damptryk_page()
    elif page == "🌡️ Koge- og frysepunkt (colligative properties)":
        render_kogepunkt_frysepunkt_page()
    elif page == "🔥 Thermochemistry":
        show_thermochemistry_page()
    elif page == "🧪 Colligative Properties":
        show_colligatives_page()
    elif page == "⚗️ Solutions":
        show_solutions_page()
    elif page == "⚡ Kinetics":
        show_kinetics_page()
    elif page == "🔋 Electrochemistry":
        show_electrochemistry_page()
    elif page == "🔷 Geometri & Bindinger":
        show_geometri_page()
    elif page == "⚗️ Ligevægt":
        show_equilibrium_page()
    elif page == "☢️ Nuklear kemi":
        render_nuclear_decay_page()
    elif page == "💧 Opløselighed & Beer-Lambert":
        render_oploselighedsregler_page()
    elif page == "🧬 Organisk kemi":
        show_organic_chemistry_page()
    elif page == "📋 Formelsamling":
        render_formelsamling_page()
    elif page == "🔬 Molekyle database":
        show_molecule_database_page()

def show_geometri_page():
    """Display the Geometry & Bonds page (VSEPR, IMF, Bond Enthalpy)."""
    st.title("🔷 Geometri & Bindinger")
    st.markdown("---")

    subpage_labels = [
        "🔷 VSEPR – Molekylgeometri",
        "🔗 Intermolekylære kræfter (IMF)",
        "⚡ Bindingsenthalpier – ΔH",
    ]
    subpage_to_query = {
        "🔷 VSEPR – Molekylgeometri":         "vsepr",
        "🔗 Intermolekylære kræfter (IMF)":   "imf",
        "⚡ Bindingsenthalpier – ΔH":         "bond-enthalpy",
    }
    query_to_subpage = {v: k for k, v in subpage_to_query.items()}

    if "nav_geometri" in st.session_state:
        _nav_target = st.session_state.pop("nav_geometri")
        if _nav_target in subpage_labels:
            st.session_state["geo_subpage"] = _nav_target

    query_sub_raw = st.query_params.get("geo_tab")
    if isinstance(query_sub_raw, list):
        query_sub_raw = query_sub_raw[0] if query_sub_raw else None
    query_sub = str(query_sub_raw).strip() if query_sub_raw else ""
    if "geo_subpage" not in st.session_state and query_sub in query_to_subpage:
        st.session_state["geo_subpage"] = query_to_subpage[query_sub]

    st.markdown(
        """
<style>
.st-key-geo_subpage label[data-testid="stWidgetLabel"] {
    position: absolute; width: 1px; height: 1px; padding: 0;
    margin: -1px; overflow: hidden; clip: rect(0,0,0,0); border: 0;
}
.st-key-geo_subpage [data-testid="stRadio"] div[role="radiogroup"] {
    display: flex; flex-wrap: wrap; gap: 0.35rem;
    border-bottom: 1px solid #e2e8f0; margin-bottom: 0.8rem;
}
.st-key-geo_subpage [data-testid="stRadio"] label[data-baseweb="radio"] {
    margin: 0; padding: 0.35rem 0.05rem 0.55rem 0.05rem;
    border-bottom: 2px solid transparent; background: transparent; min-height: 0;
}
.st-key-geo_subpage [data-testid="stRadio"] label[data-baseweb="radio"] > div:first-child {
    display: none !important;
}
.st-key-geo_subpage [data-testid="stRadio"] label[data-baseweb="radio"] p {
    margin: 0; font-size: 1.02rem; color: #0f172a;
}
.st-key-geo_subpage [data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) {
    border-bottom-color: #ff4b4b;
}
.st-key-geo_subpage [data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) p {
    color: #ff4b4b; font-weight: 600;
}
</style>
        """,
        unsafe_allow_html=True,
    )

    active_subpage = st.radio(
        "GeoSubpageNav",
        subpage_labels,
        key="geo_subpage",
        horizontal=True,
        label_visibility="collapsed",
    )

    sel_q = subpage_to_query[active_subpage]
    if st.query_params.get("geo_tab") != sel_q:
        st.query_params["geo_tab"] = sel_q

    if active_subpage == "🔷 VSEPR – Molekylgeometri":
        render_vsepr_tab()
    elif active_subpage == "🔗 Intermolekylære kræfter (IMF)":
        render_imf_tab()
    elif active_subpage == "⚡ Bindingsenthalpier – ΔH":
        render_bond_enthalpy_tab()


def _nav_card(label: str, page: str, description: str, key_suffix: str, tab: str | None = None):
    """Render a task card that navigates to the given page (and optionally a specific tab)."""
    if st.button(label, key=f"home_card_{key_suffix}", use_container_width=True, help=description):
        page_label = PAGE_QUERY_TO_LABEL.get(page, "🏠 Fundamentals")
        st.session_state["_pending_page"] = page_label
        st.query_params["page"] = page
        if tab:
            st.session_state[f"nav_{page.replace('-', '_')}"] = tab
        st.rerun()


def show_fundamentals_page():
    """Display the home/landing page with task-oriented cards."""
    st.title("🧪 Kemilommeregner")
    st.markdown("#### Hvad vil du beregne?")
    st.markdown(
        "Brug søgefeltet i sidepanelet, eller klik direkte på en opgave herunder. "
        "Alle beregnere viser trin-for-trin løsninger."
    )
    st.markdown("---")

    # ── Row 1 ────────────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("**🧪 Syrer & Baser**")
        _nav_card("pH af stærk syre / base", "acids-bases", "HCl, NaOH m.fl. – ioniserer 100%", "sa", tab="Stærk syre/base")
        _nav_card("pH af svag syre / base", "acids-bases", "Eddikesyre, ammoniak m.fl. – brug Ka / Kb", "wa", tab="Svag syre/base")
        _nav_card("⚗️ Salthydrolyse", "acids-bases", "pH af CH₃COONa, NH₄Cl – Kh = Kw/Ka", "sh", tab="⚗️ Salthydrolyse")
        _nav_card("Ioniseringsgrad α", "acids-bases", "Procentvis ioniseret, 5%-regel, eksakt ICE", "ia", tab="Svag syre/base")
    with c2:
        st.markdown("**🧮 Stofmængder & Reaktioner**")
        _nav_card("Molarmasse", "atoms-molar", "Find g/mol for en kemisk forbindelse", "mm")
        _nav_card("🔬 Empirisk formel", "atoms-molar", "Find formel fra %C, %H, %O – elementaranalyse", "ef", tab="🔬 Empirisk formel")
        _nav_card("🔢 Stofmænge fra ligning", "stoichiometry", "n_B = n_A × (ν_B/ν_A) – koefficient omregning", "sfl", tab="🔢 Stofmænge fra ligning")
        _nav_card("Begrænsende reaktant", "stoichiometry", "Find limiting reagent og teoretisk udbytte", "lr", tab="🔬 Begrænsende reaktant")
    with c3:
        st.markdown("**🔥 Termokemi**")
        _nav_card("Enthalpi ΔH", "thermochemistry", "Reaktionsvarme, Hess's lov, dannelsesenthalpi", "dh", tab="Enthalpi (ΔH°)")
        _nav_card("Gibbs fri energi ΔG", "thermochemistry", "Spontanitet, ΔG = ΔH − TΔS", "dg", tab="Gibbs (ΔG)")
        _nav_card("Kalorimetri (q = mcΔT)", "thermochemistry", "Varmeoverførsel og temperaturændring", "cal", tab="Kalorimetri (q = mcΔT)")
        _nav_card("Opvarmnings-/afkølingskurve", "thermochemistry", "Energi ved faseovergange", "heat", tab="Opvarmningskurve")
    with c4:
        st.markdown("**📊 Gasser**")
        _nav_card("Ideel gaslov PV = nRT", "gases", "Beregn P, V, n eller T", "ig", tab="Ideel gaslov")
        _nav_card("🔬 M fra densitet (ρ)", "gases", "Find molarmassen fra tryk, T og densitet – identificer ukendt gas", "mfd", tab="🔬 M fra densitet")
        _nav_card("Daltons lov (partialtryk)", "gases", "Partialtryk i en gasblanding", "dal", tab="Daltons lov")
        _nav_card("Gasstoichiometri", "gases", "Volumen og stofmængder i gasreaktioner", "gst", tab="Gasstoichiometri")

    st.markdown("---")

    # ── Row 2 ────────────────────────────────────────────────────────────────
    c5, c6, c7, c8 = st.columns(4)
    with c5:
        st.markdown("**⚗️ Ligevægt**")
        _nav_card("ICE-tabel", "ligevaegt", "Opsæt ICE-tabel og find ligevægtskoncentrationer", "ice", tab="🧊 ICE Table")
        _nav_card("Reaktionskvotient Q", "ligevaegt", "Find Q og afgør reaktionsretning", "rq", tab="📊 Reaktionskvotient Q")
        _nav_card("Kc / Kp konvertering", "ligevaegt", "Konverter mellem Kc og Kp", "kckp", tab="🔄 Kc/Kp konvertering")
        _nav_card("Le Chatelier's princip", "ligevaegt", "Forudsig ligevægtsforskydning", "lec", tab="⚖️ Le Chateliers princip")
    with c6:
        st.markdown("**🔋 Elektrokemi**")
        _nav_card("Cellespænding E°", "electrochemistry", "Standardcellespænding og spontanitet", "ecell", tab="Byg en celle")
        _nav_card("Nernst ligning", "electrochemistry", "E ved ikke-standardbetingelser", "nernst", tab="Nernst")
        _nav_card("Faradays lov", "electrochemistry", "Elektrolyse – mængde stof vs. ladning", "farad", tab="⚡ Faradays lov")
        _nav_card("Redoxafstemning", "stoichiometry", "Afstem redoxreaktioner med halvreaktioner", "redox", tab="🔋 Redoxafstemning")
    with c7:
        st.markdown("**🔷 Molekylestruktur**")
        _nav_card("VSEPR geometri", "geometri", "Molekylegeometri og bindingsvinkler", "vsepr", tab="🔷 VSEPR – Molekylgeometri")
        _nav_card("Intermolekylære kræfter", "geometri", "IMF – hydrogen-, dipol-, Londonbinding", "imf", tab="🔗 Intermolekylære kræfter (IMF)")
        _nav_card("Lewis struktur", "atoms-molar", "Tegn Lewis-struktur og find formal ladning", "lewis", tab="🧷 Lewis-struktur")
        _nav_card("Elektronkonfiguration", "atoms-molar", "Aufbau, orbital-notation og ions", "ec", tab="⚛️ Elektronkonfiguration og atomradius")
        _nav_card("⚗️ Formel ladning", "atoms-molar", "FC = V−L−½B – beregn og rangér Lewis-strukturer", "fc", tab="⚗️ Formel ladning")
    with c8:
        st.markdown("**🌡️ Avancerede emner**")
        _nav_card("📈 Van't Hoff-plot", "thermochemistry", "ΔH° og ΔS° fra K ved to temperaturer", "vhp")
        _nav_card("🌡️ Kirchhoffs lov", "thermochemistry", "ΔH°(T₂) = ΔH°(T₁) + ΔCp·ΔT", "khl")
        _nav_card("🔷 Born-Haber cyklus", "thermochemistry", "Gitterenthalpi for ioniske salte via Hess' lov", "bh")
        _nav_card("🧮 Debye-Hückel", "acids-bases", "Aktivitetskoefficenter – log γ± = −A|z+z−|√I", "dh2", tab="🧮 Debye-Hückel")

    st.markdown("---")
    st.caption("💡 Tip: Søg i sidepanelet øverst for at finde en specifik beregner hurtigt.")


# ─────────────────────────────────────────────────────────────────────────────
# EKSAMENSGUIDE
# ─────────────────────────────────────────────────────────────────────────────

_EXAM_TASKS = [
    # (opgave_tekst, nøgleord_der_afslører_typen, beregner_navn, page, tab)
    # ── Syrer & Baser ────────────────────────────────────────────────────────
    ("Beregn pH af 0,10 M HCl",
     "Nøgleord: stærk syre (HCl, HNO₃, H₂SO₄) + koncentration → pH = −log[H⁺]",
     "Stærk syre", "acids-bases", "Stærk syre/base"),
    ("En 0,050 M NaOH-opløsning – hvad er pH?",
     "Nøgleord: stærk base (NaOH, KOH) + koncentration → pOH, pH = 14 − pOH",
     "Stærk base", "acids-bases", "Stærk syre/base"),
    ("En 0,100 M eddikesyre har Ka = 1,8×10⁻⁵. Beregn pH.",
     "Nøgleord: svag syre + Ka → brug ICE-tabel til at finde [H⁺]",
     "Svag syre", "acids-bases", "Svag syre/base"),
    ("En bufferløsning indeholder 0,20 M CH₃COOH og 0,10 M CH₃COO⁻. Beregn pH.",
     "Nøgleord: buffer = svag syre + konjugeret base → Henderson-Hasselbalch: pH = pKa + log([A⁻]/[HA])",
     "Buffer (Henderson-Hasselbalch)", "acids-bases", "Buffer"),
    ("25 mL 0,10 M HCl titreres med 0,10 M NaOH. Find pH ved ækvivalenspunktet.",
     "Nøgleord: titrering + ækvivalenspunkt → bestem, hvad der er i overskud",
     "Titrering", "acids-bases", "Titrering"),
    # ── Termokemi ────────────────────────────────────────────────────────────
    ("Er reaktionen N₂ + 3H₂ → 2NH₃ spontan ved 25°C? ΔH° = −92 kJ, ΔS° = −198 J/K",
     "Nøgleord: spontan / ΔG / ΔH og ΔS givet → ΔG = ΔH − TΔS; spontan hvis ΔG < 0",
     "Gibbs fri energi (ΔG)", "thermochemistry", "Gibbs (ΔG)"),
    ("Beregn ΔH° for 2NO(g) + O₂(g) → 2NO₂(g) vha. dannelsesentalpier.",
     "Nøgleord: dannelsesentalpier (ΔHf°) givet → Hess: ΔH = Σ(ν·ΔHf° produkter) − Σ(ν·ΔHf° reaktanter)",
     "Reaktionsenthalpi (ΔH°)", "thermochemistry", "Enthalpi (ΔH°)"),
    ("100 g vand opvarmes fra 20°C til 45°C i et kalorimeter. Beregn varmeafgivelsen.",
     "Nøgleord: masse + temperaturændring + specifik varme → q = mcΔT",
     "Kalorimetri (q = mcΔT)", "thermochemistry", "Kalorimetri (q = mcΔT)"),
    # ── Stofmængder & Reaktioner ─────────────────────────────────────────────
    ("Afstem: Fe + O₂ → Fe₂O₃",
     "Nøgleord: afstem / koefficienter → balancer reaktion",
     "Balancer reaktion", "stoichiometry", "⚖️ Balancer reaktion"),
    ("5,0 g H₂ reagerer med 32 g O₂. Hvad er den begrænsende reaktant?",
     "Nøgleord: to reaktanter + masser → beregn mol af hvert, find hvem der løber tørt først",
     "Begrænsende reaktant", "stoichiometry", "🔬 Begrænsende reaktant"),
    ("Fortynding: 25 mL af 2,0 M HCl fortyndes til 500 mL. Find den nye koncentration.",
     "Nøgleord: fortynding + volumen ændres → C₁V₁ = C₂V₂",
     "Fortynding", "stoichiometry", "💧 Fortynding"),
    ("Afstem redoxreaktionen MnO₄⁻ + Fe²⁺ → Mn²⁺ + Fe³⁺ i sur opløsning.",
     "Nøgleord: redox + sur/basisk opløsning → halvreaktionsmetoden",
     "Redoxafstemning", "stoichiometry", "🔋 Redoxafstemning"),
    # ── Gasser ───────────────────────────────────────────────────────────────
    ("2,5 mol N₂ ved 25°C og 1,5 atm – hvad er volumen?",
     "Nøgleord: mol + tryk + temperatur + volumen → PV = nRT (find ubekendt)",
     "Ideel gaslov (PV = nRT)", "gases", "Ideel gaslov"),
    ("En blanding af N₂ (0,80 mol) og O₂ (0,20 mol) har totaltryk 1,0 atm. Find partialtryk.",
     "Nøgleord: gasblanding + mol + totaltryk → Daltons lov: P_i = χ_i · P_total",
     "Daltons lov (partialtryk)", "gases", "Daltons lov"),
    # ── Ligevægt ─────────────────────────────────────────────────────────────
    ("H₂ + I₂ ⇌ 2HI. Start: [H₂]₀=0,50 M, [I₂]₀=0,50 M. Beregn [HI] ved ligevægt (Kc=50).",
     "Nøgleord: ligevægtskonstant + startkoncentrationer → opstil ICE-tabel",
     "ICE-tabel", "ligevaegt", "🧊 ICE Table"),
    ("Q beregnes til 8,0. Kc = 50. Hvad sker der med reaktionen?",
     "Nøgleord: Q og K givet → Q < K: reaktion går frem; Q > K: reaktion går tilbage",
     "Reaktionskvotient (Q vs K)", "ligevaegt", "📊 Reaktionskvotient Q"),
    # ── Elektrokemi ──────────────────────────────────────────────────────────
    ("Beregn E°cell for Zn/Cu-cellen (E°Zn²⁺/Zn = −0,76 V, E°Cu²⁺/Cu = +0,34 V).",
     "Nøgleord: halvreaktionspotentialer givet → E°cell = E°katode − E°anode",
     "Cellespænding (E°cell)", "electrochemistry", "Byg en celle"),
    ("E°cell = 1,10 V, n = 2. Beregn ΔG° og K.",
     "Nøgleord: E°cell + n → ΔG° = −nFE°; K fra ΔG° = −RT·lnK",
     "ΔG° og K fra E°", "electrochemistry", "ΔG og K"),
    # ── Kinetik ──────────────────────────────────────────────────────────────
    ("En 1. ordens reaktion har k = 0,35 s⁻¹. Hvad er halvliv? Hvad er [A] efter 5 s?",
     "Nøgleord: reaktionsorden + k → integreret hastighedslov; halvliv t½ = ln2/k",
     "Integreret hastighedslov", "kinetics", "Integreret hastighedslov"),
    ("En 2. ordens reaktion: k = 0,15 M⁻¹s⁻¹, [A]₀ = 0,20 M. Hvad er t½?",
     "Nøgleord: 2. orden + k + [A]₀ → t½ = 1/(k·[A]₀) – afhænger af startkoncentration",
     "Halvliv (2. orden)", "kinetics", "📊 Halvliv"),
    ("Eksperiment 1: [A]=0,10, r=1,2×10⁻⁴. Eksperiment 2: [A]=0,20, r=4,8×10⁻⁴. Find orden og k.",
     "Nøgleord: to eksperimenter + [A] + r → m = log(r₂/r₁)/log([A]₂/[A]₁)",
     "Reaktionsorden fra initial rates", "kinetics", "📋 Initial rates"),
    ("k₁ = 1,0×10⁻³ s⁻¹ ved 25°C, Eₐ = 50 kJ/mol. Beregn k ved 35°C.",
     "Nøgleord: k ved én temp + Eₐ → Arrhenius: k₂ = k₁·exp(Eₐ/R·(1/T₁ − 1/T₂))",
     "Arrhenius", "kinetics", "Arrhenius"),
    # ── Molarmasse & Sammensætning ───────────────────────────────────────────
    ("Hvad er molarmassen af Ca(NO₃)₂?",
     "Nøgleord: kemisk formel → summer atomvægte × antal",
     "Molarmasse", "atoms-molar", "⚖️ Molar Mass"),
    ("En forbindelse indeholder 40,0% C, 6,7% H og 53,3% O. Hvad er den empiriske formel?",
     "Nøgleord: procentvis sammensætning → divider med atomvægt → find mindste heltalforhold",
     "Empirisk formel", "atoms-molar", "🔬 Empirisk formel"),
    ("To Lewis-strukturer er tegnet for samme molekyle. Rangér dem efter formel ladning.",
     "Nøgleord: FC = V − L − ½B; Σ|FC| mindst = mest sandsynlig; neg. FC på el.neg. atom",
     "Formel ladning", "atoms-molar", "⚗️ Formel ladning"),
    ("Hvilken Lewis-struktur for H₃BO₃ har den laveste Σ|FC|?",
     "Nøgleord: beregn FC for hvert atom i hver struktur og sammenlign Σ|FC|",
     "Formel ladning (struktursammenligning)", "atoms-molar", "⚗️ Formel ladning"),
    # ── Kolligative egenskaber ───────────────────────────────────────────────
    ("10 g glukose (M = 180 g/mol) opløses i 100 g vand. Find frysepunktssænkning (Kf = 1,86).",
     "Nøgleord: opløst stof + masse opløsningsmiddel + Kf → ΔTf = Kf·m (molalitet)",
     "Frysepunktssænkning", "koge-fryse", None),
    ("12 g urea (M = 60,1 g/mol) opløses i 250 g vand. Beregn kogepunktsstigningen (Kb = 0,512 °C·kg/mol).",
     "Nøgleord: opløst stof + masse opløsningsmiddel + Kb → ΔTb = Kb·m",
     "Kogepunktsstigning", "koge-fryse", None),
    ("En proteinopløsning har osmotisk tryk π = 0,245 atm ved 25°C. Hvad er molariteten?",
     "Nøgleord: osmotisk tryk + T → π = MRT → M = π/(RT)",
     "Osmotisk tryk", "koge-fryse", None),
    ("5,0 g ukendt stof opløst i 100 g vand giver ΔTf = 0,93°C (Kf = 1,86). Find molarmassen.",
     "Nøgleord: ΔTf givet → m = ΔTf/Kf → mol = m·kg opløsningsmiddel → M = g/mol",
     "M fra kolligative egenskaber", "koge-fryse", None),
    # ── Syrer & Baser – avanceret ────────────────────────────────────────────
    ("0,10 M CH₃COONa (Ka = 1,8×10⁻⁵). Beregn pH af saltopløsningen.",
     "Nøgleord: salt af svag syre + stærk base → Kh = Kw/Ka → [OH⁻] = √(Kh·C) → pH",
     "Salthydrolyse", "acids-bases", "⚗️ Salthydrolyse"),
    ("En 0,10 M eddikesyre (Ka = 1,8×10⁻⁵). Hvad er ioniseringsgraden α?",
     "Nøgleord: svag syre + Ka → α = [H⁺]/C₀; 5%-regel: ok hvis α < 0,05",
     "Ioniseringsgrad α", "acids-bases", "Svag syre/base"),
    ("Acetatbuffer: C = 0,10 M, pH = pKa = 4,74. Beregn bufferkapaciteten β.",
     "Nøgleord: buffer ved pH = pKa → maksimal β; Van Slyke: β = 2,303·C·Ka·[H⁺]/(Ka+[H⁺])²",
     "Bufferkapacitet β", "acids-bases", "Buffer"),
    ("En 0,050 M NaCl-opløsning – beregn aktivitetskoefficienten γ± (Debye-Hückel, 25°C).",
     "Nøgleord: ionsstyrke I = ½Σcᵢzᵢ² → log γ± = −A|z+z−|√I (A = 0,509)",
     "Debye-Hückel", "acids-bases", "🧮 Debye-Hückel"),
    # ── Gasser – avanceret ───────────────────────────────────────────────────
    ("En ukendt gas har densitet 1,96 g/L ved 25°C og 1,00 atm. Identificer gassen.",
     "Nøgleord: gasdensitet + T + P → M = ρRT/P (ideel gaslov baglæns)",
     "M fra gasdensitet", "gases", "🔬 M fra densitet"),
    # ── Stofmænge fra ligning ────────────────────────────────────────────────
    ("N₂ + 3H₂ → 2NH₃. Hvis 6,0 mol H₂ reagerer, hvor mange mol NH₃ dannes?",
     "Nøgleord: afstemt ligning + mol af ét stof → n_B = n_A × (ν_B/ν_A)",
     "Stofmænge fra ligning", "stoichiometry", "🔢 Stofmænge fra ligning"),
    # ── Elektrokemi – avanceret ──────────────────────────────────────────────
    ("Zn/Cu-celle: [Zn²⁺] = 0,10 M, [Cu²⁺] = 1,0 M, E° = 1,10 V, n = 2. Beregn E.",
     "Nøgleord: ikke-standard koncentrationer → Nernst: E = E° − (RT/nF)·lnQ",
     "Nernst-ligning", "electrochemistry", "Nernst"),
    ("2,0 A i 30 min. Hvor mange gram Cu aflejres fra CuSO₄? (M = 63,5 g/mol, n = 2)",
     "Nøgleord: strøm + tid + n + M → Faraday: m = I·t·M / (n·F)",
     "Faradays lov", "electrochemistry", "⚡ Faradays lov"),
    # ── Ligevægt – avanceret ─────────────────────────────────────────────────
    ("Ksp(AgCl) = 1,8×10⁻¹⁰. Hvad er opløseligheden af AgCl i mol/L?",
     "Nøgleord: Ksp + opløselighedsprodukt → ICE: AgCl ⇌ Ag⁺ + Cl⁻ → s² = Ksp",
     "Ksp – opløselighedsprodukt", "ligevaegt", "💧 Opløselighed (Ksp)"),
    ("50 mL 0,010 M AgNO₃ blandes med 50 mL 0,020 M NaCl. Ksp(AgCl) = 1,8×10⁻¹⁰. Fældes der bundfald?",
     "Nøgleord: Q vs Ksp → fortynding ved blanding → Q = [Ag⁺]·[Cl⁻] → Q > Ksp: bundfald",
     "Fælding – Q vs Ksp", "ligevaegt", "💧 Opløselighed (Ksp)"),
    ("N₂ + 3H₂ ⇌ 2NH₃. Hvad sker der med ligevægten ved øget tryk? Ved øget temperatur?",
     "Nøgleord: ligevægt + ydre påvirkning → Le Chatelier: systemet modvirker forandringen",
     "Le Chateliers princip", "ligevaegt", "⚖️ Le Chateliers princip"),
    # ── Termokemi – avanceret ────────────────────────────────────────────────
    ("Beregn samlede energi for 50 g is fra −10°C til 25°C (smelteenthalpi = 6,01 kJ/mol).",
     "Nøgleord: faseovergang + opvarmning → q_is + ΔHfus + q_vand via opvarmningskurve",
     "Opvarmningskurve", "thermochemistry", None),
    ("K = 0,010 ved 300 K og K = 0,050 ved 400 K. Find ΔH° og ΔS°.",
     "Nøgleord: K ved to temperaturer → Van't Hoff: ln(K₂/K₁) = −ΔH°/R·(1/T₂−1/T₁)",
     "Van't Hoff-plot", "thermochemistry", None),
    ("ΔH°(298 K) = −92,4 kJ/mol, ΔCp = −45,3 J/(mol·K). Beregn ΔH° ved 500 K.",
     "Nøgleord: ΔH° ved én temperatur + ΔCp → Kirchhoff: ΔH°(T₂) = ΔH°(T₁) + ΔCp·ΔT",
     "Kirchhoffs lov", "thermochemistry", None),
    ("NaCl: ΔHf° = −411, ΔHsub = 107, IE = 496, ½D(Cl₂) = 121, EA = −349 kJ/mol. Find ΔHlatt.",
     "Nøgleord: Born-Haber → Hess: ΔHlatt = ΔHf° − (ΔHsub + IE + ½D + EA)",
     "Born-Haber", "thermochemistry", None),
]


def show_exam_guide_page():
    """Eksamensguide – typiske opgavetyper og hvilken beregner de kræver."""
    st.title("📝 Eksamensguide")
    st.markdown(
        "Her kan du hurtigt finde ud af **hvilken beregner du skal bruge** til en given eksamensopgave. "
        "Klik på knappen ved opgaven for at åbne den rigtige beregner direkte."
    )
    st.markdown("---")

    # ── Søg i opgaver ────────────────────────────────────────────────────────
    exam_q = st.text_input(
        "🔍 Filtrér opgaver",
        placeholder="fx 'pH', 'spontan', 'titrering', 'ICE'...",
        key="exam_guide_filter",
    )

    # Grupper efter emne
    groups = {
        "🧪 Syrer & Baser": [
            "Stærk syre", "Stærk base", "Svag syre", "Ioniseringsgrad α",
            "Buffer (Henderson-Hasselbalch)", "Bufferkapacitet β", "Titrering",
            "Salthydrolyse", "Debye-Hückel",
        ],
        "🔥 Termokemi": [
            "Gibbs fri energi (ΔG)", "Reaktionsenthalpi (ΔH°)", "Kalorimetri (q = mcΔT)",
            "Opvarmningskurve", "Van't Hoff-plot", "Kirchhoffs lov", "Born-Haber",
        ],
        "🧮 Stofmængder & Reaktioner": [
            "Balancer reaktion", "Begrænsende reaktant", "Stofmænge fra ligning",
            "Fortynding", "Redoxafstemning", "Empirisk formel",
        ],
        "📊 Gasser": [
            "Ideel gaslov (PV = nRT)", "Daltons lov (partialtryk)", "M fra gasdensitet",
        ],
        "⚗️ Ligevægt": [
            "ICE-tabel", "Reaktionskvotient (Q vs K)",
            "Ksp – opløselighedsprodukt", "Fælding – Q vs Ksp", "Le Chateliers princip",
        ],
        "🔋 Elektrokemi": [
            "Cellespænding (E°cell)", "ΔG° og K fra E°", "Nernst-ligning", "Faradays lov",
        ],
        "⚡ Kinetik": [
            "Integreret hastighedslov", "Halvliv (2. orden)",
            "Reaktionsorden fra initial rates", "Arrhenius",
        ],
        "⚖️ Atoms & Molarmasse": [
            "Molarmasse", "Empirisk formel",
            "Formel ladning", "Formel ladning (struktursammenligning)",
        ],
        "🌡️ Kolligative egenskaber": [
            "Frysepunktssænkning", "Kogepunktsstigning", "Osmotisk tryk",
            "M fra kolligative egenskaber",
        ],
    }
    # ── Hop til emne ─────────────────────────────────────────────────────────
    _EXAM_SHORTCUTS = [
        ("📋 Alle",        None),
        ("🧪 Syrer",       "🧪 Syrer & Baser"),
        ("🔥 Termo",       "🔥 Termokemi"),
        ("🧮 Stofmæng.",   "🧮 Stofmængder & Reaktioner"),
        ("📊 Gasser",      "📊 Gasser"),
        ("⚗️ Ligevægt",    "⚗️ Ligevægt"),
        ("🔋 Elektro",     "🔋 Elektrokemi"),
        ("⚡ Kinetik",     "⚡ Kinetik"),
        ("⚖️ Atoms",       "⚖️ Atoms & Molarmasse"),
        ("🌡️ Kolligative", "🌡️ Kolligative egenskaber"),
    ]
    active_group = st.session_state.get("_exam_group_filter", None)
    st.caption("📚 Hop til emne:")
    _SC_ROW = 5
    sc_rows = [_EXAM_SHORTCUTS[i:i+_SC_ROW] for i in range(0, len(_EXAM_SHORTCUTS), _SC_ROW)]
    for ri, row in enumerate(sc_rows):
        cols = st.columns(len(row))
        for col, (sc_label, grp_key) in zip(cols, row):
            with col:
                btn_t = "primary" if active_group == grp_key else "secondary"
                if st.button(sc_label, key=f"exam_sc_{ri}_{sc_label}", use_container_width=True, type=btn_t):
                    st.session_state["_exam_group_filter"] = grp_key
                    st.rerun()
    st.markdown("---")

    name_to_task = {t[2]: t for t in _EXAM_TASKS}
    btn_counter = 0

    for group_label, task_names in groups.items():
        if active_group and group_label != active_group:
            btn_counter += sum(1 for n in task_names if n in name_to_task)
            continue
        tasks_in_group = [name_to_task[n] for n in task_names if n in name_to_task]
        if exam_q:
            q_low = exam_q.lower()
            tasks_in_group = [
                t for t in tasks_in_group
                if q_low in t[0].lower() or q_low in t[1].lower() or q_low in t[2].lower()
            ]
        if not tasks_in_group:
            continue

        with st.expander(group_label, expanded=True):
            for opgave, tip, beregner, page, tab in tasks_in_group:
                col_text, col_btn = st.columns([5, 1])
                with col_text:
                    st.markdown(f"**{opgave}**")
                    st.caption(f"→ {tip}")
                with col_btn:
                    if st.button("Åbn →", key=f"exam_nav_{btn_counter}", use_container_width=True):
                        page_label = PAGE_QUERY_TO_LABEL.get(page, "🏠 Fundamentals")
                        st.session_state["_pending_page"] = page_label
                        st.query_params["page"] = page
                        if tab:
                            st.session_state[f"nav_{page.replace('-', '_')}"] = tab
                        st.rerun()
                btn_counter += 1
                st.markdown("---")

    st.caption("Tip: Søg i sidepanelet for endnu hurtigere navigation.")


def format_formula_with_subscripts(formula: str) -> str:
    """
    Convert a chemical formula string to HTML with subscript formatting.
    E.g., "H2O" becomes "H<sub>2</sub>O"
    
    Args:
        formula: Chemical formula string (e.g., "H2O", "Fe2(SO4)3")
    
    Returns:
        HTML string with subscripts
    """
    import re
    
    # Replace numbers with subscript HTML tags
    result = ""
    i = 0
    while i < len(formula):
        char = formula[i]
        
        if char.isdigit():
            # Collect all consecutive digits
            num_str = ""
            while i < len(formula) and formula[i].isdigit():
                num_str += formula[i]
                i += 1
            result += f"<sub>{num_str}</sub>"
        else:
            result += char
            i += 1
    
    return result


def format_chemical_notation_html(text: str) -> str:
    """
    Format chemical notation to HTML with subscripts and superscripts.

    Supported input styles:
    - Subscripts: H2O -> H<sub>2</sub>O
    - Explicit superscripts: Fe^2+, Fe_2+, SO4^- -> Fe<sup>2+</sup>, SO<sub>4</sub><sup>-</sup>
    """
    import html
    import re
    from calculators.redox_balance import _split_formula_and_charge

    def format_species(species_text: str) -> str:
        species_text = species_text.strip()
        if not species_text:
            return ""

        try:
            formula_part, charge_value = _split_formula_and_charge(species_text)
        except Exception:
            formula_part, charge_value = species_text, 0

        charge_sign = ""
        charge_mag = ""
        if charge_value != 0:
            charge_sign = "+" if charge_value > 0 else "-"
            abs_charge = abs(int(charge_value))
            charge_mag = "" if abs_charge == 1 else str(abs_charge)

        result = ""
        i = 0
        while i < len(formula_part):
            char = formula_part[i]
            if char.isdigit() and i > 0 and (formula_part[i - 1].isalpha() or formula_part[i - 1] in ")]}"):
                digits = ""
                while i < len(formula_part) and formula_part[i].isdigit():
                    digits += formula_part[i]
                    i += 1
                result += f"<sub>{digits}</sub>"
                continue

            result += html.escape(char)
            i += 1

        if charge_sign:
            sup_content = f"{charge_mag}{charge_sign}" if charge_mag else charge_sign
            result += f"<sup>{sup_content}</sup>"

        return result

    tokens = re.split(r"(\s*(?:->|=|→)\s*|\s+\+\s+)", text)
    rendered = ""

    for token in tokens:
        if not token:
            continue
        if re.fullmatch(r"\s*(?:->|=|→)\s*", token):
            rendered += " → "
            continue
        if re.fullmatch(r"\s+\+\s+", token):
            rendered += " + "
            continue

        term = token.strip()
        coeff_match = re.match(r"^(\d+)\s+(.+)$", term)
        if coeff_match:
            coeff, species = coeff_match.groups()
            rendered += f"{html.escape(coeff)} {format_species(species)}"
        else:
            rendered += format_species(term)

    return rendered


def format_chemical_notation_unicode(text: str) -> str:
    """Format chemical notation to plain unicode (for tables/dataframes)."""
    import html
    import re

    sub_map = str.maketrans({
        "0": "₀", "1": "₁", "2": "₂", "3": "₃", "4": "₄",
        "5": "₅", "6": "₆", "7": "₇", "8": "₈", "9": "₉",
        "+": "₊", "-": "₋",
    })
    sup_map = str.maketrans({
        "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴",
        "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹",
        "+": "⁺", "-": "⁻",
    })

    html_text = format_chemical_notation_html(text)

    def repl_sub(match):
        return match.group(1).translate(sub_map)

    def repl_sup(match):
        return match.group(1).translate(sup_map)

    out = re.sub(r"<sub>(.*?)</sub>", repl_sub, html_text)
    out = re.sub(r"<sup>(.*?)</sup>", repl_sup, out)
    return html.unescape(out)


def format_electron_configuration_html(config: str) -> str:
    """Format electron configuration as HTML with superscript occupancies."""
    import html
    import re

    tokens = [token.strip() for token in config.split() if token.strip()]
    rendered_tokens = []

    for token in tokens:
        orbital_match = re.fullmatch(r"(\d[spdf])(\d+)", token)
        if orbital_match:
            orbital = html.escape(orbital_match.group(1))
            occupancy = html.escape(orbital_match.group(2))
            rendered_tokens.append(f"{orbital}<sup>{occupancy}</sup>")
        else:
            rendered_tokens.append(html.escape(token))

    return " ".join(rendered_tokens)


def format_electron_configuration_grouped_html(config_grouped: str) -> str:
    """Format grouped shell-sorted electron configuration with line breaks and superscripts."""
    lines = [line.strip() for line in config_grouped.splitlines() if line.strip()]
    return "<br>".join(format_electron_configuration_html(line) for line in lines)

def show_molar_mass_page():
    """Display atom-focused calculators (molar mass + electron configuration)."""
    st.title("⚖️ Atoms & Molar Mass")
    st.markdown("---")

    subpage_labels = [
        "⚖️ Molar Mass",
        "🔬 Empirisk formel",
        "⚛️ Elektronkonfiguration og atomradius",
        "🧭 Interaktivt periodisk system",
        "🧷 Lewis-struktur",
        "🔋 Ionization Energy",
        "⚗️ Formel ladning",
    ]

    subpage_to_query = {
        "⚖️ Molar Mass": "molar",
        "🔬 Empirisk formel": "empirisk",
        "⚛️ Elektronkonfiguration og atomradius": "electron",
        "🧭 Interaktivt periodisk system": "periodic",
        "🧷 Lewis-struktur": "lewis",
        "🔋 Ionization Energy": "ionization",
        "⚗️ Formel ladning": "formel-ladning",
    }
    query_to_subpage = {value: key for key, value in subpage_to_query.items()}

    # Keep selected atoms subpage stable across full-page GET submissions.
    query_subpage_raw = st.query_params.get("atoms_tab")
    if isinstance(query_subpage_raw, list):
        query_subpage_raw = query_subpage_raw[0] if query_subpage_raw else None
    query_subpage = str(query_subpage_raw).strip() if query_subpage_raw else ""
    if "nav_atoms_molar" in st.session_state:
        _nav_target = st.session_state.pop("nav_atoms_molar")
        if _nav_target in subpage_labels:
            st.session_state["atoms_subpage"] = _nav_target
    if "atoms_subpage" not in st.session_state and query_subpage in query_to_subpage:
        st.session_state["atoms_subpage"] = query_to_subpage[query_subpage]

    st.markdown(
        """
<style>
.st-key-atoms_subpage label[data-testid="stWidgetLabel"] {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    border: 0;
}

.st-key-atoms_subpage [data-testid="stRadio"] div[role="radiogroup"] {
    display: flex;
    flex-wrap: wrap;
    gap: 0.35rem;
    border-bottom: 1px solid #e2e8f0;
    margin-bottom: 0.8rem;
}

.st-key-atoms_subpage [data-testid="stRadio"] label[data-baseweb="radio"] {
    margin: 0;
    padding: 0.35rem 0.05rem 0.55rem 0.05rem;
    border-bottom: 2px solid transparent;
    background: transparent;
    min-height: 0;
}

/* Hide the built-in radio circle so the control looks like tabs. */
.st-key-atoms_subpage [data-testid="stRadio"] label[data-baseweb="radio"] > div:first-child {
    display: none !important;
}

.st-key-atoms_subpage [data-testid="stRadio"] label[data-baseweb="radio"] p {
    margin: 0;
    font-size: 1.02rem;
    color: #0f172a;
}

.st-key-atoms_subpage [data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) {
    border-bottom-color: #ff4b4b;
}

.st-key-atoms_subpage [data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) p {
    color: #ff4b4b;
    font-weight: 600;
}
</style>
        """,
        unsafe_allow_html=True,
    )

    active_subpage = st.radio(
        "AtomsSubpageNav",
        subpage_labels,
        key="atoms_subpage",
        horizontal=True,
        label_visibility="collapsed",
    )

    selected_subpage_query = subpage_to_query[active_subpage]
    if st.query_params.get("atoms_tab") != selected_subpage_query:
        st.query_params["atoms_tab"] = selected_subpage_query

    if active_subpage == "⚖️ Molar Mass":
        st.markdown("### Enter Chemical Formula")

        col1, col2 = st.columns([3, 1])

        with col1:
            formula = st.text_input(
                "Chemical Formula:",
                placeholder="e.g., C6H12O6, Fe2(SO4)3, Ca(OH)2",
                help="Enter a chemical formula. Supports parentheses and subscripts."
            )

        with col2:
            st.markdown("### Examples:")
            st.markdown("- **H₂O** (water)")
            st.markdown("- **C₆H₁₂O₆** (glucose)")
            st.markdown("- **Fe₂(SO₄)₃** (iron sulfate)")
            st.markdown("- **Ca(OH)₂** (calcium hydroxide)")

        if st.button("Calculate Molar Mass", type="primary"):
            if not formula:
                st.error("Please enter a chemical formula.")
            else:
                formatted_formula = format_formula_with_subscripts(formula)
                st.markdown(f"**Formula read as:** {formatted_formula}", unsafe_allow_html=True)

                try:
                    with st.spinner("Calculating..."):
                        result, steps, metadata = calculate_molar_mass_with_steps(formula)

                    st.success(f"✅ **Molar Mass: {result:.3f} g/mol**")

                    if 'composition' in metadata:
                        st.markdown("### Elemental Composition")
                        composition_table = format_composition_table(metadata['composition'])
                        st.markdown(composition_table)

                    with st.expander("🔍 Vis trin", expanded=False):
                        for step in steps:
                            st.markdown(step)

                    if 'element_counts' in metadata:
                        st.markdown("### Element Counts")
                        element_counts_df = pd.DataFrame([
                            {"Element": element, "Count": count}
                            for element, count in metadata['element_counts'].items()
                        ])
                        st.dataframe(element_counts_df, use_container_width=True)

                except Exception as e:
                    st.error(f"❌ **Fejl**: {str(e)}")
                    st.info("Please check your formula and try again.")

    if active_subpage == "⚛️ Elektronkonfiguration og atomradius":
        st.markdown("### Elektronkonfiguration & Bindingskarakter")
        ec_mode = st.radio(
            "Tilstand:",
            ["⚛️ Enkelt atom / ion", "🔗 Bindingskarakter (ionisk/kovalent)"],
            horizontal=True,
            key="ec_mode",
        )
        st.markdown("---")

        if ec_mode == "🔗 Bindingskarakter (ionisk/kovalent)":
            _show_bindingskarakter_section()

        if ec_mode == "⚛️ Enkelt atom / ion":
            st.markdown("Angiv symbol eller atomnummer med valgfri ladning.")
            col1, col2 = st.columns([3, 1])
            with col1:
                species_input = st.text_input(
                    "Input (symbol eller atomnummer):",
                    placeholder="e.g., Na, O2-, O^2-, Fe3+, Fe2+, Cl-, Br1-, Cu+, Cr2+",
                    help="Understøtter symbol/atomnummer + ladning som fx 2+, +2, 2-, -2."
                )
                show_all_orbitals = st.checkbox(
                    "Vis alle skaller (inkl. kerneskaller)",
                    value=True,
                )
            with col2:
                st.markdown("### Eksempler:")
                st.markdown("- **Na**")
                st.markdown("- **O2-**")
                st.markdown("- **Fe3+**")
                st.markdown("- **Fe2+**")
                st.markdown("- **Cr2+**")

            if st.button("Beregn elektronkonfiguration", type="primary"):
                if not species_input.strip():
                    st.error("Indtast et grundstof (symbol eller atomnummer).")
                else:
                    try:
                        with st.spinner("Beregner elektronkonfiguration..."):
                            result, steps, metadata = calculate_electron_configuration_with_steps(
                                species_input,
                                orbital_view="all" if show_all_orbitals else "valence",
                            )

                        st.success("✅ Beregning gennemført")
                        st.markdown(
                            f"**Symbol:** {metadata['symbol']}  " +
                            f"**Z:** {metadata['Z']}  " +
                            f"**Ladning:** {metadata['charge']:+d}  " +
                            f"**Elektroner:** {metadata['electrons']}"
                        )

                        st.markdown("### Elektronkonfiguration")
                        st.caption("Aufbau = orbitalernes energirækkefølge. Skal-sorteret = organiseret efter hovedskal (n).")
                        st.markdown("**Auffyldningsrækkefølge (Aufbau):**")
                        st.markdown(format_electron_configuration_html(result['aufbau']), unsafe_allow_html=True)
                        st.markdown("**Skal-sorteret elektronkonfiguration:**")
                        st.markdown(
                            format_electron_configuration_grouped_html(result['shell_sorted_grouped']),
                            unsafe_allow_html=True,
                        )
                        st.markdown("**Ædelgasnotation:**")
                        st.markdown(format_electron_configuration_html(result['noble']), unsafe_allow_html=True)

                        radius = result.get("radius") or {}
                        radius_value = radius.get("value")
                        if radius_value is None:
                            radius_note = radius.get("note", "ingen data")
                            st.markdown(f"**Radius:** ukendt ({radius_note})")
                        else:
                            if metadata["charge"] == 0:
                                radius_type = "atomradius (neutral)"
                            elif metadata["charge"] > 0:
                                radius_type = "ionradius (kation)"
                            else:
                                radius_type = "ionradius (anion)"
                            st.markdown(f"**Radius:** {radius_value:.3g} {radius.get('unit', 'pm')} ({radius_type})")

                        st.markdown(f"**Elektroner i yderste skal:** {metadata['outer_shell_electrons']}")

                        st.caption(f"Maskinlæsbar (long): {result['long']}")
                        st.caption(f"Maskinlæsbar (aufbau): {result['aufbau']}")
                        st.caption(f"Maskinlæsbar (shell sorted): {result['shell_sorted']}")
                        st.caption(f"Maskinlæsbar (noble): {result['noble']}")
                        if radius.get("source"):
                            st.caption(f"Radius-kilde: {radius['source']}")

                        st.markdown("**Orbitalfordeling (Hund + Pauli):**")
                        distribution_rows = result.get("orbital_distribution") or []
                        if distribution_rows:
                            for row in distribution_rows:
                                st.text(row["text"])

                            quantum_rows = []
                            for row in distribution_rows:
                                for orbital in row.get("orbitals", []):
                                    occupancy = orbital.get("occupancy")
                                    quantum_rows.append(
                                        {
                                            "Underskal": row.get("subshell_label"),
                                            "Orbital": orbital.get("name"),
                                            "n": orbital.get("n"),
                                            "l": orbital.get("l"),
                                            "m": orbital.get("m"),
                                            "Besættelse": occupancy if occupancy else "tom",
                                        }
                                    )

                            st.markdown("**Kvantetal (n, l, m):**")
                            st.dataframe(pd.DataFrame(quantum_rows), hide_index=True, use_container_width=True)
                            st.caption(
                                "n = hovedkvantetal (skal/energiniveau), "
                                "l = bikvantetal (underskal: s=0, p=1, d=2, f=3), "
                                "m = magnetisk kvantetal (orbitalens orientering, fra -l til +l)."
                            )
                        else:
                            st.text("Ingen orbitalfordeling at vise for valgt visning.")

                        with st.expander("🔍 Vis trin", expanded=False):
                            for step in steps:
                                st.markdown(step)
                    except Exception as e:
                        st.error(f"❌ **Fejl**: {str(e)}")

    if active_subpage == "🧭 Interaktivt periodisk system":
        render_periodic_table_tab()

    if active_subpage == "🧷 Lewis-struktur":
        st.markdown("### Lewis-struktur")
        st.markdown("Indtast en molekylformel og tegn en Lewis-struktur.")
        st.info(
            "**Skriv ioner sådan:** brug fx `CO3^2-`, `NO3-`, `NH4+` eller `SO4^2-`. "
            "Tal i formlen bliver sænkede (subscript), og ladning bliver hævet (superscript)."
        )

        molecule_input = st.text_input(
            "Molekyle/ion:",
            placeholder="fx H2O, CO2, NH3, CH4, SO2, NO3-, NH4+",
            key="lewis_input",
        )

        if molecule_input.strip():
            try:
                parsed_preview = parse_species_input(molecule_input.strip())
                charge = parsed_preview.charge
                if charge == 0:
                    normalized_input = parsed_preview.formula
                else:
                    sign = "+" if charge > 0 else "-"
                    magnitude = "" if abs(charge) == 1 else str(abs(charge))
                    normalized_input = f"{parsed_preview.formula}^{magnitude}{sign}"

                formatted_preview = format_chemical_notation_html(normalized_input)
                st.markdown(
                    f"<div style='padding:0.45rem 0.65rem;border:1px solid #e2e8f0;border-radius:0.5rem;'>"
                    f"<strong>Læst som:</strong> {formatted_preview}</div>",
                    unsafe_allow_html=True,
                )
            except LewisStructureError:
                st.caption("Input kunne ikke fortolkes endnu. Tjek formel og ladning.")

        if st.button("Tegn Lewis-struktur", type="primary", key="lewis_draw"):
            if not molecule_input.strip():
                st.error("Indtast en molekylformel for at tegne en Lewis-struktur.")
            else:
                st.session_state["lewis_last_input"] = molecule_input.strip()
                try:
                    structure, lewis_steps = calculate_lewis_structure_with_steps(molecule_input.strip())
                    st.session_state["lewis_last_structure"] = structure
                    st.session_state["lewis_last_steps"] = lewis_steps
                    st.session_state.pop("lewis_last_error", None)
                except LewisStructureError as e:
                    st.session_state["lewis_last_error"] = str(e)
                    st.session_state.pop("lewis_last_structure", None)
                    st.session_state.pop("lewis_last_steps", None)
                except Exception as e:
                    st.session_state["lewis_last_error"] = f"Uventet fejl: {str(e)}"
                    st.session_state.pop("lewis_last_structure", None)
                    st.session_state.pop("lewis_last_steps", None)

        st.markdown("#### Output")
        last_error = st.session_state.get("lewis_last_error")
        last_structure = st.session_state.get("lewis_last_structure")

        if last_error:
            st.error(last_error)
        elif last_structure is not None:
            st.success("Lewis-struktur genereret.")

            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Valenselektroner", last_structure.total_valence_electrons)
            with c2:
                st.metric("Samlet ladning", f"{last_structure.parsed.charge:+d}")
            with c3:
                st.metric("Resonansformer", last_structure.resonance_forms)

            st.caption(
                "**Resonansformer** er alternative, gyldige Lewis-strukturer med samme atomplacering, "
                "men forskellig placering af pi-bindinger/lone pairs. Den reelle struktur er et hybrid af disse."
            )

            st.markdown(render_lewis_structure_svg(last_structure), unsafe_allow_html=True)

            if last_structure.resonance_forms > 1:
                max_forms_to_show = 12
                if last_structure.resonance_forms <= max_forms_to_show:
                    with st.expander("Vis alle resonansformer", expanded=False):
                        variants = generate_resonance_structures(last_structure, max_forms=max_forms_to_show)
                        for i, variant in enumerate(variants, start=1):
                            st.markdown(f"**Resonansform {i}**")
                            st.markdown(render_lewis_structure_svg(variant), unsafe_allow_html=True)
                else:
                    st.info(
                        f"Der er {last_structure.resonance_forms} resonansformer. "
                        "Det er for mange at vise overskueligt i UI."
                    )

            with st.expander("Detaljeret strukturdata", expanded=False):
                st.code(render_lewis_structure_text(last_structure), language="text")

            with st.expander("Trinvis beregning", expanded=False):
                for step in st.session_state.get("lewis_last_steps", []):
                    st.markdown(f"- {step}")
        else:
            st.info("Ingen struktur tegnet endnu.")
    if active_subpage == "🔋 Ionization Energy":
        # Render the Ionization Energy lookup UI (uses shared periodic table data)
        try:
            render_ionization_energy_tab()
        except Exception as e:
            st.error(f"Could not render Ionization Energy tab: {e}")

    if active_subpage == "🔬 Empirisk formel":
        _show_empirisk_formel_tab()

    if active_subpage == "⚗️ Formel ladning":
        _show_formel_ladning_tab()


def _show_bindingskarakter_section():
    """Bindingskarakter: ΔEN, % ionisk karakter og rangering af forbindelser."""
    import re
    import math

    # Pauling elektronegativity (kilde: standard tabel)
    _EN = {
        "H": 2.20, "Li": 0.98, "Be": 1.57, "B": 2.04, "C": 2.55,
        "N": 3.04, "O": 3.44, "F": 3.98, "Na": 0.93, "Mg": 1.31,
        "Al": 1.61, "Si": 1.90, "P": 2.19, "S": 2.58, "Cl": 3.16,
        "K": 0.82, "Ca": 1.00, "Sc": 1.36, "Ti": 1.54, "V": 1.63,
        "Cr": 1.66, "Mn": 1.55, "Fe": 1.83, "Co": 1.88, "Ni": 1.91,
        "Cu": 1.90, "Zn": 1.65, "Ga": 1.81, "Ge": 2.01, "As": 2.18,
        "Se": 2.55, "Br": 2.96, "Rb": 0.82, "Sr": 0.95, "Y": 1.22,
        "Zr": 1.33, "Ag": 1.93, "Cd": 1.69, "Sn": 1.96, "Sb": 2.05,
        "Te": 2.10, "I": 2.66, "Cs": 0.79, "Ba": 0.89, "La": 1.10,
        "Hg": 2.00, "Tl": 1.62, "Pb": 2.33, "Bi": 2.02,
    }

    def _parse_binary(formula: str):
        """Returnér (el1, el2) fra en binær forbindelsesformel, fx 'NaF' → ('Na','F')."""
        formula = formula.strip()
        # Match alle grundstofsymboler (stor + evt. lille)
        tokens = re.findall(r"[A-Z][a-z]?", formula)
        unique = list(dict.fromkeys(tokens))  # bevar rækkefølge, fjern dubletter
        if len(unique) == 1:
            return unique[0], unique[0]   # homodiatomisk (F2, N2 …)
        if len(unique) == 2:
            return unique[0], unique[1]
        return None, None

    def _bond_type(den: float) -> str:
        if den < 0.4:
            return "Upolar kovalent"
        if den < 1.7:
            return "Polar kovalent"
        return "Ionisk"

    def _pct_ionic(den: float) -> float:
        return (1 - math.exp(-0.25 * den ** 2)) * 100

    st.markdown("### 🔗 Bindingskarakter (ionisk/kovalent)")
    with st.expander("ℹ️ Teori", expanded=False):
        st.markdown(
            "**Elektronegativity-forskel (ΔEN)** bestemmer bindingskarakteren:\n\n"
            "| ΔEN | Bindingstype |\n"
            "|-----|-------------|\n"
            "| < 0,4 | Upolar kovalent |\n"
            "| 0,4 – 1,7 | Polar kovalent |\n"
            "| > 1,7 | Ionisk |\n\n"
            "**% ionisk karakter** (Paulings formel):\n\n"
            "% = (1 − e^(−0,25 · ΔEN²)) × 100\n\n"
            "**Rangering:** Større ΔEN → større ionisk karakter → mere ionisk."
        )

    # ── Tilføj forbindelser ───────────────────────────────────────────────────
    if "bc_compounds" not in st.session_state:
        st.session_state["bc_compounds"] = []

    st.caption("Tilføj forbindelser/bindinger at sammenligne (fx NaF, BaO, F2, NO):")
    c1, c2, c3 = st.columns([2, 2, 1])
    formula_in = c1.text_input(
        "Forbindelsesformel:",
        placeholder="fx NaF, BaS, F2, NO, HCl",
        key="bc_formula",
    )
    label_in = c2.text_input(
        "Valgfrit label (fx 'A'):",
        placeholder="lades tom → brug formlen",
        key="bc_label",
    )
    c3.markdown("<br>", unsafe_allow_html=True)
    if c3.button("➕ Tilføj", key="bc_add", use_container_width=True):
        if formula_in.strip():
            el1, el2 = _parse_binary(formula_in.strip())
            if el1 and el2:
                en1 = _EN.get(el1)
                en2 = _EN.get(el2)
                if en1 is None or en2 is None:
                    missing = el1 if en1 is None else el2
                    st.error(f"Elektronegativity for **{missing}** kendes ikke i databasen.")
                else:
                    lbl = label_in.strip() or formula_in.strip()
                    den = abs(en1 - en2)
                    st.session_state["bc_compounds"].append({
                        "label": lbl,
                        "formula": formula_in.strip(),
                        "el1": el1, "el2": el2,
                        "en1": en1, "en2": en2,
                        "den": den,
                        "pct": _pct_ionic(den),
                        "type": _bond_type(den),
                    })
                    st.rerun()
            else:
                st.error("Kunne ikke parse forbindelsen – skriv fx NaF, BaO, F2, NO.")

    compounds = st.session_state["bc_compounds"]

    if compounds:
        st.markdown("#### Resultater")
        hdr = st.columns([1.5, 1, 1, 1, 1, 1.5, 1, 0.6])
        for col, h in zip(hdr, ["Forbindelse", "El₁", "EN₁", "El₂", "EN₂", "ΔEN", "% ionisk", ""]):
            col.markdown(f"**{h}**")

        for i, c in enumerate(compounds):
            row = st.columns([1.5, 1, 1, 1, 1, 1.5, 1, 0.6])
            row[0].markdown(f"**{c['label']}**")
            row[1].markdown(c["el1"])
            row[2].markdown(f"{c['en1']:.2f}")
            row[3].markdown(c["el2"])
            row[4].markdown(f"{c['en2']:.2f}")
            row[5].markdown(f"**{c['den']:.2f}** – *{c['type']}*")
            row[6].markdown(f"{c['pct']:.1f}%")
            if row[7].button("✕", key=f"bc_del_{i}", use_container_width=True):
                st.session_state["bc_compounds"].pop(i)
                st.rerun()

        st.markdown("---")
        # Rangering: faldende ionisk karakter
        ranked = sorted(compounds, key=lambda x: x["den"], reverse=True)
        st.markdown("#### Rangering – faldende ionisk karakter")
        medals = ["🥇", "🥈", "🥉"] + [f"{n}." for n in range(4, 20)]
        rank_parts = []
        prev_den = None
        rank_idx = 0
        for c in ranked:
            if prev_den is not None and abs(c["den"] - prev_den) < 0.001:
                pass  # delt plads
            else:
                rank_idx += 1
            prev_den = c["den"]
            rank_parts.append(f"**{c['label']}** (ΔEN={c['den']:.2f}, {c['pct']:.0f}% ionisk)")

        st.markdown("  >  ".join(rank_parts))

        st.markdown("#### Individuel analyse")
        for c in ranked:
            if c["type"] == "Ionisk":
                col_badge = "🔴 Ionisk"
            elif c["type"] == "Polar kovalent":
                col_badge = "🟡 Polar kovalent"
            else:
                col_badge = "🟢 Upolar kovalent"
            st.markdown(
                f"**{c['label']}** ({c['el1']}–{c['el2']}):  "
                f"ΔEN = |{c['en1']:.2f} − {c['en2']:.2f}| = **{c['den']:.2f}**  |  "
                f"{c['pct']:.1f}% ionisk  |  {col_badge}"
            )

        if st.button("🗑 Ryd alle forbindelser", key="bc_clr"):
            st.session_state["bc_compounds"] = []
            st.rerun()
    else:
        st.info("Tilføj forbindelser ovenfor for at beregne og sammenligne bindingskarakter.")


def _show_formel_ladning_tab():
    """Beregn formel ladning (FC) og rangér Lewis-strukturer."""

    _VALENCE = {
        "H": 1, "B": 3, "C": 4, "N": 5, "O": 6, "F": 7,
        "Na": 1, "Mg": 2, "Al": 3, "Si": 4, "P": 5, "S": 6, "Cl": 7,
        "K": 1, "Ca": 2, "Br": 7, "I": 7, "He": 2, "Ne": 8, "Ar": 8, "Xe": 8,
    }

    def _fc(el, bonds, lp):
        return _VALENCE.get(el, 0) - (lp * 2) - bonds

    def _fc_badge(fc):
        if fc == 0:
            return "🟢 **0**"
        if abs(fc) == 1:
            return f"🟡 **{fc:+d}**"
        return f"🔴 **{fc:+d}**"

    ELEMENTS = sorted(_VALENCE.keys())

    st.markdown("### ⚗️ Formel ladning")
    with st.expander("ℹ️ Formel og regler", expanded=False):
        st.markdown(
            "**FC = V − L − ½·B**\n\n"
            "| Symbol | Forklaring |\n"
            "|--------|------------|\n"
            "| V | Valenselektroner (neutralt atom) |\n"
            "| L | Ikke-bindende elektroner = lone pairs × 2 |\n"
            "| B | Bindende elektroner = antal bindinger × 2 |\n\n"
            "**Rangering af strukturer (mest → mindst sandsynlig):**\n"
            "1. Alle FC = 0 er bedst\n"
            "2. Minimér Σ|FC| (sum af absolutte formelle ladninger)\n"
            "3. Negativ FC bør sidde på det mest elektronegative atom\n"
            "4. Undgå naboatomer med samme fortegn på FC\n\n"
            "🟢 FC = 0 &nbsp; 🟡 |FC| = 1 &nbsp; 🔴 |FC| ≥ 2"
        )

    mode = st.radio(
        "Tilstand:",
        ["🔬 Enkelt struktur", "📊 Sammenlign strukturer (A–D)"],
        horizontal=True,
        key="fc_mode",
    )
    st.markdown("---")

    # ── Enkelt struktur ───────────────────────────────────────────────────────
    if mode == "🔬 Enkelt struktur":
        if "fc_atoms" not in st.session_state:
            st.session_state["fc_atoms"] = []

        st.caption("Tilføj hvert atom i din struktur:")
        c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
        el = c1.selectbox("Grundstof:", ELEMENTS, key="fc_el")
        bonds = c2.number_input(
            "Bindinger:", min_value=0, max_value=8, value=1, step=1, key="fc_bonds",
            help="Enkelt binding = 1, dobbelt = 2, tripel = 3",
        )
        lp = c3.number_input(
            "Lone pairs:", min_value=0, max_value=6, value=0, step=1, key="fc_lp",
            help="Antal frie elektronpar",
        )
        c4.markdown("<br>", unsafe_allow_html=True)
        if c4.button("➕ Tilføj", key="fc_add", use_container_width=True):
            st.session_state["fc_atoms"].append({"el": el, "bonds": bonds, "lp": lp})
            st.rerun()

        atoms = st.session_state["fc_atoms"]
        if atoms:
            st.markdown("#### Resultat")
            hdr = st.columns([1.5, 0.8, 1, 1, 0.8, 1, 0.6])
            for col, h in zip(hdr, ["Atom", "V", "Bindinger", "Lone pairs", "L", "FC", ""]):
                col.markdown(f"**{h}**")

            total_fc = 0
            for i, a in enumerate(atoms):
                fc = _fc(a["el"], a["bonds"], a["lp"])
                total_fc += fc
                V = _VALENCE.get(a["el"], "?")
                L = a["lp"] * 2
                row = st.columns([1.5, 0.8, 1, 1, 0.8, 1, 0.6])
                row[0].markdown(f"**{a['el']}**")
                row[1].markdown(str(V))
                row[2].markdown(str(a["bonds"]))
                row[3].markdown(str(a["lp"]))
                row[4].markdown(str(L))
                row[5].markdown(_fc_badge(fc))
                if row[6].button("✕", key=f"fc_del_{i}", use_container_width=True):
                    st.session_state["fc_atoms"].pop(i)
                    st.rerun()

            st.markdown("---")
            sum_abs = sum(abs(_fc(a["el"], a["bonds"], a["lp"])) for a in atoms)

            res_col, clr_col = st.columns([5, 1])
            if total_fc == 0:
                res_col.success(f"Total ladning: **{total_fc:+d}** (neutral) &nbsp;|&nbsp; Σ|FC| = {sum_abs}")
            else:
                res_col.warning(f"Total ladning: **{total_fc:+d}** &nbsp;|&nbsp; Σ|FC| = {sum_abs}")
            if clr_col.button("🗑 Ryd", key="fc_clr", use_container_width=True):
                st.session_state["fc_atoms"] = []
                st.rerun()

            if sum_abs == 0:
                st.success("✅ Σ|FC| = 0 — alle atomer har formel ladning 0. Mest sandsynlige Lewis-struktur.")
            elif sum_abs <= 2:
                st.info(f"ℹ️ Σ|FC| = {sum_abs} — lav formal ladning, rimelig sandsynlig struktur.")
            else:
                st.warning(f"⚠️ Σ|FC| = {sum_abs} — høj samlet ladning, usandsynlig struktur.")

            with st.expander("📐 Vis beregning", expanded=False):
                for a in atoms:
                    fc = _fc(a["el"], a["bonds"], a["lp"])
                    V = _VALENCE.get(a["el"], "?")
                    L = a["lp"] * 2
                    B = a["bonds"] * 2
                    st.markdown(
                        f"**{a['el']}:** FC = {V} − {L} − {B}÷2 = {V} − {L} − {a['bonds']} = **{fc:+d}**"
                    )
        else:
            st.info("Tilføj atomer ovenfor for at beregne formelle ladninger.")

    # ── Sammenlign strukturer ─────────────────────────────────────────────────
    else:
        _SK = ["A", "B", "C", "D"]
        for k in _SK:
            if f"fc_s_{k}" not in st.session_state:
                st.session_state[f"fc_s_{k}"] = []

        st.markdown("#### Definer strukturer")
        active = st.radio("Redigér struktur:", _SK, horizontal=True, key="fc_active")
        sk = f"fc_s_{active}"

        c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
        el2 = c1.selectbox("Grundstof:", ELEMENTS, key="fc_el2")
        bonds2 = c2.number_input(
            "Bindinger:", min_value=0, max_value=8, value=1, step=1, key="fc_bonds2",
        )
        lp2 = c3.number_input("Lone pairs:", min_value=0, max_value=6, value=0, step=1, key="fc_lp2")
        c4.markdown("<br>", unsafe_allow_html=True)
        if c4.button("➕ Tilføj", key="fc_add2", use_container_width=True):
            st.session_state[sk].append({"el": el2, "bonds": bonds2, "lp": lp2})
            st.rerun()

        atoms_cur = st.session_state[sk]
        if atoms_cur:
            hdr2 = st.columns([1.5, 1, 1, 1, 0.6])
            for col, h in zip(hdr2, ["Atom", "Bindinger", "Lone pairs", "FC", ""]):
                col.markdown(f"**{h}**")
            for i, a in enumerate(atoms_cur):
                fc = _fc(a["el"], a["bonds"], a["lp"])
                row = st.columns([1.5, 1, 1, 1, 0.6])
                row[0].markdown(f"**{a['el']}**")
                row[1].markdown(str(a["bonds"]))
                row[2].markdown(str(a["lp"]))
                row[3].markdown(_fc_badge(fc))
                if row[4].button("✕", key=f"fc_del2_{active}_{i}", use_container_width=True):
                    st.session_state[sk].pop(i)
                    st.rerun()
            if st.button(f"🗑 Ryd struktur {active}", key=f"fc_clr2_{active}"):
                st.session_state[sk] = []
                st.rerun()
        else:
            st.info(f"Ingen atomer i struktur {active} endnu. Tilføj ovenfor.")

        # ── Oversigt + rangering ──────────────────────────────────────────────
        filled = [(k, st.session_state[f"fc_s_{k}"]) for k in _SK if st.session_state[f"fc_s_{k}"]]
        if filled:
            st.markdown("---")
            st.markdown("#### Oversigt")
            for k, atms in filled:
                fcs = [_fc(a["el"], a["bonds"], a["lp"]) for a in atms]
                s_abs = sum(abs(f) for f in fcs)
                tot = sum(fcs)
                parts = ",  ".join(f"{a['el']}({f:+d})" for a, f in zip(atms, fcs))
                st.markdown(f"**Struktur {k}:** {parts} &nbsp; total = {tot:+d}, Σ|FC| = {s_abs}")

        if len(filled) >= 2:
            st.markdown("---")
            st.markdown("#### Rangering (mest → mindst sandsynlig)")

            ranked = []
            for k, atms in filled:
                fcs = [_fc(a["el"], a["bonds"], a["lp"]) for a in atms]
                s_abs = sum(abs(f) for f in fcs)
                n_nz = sum(1 for f in fcs if f != 0)
                ranked.append((s_abs, n_nz, k, atms, fcs))
            ranked.sort(key=lambda x: (x[0], x[1]))

            medals = ["🥇", "🥈", "🥉", "4️⃣"]
            prev_score = None
            for rank, (s_abs, n_nz, k, atms, fcs) in enumerate(ranked):
                medal = medals[rank] if rank < 4 else f"{rank+1}."
                parts = "  |  ".join(f"{a['el']}: {_fc_badge(f)}" for a, f in zip(atms, fcs))
                if s_abs == 0:
                    note = "alle FC = 0 → **bedste struktur**"
                elif prev_score == s_abs:
                    note = f"Σ|FC| = {s_abs} → delt plads"
                else:
                    note = f"Σ|FC| = {s_abs}"
                prev_score = s_abs
                st.markdown(f"{medal} **Struktur {k}** — {note}  \n{parts}")
        elif filled:
            st.info("Tilføj atomer til mindst 2 strukturer for at sammenligne og rangere.")


def _show_empirisk_formel_tab():
    """Empirisk formel og procentsammensætning beregner."""
    import math

    # Grundlæggende atomvægte
    ATOMIC_MASSES: dict[str, float] = {
        "H": 1.008, "He": 4.003, "Li": 6.941, "Be": 9.012, "B": 10.811,
        "C": 12.011, "N": 14.007, "O": 15.999, "F": 18.998, "Ne": 20.180,
        "Na": 22.990, "Mg": 24.305, "Al": 26.982, "Si": 28.086, "P": 30.974,
        "S": 32.065, "Cl": 35.453, "Ar": 39.948, "K": 39.098, "Ca": 40.078,
        "Fe": 55.845, "Cu": 63.546, "Zn": 65.38, "Br": 79.904, "Ag": 107.868,
        "I": 126.904, "Ba": 137.327, "Pb": 207.2,
    }

    st.markdown("### 🔬 Empirisk formel og procentsammensætning")
    st.caption("Find empirisk/molekylær formel fra procentvis sammensætning, eller beregn % fra formel.")

    mode = st.radio(
        "Beregningsretning:",
        ["% sammensætning → Empirisk formel", "Formel → % sammensætning"],
        horizontal=True,
        key="emp_mode",
    )

    if mode == "% sammensætning → Empirisk formel":
        st.markdown("#### Trin 1 – Indtast procentvis massesammensætning")
        st.caption("Summer skal give ~100%. Kan også bruges med absolutte masser (g) fra forbrændingsanalyse.")

        col1, col2 = st.columns(2)
        with col1:
            n_elements = st.number_input("Antal grundstoffer:", min_value=2, max_value=6, value=3, step=1, key="emp_n_el")
            input_type = st.radio("Input-type:", ["Procent (%)", "Masse (g)"], horizontal=True, key="emp_input_type")

        elements: list[tuple[str, float]] = []
        with col2:
            for i in range(int(n_elements)):
                c1, c2 = st.columns(2)
                with c1:
                    sym = st.text_input(f"Element {i+1}:", key=f"emp_sym_{i}", placeholder="fx C")
                with c2:
                    val = st.number_input(
                        "%" if input_type == "Procent (%)" else "g",
                        value=0.0, min_value=0.0, key=f"emp_val_{i}", format="%.4f"
                    )
                if sym.strip():
                    elements.append((sym.strip().capitalize(), val))

        mol_mass_known = st.checkbox("Jeg kender den molekylære molarmasse (find molekylær formel)", key="emp_mm_known")
        mol_mass = None
        if mol_mass_known:
            mol_mass = st.number_input("Molekylær molarmasse (g/mol):", value=180.0, min_value=1.0, key="emp_mm_val")

        if st.button("Beregn empirisk formel", type="primary", key="emp_btn"):
            errors = []
            for sym, val in elements:
                if sym not in ATOMIC_MASSES:
                    errors.append(f"Ukendt grundstof: '{sym}'. Brug kemisk symbol (fx C, H, O, N, S).")
            if not elements:
                errors.append("Ingen grundstoffer angivet.")
            if errors:
                for e in errors:
                    st.error(e)
            else:
                # Convert to moles
                moles = {sym: val / ATOMIC_MASSES[sym] for sym, val in elements if val > 0}
                if not moles:
                    st.error("Alle værdier er 0.")
                else:
                    min_mol = min(moles.values())
                    ratios = {sym: m / min_mol for sym, m in moles.items()}

                    # Find multiplier to make all ratios close to integers
                    def to_int_ratio(r: float, tol: float = 0.05) -> int | None:
                        for mult in range(1, 13):
                            val = r * mult
                            if abs(val - round(val)) < tol * mult:
                                return round(val * mult) if False else round(val)
                        return None

                    best_mult = 1
                    for mult in range(1, 13):
                        scaled = {s: r * mult for s, r in ratios.items()}
                        if all(abs(v - round(v)) < 0.08 for v in scaled.values()):
                            best_mult = mult
                            break

                    int_ratios = {sym: round(r * best_mult) for sym, r in ratios.items()}
                    empirical = "".join(
                        f"{sym}{n if n > 1 else ''}" for sym, n in int_ratios.items()
                    )

                    # Empirical molar mass
                    M_emp = sum(ATOMIC_MASSES[sym] * n for sym, n in int_ratios.items())

                    st.success(f"**Empirisk formel: {empirical}** (M_emp = {M_emp:.3f} g/mol)")

                    # Steps
                    st.markdown("**Trin-for-trin:**")
                    unit = "%" if input_type == "Procent (%)" else "g"
                    for sym, val in elements:
                        if val > 0:
                            m = val / ATOMIC_MASSES[sym]
                            st.markdown(
                                f"- {sym}: {val:.4g} {unit} ÷ {ATOMIC_MASSES[sym]:.3f} g/mol = **{m:.4f} mol**"
                            )
                    st.markdown(f"- Mindste moltal: **{min_mol:.4f} mol** ({min(moles, key=moles.get)})")
                    for sym, r in ratios.items():
                        st.markdown(f"- {sym}: {r:.4f} × {best_mult} ≈ **{int_ratios[sym]}**")
                    st.markdown(f"→ Empirisk formel: **{empirical}**")

                    if mol_mass_known and mol_mass:
                        n_mol = mol_mass / M_emp
                        n_int = round(n_mol)
                        molecular = "".join(
                            f"{sym}{int_ratios[sym]*n_int if int_ratios[sym]*n_int > 1 else ''}"
                            for sym in int_ratios
                        )
                        st.info(
                            f"**Molekylær formel:** n = {mol_mass:.2f} / {M_emp:.3f} ≈ **{n_int}**  \n"
                            f"→ Molekylær formel: **{molecular}** (M = {M_emp * n_int:.3f} g/mol)"
                        )

                    st.markdown("---")
                    st.caption(
                        "💡 Eksempel: 40,0% C, 6,7% H, 53,3% O → "
                        "C: 40,0/12,011=3,33, H: 6,7/1,008=6,65, O: 53,3/15,999=3,33 → "
                        "ratio 1:2:1 → **CH₂O** (formaldehyd/glucose-serie)"
                    )

    else:  # Formel → % sammensætning
        st.markdown("#### Formel → Procentvis massesammensætning")
        formula_input = st.text_input(
            "Kemisk formel:", placeholder="fx C6H12O6, Fe2O3, Ca(OH)2", key="emp_formula_pct"
        )
        if st.button("Beregn % sammensætning", type="primary", key="emp_pct_btn"):
            if not formula_input:
                st.error("Angiv en kemisk formel.")
            else:
                try:
                    from calculators.molar_mass import calculate_molar_mass_with_steps
                    M, steps, meta = calculate_molar_mass_with_steps(formula_input)
                    comp = meta.get("composition", {})
                    if not comp:
                        st.error("Kunne ikke beregne sammensætning for denne formel.")
                    else:
                        st.success(f"Molarmasse: **{M:.4f} g/mol**")
                        st.markdown("**Procentvis massesammensætning:**")
                        rows = []
                        for sym, data in comp.items():
                            count = data.get("count", data.get("atom_count", 1))
                            m_elem = ATOMIC_MASSES.get(sym, data.get("atomic_mass", 0))
                            m_total_elem = count * m_elem
                            pct = (m_total_elem / M) * 100
                            rows.append({"Element": sym, "Antal": count,
                                         "Atommasse (g/mol)": f"{m_elem:.3f}",
                                         "Masse i formel": f"{m_total_elem:.4f}",
                                         "Masseprocent": f"{pct:.2f}%"})
                        import pandas as pd
                        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                except Exception as exc:
                    st.error(f"Fejl: {exc}")

    _quick_links([
        ("⚖️ Molarmasse", "atoms-molar", "⚖️ Molar Mass"),
        ("🔬 Begrænsende reaktant", "stoichiometry", "🔬 Begrænsende reaktant"),
    ])


def _default_gibbs_reaction_rows():
    return [
        {"Side": "reactant", "Species": "N2(g)", "nu": 1.0, "ΔHf° (kJ/mol)": 0.0, "S° (J/mol·K)": 191.5},
        {"Side": "reactant", "Species": "H2(g)", "nu": 3.0, "ΔHf° (kJ/mol)": 0.0, "S° (J/mol·K)": 130.68},
        {"Side": "product", "Species": "NH3(g)", "nu": 2.0, "ΔHf° (kJ/mol)": -46.11, "S° (J/mol·K)": 192.77},
    ]


def _empty_gibbs_row(side: str) -> dict:
    return {"Side": side, "Species": "", "nu": 1.0, "ΔHf° (kJ/mol)": "-", "S° (J/mol·K)": "-"}


def _gibbs_rows_from_reaction_ast(ast: dict, existing_rows: list | None = None) -> list:
    existing_rows = existing_rows or []
    existing_values = {}
    for row in existing_rows:
        species = str(row.get("Species", "")).strip()
        side = str(row.get("Side", "")).strip().lower()
        if species and side:
            existing_values[(side, species)] = {
                "ΔHf° (kJ/mol)": row.get("ΔHf° (kJ/mol)", "-"),
                "S° (J/mol·K)": row.get("S° (J/mol·K)", "-"),
            }

    new_rows = []
    for side_name, items in (("reactant", ast["reactants"]), ("product", ast["products"])):
        for item in items:
            species = f"{item['formula']}({item['phase']})"
            preserved = existing_values.get((side_name, species), {})
            new_rows.append(
                {
                    "Side": side_name,
                    "Species": species,
                    "nu": float(item["coefficient"]),
                    "ΔHf° (kJ/mol)": preserved.get("ΔHf° (kJ/mol)", "-"),
                    "S° (J/mol·K)": preserved.get("S° (J/mol·K)", "-"),
                }
            )
    return new_rows


def _render_gibbs_result_explanations() -> None:
    """Render a compact help section explaining Gibbs output metrics."""
    with st.expander("Hvad betyder resultaterne?", expanded=False):
        st.markdown("**K**: Ligevægtskonstanten. Stor K betyder at produkter favoriseres, lille K betyder at reaktanter favoriseres, og K omkring 1 betyder at ingen side er stærkt favoriseret.")
        st.markdown("**ΔH°rxn (kJ/mol)**: Reaktionens standard entalpiændring. Negativ værdi betyder at varme afgives (exoterm), positiv værdi betyder at varme optages (endoterm).")
        st.markdown("**ΔS°rxn (J/mol·K)**: Reaktionens standard entropiændring. Positiv værdi betyder mere uorden/spredning, negativ værdi betyder mindre uorden/spredning.")
        st.markdown("**ΔG° (kJ/mol)**: Reaktionens standard Gibbs frie energi ved den valgte temperatur. Negativ værdi er termodynamisk favorabel/spontan, positiv værdi er ikke favorabel, og tæt på 0 betyder nær ligevægt.")
        st.markdown("**log10 K**: 10-talslogaritmen til K. Nyttig når K er meget stor eller meget lille, så værdier er lettere at læse og sammenligne.")


def _render_gibbs_calculator(include_page_header: bool = False):
    """Render Gibbs calculator controls/results for standalone or tab usage."""
    if include_page_header:
        st.title("🔥 Gibbs Free Energy Calculator")
        st.markdown("---")
    else:
        st.markdown("#### Gibbs Free Energy (ΔG)")

    st.markdown(
        "Byg reaktionen i tabellen og beregn $\\Delta H^\\circ_{rxn}$, "
        "$\\Delta S^\\circ_{rxn}$, $\\Delta G^\\circ$ og ligevægtskonstanten $K$ ved valgt temperatur."
    )

    if "thermo_gibbs_rows" not in st.session_state:
        st.session_state["thermo_gibbs_rows"] = _default_gibbs_reaction_rows()

    if "thermo_gibbs_temperature" not in st.session_state:
        st.session_state["thermo_gibbs_temperature"] = 298.15

    if "thermo_gibbs_temp_unit" not in st.session_state:
        st.session_state["thermo_gibbs_temp_unit"] = "K"

    if "thermo_gibbs_reaction_input" not in st.session_state:
        st.session_state["thermo_gibbs_reaction_input"] = "N2(g) + 3 H2(g) -> 2 NH3(g)"

    st.markdown("### Reaction")
    reaction_input = st.text_input(
        "Chemical reaction",
        key="thermo_gibbs_reaction_input",
        help="Eksempel: N2(g) + 3 H2(g) -> 2 NH3(g)",
    )

    reaction_col1, reaction_col2 = st.columns([1, 3])
    with reaction_col1:
        load_from_reaction = st.button("Load reaction", key="thermo_gibbs_load_reaction")
    with reaction_col2:
        if reaction_input.strip():
            st.markdown(
                "**Read reaction:** " + format_chemical_notation_html(reaction_input.strip()),
                unsafe_allow_html=True,
            )

    if load_from_reaction:
        try:
            from core.reaction_enthalpy import parseReaction

            ast = parseReaction(reaction_input)
            st.session_state["thermo_gibbs_rows"] = _gibbs_rows_from_reaction_ast(
                ast,
                st.session_state.get("thermo_gibbs_rows", []),
            )
            for warning in ast.get("warnings", []):
                st.warning(warning)
            st.success("Reaction loaded into the Gibbs table.")
            st.rerun()
        except Exception as e:
            st.error(str(e))

    st.markdown("### Inputs")
    st.caption("Brug '-' i ΔHf° og S° hvis en værdi ikke er givet endnu.")
    temp_col1, temp_col2 = st.columns([2, 1])
    with temp_col1:
        temperature = st.number_input(
            "Temperature",
            value=float(st.session_state["thermo_gibbs_temperature"]),
            step=0.1,
            format="%.3f",
            key="thermo_gibbs_temperature",
        )
    with temp_col2:
        temp_unit = st.selectbox(
            "Temperature unit",
            ["K", "°C"],
            index=0 if st.session_state["thermo_gibbs_temp_unit"] == "K" else 1,
            key="thermo_gibbs_temp_unit",
        )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("Add reactant row", key="thermo_gibbs_add_reactant"):
            st.session_state["thermo_gibbs_rows"].append(_empty_gibbs_row("reactant"))
            st.rerun()
    with c2:
        if st.button("Add product row", key="thermo_gibbs_add_product"):
            st.session_state["thermo_gibbs_rows"].append(_empty_gibbs_row("product"))
            st.rerun()
    with c3:
        if st.button("Load example", key="thermo_gibbs_load_example"):
            st.session_state["thermo_gibbs_rows"] = _default_gibbs_reaction_rows()
            st.session_state["thermo_gibbs_temperature"] = 298.15
            st.session_state["thermo_gibbs_temp_unit"] = "K"
            st.rerun()
    with c4:
        if st.button("Reset", key="thermo_gibbs_reset"):
            st.session_state["thermo_gibbs_rows"] = [
                _empty_gibbs_row("reactant"),
                _empty_gibbs_row("product"),
            ]
            st.rerun()

    row_df = pd.DataFrame(st.session_state["thermo_gibbs_rows"])
    edited_df = st.data_editor(
        row_df,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        key="thermo_gibbs_editor",
    )

    st.session_state["thermo_gibbs_rows"] = edited_df.to_dict("records")

    def _coeff_text(value):
        try:
            v = float(value)
        except Exception:
            return str(value)
        if abs(v - int(v)) < 1e-12:
            return str(int(v))
        return f"{v:g}"

    preview_reactants = []
    preview_products = []
    rows_for_calc = []
    for _, row in edited_df.iterrows():
        side = str(row.get("Side", "")).strip().lower()
        species = str(row.get("Species", "")).strip()
        nu_raw = row.get("nu", None)
        dhf_raw = row.get("ΔHf° (kJ/mol)", None)
        s_raw = row.get("S° (J/mol·K)", None)

        if not species:
            continue

        rows_for_calc.append(
            {
                "side": side,
                "species": species,
                "nu": nu_raw,
                "dhf": dhf_raw,
                "s": s_raw,
                "dhf_unit": "kJ/mol",
                "s_unit": "J/(mol·K)",
            }
        )

        if species and side in ("reactant", "reaktant"):
            prefix = "" if _coeff_text(nu_raw) == "1" else f"{_coeff_text(nu_raw)} "
            preview_reactants.append(prefix + species)
        if species and side in ("product", "produkt"):
            prefix = "" if _coeff_text(nu_raw) == "1" else f"{_coeff_text(nu_raw)} "
            preview_products.append(prefix + species)

    if preview_reactants and preview_products:
        equation_preview = " + ".join(preview_reactants) + " -> " + " + ".join(preview_products)
        st.markdown(
            "**Read reaction:** " + format_chemical_notation_html(equation_preview),
            unsafe_allow_html=True,
        )

    if st.button("Calculate thermodynamic profile", type="primary", key="thermo_gibbs_calculate"):
        try:
            result, steps, metadata = calculate_reaction_gibbs_with_steps(
                rows_for_calc,
                temperature=temperature,
                temp_unit=temp_unit,
            )

            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("ΔH°rxn (kJ/mol)", f"{result['delta_h_rxn_kj_per_mol']:.6g}")
            with m2:
                st.metric("ΔS°rxn (J/mol·K)", f"{result['delta_s_rxn_j_per_mol_k']:.6g}")
            with m3:
                st.metric("ΔG° (kJ/mol)", f"{result['delta_g_rxn_kj_per_mol']:.6g}")
            with m4:
                st.metric("log10 K", f"{result['log10_k']:.6g}")

            st.success(f"K ≈ {result['k_display']}")
            if result["spontaneity"] == "spontaneous":
                st.success("Reaction is spontaneous under the selected conditions.")
            elif result["spontaneity"] == "non-spontaneous":
                st.warning("Reaction is non-spontaneous under the selected conditions.")
            else:
                st.info("Reaction is at equilibrium under the selected conditions.")

            with st.expander("Species contributions", expanded=False):
                contribution_df = pd.DataFrame(metadata["row_contributions"])
                st.dataframe(contribution_df, use_container_width=True, hide_index=True)

            with st.expander("Vis trin", expanded=False):
                for step in steps:
                    st.markdown(step)

            _render_gibbs_result_explanations()
        except Exception as e:
            st.error(str(e))


def show_gibbs_page():
    """Display the Gibbs free energy calculator page."""
    _render_gibbs_calculator(include_page_header=True)

def show_stoichiometry_page():
    """Display the stoichiometry calculator page."""
    st.title("🧮 Balancering og stofmængde")
    st.markdown("---")
    
    _st_options = [
        "⚖️ Balancer reaktion", "🔋 Redoxafstemning", "🔬 Begrænsende reaktant",
        "🔢 Stofmænge fra ligning", "Tung/let opløselighed", "🧭 Reaktionstype", "💧 Fortynding",
    ]
    _st_active = _render_styled_tab_nav(_st_options, key="stoich_tab", nav_key="nav_stoichiometry")

    if _st_active == "⚖️ Balancer reaktion":
        show_reaction_balancing_tab()
        _quick_links([
            ("🔬 Begrænsende reaktant", "stoichiometry", "🔬 Begrænsende reaktant"),
            ("🔋 Redoxafstemning", "stoichiometry", "🔋 Redoxafstemning"),
        ])
    elif _st_active == "🔋 Redoxafstemning":
        show_redox_balancing_tab()
        _quick_links([
            ("⚖️ Balancer reaktion", "stoichiometry", "⚖️ Balancer reaktion"),
            ("🔋 Byg en celle", "electrochemistry", "Byg en celle"),
        ])
    elif _st_active == "🔬 Begrænsende reaktant":
        show_limiting_reagent_tab()
        _quick_links([
            ("⚖️ Molarmasse", "atoms-molar", None),
            ("💧 Fortynding", "stoichiometry", "💧 Fortynding"),
            ("⚖️ Balancer reaktion", "stoichiometry", "⚖️ Balancer reaktion"),
        ])
    elif _st_active == "🔢 Stofmænge fra ligning":
        _show_stofmaengde_tab()
        _quick_links([
            ("🔬 Begrænsende reaktant", "stoichiometry", "🔬 Begrænsende reaktant"),
            ("⚖️ Balancer reaktion", "stoichiometry", "⚖️ Balancer reaktion"),
            ("⚖️ Molarmasse", "atoms-molar", None),
        ])
    elif _st_active == "Tung/let opløselighed":
        show_salt_solubility_tab()
    elif _st_active == "🧭 Reaktionstype":
        show_reaction_type_tab()
    elif _st_active == "💧 Fortynding":
        show_dilution_tab()
        _quick_links([
            ("🔬 Begrænsende reaktant", "stoichiometry", "🔬 Begrænsende reaktant"),
            ("⚖️ Molarmasse", "atoms-molar", None),
        ])


def _show_stofmaengde_tab():
    """Stofmængeberegning fra reaktionsligning – koefficient-baseret omregning."""
    import re
    st.markdown("### 🔢 Stofmængeberegning fra reaktionsligning")
    st.markdown(
        "Givet en **afstemt reaktionsligning** kan du omregne stofmængden af ét stof til stofmængden af et andet "
        "vha. **koefficientsforholdet** (det molare forhold)."
    )
    st.latex(r"n_B = n_A \times \frac{\nu_B}{\nu_A}")

    st.markdown("#### Reaktionsligning")
    rxn_input = st.text_input(
        "Skriv afstemt reaktionsligning:",
        value="2 H2 + O2 → 2 H2O",
        key="stof_rxn",
        help="Eksempel: 2 H2 + O2 → 2 H2O  eller  N2 + 3 H2 → 2 NH3",
    )

    def parse_rxn(rxn_str):
        rxn_str = rxn_str.replace("->", "→").replace("=", "→")
        if "→" not in rxn_str:
            return None, "Mangler pil (→ eller ->)"
        sides = rxn_str.split("→", 1)
        species = {}
        for side_sign, side_str in [(1, sides[1].strip()), (-1, sides[0].strip())]:
            for part in re.split(r"\s*\+\s*", side_str):
                part = part.strip()
                if not part:
                    continue
                m = re.match(r"^(\d+(?:\.\d+)?)\s*(.+)$", part)
                if m:
                    coeff = float(m.group(1))
                    name = m.group(2).strip()
                else:
                    coeff = 1.0
                    name = part
                label = ("→ " if side_sign > 0 else "") + name
                species[label] = coeff
        return species, None

    species_map, err = parse_rxn(rxn_input)

    if err:
        st.error(f"❌ {err}")
        return

    if not species_map or len(species_map) < 2:
        st.warning("Angiv mindst to stoffer i ligningen.")
        return

    names = list(species_map.keys())
    coeffs = list(species_map.values())

    col1, col2 = st.columns(2)
    with col1:
        src_label = st.selectbox("Kendt stof (kilde):", names, key="stof_src")
        n_src = st.number_input(
            f"Stofmængde af {src_label.replace('→ ', '')} (mol):",
            value=1.0, min_value=0.0, step=0.1, key="stof_n_src",
        )
        input_mode = st.radio("Eller beregn fra:", ["Stofmængde (mol)", "Masse (g)", "Volumen af gas (L ved STP)"],
                               key="stof_input_mode")
        if input_mode == "Masse (g)":
            m_src = st.number_input("Masse (g):", value=2.0, min_value=0.0, key="stof_m_src")
            M_src = st.number_input("Molarmasse kilde (g/mol):", value=2.016, min_value=0.1, key="stof_M_src")
            n_src = m_src / M_src
            st.info(f"n = {m_src:.3f} g / {M_src:.3f} g/mol = **{n_src:.4f} mol**")
        elif input_mode == "Volumen af gas (L ved STP)":
            V_src = st.number_input("Volumen (L):", value=22.4, min_value=0.0, key="stof_V_src")
            n_src = V_src / 22.414
            st.info(f"n = {V_src:.3f} L / 22,414 L/mol = **{n_src:.4f} mol**")

    with col2:
        tgt_label = st.selectbox("Ukendt stof (mål):", [n for n in names if n != src_label], key="stof_tgt")
        output_mode = st.radio("Vis resultat som:", ["Stofmængde (mol)", "Masse (g)", "Volumen af gas (L ved STP)"],
                                key="stof_output_mode")
        if output_mode == "Masse (g)":
            M_tgt = st.number_input("Molarmasse mål (g/mol):", value=18.015, min_value=0.1, key="stof_M_tgt")
        elif output_mode == "Volumen af gas (L ved STP)":
            pass

    if st.button("Beregn", type="primary", key="stof_calc"):
        nu_src = species_map[src_label]
        nu_tgt = species_map[tgt_label]
        n_tgt = n_src * (nu_tgt / nu_src)

        src_name = src_label.replace("→ ", "")
        tgt_name = tgt_label.replace("→ ", "")

        st.success(f"✅ **n({tgt_name}) = {n_tgt:.4f} mol**")

        if output_mode == "Masse (g)":
            m_tgt = n_tgt * M_tgt
            st.success(f"⚖️ **m({tgt_name}) = {n_tgt:.4f} × {M_tgt:.3f} = {m_tgt:.4f} g**")
        elif output_mode == "Volumen af gas (L ved STP)":
            V_tgt = n_tgt * 22.414
            st.success(f"💨 **V({tgt_name}) = {n_tgt:.4f} × 22,414 = {V_tgt:.4f} L ved STP**")

        with st.expander("🔍 Trin-for-trin", expanded=True):
            st.markdown(f"""
**Reaktionsligning:** {rxn_input}

| Stof | Koefficient ν |
|------|--------------|
| {src_name} (kilde) | {nu_src:.0f} |
| {tgt_name} (mål) | {nu_tgt:.0f} |

1. Molvægtforhold: ν({tgt_name}) / ν({src_name}) = {nu_tgt:.0f} / {nu_src:.0f} = **{nu_tgt/nu_src:.4f}**
2. n({tgt_name}) = n({src_name}) × (ν({tgt_name}) / ν({src_name}))
   = {n_src:.4f} mol × {nu_tgt/nu_src:.4f} = **{n_tgt:.4f} mol**
""")

    st.markdown("---")
    st.markdown("**Eksempler:**")
    ex_data = {
        "Reaktion": ["2 H₂ + O₂ → 2 H₂O", "N₂ + 3 H₂ → 2 NH₃", "CH₄ + 2 O₂ → CO₂ + 2 H₂O"],
        "Forklaring": [
            "2 mol H₂ giver 2 mol H₂O (1:1 forhold)",
            "3 mol H₂ giver 2 mol NH₃",
            "1 mol CH₄ forbrænder med 2 mol O₂",
        ],
    }
    import pandas as pd
    st.dataframe(pd.DataFrame(ex_data), hide_index=True, use_container_width=True)


def show_salt_solubility_tab():
    """Display rule-based salt solubility analysis tab."""
    st.markdown("### 🧂 Tung/let opløselighed")
    st.markdown("Vurdering af ioniske salte i vand baseret på eksplicitte opløselighedsregler.")

    if "solubility_input" not in st.session_state:
        st.session_state["solubility_input"] = ""
    if "solubility_result" not in st.session_state:
        st.session_state["solubility_result"] = None
    if "solubility_steps" not in st.session_state:
        st.session_state["solubility_steps"] = []
    if "solubility_error" not in st.session_state:
        st.session_state["solubility_error"] = None

    salt_formula = st.text_input(
        "Indtast salt",
        key="solubility_input",
        placeholder="NaCl, AgCl, BaSO4, (NH4)2CO3",
    )

    b1, b2, b3 = st.columns(3)
    with b1:
        do_analyze = st.button("Analyser opløselighed", type="primary", key="solubility_analyze")
    with b2:
        if st.button("Indlæs eksempel", key="solubility_example"):
            st.session_state["solubility_input"] = "AgCl"
            st.session_state["solubility_result"] = None
            st.session_state["solubility_steps"] = []
            st.session_state["solubility_error"] = None
            st.rerun()
    with b3:
        if st.button("Nulstil", key="solubility_reset"):
            st.session_state["solubility_input"] = ""
            st.session_state["solubility_result"] = None
            st.session_state["solubility_steps"] = []
            st.session_state["solubility_error"] = None
            st.rerun()

    if do_analyze:
        try:
            result, steps, _ = analyze_salt_solubility_with_steps(salt_formula)
            st.session_state["solubility_result"] = result
            st.session_state["solubility_steps"] = steps
            st.session_state["solubility_error"] = None
        except ValueError as e:
            st.session_state["solubility_result"] = None
            st.session_state["solubility_steps"] = []
            st.session_state["solubility_error"] = str(e)

    if st.session_state.get("solubility_error"):
        st.error(st.session_state["solubility_error"])

    result = st.session_state.get("solubility_result")
    if result:
        status = result["status"]
        if status == "soluble":
            st.success(f"Klassifikation: {result['classification_da']} / {result['classification_en']}")
        elif status == "slightly_soluble":
            st.warning(f"Klassifikation: {result['classification_da']} / {result['classification_en']}")
        elif status == "insoluble":
            st.warning(f"Klassifikation: {result['classification_da']} / {result['classification_en']}")
        else:
            st.info(f"Klassifikation: {result['classification_da']} / {result['classification_en']}")

        st.markdown("#### Resultat")
        st.markdown(f"**Salt:** {format_chemical_notation_html(result['salt'])}", unsafe_allow_html=True)
        st.markdown(f"**Kation:** {result['cation']['symbol']}")
        st.markdown(f"**Anion:** {result['anion']['symbol']}")
        st.markdown(f"**Dansk vurdering:** {result['classification_da']}")
        st.markdown(f"**English:** {result['classification_en']}")
        st.markdown(f"**Regel:** {result['rule']}")
        st.markdown(f"**Begrundelse:** {result['reason']}")

        with st.expander("Vis analyse-trin", expanded=False):
            for step in st.session_state.get("solubility_steps", []):
                st.markdown(f"- {step}")

    st.caption(
        "Vurderingen er baseret på standard opløselighedsregler for ioniske forbindelser i vand. "
        "Nogle salte kan afhænge af temperatur og detaljerede betingelser."
    )


def show_reaction_type_tab() -> None:
    """Display reaction-type classification tab."""
    st.markdown("### 🧭 Reaktionstype")
    st.markdown("Indtast en reaktion og få en konservativ, regelbaseret klassifikation.")

    if "reaction_type_input" not in st.session_state:
        st.session_state["reaction_type_input"] = ""

    reaction_text = st.text_area(
        "Reaktion",
        key="reaction_type_input",
        placeholder="fx CaBr2 (aq) + K2SO4 (aq) -> CaSO4 (s) + 2KBr (aq)",
        height=100,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        run = st.button("Bestem reaktionstype", type="primary", key="reaction_type_run")
    with c2:
        if st.button("Indlæs eksempel", key="reaction_type_example"):
            st.session_state["reaction_type_input"] = "AgNO3 (aq) + NaCl (aq) -> AgCl (s) + NaNO3 (aq)"
            st.rerun()
    with c3:
        if st.button("Nulstil", key="reaction_type_reset"):
            st.session_state["reaction_type_input"] = ""
            st.rerun()

    if run:
        try:
            result = classify_reaction_text(reaction_text)
            classification = result["classification"]
            parsed = result["parsed"]

            st.success(f"Primær type: {classification['primaryType']}")
            st.markdown("#### Resultat")
            st.markdown(f"**Reaktionstype:** {classification['primaryType']}")
            st.markdown(f"**Sikkerhed:** {classification['confidence']}")
            st.markdown(f"**Begrundelse:** {classification['explanation']}")

            if classification["secondaryTypes"]:
                st.markdown(
                    "**Sekundære typer:** " + ", ".join(classification["secondaryTypes"])
                )

            with st.expander("Vis parsed reaktion", expanded=False):
                st.markdown("**Reaktanter:**")
                for s in parsed["reactants"]:
                    state = f" ({s['state']})" if s["state"] else ""
                    st.markdown(
                        f"- {s['coefficient']} {format_chemical_notation_html(s['formula'])}{state}",
                        unsafe_allow_html=True,
                    )
                st.markdown("**Produkter:**")
                for s in parsed["products"]:
                    state = f" ({s['state']})" if s["state"] else ""
                    st.markdown(
                        f"- {s['coefficient']} {format_chemical_notation_html(s['formula'])}{state}",
                        unsafe_allow_html=True,
                    )
        except ReactionParseError as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"Klassifikation mislykkedes: {e}")


def show_redox_balancing_tab():
    """Display the redox balancing tab."""
    st.markdown("### 🔋 Redoxafstemning")

    tab_balance, tab_oxidation = st.tabs([
        "⚖️ Afstemning",
        "🧮 Oxidationstal (art)",
    ])

    with tab_balance:
        st.markdown("**Eksempel på indtastning af notation:**")
        st.markdown("Fe^2+ + MnO4^- + H^+ -> Fe^3+ + Mn^2+ + H2O")

        redox_equation = st.text_input(
            "Redoxreaktion:",
            placeholder="f.eks. Fe^2+ + MnO4^- + H^+ -> Fe^3+ + Mn^2+ + H2O",
            help="Ladning kan skrives som Fe2+, Fe^2+ eller Fe_2+. Brug + mellem stoffer og -> (eller =) som pil.",
            key="redox_equation"
        )

        example_equation = "Fe^2+ + MnO4^- + H^+ -> Fe^3+ + Mn^2+ + H2O"
        preview_source = redox_equation.strip() if redox_equation.strip() else example_equation
        formatted_input = format_chemical_notation_html(preview_source)
        st.markdown(f"**Din indtastning:** {formatted_input}", unsafe_allow_html=True)

        medium_label = st.selectbox(
            "Medium:",
            ["Sur (acid)", "Basisk (base)", "Neutral"],
            key="redox_medium"
        )

        medium_map = {
            "Sur (acid)": "acid",
            "Basisk (base)": "base",
            "Neutral": "neutral"
        }
        medium = medium_map[medium_label]

        if st.button("Afstem redoxreaktion", type="primary", key="balance_redox_btn"):
            if not redox_equation.strip():
                st.error("Skriv en redoxreaktion først.")
            else:
                try:
                    with st.spinner("Afstemmer redoxreaktion..."):
                        balanced_eq, steps, metadata = balance_redox_with_steps(redox_equation, medium)

                    st.success("✅ **Redoxreaktion afstemt**")
                    formatted_balanced = format_chemical_notation_html(balanced_eq)
                    st.markdown(f"**Afstemt ligning:** {formatted_balanced}", unsafe_allow_html=True)

                    if metadata.get("species_order") and metadata.get("coefficients"):
                        st.markdown("**Koefficienter:**")
                        for species, coeff in zip(metadata["species_order"], metadata["coefficients"]):
                            formatted_species = format_chemical_notation_html(species)
                            st.markdown(f"- {formatted_species}: {coeff}", unsafe_allow_html=True)

                    try:
                        oxidation_data = analyze_oxidation_numbers(balanced_eq)
                        st.markdown("**Oxidationstal (pr. art):**")

                        oxidation_rows = []
                        for row in oxidation_data.get("species_analysis", []):
                            species_fmt = format_chemical_notation_unicode(row["species"])
                            side_label = "Reaktant" if row["side"] == "reactant" else "Produkt"

                            ox_parts = []
                            for element, ox_val in row.get("oxidation_states", {}).items():
                                val_txt = "?" if ox_val is None else f"{ox_val:+g}"
                                ox_parts.append(f"{element}: {val_txt}")

                            oxidation_rows.append(
                                {
                                    "Side": side_label,
                                    "Koefficient": row["coefficient"],
                                    "Art": species_fmt,
                                    "Oxidationstal": ", ".join(ox_parts),
                                }
                            )

                        if oxidation_rows:
                            oxidation_df = pd.DataFrame(oxidation_rows)
                            st.dataframe(oxidation_df, use_container_width=True, hide_index=True)

                        oxidized = oxidation_data.get("oxidized_elements", [])
                        reduced = oxidation_data.get("reduced_elements", [])
                        if oxidized:
                            st.markdown(f"**Oxideret:** {', '.join(oxidized)}")
                        if reduced:
                            st.markdown(f"**Reduceret:** {', '.join(reduced)}")

                        changes = oxidation_data.get("element_changes", [])
                        if changes:
                            st.markdown("**Ændringer i oxidationstal:**")
                            for change in changes:
                                st.markdown(
                                    f"- {change['element']}: {change['from']} → {change['to']} ({change['change']})"
                                )
                    except Exception as oxidation_error:
                        st.warning(f"Kunne ikke udlede alle oxidationstal: {oxidation_error}")

                    with st.expander("🔍 Vis trin", expanded=False):
                        for step in steps:
                            st.markdown(step)

                except Exception as e:
                    error_text = str(e)
                    st.error(f"❌ {error_text}")

                    tips = ["Kontrollér at reaktionen har både oxidation og reduktion (elektroner skal både afgives og optages)."]
                    if medium == "neutral":
                        tips.append("Hvis der indgår ioner, prøv også Sur (acid) eller Basisk (base).")
                    if "forkert side" in error_text.lower() or "koefficient 0" in error_text.lower():
                        tips.append("Tjek at hvert input-stof faktisk skal optræde i den samlede nettoreaktion.")
                    if "mangler reduktions-halvreaktion" in error_text.lower() or "mangler oxidations-halvreaktion" in error_text.lower():
                        tips.append("Tilføj det manglende modstykke i reaktionen eller et relevant stof/produkt.")

                    st.info("💡 " + " ".join(tips))

        st.markdown("### Eksempler")
        st.markdown("- **Fe^2+ + MnO4^- + H^+ -> Fe^3+ + Mn^2+ + H2O** (sur)")
        st.markdown("- **Fe_2+ + MnO4_- + H_+ -> Fe_3+ + Mn_2+ + H2O** (sur)")
        st.markdown("- **Cl2 + OH- -> ClO- + Cl- + H2O** (basisk)")
        st.markdown("- **C6H12O6 + O2 -> CO2 + H2O** (neutral)")

    with tab_oxidation:
        st.markdown("### 🧮 Oxidationstal for en art")
        st.markdown("Indtast en enkelt art (molekyle eller ion) og få oxidationstal for hvert grundstof.")

        if "redox_species_input" not in st.session_state:
            st.session_state["redox_species_input"] = ""
        if "redox_species_result" not in st.session_state:
            st.session_state["redox_species_result"] = None
        if "redox_species_error" not in st.session_state:
            st.session_state["redox_species_error"] = None

        species_input = st.text_input(
            "Art/molekyle:",
            placeholder="f.eks. MnO4^-, H2O2, Fe^3+, KO2, OF2, NaH",
            help="Ladning kan skrives som Fe2+, Fe^2+ eller Fe_2+. Brug evt. (s), (l), (g), (aq) som fase.",
            key="redox_species_input",
        )

        example_species = "MnO4^-"
        preview_species = species_input.strip() if species_input.strip() else example_species
        formatted_species = format_chemical_notation_html(preview_species)
        st.markdown(f"**Din indtastning:** {formatted_species}", unsafe_allow_html=True)

        b1, b2, b3 = st.columns(3)
        with b1:
            do_calc = st.button("Beregn oxidationstal", type="primary", key="redox_species_calc")
        with b2:
            if st.button("Indlæs eksempel", key="redox_species_example"):
                st.session_state["redox_species_input"] = "H2O2"
                st.session_state["redox_species_result"] = None
                st.session_state["redox_species_error"] = None
                st.rerun()
        with b3:
            if st.button("Nulstil", key="redox_species_reset"):
                st.session_state["redox_species_input"] = ""
                st.session_state["redox_species_result"] = None
                st.session_state["redox_species_error"] = None
                st.rerun()

        if do_calc:
            if not species_input.strip():
                st.error("Skriv en art først.")
            else:
                try:
                    raw_states = _oxidation_states_for_species(species_input)
                    normalized = {
                        element: _normalize_ox_number(value)
                        for element, value in raw_states.items()
                    }
                    st.session_state["redox_species_result"] = normalized
                    st.session_state["redox_species_error"] = None
                except Exception as exc:
                    st.session_state["redox_species_result"] = None
                    st.session_state["redox_species_error"] = str(exc)

        if st.session_state.get("redox_species_error"):
            st.error(st.session_state["redox_species_error"])

        result = st.session_state.get("redox_species_result")
        if result:
            rows = []
            for element, ox_val in result.items():
                val_txt = "?" if ox_val is None else f"{ox_val:+g}"
                rows.append({"Element": element, "Oxidationstal": val_txt})

            result_df = pd.DataFrame(rows)
            st.dataframe(result_df, use_container_width=True, hide_index=True)

            unknown = [element for element, ox_val in result.items() if ox_val is None]
            if unknown:
                st.warning("Kunne ikke bestemme oxidationstal for: " + ", ".join(unknown))
            else:
                st.success("✅ Oxidationstal fundet for alle elementer.")


def show_reaction_balancing_tab():
    """Display the reaction balancing tab."""
    st.markdown("### ⚖️ Balance Chemical Reaction")
    
    # Input section
    equation = st.text_input(
        "Chemical Equation:",
        placeholder="e.g., Fe2(SO4)3 + KOH -> Fe(OH)3 + K2SO4",
        help="Enter a chemical equation. Use ->, =>, or = as arrow. Supports + as separator."
    )
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if st.button("Balance Equation", type="primary"):
            if not equation:
                st.error("Please enter a chemical equation.")
            else:
                try:
                    with st.spinner("Balancing equation..."):
                        result = balance_equation(equation)
                    
                    # Results section
                    st.success("✅ **Equation Balanced Successfully!**")
                    
                    # Display balanced equation
                    st.markdown(f"**Balanced Equation:** {result['equation_str']}")
                    
                    # Show coefficients
                    st.markdown("**Coefficients:**")
                    for i, species in enumerate(result['species_order']):
                        coeff = result['coefficients'][i]
                        st.markdown(f"- {species}: {coeff}")
                    
                    # Steps section
                    with st.expander("🔍 Vis trin", expanded=False):
                        for step in result['steps']:
                            st.markdown(step)
                    
                except Exception as e:
                    st.error(f"❌ **Fejl**: {str(e)}")
                    st.info("Please check your equation and try again.")
    
    with col2:
        st.markdown("### Examples:")
        st.markdown("- **Fe₂(SO₄)₃ + KOH → Fe(OH)₃ + K₂SO₄**")
        st.markdown("- **C₂H₅OH + O₂ → CO₂ + H₂O**")
        st.markdown("- **H₂ + O₂ → H₂O**")
        st.markdown("- **N₂ + H₂ → NH₃**")


def show_limiting_reagent_tab():
    """Display the limiting reagent tab."""
    st.markdown("### 🔬 Limiting Reagent & Theoretical Yield")
    
    # Input section
    equation = st.text_input(
        "Chemical Equation:",
        placeholder="e.g., N2 + H2 -> NH3",
        help="Enter a chemical equation. It will be automatically balanced."
    )

    if equation:
        st.markdown("##### Sådan blev ligningen læst")
        st.markdown(
            (
                "<div style='padding: 0.3rem 0 0.6rem 0; font-size: 1.05rem;'>"
                f"{format_chemical_notation_html(equation)}"
                "</div>"
            ),
            unsafe_allow_html=True,
        )
    
    if equation:
        try:
            # Parse the equation to get reactants and products
            from core.reaction import parse_reaction_equation
            parsed = parse_reaction_equation(equation)
            reactants = parsed['reactants']
            products = parsed['products']

            try:
                balanced = balance_equation(equation)
                st.markdown("##### Afstemt reaktion")
                st.markdown(
                    (
                        "<div style='padding: 0.1rem 0 0.8rem 0; font-size: 1.05rem;'>"
                        f"{format_chemical_notation_html(balanced['equation_str'])}"
                        "</div>"
                    ),
                    unsafe_allow_html=True,
                )
            except Exception:
                # Keep the page usable even if balancing fails for a specific input.
                st.info("Kunne ikke afstemme reaktionen automatisk for denne input.")
            
            reactants_html = ", ".join(format_chemical_notation_html(r) for r in reactants)
            products_html = ", ".join(format_chemical_notation_html(p) for p in products)
            st.markdown(
                f"<p><strong>Reactants:</strong> {reactants_html}</p>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<p><strong>Products:</strong> {products_html}</p>",
                unsafe_allow_html=True,
            )
            
            # Reactant inputs
            st.markdown("#### Reactant Quantities")
            reactant_inputs = []
            
            for i, reactant in enumerate(reactants):
                st.markdown(
                    (
                        "<div style='padding-top: 0.2rem;'><strong>"
                        f"{format_chemical_notation_html(reactant)}:"
                        "</strong></div>"
                    ),
                    unsafe_allow_html=True,
                )
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    mode = st.selectbox(
                        "Mode:",
                        ["mass", "moles", "solution"],
                        key=f"mode_{i}"
                    )
                
                with col2:
                    if mode == "mass":
                        value = st.number_input("Mass (g):", value=10.0, step=0.1, key=f"value_{i}")
                        unit = "g"
                    elif mode == "moles":
                        value = st.number_input("Mol (n):", value=1.0, step=0.1, key=f"value_{i}")
                        unit = "mol"
                    else:  # solution
                        value = st.number_input("Molarity (M):", value=1.0, step=0.1, key=f"value_{i}")
                        unit = "M"
                
                with col3:
                    if mode == "solution":
                        volume = st.number_input("Volume (mL):", value=100, step=1, key=f"volume_{i}")
                    else:
                        volume = None
                
                with col4:
                    st.markdown("")  # Spacer
                
                reactant_inputs.append({
                    'formula': reactant,
                    'mode': mode,
                    'value': value,
                    'unit': unit,
                    'volume': volume
                })
            
            # Target product selection
            st.markdown("#### Target Product")
            target_product = st.selectbox(
                "Select target product for yield calculation:",
                products,
                key="target_product"
            )
            
            # Actual yield (optional)
            actual_yield = st.number_input(
                "Actual yield (g) - optional:",
                value=None,
                step=0.01,
                help="Leave empty if you only want theoretical yield"
            )
            
            # Calculate button
            if st.button("Calculate Limiting Reagent & Yield", type="primary"):
                try:
                    with st.spinner("Calculating..."):
                        result, steps, metadata = calculate_limiting_reagent_with_steps(
                            equation, reactant_inputs, target_product, actual_yield
                        )
                    
                    # Results section
                    st.success("✅ **Calculation Complete!**")
                    
                    # Check if there is a limiting reagent
                    if result.get('limiting_reagent') is None or result.get('limiting_reagent') == '':
                        st.warning("⚠️ **No Limiting Reagent Found:** All reactants are in excess. None of the reactants limit the reaction.")
                    else:
                        # Key results when there is a limiting reagent
                        st.markdown("---")
                        st.markdown("## 📊 Results")
                        
                        # Limiting Reagent
                        st.markdown(f"**Limiting Reagent:** {result['limiting_reagent']}")
                        
                        # Theoretical Yield with product specification
                        st.markdown(f"**Theoretical Yield of {target_product}:** {result['theoretical_yield_moles']:.4f} mol ({result['theoretical_yield_mass']:.3f} g)")
                        
                        # Percent Yield if provided
                        if result['percent_yield']:
                            st.markdown(f"**Percent Yield:** {result['percent_yield']:.1f}%")
                        
                        # Excess reactants with detailed breakdown
                        if result['excess_data']:
                            st.markdown("### Reactant Summary:")
                            for reactant, excess in result['excess_data'].items():
                                initial_moles = metadata['reactant_moles'].get(reactant, 0)
                                initial_mass = metadata['reactant_masses'].get(reactant, 0)
                                moles_used = initial_moles - excess['moles_excess']
                                mass_used = initial_mass - excess['mass_excess']
                                
                                if excess['moles_excess'] > 0:
                                    st.markdown(f"**Excess Reactant: {reactant}**")
                                    col_r1, col_r2, col_r3 = st.columns(3)
                                    with col_r1:
                                        st.markdown(f"**Initial:** {initial_moles:.4f} mol ({initial_mass:.3f} g)")
                                    with col_r2:
                                        st.markdown(f"**Used:** {moles_used:.4f} mol ({mass_used:.3f} g)")
                                    with col_r3:
                                        st.markdown(f"**Remaining:** {excess['moles_excess']:.4f} mol ({excess['mass_excess']:.3f} g)")
                                else:
                                    st.markdown(f"**Completely Consumed: {reactant}**")
                                    st.markdown(f"Initial: {initial_moles:.4f} mol ({initial_mass:.3f} g) → All consumed")
                    
                    # Steps section
                    with st.expander("🔍 Vis trin", expanded=False):
                        for step in steps:
                            st.markdown(step)
                    
                except Exception as e:
                    st.error(f"❌ **Fejl**: {str(e)}")
                    st.info("Please check your inputs and try again.")
        
        except Exception as e:
            st.error(f"❌ **Error parsing equation**: {str(e)}")


def show_dilution_tab():
    """Display the dilution calculator tab."""
    st.markdown("### 💧 Dilution Calculator (M₁V₁ = M₂V₂)")
    
    st.markdown("""
    Solve for any one variable in the dilution equation: **M₁V₁ = M₂V₂**
    
    Where:
    - M₁ = Initial concentration
    - V₁ = Initial volume
    - M₂ = Final concentration
    - V₂ = Final volume
    """)
    
    # Input section
    st.markdown("#### Select the unknown variable:")
    unknown = st.radio(
        "Ubekendt:",
        ["M₁ (Initial concentration)", "V₁ (Initial volume)",
         "M₂ (Final concentration)", "V₂ (Final volume)"],
        horizontal=True
    )
    st.caption("💡 Vælg den størrelse du vil beregne – de øvrige tre kendte værdier skal du indtaste.")

    # Create input fields based on selection
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Initial Values:**")
        if unknown != "M₁ (Initial concentration)":
            m1 = st.number_input("M₁ (Initial concentration):", value=2.0, step=0.1)
            m1_unit = st.selectbox("M₁ unit:", ["M", "mM", "μM"], key="m1_unit")
        else:
            m1 = None
            m1_unit = "M"
        
        if unknown != "V₁ (Initial volume)":
            v1 = st.number_input("V₁ (Initial volume):", value=100.0, step=0.1)
            v1_unit = st.selectbox("V₁ unit:", ["mL", "L"], key="v1_unit")
        else:
            v1 = None
            v1_unit = "mL"
    
    with col2:
        st.markdown("**Final Values:**")
        if unknown != "M₂ (Final concentration)":
            m2 = st.number_input("M₂ (Final concentration):", value=0.25, step=0.01)
            m2_unit = st.selectbox("M₂ unit:", ["M", "mM", "μM"], key="m2_unit")
        else:
            m2 = None
            m2_unit = "M"
        
        if unknown != "V₂ (Final volume)":
            v2 = st.number_input("V₂ (Final volume):", value=250.0, step=0.1)
            v2_unit = st.selectbox("V₂ unit:", ["mL", "L"], key="v2_unit")
        else:
            v2 = None
            v2_unit = "L"
    
    # Calculate button
    if st.button("Calculate", type="primary"):
        try:
            with st.spinner("Calculating..."):
                result, steps, metadata = calculate_dilution_with_steps(
                    m1=m1, v1=v1, m2=m2, v2=v2,
                    m1_unit=m1_unit, v1_unit=v1_unit,
                    m2_unit=m2_unit, v2_unit=v2_unit
                )
            
            # Results section
            st.success("✅ **Calculation Complete!**")
            
            # Display result
            unknown_symbol = result['unknown']
            result_value = result['result']
            result_unit = result['result_unit']
            
            st.markdown(f"**{unknown_symbol} = {result_value:.6f} {result_unit}**")
            
            # Steps section
            with st.expander("🔍 Vis trin", expanded=False):
                for step in steps:
                    st.markdown(step)
        
        except Exception as e:
            st.error(f"❌ **Fejl**: {str(e)}")
            st.info("Please check your inputs and try again.")


def show_acids_bases_page():
    """Display the acids and bases calculator page."""
    st.title("🧪 Acids & Bases Calculator")
    st.markdown("---")

    _ab_options = ["Stærk syre/base", "Svag syre/base", "⚗️ Salthydrolyse", "Buffer", "Titrering", "🧮 Debye-Hückel", "📋 pH-beregner"]
    _ab_active = _render_styled_tab_nav(_ab_options, key="acids_bases_tab", nav_key="nav_acids_bases")

    if _ab_active == "Stærk syre/base":
        show_strong_acids_bases_tab()
        _quick_links([
            ("Svag syre/base", "acids-bases", "Svag syre/base"),
            ("Buffer", "acids-bases", "Buffer"),
            ("Titrering", "acids-bases", "Titrering"),
        ])
    elif _ab_active == "Svag syre/base":
        show_weak_acids_bases_tab()
        _quick_links([
            ("⚗️ Salthydrolyse", "acids-bases", "⚗️ Salthydrolyse"),
            ("Buffer", "acids-bases", "Buffer"),
            ("Titrering", "acids-bases", "Titrering"),
            ("⚗️ ICE-tabel", "ligevaegt", "🧊 ICE Table"),
        ])
    elif _ab_active == "⚗️ Salthydrolyse":
        _show_salthydrolyse_tab()
        _quick_links([
            ("Svag syre/base", "acids-bases", "Svag syre/base"),
            ("Buffer", "acids-bases", "Buffer"),
        ])
    elif _ab_active == "Buffer":
        show_buffers_tab()
        _quick_links([
            ("Svag syre/base", "acids-bases", "Svag syre/base"),
            ("Titrering", "acids-bases", "Titrering"),
        ])
    elif _ab_active == "Titrering":
        show_titrations_tab()
        _quick_links([
            ("Stærk syre/base", "acids-bases", "Stærk syre/base"),
            ("Svag syre/base", "acids-bases", "Svag syre/base"),
            ("Buffer", "acids-bases", "Buffer"),
        ])
    elif _ab_active == "🧮 Debye-Hückel":
        _show_debye_huckel_tab()
        _quick_links([
            ("Svag syre/base", "acids-bases", "Svag syre/base"),
            ("⚗️ Salthydrolyse", "acids-bases", "⚗️ Salthydrolyse"),
            ("Buffer", "acids-bases", "Buffer"),
        ])
    elif _ab_active == "📋 pH-beregner":
        show_pH_calculator_page()


def _show_salthydrolyse_tab():
    """pH af saltopløsninger via hydrolyse – DTU-relevant."""
    import math
    KW = 1.0e-14

    st.markdown("### ⚗️ Salthydrolyse – pH af saltopløsninger")
    st.markdown(
        "Salte af svag syre + stærk base (fx CH₃COONa) eller stærk syre + svag base (fx NH₄Cl) "
        "giver sur/basisk opløsning pga. hydrolyse af det konjugerede ion."
    )

    salt_type = st.radio(
        "Salttype:",
        [
            "Svag syre + stærk base (fx CH₃COONa → basisk)",
            "Stærk syre + svag base (fx NH₄Cl → sur)",
            "Svag syre + svag base (fx CH₃COONH₄)",
        ],
        key="sh_type",
    )

    col1, col2 = st.columns(2)
    with col1:
        C = st.number_input("Saltkoncentration C (mol/L):", value=0.10, min_value=1e-9,
                            format="%.4f", key="sh_conc")
    with col2:
        if "svag syre + stærk base" in salt_type:
            ka = st.number_input("Ka for den svage syre:", value=1.8e-5, min_value=1e-14,
                                  format="%.2e", key="sh_ka")
        elif "stærk syre + svag base" in salt_type:
            kb = st.number_input("Kb for den svage base:", value=1.8e-5, min_value=1e-14,
                                  format="%.2e", key="sh_kb")
        else:
            ka = st.number_input("Ka for den svage syre:", value=1.8e-5, min_value=1e-14,
                                  format="%.2e", key="sh_ka2")
            kb = st.number_input("Kb for den svage base:", value=1.8e-5, min_value=1e-14,
                                  format="%.2e", key="sh_kb2")

    if st.button("Beregn pH", type="primary", key="sh_btn"):
        try:
            if "svag syre + stærk base" in salt_type:
                # Kh = Kw/Ka (hydrolyse af A⁻)
                # A⁻ + H₂O ⇌ HA + OH⁻
                Kh = KW / ka
                pka = -math.log10(ka)
                # ICE approx: [OH⁻] = sqrt(Kh * C)
                oh = math.sqrt(Kh * C)
                poh = -math.log10(oh)
                pH = 14 - poh
                alpha_h = oh / C * 100

                st.success(f"**pH = {pH:.3f}** (basisk opløsning ✓)")
                st.markdown(f"""
**Trin-for-trin:**

1. Hydrolyse: A⁻ + H₂O ⇌ HA + OH⁻
2. K_h = Kw / Ka = {KW:.2e} / {ka:.2e} = **{Kh:.3e}**
3. ICE-tabel: [OH⁻] ≈ √(K_h × C) = √({Kh:.3e} × {C:.4f}) = **{oh:.4e} M**
4. pOH = −log({oh:.4e}) = **{poh:.3f}**
5. pH = 14 − pOH = 14 − {poh:.3f} = **{pH:.3f}**
6. Hydrolysationsgrad: α = {oh:.4e}/{C:.4f} × 100 = **{alpha_h:.3f}%**

💡 Alternativ formel: pH = 7 + ½(pKa + log C) = 7 + ½({pka:.3f} + log({C:.4f})) = **{7 + 0.5*(pka + math.log10(C)):.3f}**
""")
                st.info(f"K_h = {Kh:.3e} – hydrolysekonstant (lille → kun svag hydrolyse)")

            elif "stærk syre + svag base" in salt_type:
                # Kh = Kw/Kb (hydrolyse af BH⁺)
                # BH⁺ + H₂O ⇌ B + H₃O⁺
                Kh = KW / kb
                pkb = -math.log10(kb)
                pka_conj = 14 - pkb
                h = math.sqrt(Kh * C)
                pH = -math.log10(h)
                alpha_h = h / C * 100

                st.success(f"**pH = {pH:.3f}** (sur opløsning ✓)")
                st.markdown(f"""
**Trin-for-trin:**

1. Hydrolyse: BH⁺ + H₂O ⇌ B + H₃O⁺
2. K_h = Kw / Kb = {KW:.2e} / {kb:.2e} = **{Kh:.3e}**
3. ICE-tabel: [H₃O⁺] ≈ √(K_h × C) = √({Kh:.3e} × {C:.4f}) = **{h:.4e} M**
4. pH = −log({h:.4e}) = **{pH:.3f}**
5. Hydrolysationsgrad: α = {h:.4e}/{C:.4f} × 100 = **{alpha_h:.3f}%**

💡 Alternativ formel: pH = 7 − ½(pKb + log C) = 7 − ½({pkb:.3f} + log({C:.4f})) = **{7 - 0.5*(pkb + math.log10(C)):.3f}**
""")

            else:  # Svag syre + svag base
                # pH ≈ 7 + ½(pKa − pKb)
                pka = -math.log10(ka)
                pkb = -math.log10(kb)
                pH_approx = 7 + 0.5 * (pka - pkb)
                Kh1 = KW / ka
                Kh2 = KW / kb

                st.success(f"**pH ≈ {pH_approx:.3f}** (approx. formel)")
                st.markdown(f"""
**Trin-for-trin (approx. formel):**

For salt af svag syre (Ka) og svag base (Kb):

pH ≈ 7 + ½(pKa − pKb)

1. pKa = −log({ka:.2e}) = **{pka:.3f}**
2. pKb = −log({kb:.2e}) = **{pkb:.3f}**
3. pH ≈ 7 + ½({pka:.3f} − {pkb:.3f}) = **{pH_approx:.3f}**

📌 Hvis pKa = pKb → pH = 7 (neutral opløsning)
📌 Gyldigt når Ka og Kb er af sammenlignelig størrelse.
""")
                st.caption(
                    f"K_h(syre) = Kw/Ka = {Kh1:.2e}, K_h(base) = Kw/Kb = {Kh2:.2e}"
                )

        except Exception as exc:
            st.error(f"Fejl: {exc}")

    st.markdown("---")
    st.markdown("**Kendte eksempler:**")
    ex_data = [
        ("CH₃COONa", "Svag syre + stærk base", "Ka(CH₃COOH) = 1,8×10⁻⁵", "Basisk, pH > 7"),
        ("NH₄Cl", "Stærk syre + svag base", "Kb(NH₃) = 1,8×10⁻⁵", "Sur, pH < 7"),
        ("NaCl", "Stærk syre + stærk base", "—", "Neutral, pH = 7"),
        ("CH₃COONH₄", "Svag syre + svag base", "Ka ≈ Kb → pH ≈ 7", "Næsten neutral"),
    ]
    import pandas as pd
    st.dataframe(
        pd.DataFrame(ex_data, columns=["Salt", "Type", "Konstant", "pH"]),
        use_container_width=True, hide_index=True,
    )


def show_strong_acids_bases_tab():
    """Display the strong acids/bases tab."""
    st.markdown("### 💪 Strong Acids & Bases")
    
    # Mode selection
    mode = st.radio(
        "Calculation Mode:",
        ["Single strong acid", "Single strong base", "Mixture of strong acid + base"],
        horizontal=True
    )
    _strong_help = {
        "Single strong acid": "💡 **Hvornår?** Stærke syrer (HCl, HNO₃, H₂SO₄) ioniserer 100% → pH = −log[H⁺].",
        "Single strong base": "💡 **Hvornår?** Stærke baser (NaOH, KOH) ioniserer 100% → pOH = −log[OH⁻], pH = 14 − pOH.",
        "Mixture of strong acid + base": "💡 **Hvornår?** Du blander en stærk syre og en stærk base. Beregner nettosyre/base efter neutralisation.",
    }
    st.info(_strong_help[mode])

    if mode == "Single strong acid":
        st.markdown("#### Strong Acid pH")
        concentration = st.number_input("Acid concentration (M):", value=0.1, step=0.01, min_value=1e-7, key="strong_acid_conc")
        volume = st.number_input("Volume (L):", value=1.0, step=0.1, min_value=0.001, key="strong_acid_vol")
        
        if st.button("Calculate pH", type="primary", key="strong_acid_calc_ph"):
            try:
                with st.spinner("Calculating..."):
                    ph, steps, metadata = calculate_strong_acid_ph(concentration, volume)
                
                st.success(f"✅ **pH = {ph:.3f}**")
                
                with st.expander("🔍 Vis trin", expanded=False):
                    for step in steps:
                        st.markdown(step)
            
            except Exception as e:
                st.error(f"❌ **Fejl**: {str(e)}")
    
    elif mode == "Single strong base":
        st.markdown("#### Strong Base pH")
        concentration = st.number_input("Base concentration (M):", value=0.01, step=0.001, min_value=1e-7, key="strong_base_conc")
        volume = st.number_input("Volume (L):", value=1.0, step=0.1, min_value=0.001, key="strong_base_vol")
        
        if st.button("Calculate pH", type="primary", key="strong_base_calc_ph"):
            try:
                with st.spinner("Calculating..."):
                    ph, steps, metadata = calculate_strong_base_ph(concentration, volume)
                
                st.success(f"✅ **pH = {ph:.3f}**")
                
                with st.expander("🔍 Vis trin", expanded=False):
                    for step in steps:
                        st.markdown(step)
            
            except Exception as e:
                st.error(f"❌ **Fejl**: {str(e)}")
    
    else:  # Mixture
        st.markdown("#### Strong Acid + Base Mixture")
        col1, col2 = st.columns(2)
        
        with col1:
            acid_conc = st.number_input("Acid concentration (M):", value=0.1, step=0.01, min_value=1e-7, key="strong_mix_acid_conc")
            acid_vol = st.number_input("Acid volume (L):", value=1.0, step=0.1, min_value=0.001, key="strong_mix_acid_vol")
        
        with col2:
            base_conc = st.number_input("Base concentration (M):", value=0.05, step=0.01, min_value=1e-7, key="strong_mix_base_conc")
            base_vol = st.number_input("Base volume (L):", value=1.0, step=0.1, min_value=0.001, key="strong_mix_base_vol")
        
        if st.button("Calculate pH", type="primary", key="strong_mix_calc_ph"):
            try:
                with st.spinner("Calculating..."):
                    ph, steps, metadata = calculate_strong_acid_base_mixture(
                        acid_conc, acid_vol, base_conc, base_vol
                    )
                
                st.success(f"✅ **pH = {ph:.3f}**")
                st.info(f"**Limiting species:** {metadata['limiting_species']}")
                
                with st.expander("🔍 Vis trin", expanded=False):
                    for step in steps:
                        st.markdown(step)
            
            except Exception as e:
                st.error(f"❌ **Fejl**: {str(e)}")


def _show_debye_huckel_tab():
    """Debye-Hückel aktivitetskoefficent – DTU 26021 relevant."""
    import math
    st.markdown("### 🧮 Debye-Hückel – aktivitetskoefficenter")
    st.latex(r"\log \gamma_\pm = -A |z_+ z_-| \sqrt{I}")
    st.markdown(
        "Aktivitetskoefficienten γ± korrigerer for ioniske interaktioner i opløsninger med høj ionsstyrke. "
        "**Gyldigt for I < 0,01 M** (forenklet Debye-Hückel). Den udvidede form er gyldig op til I ≈ 0,1 M."
    )

    mode_dh = st.radio(
        "Beregningstype:",
        ["Simpel Debye-Hückel (lav I)", "Udvidet Debye-Hückel", "Beregn ionsstyrke I"],
        horizontal=True, key="dh_mode",
    )

    A = 0.509  # 25°C, vand
    B = 3.281  # nm⁻¹

    if mode_dh in ["Simpel Debye-Hückel (lav I)", "Udvidet Debye-Hückel"]:
        col1, col2 = st.columns(2)
        with col1:
            z_plus = st.number_input("Ladning z₊ (kation):", value=1, min_value=1, max_value=4, step=1, key="dh_zp")
            z_minus = st.number_input("Ladning |z₋| (anion):", value=1, min_value=1, max_value=4, step=1, key="dh_zm")
            I_val = st.number_input("Ionsstyrke I (mol/L):", value=0.01, min_value=1e-6, format="%.4f", step=0.001, key="dh_I")
        with col2:
            if mode_dh == "Udvidet Debye-Hückel":
                a_ion = st.number_input(
                    "Ionparameter a (nm):", value=0.3, min_value=0.1, max_value=1.0, step=0.05, key="dh_a",
                    help="Typiske værdier: Na⁺≈0,4, K⁺≈0,3, Ca²⁺≈0,6, Cl⁻≈0,3 nm",
                )
            st.markdown("**Konstanter (25°C, H₂O):**")
            st.markdown(f"- A = {A}")
            st.markdown(f"- B = {B} nm⁻¹")

        if st.button("Beregn γ±", type="primary", key="dh_calc"):
            sqrt_I = math.sqrt(I_val)
            if mode_dh == "Simpel Debye-Hückel (lav I)":
                log_gamma = -A * abs(z_plus * z_minus) * sqrt_I
                denom_str = ""
                formula_note = "Simpel Debye-Hückel"
            else:
                denom = 1 + B * a_ion * sqrt_I
                log_gamma = -A * abs(z_plus * z_minus) * sqrt_I / denom
                denom_str = f" / (1 + {B}×{a_ion}×{sqrt_I:.4f})"
                formula_note = "Udvidet Debye-Hückel"

            gamma = 10 ** log_gamma

            st.success(f"✅ **log γ± = {log_gamma:.4f}** → **γ± = {gamma:.4f}**")

            with st.expander("🔍 Trin-for-trin", expanded=True):
                st.markdown(f"""
**{formula_note}**

1. |z₊ × z₋| = |{z_plus} × {z_minus}| = **{abs(z_plus * z_minus)}**
2. √I = √{I_val:.4f} = **{sqrt_I:.4f}**
3. log γ± = −{A} × {abs(z_plus * z_minus)} × {sqrt_I:.4f}{denom_str} = **{log_gamma:.4f}**
4. γ± = 10^({log_gamma:.4f}) = **{gamma:.4f}**

**Fortolkning:** γ± = {gamma:.4f} betyder, at den effektive koncentration (aktivitet) er {gamma*100:.1f}% af den nominelle koncentration.
""")

            if I_val > 0.1 and mode_dh == "Simpel Debye-Hückel (lav I)":
                st.warning("⚠️ I > 0,1 M – simpel Debye-Hückel er ikke præcis ved denne ionsstyrke. Brug udvidet form.")
            elif I_val > 0.5:
                st.warning("⚠️ I > 0,5 M – Debye-Hückel er generelt ikke gyldig. Brug Pitzer-modellen.")

            st.markdown("---")
            st.markdown("**Aktivitet a± = γ± × c/c°**  \nBrug γ± til at korrigere Ka, Ksp mv. for ionstyrkeeffekter.")

    else:  # Beregn ionsstyrke
        st.markdown("#### Beregn ionsstyrke I fra ionsammensætning")
        st.latex(r"I = \frac{1}{2} \sum_i c_i z_i^2")
        st.markdown("Tilføj ioner med deres koncentration og ladning:")

        if "dh_ions" not in st.session_state:
            st.session_state["dh_ions"] = [
                {"name": "Na⁺", "c": 0.10, "z": 1},
                {"name": "Cl⁻", "c": 0.10, "z": 1},
            ]

        col_add, col_reset = st.columns([3, 1])
        with col_add:
            if st.button("➕ Tilføj ion", key="dh_add_ion"):
                st.session_state["dh_ions"].append({"name": "", "c": 0.01, "z": 1})
        with col_reset:
            if st.button("↩️ Nulstil", key="dh_reset_ions"):
                st.session_state["dh_ions"] = [
                    {"name": "Na⁺", "c": 0.10, "z": 1},
                    {"name": "Cl⁻", "c": 0.10, "z": 1},
                ]

        ions = st.session_state["dh_ions"]
        for i, ion in enumerate(ions):
            c1, c2, c3 = st.columns([2, 2, 1])
            with c1:
                ion["name"] = st.text_input(f"Ion {i+1}", value=ion["name"], key=f"dh_ion_name_{i}")
            with c2:
                ion["c"] = st.number_input(f"c (M)", value=ion["c"], min_value=0.0, step=0.001,
                                            format="%.4f", key=f"dh_ion_c_{i}")
            with c3:
                ion["z"] = st.number_input(f"|z|", value=ion["z"], min_value=1, max_value=4, step=1,
                                            key=f"dh_ion_z_{i}")

        I_calc = 0.5 * sum(ion["c"] * ion["z"] ** 2 for ion in ions)
        st.metric("Ionsstyrke I", f"{I_calc:.4f} mol/L")

        terms = " + ".join(f"{ion['c']:.4f}×{ion['z']}²" for ion in ions if ion["name"])
        st.markdown(f"I = ½ × ({terms}) = **{I_calc:.4f} mol/L**")

        if I_calc < 0.01:
            st.success("✅ Simpel Debye-Hückel er præcis (I < 0,01 M)")
        elif I_calc < 0.1:
            st.info("ℹ️ Brug udvidet Debye-Hückel (0,01 < I < 0,1 M)")
        else:
            st.warning("⚠️ I > 0,1 M – Debye-Hückel er usikker")

    st.markdown("---")
    st.markdown("**Referencetabel – typiske ionparametre a (nm):**")
    ref_data = {
        "Ion": ["H⁺", "Li⁺", "Na⁺", "K⁺, NH₄⁺", "Ca²⁺, Cu²⁺, Zn²⁺", "Mg²⁺, Be²⁺", "Al³⁺, Fe³⁺", "F⁻, OH⁻", "Cl⁻, Br⁻, I⁻", "SO₄²⁻"],
        "z": [1, 1, 1, 1, 2, 2, 3, 1, 1, 2],
        "a (nm)": [0.9, 0.6, 0.4, 0.3, 0.6, 0.8, 0.9, 0.35, 0.3, 0.4],
    }
    import pandas as pd
    st.dataframe(pd.DataFrame(ref_data), hide_index=True, use_container_width=True)


def show_weak_acids_bases_tab():
    """Display the weak acids/bases tab."""
    st.markdown("### 🥶 Weak Acids & Bases")

    # Mode selection
    mode = st.radio(
        "Calculation Mode:",
        ["Weak acid", "Weak base", "🔬 Ioniseringsgrad (α)"],
        horizontal=True
    )
    _weak_help = {
        "Weak acid": "💡 **Hvornår?** Svage syrer (eddikesyre, citronsyre) ioniserer kun delvist. Du skal kende Ka og startkoncentrationen.",
        "Weak base": "💡 **Hvornår?** Svage baser (ammoniak, aminer) reagerer delvist med vand. Du skal kende Kb (eller Ka for den konjugerede syre).",
        "🔬 Ioniseringsgrad (α)": "💡 **Hvornår?** Du vil vide, hvilken andel af syren/basen der er ioniseret ved ligevægt – fx til at afgøre om 5%-reglen holder.",
    }
    st.info(_weak_help[mode])

    if mode == "Weak acid":
        st.markdown("#### Weak Acid pH")
        col1, col2 = st.columns(2)
        
        with col1:
            concentration = st.number_input("Acid concentration (M):", value=0.1, step=0.01, min_value=1e-7, key="weak_acid_conc")
            stoich_h3o = st.number_input("H₃O⁺ ions per molecule (n):", value=1.0, step=0.5, min_value=0.5, key="weak_acid_stoich")
        
        with col2:
            ka = st.number_input("Ka value:", value=1.8e-5, step=1e-6, min_value=1e-12, format="%.2e", key="weak_acid_ka")
            reaction_eq = st.text_input("Reaction equation (optional):", value="HA ⇌ H₃O⁺ + A⁻", key="weak_acid_rxn")
        
        if st.button("Calculate pH", type="primary", key="weak_acid_calc_ph"):
            try:
                with st.spinner("Calculating..."):
                    ph, steps, metadata = calculate_weak_acid_ph(concentration, ka, stoichiometry=stoich_h3o)
                
                st.success(f"✅ **pH = {ph:.3f}**")
                st.info(f"**Percent ionization:** {metadata['percent_ionization']:.2f}%")
                
                with st.expander("🔍 Vis trin", expanded=False):
                    for step in steps:
                        st.markdown(step)
            
            except Exception as e:
                st.error(f"❌ **Fejl**: {str(e)}")
    
    else:  # Weak base
        st.markdown("#### Weak Base pH")
        col1, col2 = st.columns(2)
        
        with col1:
            concentration = st.number_input("Base concentration (M):", value=0.1, step=0.01, min_value=1e-7, key="weak_base_conc")
            stoich_oh = st.number_input("OH⁻ ions per molecule (n):", value=1.0, step=0.5, min_value=0.5, key="weak_base_stoich")
        
        with col2:
            reaction_eq = st.text_input("Reaction equation (optional):", value="B + H₂O ⇌ BH⁺ + OH⁻", key="weak_base_rxn")
        
        kb_method = st.radio(
            "Kb input method:",
            ["Direct Kb value", "Ka of conjugate acid"],
            horizontal=True,
            key="weak_base_method"
        )
        _kb_help = {
            "Direct Kb value": "💡 Du kender Kb direkte (fx fra en tabel). Kb for NH₃ er 1,8 × 10⁻⁵.",
            "Ka of conjugate acid": "💡 Du kender Ka for den konjugerede syre i stedet. Beregner Kb = Kw / Ka automatisk.",
        }
        st.caption(_kb_help[kb_method])

        if kb_method == "Direct Kb value":
            kb = st.number_input("Kb value:", value=1.8e-5, step=1e-6, min_value=1e-12, format="%.2e", key="weak_base_kb")
            ka_conjugate = None
        else:
            kb = None
            ka_conjugate = st.number_input("Ka of conjugate acid:", value=5.6e-10, step=1e-11, min_value=1e-12, format="%.2e", key="weak_base_ka_conj")
        
        if st.button("Calculate pH", type="primary", key="weak_base_calc_ph"):
            try:
                with st.spinner("Calculating..."):
                    ph, steps, metadata = calculate_weak_base_ph(
                        concentration, kb=kb, ka_conjugate=ka_conjugate, stoichiometry=stoich_oh
                    )
                
                st.success(f"✅ **pH = {ph:.3f}**")
                if 'percent_ionization' in metadata:
                    st.info(f"**Percent ionization:** {metadata['percent_ionization']:.2f}%")
                
                with st.expander("🔍 Vis trin", expanded=False):
                    for step in steps:
                        st.markdown(step)
            
            except Exception as e:
                st.error(f"❌ **Fejl**: {str(e)}")

    if mode == "🔬 Ioniseringsgrad (α)":
        import math
        st.markdown("#### 🔬 Ioniseringsgrad α for svag syre/base")
        st.latex(r"\alpha = \frac{[\mathrm{H^+}]}{C_0} \quad \text{(svag syre)} \qquad \alpha = \frac{[\mathrm{OH^-}]}{C_0} \quad \text{(svag base)}")
        st.caption("α angiver brøkdelen af syren/basen der er ioniseret ved ligevægt. Procentvis ionisering = α × 100%.")

        acid_or_base = st.radio("Type:", ["Svag syre", "Svag base"], horizontal=True, key="alpha_type")
        col1, col2 = st.columns(2)
        with col1:
            C0 = st.number_input("Startkoncentration C₀ (mol/L):", value=0.10, min_value=1e-10,
                                  format="%.6f", key="alpha_C0")
        with col2:
            if acid_or_base == "Svag syre":
                K = st.number_input("Ka:", value=1.8e-5, min_value=1e-14, format="%.2e", key="alpha_Ka")
            else:
                K = st.number_input("Kb:", value=1.8e-5, min_value=1e-14, format="%.2e", key="alpha_Kb")

        if st.button("Beregn ioniseringsgrad", type="primary", key="alpha_btn"):
            # Solve x² + Ka*x - Ka*C0 = 0 (exact quadratic)
            a_coef, b_coef, c_coef = 1.0, K, -K * C0
            discriminant = b_coef**2 - 4 * a_coef * c_coef
            x = (-b_coef + math.sqrt(discriminant)) / (2 * a_coef)
            alpha = x / C0
            pct = alpha * 100
            approx = math.sqrt(K / C0)

            five_pct_ok = pct < 5.0

            if acid_or_base == "Svag syre":
                pH = -math.log10(x)
                result_label = f"[H⁺] = {x:.4e} M,  pH = {pH:.3f}"
            else:
                pOH = -math.log10(x)
                pH = 14 - pOH
                result_label = f"[OH⁻] = {x:.4e} M,  pH = {pH:.3f}"

            st.success(f"**α = {alpha:.4f}  →  {pct:.2f}% ioniseret**")
            st.info(result_label)

            if five_pct_ok:
                st.success("✅ 5%-reglen holder (α < 5%) – approx. formel er gyldig.")
            else:
                st.warning(f"⚠️ 5%-reglen holder IKKE (α = {pct:.1f}% > 5%) – brug den eksakte kvaderatløsning.")

            st.markdown(f"""
**Trin-for-trin (eksakt):**

ICE-tabel for HA ⇌ H⁺ + A⁻:

| | HA | H⁺ | A⁻ |
|---|---|---|---|
| Start | {C0:.4f} | 0 | 0 |
| Ændring | −x | +x | +x |
| Ligevægt | {C0:.4f}−x | x | x |

Ka = x² / ({C0:.4f} − x)

Eksakt: x = (−Ka + √(Ka² + 4·Ka·C₀)) / 2 = **{x:.4e} M**

Approx. (5%-regel): x ≈ √(Ka × C₀) = √({K:.2e} × {C0:.4f}) = **{approx:.4e} M** (fejl: {abs(x-approx)/x*100:.1f}%)

α = x / C₀ = {x:.4e} / {C0:.4f} = **{alpha:.4f}** = **{pct:.2f}%**
""")

            st.markdown("---")
            st.caption("💡 Jo mere fortyndet (lavere C₀) og jo svagere syren (højere Ka), jo større ioniseringsgrad.")


def show_buffers_tab():
    """Display the buffers tab."""
    st.markdown("### 🧪 Buffer Solutions")

    # Mode selection
    mode = st.radio(
        "Buffer calculation mode:",
        ["Known concentrations", "Mixing solutions", "Target pH", "📊 Bufferkapacitet β"],
        horizontal=True
    )
    _buffer_help = {
        "Known concentrations": "💡 **Hvornår?** Du kender allerede [HA] og [A⁻] i opløsningen og vil finde pH via Henderson-Hasselbalch.",
        "Mixing solutions": "💡 **Hvornår?** Du blander en syreløsning og en baseløsning og vil finde pH af den resulterende buffer.",
        "Target pH": "💡 **Hvornår?** Du ved hvilken pH du ønsker, og vil finde det rette forhold mellem syre og base.",
        "📊 Bufferkapacitet β": "💡 **Hvornår?** Du vil beregne, hvor meget syre/base bufferen kan optage uden stor pH-ændring. β er maksimal ved pH = pKa.",
    }
    st.info(_buffer_help[mode])
    
    if mode == "Known concentrations":
        st.markdown("#### Buffer pH from Concentrations")
        col1, col2 = st.columns(2)
        
        with col1:
            conc_a_minus = st.number_input("[A⁻] concentration (M):", value=0.1, step=0.01, min_value=1e-7, key="buf_conc_a")
            conc_ha = st.number_input("[HA] concentration (M):", value=0.1, step=0.01, min_value=1e-7, key="buf_conc_ha")
        
        with col2:
            ka = st.number_input("Ka value:", value=1.8e-5, step=1e-6, min_value=1e-12, format="%.2e", key="buf_ka")
            pka = st.number_input("pKa value (optional):", value=None, step=0.01, help="Leave empty to calculate from Ka", key="buf_pka")
        
        if st.button("Calculate pH", type="primary", key="buffer_known_calc_ph"):
            try:
                with st.spinner("Calculating..."):
                    ph, steps, metadata = calculate_buffer_ph(
                        conc_a_minus, conc_ha, ka, pka
                    )
                
                st.success(f"✅ **pH = {ph:.3f}**")
                
                with st.expander("🔍 Vis trin", expanded=False):
                    for step in steps:
                        st.markdown(step)
            
            except Exception as e:
                st.error(f"❌ **Fejl**: {str(e)}")
    
    elif mode == "Mixing solutions":
        st.markdown("#### Buffer pH fra blanding")

        mix_type = st.radio(
            "Blandingstype:",
            [
                "Svag syre + konjugeret base",
                "Svag syre + stærk base (NaOH/KOH)",
                "Svag base + stærk syre (HCl/HNO₃)",
                "Tilsæt syre/base til eksisterende buffer",
            ],
            horizontal=False,
            key="buf_mix_type",
        )
        st.markdown("---")

        import math as _math

        if mix_type == "Svag syre + konjugeret base":
            st.info("💡 Bland HA og A⁻ direkte – Henderson-Hasselbalch bruges.")
            col1, col2 = st.columns(2)
            with col1:
                acid_conc = st.number_input("Svag syre [HA] (M):", value=0.1, step=0.01, min_value=1e-7, key="buf_acid_conc")
                acid_vol  = st.number_input("Volumen syre (L):", value=1.0, step=0.1, min_value=0.001, key="buf_acid_vol")
            with col2:
                base_conc = st.number_input("Konjugeret base [A⁻] (M):", value=0.1, step=0.01, min_value=1e-7, key="buf_base_conc")
                base_vol  = st.number_input("Volumen base (L):", value=1.0, step=0.1, min_value=0.001, key="buf_base_vol")
                ka        = st.number_input("Ka:", value=1.8e-5, step=1e-6, min_value=1e-15, format="%.2e", key="buf_mix_ka")

            if st.button("Beregn pH", type="primary", key="buf_mix_classic"):
                try:
                    ph, steps, _ = calculate_buffer_mixing_ph(acid_conc, acid_vol, base_conc, base_vol, ka)
                    st.success(f"✅ **pH = {ph:.3f}**")
                    with st.expander("🔍 Vis trin", expanded=False):
                        for step in steps:
                            st.markdown(step)
                except Exception as e:
                    st.error(f"❌ **Fejl**: {str(e)}")

        elif mix_type == "Svag syre + stærk base (NaOH/KOH)":
            st.info(
                "💡 **Hvornår?** Du blander en svag syre (HA) med en stærk base (NaOH).  \n"
                "Basen neutraliserer en del af syren: HA + OH⁻ → A⁻ + H₂O.  \n"
                "Resultatet er en bufferblanding af resterende HA og dannet A⁻."
            )
            col1, col2 = st.columns(2)
            with col1:
                c_ha  = st.number_input("Svag syre [HA] (M):", value=0.100, step=0.01, min_value=1e-7, key="bms_c_ha")
                v_ha  = st.number_input("Volumen HA (L):", value=1.0, step=0.1, min_value=0.001, key="bms_v_ha")
            with col2:
                c_oh  = st.number_input("Stærk base [NaOH] (M):", value=0.050, step=0.01, min_value=1e-7, key="bms_c_oh")
                v_oh  = st.number_input("Volumen NaOH (L):", value=1.0, step=0.1, min_value=0.001, key="bms_v_oh")
                ka2   = st.number_input("Ka for svag syre:", value=1.8e-5, step=1e-6, min_value=1e-15, format="%.2e", key="bms_ka")

            if st.button("Beregn pH", type="primary", key="buf_mix_sa_sb"):
                n_ha  = c_ha * v_ha
                n_oh  = c_oh * v_oh
                pka   = -_math.log10(ka2)
                v_tot = v_ha + v_oh

                if n_oh >= n_ha:
                    st.error(
                        f"⚠️ Overskud af base (n_NaOH = {n_oh:.4f} mol ≥ n_HA = {n_ha:.4f} mol). "
                        "Der dannes ingen buffer – al syren er neutraliseret."
                    )
                else:
                    n_a   = n_oh           # moles A⁻ dannet
                    n_ha_rest = n_ha - n_oh  # moles HA tilbage
                    ratio = n_a / n_ha_rest
                    ph    = pka + _math.log10(ratio)
                    c_a_eq  = n_a / v_tot
                    c_ha_eq = n_ha_rest / v_tot

                    st.success(f"✅ **pH = {ph:.3f}**")
                    st.markdown(
                        f"**pKa** = {pka:.3f}  \n"
                        f"**n(HA)** = {c_ha} × {v_ha} = {n_ha:.4f} mol  \n"
                        f"**n(NaOH)** = {c_oh} × {v_oh} = {n_oh:.4f} mol"
                    )
                    with st.expander("🔍 Trin-for-trin", expanded=True):
                        st.markdown(f"""
**Reaktion:** HA + OH⁻ → A⁻ + H₂O

| | HA | OH⁻ | A⁻ |
|--|--|--|--|
| Før (mol) | {n_ha:.4f} | {n_oh:.4f} | 0 |
| Ændring | −{n_oh:.4f} | −{n_oh:.4f} | +{n_oh:.4f} |
| Efter (mol) | **{n_ha_rest:.4f}** | 0 | **{n_a:.4f}** |

**Henderson-Hasselbalch:**
pH = pKa + log([A⁻]/[HA])
pH = {pka:.3f} + log({n_a:.4f}/{n_ha_rest:.4f})
pH = {pka:.3f} + log({ratio:.4f})
pH = {pka:.3f} + ({_math.log10(ratio):.3f})
**pH = {ph:.3f}**

Koncentrationer i blandingen (V_total = {v_tot:.3f} L):
[HA] = {c_ha_eq:.4f} M, [A⁻] = {c_a_eq:.4f} M
""")

        elif mix_type == "Svag base + stærk syre (HCl/HNO₃)":
            st.info(
                "💡 **Hvornår?** Du blander en konjugeret base (A⁻) med en stærk syre (HCl).  \n"
                "Syren neutraliserer en del af basen: A⁻ + H⁺ → HA.  \n"
                "Resultatet er en bufferblanding af resterende A⁻ og dannet HA."
            )
            col1, col2 = st.columns(2)
            with col1:
                c_a2  = st.number_input("Svag base [A⁻] (M):", value=0.100, step=0.01, min_value=1e-7, key="bmb_c_a")
                v_a2  = st.number_input("Volumen A⁻ (L):", value=1.0, step=0.1, min_value=0.001, key="bmb_v_a")
            with col2:
                c_h2  = st.number_input("Stærk syre [HCl] (M):", value=0.050, step=0.01, min_value=1e-7, key="bmb_c_h")
                v_h2  = st.number_input("Volumen HCl (L):", value=1.0, step=0.1, min_value=0.001, key="bmb_v_h")
                ka3   = st.number_input("Ka for den svage syre HA:", value=1.8e-5, step=1e-6, min_value=1e-15, format="%.2e", key="bmb_ka")

            if st.button("Beregn pH", type="primary", key="buf_mix_wb_sa"):
                n_a2  = c_a2 * v_a2
                n_h2  = c_h2 * v_h2
                pka3  = -_math.log10(ka3)
                v_tot2 = v_a2 + v_h2

                if n_h2 >= n_a2:
                    st.error(
                        f"⚠️ Overskud af syre (n_HCl = {n_h2:.4f} mol ≥ n_A⁻ = {n_a2:.4f} mol). "
                        "Der dannes ingen buffer – al basen er neutraliseret."
                    )
                else:
                    n_ha2      = n_h2            # moles HA dannet
                    n_a2_rest  = n_a2 - n_h2     # moles A⁻ tilbage
                    ratio2     = n_a2_rest / n_ha2
                    ph2        = pka3 + _math.log10(ratio2)
                    c_a_eq2    = n_a2_rest / v_tot2
                    c_ha_eq2   = n_ha2 / v_tot2

                    st.success(f"✅ **pH = {ph2:.3f}**")
                    st.markdown(
                        f"**pKa** = {pka3:.3f}  \n"
                        f"**n(A⁻)** = {c_a2} × {v_a2} = {n_a2:.4f} mol  \n"
                        f"**n(HCl)** = {c_h2} × {v_h2} = {n_h2:.4f} mol"
                    )
                    with st.expander("🔍 Trin-for-trin", expanded=True):
                        st.markdown(f"""
**Reaktion:** A⁻ + H⁺ → HA

| | A⁻ | H⁺ | HA |
|--|--|--|--|
| Før (mol) | {n_a2:.4f} | {n_h2:.4f} | 0 |
| Ændring | −{n_h2:.4f} | −{n_h2:.4f} | +{n_h2:.4f} |
| Efter (mol) | **{n_a2_rest:.4f}** | 0 | **{n_ha2:.4f}** |

**Henderson-Hasselbalch:**
pH = pKa + log([A⁻]/[HA])
pH = {pka3:.3f} + log({n_a2_rest:.4f}/{n_ha2:.4f})
pH = {pka3:.3f} + log({ratio2:.4f})
pH = {pka3:.3f} + ({_math.log10(ratio2):.3f})
**pH = {ph2:.3f}**

Koncentrationer i blandingen (V_total = {v_tot2:.3f} L):
[A⁻] = {c_a_eq2:.4f} M, [HA] = {c_ha_eq2:.4f} M
""")

        else:  # Tilsæt syre/base til eksisterende buffer
            st.info(
                "💡 **Hvornår?** Du har en eksisterende buffer og tilsætter stærk syre eller stærk base.  \n"
                "Typisk eksamen: buffer lavet af NH₃ + NH₄Cl (eller HA + A⁻), derefter tilsættes NaOH/HCl.  \n"
                "Understøtter både **Ka-system** (eddikesyre/acetat) og **Kb-system** (NH₃/NH₄⁺)."
            )

            buf_sys = st.radio(
                "Buffersystem:",
                ["Ka-system (HA/A⁻ – fx eddikesyre/acetat)", "Kb-system (B/BH⁺ – fx NH₃/NH₄⁺)"],
                horizontal=True,
                key="bab_sys",
            )
            _is_kb_sys = buf_sys.startswith("Kb")

            if _is_kb_sys:
                st.markdown(
                    "_I et Kb-system er den **konjugerede syre (BH⁺)** fx NH₄⁺ og den **svage base (B)** fx NH₃.  \n"
                    "Angiv Kb for basen – Ka beregnes automatisk: Ka = Kw / Kb_"
                )
                _label_acid = "Konjugeret syre [BH⁺] (M):"
                _label_base = "Svag base [B] (M):"
                _label_acid_v = "Volumen BH⁺-opløsning (L):"
                _label_base_v = "Volumen B-opløsning (L):"
                _label_k    = "Kb for svag base (B):"
                _k_default  = 1.80e-5
            else:
                _label_acid = "Svag syre [HA] (M):"
                _label_base = "Konjugeret base [A⁻] (M):"
                _label_acid_v = "Volumen HA-opløsning (L):"
                _label_base_v = "Volumen A⁻-opløsning (L):"
                _label_k    = "Ka for svag syre (HA):"
                _k_default  = 1.8e-5

            st.markdown("**Trin 1 – Eksisterende buffer**")
            col1, col2 = st.columns(2)
            with col1:
                c_ha_buf = st.number_input(_label_acid,  value=1.000, step=0.01, min_value=1e-10, key="bab_c_ha")
                v_ha_buf = st.number_input(_label_acid_v, value=0.500, step=0.1,  min_value=0.001, key="bab_v_ha")
            with col2:
                c_a_buf  = st.number_input(_label_base,  value=1.000, step=0.01, min_value=1e-10, key="bab_c_a")
                v_a_buf  = st.number_input(_label_base_v, value=0.500, step=0.1,  min_value=0.001, key="bab_v_a")
                k_buf    = st.number_input(_label_k, value=_k_default, step=1e-6, min_value=1e-15, format="%.2e", key="bab_k")

            if _is_kb_sys:
                _ka_derived = 1e-14 / k_buf
                st.caption(f"Ka(BH⁺) = Kw / Kb = 1×10⁻¹⁴ / {k_buf:.2e} = **{_ka_derived:.4e}** (pKa = {-_math.log10(_ka_derived):.3f})")
            else:
                _ka_derived = k_buf

            st.markdown("**Trin 2 – Tilsæt syre eller base**")
            add_type = st.radio(
                "Tilsæt:",
                ["Stærk syre (HCl/HNO₃)", "Stærk base (NaOH/KOH)"],
                horizontal=True,
                key="bab_add_type",
            )
            col3, col4 = st.columns(2)
            with col3:
                c_add = st.number_input(
                    "Koncentration tilsat opløsning (M):",
                    value=1.00, step=0.01, min_value=1e-10, key="bab_c_add"
                )
            with col4:
                v_add = st.number_input(
                    "Volumen tilsat opløsning (L):",
                    value=0.030, step=0.001, min_value=0.0001, format="%.4f", key="bab_v_add"
                )

            # Labels for display
            _lbl_acid = "BH⁺" if _is_kb_sys else "HA"
            _lbl_base = "B"   if _is_kb_sys else "A⁻"

            if st.button("Beregn ny pH", type="primary", key="buf_mix_add"):
                n_ha_buf  = c_ha_buf * v_ha_buf
                n_a_buf   = c_a_buf  * v_a_buf
                n_add     = c_add    * v_add
                pka_buf   = -_math.log10(_ka_derived)
                v_tot_buf = v_ha_buf + v_a_buf + v_add
                ph_start  = pka_buf + _math.log10(n_a_buf / n_ha_buf)

                if add_type == "Stærk syre (HCl/HNO₃)":
                    # H⁺ + A⁻(eller B) → HA(eller BH⁺)
                    if n_add >= n_a_buf:
                        st.error(
                            f"⚠️ Overskud af syre (n = {n_add:.4f} mol ≥ n({_lbl_base}) = {n_a_buf:.4f} mol). "
                            "Bufferen er overskredet."
                        )
                    else:
                        n_ha_new  = n_ha_buf + n_add
                        n_a_new   = n_a_buf  - n_add
                        ratio_buf = n_a_new / n_ha_new
                        ph_buf    = pka_buf + _math.log10(ratio_buf)
                        st.success(f"✅ **Ny pH = {ph_buf:.3f}**")
                        with st.expander("🔍 Trin-for-trin", expanded=True):
                            st.markdown(f"""
**Buffer (del der bruges):**
- n({_lbl_acid}) = {c_ha_buf} M × {v_ha_buf} L = **{n_ha_buf:.4f} mol**
- n({_lbl_base}) = {c_a_buf} M × {v_a_buf} L = **{n_a_buf:.4f} mol**
{'- Ka(BH⁺) = Kw/Kb = ' + f'{_ka_derived:.4e}' if _is_kb_sys else '- Ka = ' + f'{_ka_derived:.2e}'}
- pKa = **{pka_buf:.3f}**
- pH_start = {pka_buf:.3f} + log({n_a_buf:.4f}/{n_ha_buf:.4f}) = **{ph_start:.3f}**

**Tilsæt stærk syre:**
- n(H⁺) = {c_add} M × {v_add} L = **{n_add:.4f} mol**

**Reaktion:** H⁺ + {_lbl_base} → {_lbl_acid}

| | {_lbl_base} | H⁺ | {_lbl_acid} |
|--|--|--|--|
| Før (mol) | {n_a_buf:.4f} | {n_add:.4f} | {n_ha_buf:.4f} |
| Ændring | −{n_add:.4f} | −{n_add:.4f} | +{n_add:.4f} |
| Efter (mol) | **{n_a_new:.4f}** | 0 | **{n_ha_new:.4f}** |

**Henderson-Hasselbalch:**
pH = pKa + log([{_lbl_base}]/[{_lbl_acid}])
pH = {pka_buf:.3f} + log({n_a_new:.4f}/{n_ha_new:.4f})
pH = {pka_buf:.3f} + ({_math.log10(ratio_buf):.3f})
**pH = {ph_buf:.3f}**

V_total = {v_tot_buf:.4f} L → [{_lbl_acid}] = {n_ha_new/v_tot_buf:.4f} M, [{_lbl_base}] = {n_a_new/v_tot_buf:.4f} M
""")
                else:
                    # OH⁻ + HA(eller BH⁺) → A⁻(eller B) + H₂O
                    if n_add >= n_ha_buf:
                        st.error(
                            f"⚠️ Overskud af base (n = {n_add:.4f} mol ≥ n({_lbl_acid}) = {n_ha_buf:.4f} mol). "
                            "Bufferen er overskredet."
                        )
                    else:
                        n_ha_new  = n_ha_buf - n_add
                        n_a_new   = n_a_buf  + n_add
                        ratio_buf = n_a_new / n_ha_new
                        ph_buf    = pka_buf + _math.log10(ratio_buf)
                        st.success(f"✅ **Ny pH = {ph_buf:.3f}**")
                        with st.expander("🔍 Trin-for-trin", expanded=True):
                            st.markdown(f"""
**Buffer (del der bruges):**
- n({_lbl_acid}) = {c_ha_buf} M × {v_ha_buf} L = **{n_ha_buf:.4f} mol**
- n({_lbl_base}) = {c_a_buf} M × {v_a_buf} L = **{n_a_buf:.4f} mol**
{'- Ka(BH⁺) = Kw/Kb = ' + f'{_ka_derived:.4e}' if _is_kb_sys else '- Ka = ' + f'{_ka_derived:.2e}'}
- pKa = **{pka_buf:.3f}**
- pH_start = {pka_buf:.3f} + log({n_a_buf:.4f}/{n_ha_buf:.4f}) = **{ph_start:.3f}**

**Tilsæt stærk base:**
- n(OH⁻) = {c_add} M × {v_add} L = **{n_add:.4f} mol**

**Reaktion:** OH⁻ + {_lbl_acid} → {_lbl_base} + H₂O

| | {_lbl_acid} | OH⁻ | {_lbl_base} |
|--|--|--|--|
| Før (mol) | {n_ha_buf:.4f} | {n_add:.4f} | {n_a_buf:.4f} |
| Ændring | −{n_add:.4f} | −{n_add:.4f} | +{n_add:.4f} |
| Efter (mol) | **{n_ha_new:.4f}** | 0 | **{n_a_new:.4f}** |

**Henderson-Hasselbalch:**
pH = pKa + log([{_lbl_base}]/[{_lbl_acid}])
pH = {pka_buf:.3f} + log({n_a_new:.4f}/{n_ha_new:.4f})
pH = {pka_buf:.3f} + ({_math.log10(ratio_buf):.3f})
**pH = {ph_buf:.3f}**

V_total = {v_tot_buf:.4f} L → [{_lbl_acid}] = {n_ha_new/v_tot_buf:.4f} M, [{_lbl_base}] = {n_a_new/v_tot_buf:.4f} M
""")


    elif mode == "Target pH":
        st.markdown("#### Target Buffer pH")
        target_ph = st.number_input("Target pH:", value=5.0, step=0.1, min_value=0.0, max_value=14.0, key="buf_target_ph")
        pka = st.number_input("pKa value:", value=4.74, step=0.01, key="buf_target_pka")
        ka = st.number_input("Ka value (optional):", value=None, step=1e-6, format="%.2e", help="Leave empty to calculate from pKa", key="buf_target_ka")
        
        if st.button("Calculate Ratio", type="primary", key="buffer_target_calc_ratio"):
            try:
                with st.spinner("Calculating..."):
                    ratio, steps, metadata = calculate_target_buffer_ratio(target_ph, pka, ka)
                
                st.success(f"✅ **[A⁻]/[HA] ratio = {ratio:.3f}**")
                st.info(f"**Target pH:** {target_ph:.1f}, **pKa:** {pka:.2f}")
                
                with st.expander("🔍 Vis trin", expanded=False):
                    for step in steps:
                        st.markdown(step)
            
            except Exception as e:
                st.error(f"❌ **Fejl**: {str(e)}")

    elif mode == "📊 Bufferkapacitet β":
        import math
        st.markdown("#### 📊 Bufferkapacitet β")
        st.latex(r"\beta = 2{,}303 \left( \frac{K_w}{[H^+]} + [H^+] + \frac{C \cdot K_a \cdot [H^+]}{(K_a + [H^+])^2} \right)")
        st.markdown(
            "β (mol/L·pH-enhed) angiver, hvor mange mol stærk syre eller base der skal til for at ændre pH med 1 enhed. "
            "**Maksimal β opnås ved pH = pKa.**"
        )
        col1, col2 = st.columns(2)
        with col1:
            C_buf = st.number_input("Samlet bufferkoncentration C (M):", value=0.10, min_value=1e-6, step=0.01, key="buf_beta_C",
                                    help="C = [HA] + [A⁻]")
            Ka_b = st.number_input("Ka:", value=1.8e-5, min_value=1e-14, format="%.2e", step=1e-6, key="buf_beta_ka")
        with col2:
            pH_b = st.number_input("pH:", value=4.74, min_value=0.0, max_value=14.0, step=0.01, key="buf_beta_ph")

        if st.button("Beregn β", type="primary", key="buf_beta_calc"):
            KW = 1e-14
            H = 10 ** (-pH_b)
            OH = KW / H
            beta_water = 2.303 * (OH + H)
            beta_buf = 2.303 * C_buf * Ka_b * H / (Ka_b + H) ** 2
            beta_total = beta_water + beta_buf
            pKa_b = -math.log10(Ka_b)

            st.success(f"✅ **β = {beta_total:.4f} mol/(L·ΔpH)**")
            col_a, col_b = st.columns(2)
            col_a.metric("β buffer-led", f"{beta_buf:.4f}")
            col_b.metric("β vand-led", f"{beta_water:.4f}")

            with st.expander("🔍 Trin-for-trin", expanded=True):
                st.markdown(f"""
1. pKa = −log({Ka_b:.2e}) = **{pKa_b:.3f}**
2. [H⁺] = 10^(−{pH_b:.2f}) = **{H:.3e} M**
3. [OH⁻] = Kw/[H⁺] = **{OH:.3e} M**
4. **Vand-led:** β_w = 2,303 × ([H⁺] + [OH⁻]) = 2,303 × {H+OH:.3e} = **{beta_water:.4f}**
5. **Buffer-led:** β_b = 2,303 × C × Ka × [H⁺] / (Ka + [H⁺])²
   = 2,303 × {C_buf} × {Ka_b:.2e} × {H:.3e} / ({Ka_b:.2e} + {H:.3e})²
   = **{beta_buf:.4f}**
6. **β_total = {beta_water:.4f} + {beta_buf:.4f} = {beta_total:.4f} mol/(L·ΔpH)**
""")
            if abs(pH_b - pKa_b) < 0.05:
                st.success(f"✅ pH ≈ pKa = {pKa_b:.3f} – du er ved maksimal bufferkapacitet!")
            else:
                pH_max = pKa_b
                H_max = 10 ** (-pH_max)
                beta_max = 2.303 * (KW / H_max + H_max + C_buf * Ka_b * H_max / (Ka_b + H_max) ** 2)
                st.info(f"💡 Maksimal bufferkapacitet opnås ved pH = pKa = {pKa_b:.3f}, hvor β_max ≈ {beta_max:.4f}")


def show_titrations_tab():
    """Display the titrations tab."""
    st.markdown("### 🧪 Titration Calculations")

    # Mode selection
    mode = st.radio(
        "Titration type:",
        ["Strong acid + Strong base", "Weak acid + Strong base"],
        horizontal=True
    )
    _titr_help = {
        "Strong acid + Strong base": "💡 **Hvornår?** Begge reaktanter ioniserer 100% (fx HCl + NaOH). Ækvivalenspunktet er ved pH = 7.",
        "Weak acid + Strong base": "💡 **Hvornår?** Syren er svag (fx eddikesyre + NaOH). Ækvivalenspunktet er ved pH > 7, og du skal kende Ka.",
    }
    st.info(_titr_help[mode])
    
    if mode == "Strong acid + Strong base":
        st.markdown("#### Strong Acid + Strong Base")
        col1, col2 = st.columns(2)
        
        with col1:
            acid_conc = st.number_input("Acid concentration (M):", value=0.1, step=0.01, min_value=1e-7, key="titr_sasb_acid_conc")
            acid_vol = st.number_input("Acid volume (L):", value=1.0, step=0.1, min_value=0.001, key="titr_sasb_acid_vol")
        
        with col2:
            base_conc = st.number_input("Base concentration (M):", value=0.1, step=0.01, min_value=1e-7, key="titr_sasb_base_conc")
            base_vol = st.number_input("Base volume (L):", value=1.0, step=0.1, min_value=0.001, key="titr_sasb_base_vol")
        
        if st.button("Calculate Titration Point", type="primary", key="titration_sasb_calc_point"):
            try:
                with st.spinner("Calculating..."):
                    ph, point_type, steps, metadata = calculate_titration_strong_acid_strong_base(
                        acid_conc, acid_vol, base_conc, base_vol
                    )
                
                st.success(f"✅ **pH = {ph:.3f}**")
                st.info(f"**Point type:** {point_type}")
                
                with st.expander("🔍 Vis trin", expanded=False):
                    for step in steps:
                        st.markdown(step)
            
            except Exception as e:
                st.error(f"❌ **Fejl**: {str(e)}")
    
    else:  # Weak acid + Strong base
        st.markdown("#### Weak Acid + Strong Base")
        col1, col2 = st.columns(2)
        
        with col1:
            acid_conc = st.number_input("Acid concentration (M):", value=0.1, step=0.01, min_value=1e-7, key="titr_wasb_acid_conc")
            acid_vol = st.number_input("Acid volume (L):", value=1.0, step=0.1, min_value=0.001, key="titr_wasb_acid_vol")
            ka = st.number_input("Ka value:", value=1.8e-5, step=1e-6, min_value=1e-12, format="%.2e", key="titr_wasb_ka")
        
        with col2:
            base_conc = st.number_input("Base concentration (M):", value=0.1, step=0.01, min_value=1e-7, key="titr_wasb_base_conc")
            base_vol = st.number_input("Base volume (L):", value=1.0, step=0.1, min_value=0.001, key="titr_wasb_base_vol")
        
        if st.button("Calculate Titration Point", type="primary", key="titration_wasb_calc_point"):
            try:
                with st.spinner("Calculating..."):
                    ph, point_type, steps, metadata = calculate_titration_weak_acid_strong_base(
                        acid_conc, acid_vol, ka, base_conc, base_vol
                    )
                
                st.success(f"✅ **pH = {ph:.3f}**")
                st.info(f"**Point type:** {point_type}")
                
                with st.expander("🔍 Vis trin", expanded=False):
                    for step in steps:
                        st.markdown(step)
            
            except Exception as e:
                st.error(f"❌ **Fejl**: {str(e)}")


def show_pH_calculator_page():
    """Display the pH calculator page with 5 subtabs for different calculation types."""
    st.title("📋 pH-beregner")
    st.markdown("---")
    st.markdown("Calculate pH for strong acids, weak acids, bases, and buffer systems.")
    
    # Create tabs for different calculators
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Strong Acid/Base", "Weak Acid/Base", "Ksp Solubility pH", "Buffer Henderson-Hasselbalch", "Buffer After Addition"
    ])
    
    with tab1:
        show_pH_strong_acid_base_tab()
    
    with tab2:
        show_pH_weak_acid_base_tab()
    
    with tab3:
        show_pH_ksp_solubility_tab()
    
    with tab4:
        show_pH_buffer_tab()
    
    with tab5:
        show_pH_buffer_addition_tab()


def show_pH_strong_acid_base_tab():
    """Strong Acid/Base pH calculator."""
    st.markdown("### 💪 Strong Acid/Base")
    st.markdown("Calculate pH of strong acids and bases that completely dissociate in water.")
    
    mode = st.radio("Select Type:", ["Strong Acid", "Strong Base"], horizontal=True, key="ph_strong_mode")
    
    col1, col2 = st.columns(2)
    
    with col1:
        concentration = st.number_input(
            "Concentration (M):",
            value=0.1,
            min_value=1e-10,
            format="%.2e",
            help="Concentration in mol/L",
            key="ph_strong_conc"
        )
    
    if st.button("Calculate pH", type="primary", key="ph_strong_calc"):
        try:
            if mode == "Strong Acid":
                # Strong acid: [H3O+] = concentration
                h3o = concentration
                ph = -math.log10(h3o)
                poh = 14 - ph
                oh = 1.0e-14 / h3o
                
                st.success(f"✅ **pH = {ph:.3f}**")
                st.markdown("---")
                
                col_res1, col_res2 = st.columns(2)
                with col_res1:
                    st.markdown(f"**[H₃O⁺] = {h3o:.2e} M**")
                    st.markdown(f"**[OH⁻] = {oh:.2e} M**")
                with col_res2:
                    st.markdown(f"**pOH = {poh:.3f}**")
                    st.markdown(f"**Kw = [H₃O⁺][OH⁻] = {h3o * oh:.2e}**")
                
                with st.expander("🔍 Vis trin"):
                    st.markdown("**Step 1: Strong Acid Dissociation**")
                    st.markdown("For a strong acid (e.g., HCl): HA → H₃O⁺ + A⁻")
                    st.markdown(f"Since it completely dissociates: [H₃O⁺] = [HA]₀ = {concentration:.2e} M")
                    
                    st.markdown("\n**Step 2: Calculate pH**")
                    st.markdown(f"pH = -log₁₀[H₃O⁺] = -log₁₀({concentration:.2e}) = **{ph:.3f}**")
                    
                    st.markdown("\n**Step 3: Calculate pOH and [OH⁻]**")
                    st.markdown(f"pOH = 14.00 - pH = 14.00 - {ph:.3f} = **{poh:.3f}**")
                    st.markdown(f"[OH⁻] = 10⁻ᵖᴼᴴ = 10⁻^{poh:.3f} = **{oh:.2e} M**")
                    
                    st.markdown("\n**Step 4: Verify Kw**")
                    st.markdown(f"Kw = [H₃O⁺][OH⁻] = {h3o:.2e} × {oh:.2e} = **{h3o * oh:.2e}**")
            
            else:  # Strong Base
                # Strong base: [OH-] = concentration
                oh = concentration
                poh = -math.log10(oh)
                ph = 14 - poh
                h3o = 1.0e-14 / oh
                
                st.success(f"✅ **pH = {ph:.3f}**")
                st.markdown("---")
                
                col_res1, col_res2 = st.columns(2)
                with col_res1:
                    st.markdown(f"**[OH⁻] = {oh:.2e} M**")
                    st.markdown(f"**[H₃O⁺] = {h3o:.2e} M**")
                with col_res2:
                    st.markdown(f"**pOH = {poh:.3f}**")
                    st.markdown(f"**Kw = [H₃O⁺][OH⁻] = {h3o * oh:.2e}**")
                
                with st.expander("🔍 Vis trin"):
                    st.markdown("**Step 1: Strong Base Dissociation**")
                    st.markdown("For a strong base (e.g., NaOH): BOH → B⁺ + OH⁻")
                    st.markdown(f"Since it completely dissociates: [OH⁻] = [BOH]₀ = {concentration:.2e} M")
                    
                    st.markdown("\n**Step 2: Calculate pOH**")
                    st.markdown(f"pOH = -log₁₀[OH⁻] = -log₁₀({concentration:.2e}) = **{poh:.3f}**")
                    
                    st.markdown("\n**Step 3: Calculate pH and [H₃O⁺]**")
                    st.markdown(f"pH = 14.00 - pOH = 14.00 - {poh:.3f} = **{ph:.3f}**")
                    st.markdown(f"[H₃O⁺] = 10⁻ᵖᴴ = 10⁻^{ph:.3f} = **{h3o:.2e} M**")
                    
                    st.markdown("\n**Step 4: Verify Kw**")
                    st.markdown(f"Kw = [H₃O⁺][OH⁻] = {h3o:.2e} × {oh:.2e} = **{h3o * oh:.2e}**")
        
        except Exception as e:
            st.error(f"❌ **Fejl**: {str(e)}")


def show_pH_weak_acid_base_tab():
    """Weak Acid/Base pH calculator."""
    st.markdown("### 🔹 Weak Acid/Base")
    st.markdown("Calculate pH using Ka/Kb or pKa/pKb for weak acids and bases.")
    
    mode = st.radio("Select Type:", ["Weak Acid", "Weak Base"], horizontal=True, key="ph_weak_mode")
    
    col1, col2 = st.columns(2)
    
    with col1:
        concentration = st.number_input(
            "Initial Concentration (M):",
            value=0.1,
            min_value=1e-10,
            format="%.2e",
            help="Starting concentration of weak acid or base",
            key="ph_weak_conc"
        )
    
    with col2:
        k_type = st.radio("Use:", ["Ka/Kb", "pKa/pKb"], horizontal=True, key="ph_weak_k_type")
    
    if mode == "Weak Acid":
        if k_type == "Ka/Kb":
            ka = st.number_input("Ka (acid dissociation constant):", value=1.8e-5, format="%.2e", key="ph_weak_ka")
            pka = -math.log10(ka) if ka > 0 else 0
        else:
            pka = st.number_input("pKa:", value=4.74, key="ph_weak_pka")
            ka = 10 ** (-pka) if pka >= 0 else 0
    else:
        if k_type == "Ka/Kb":
            kb = st.number_input("Kb (base dissociation constant):", value=1.8e-5, format="%.2e", key="ph_weak_kb")
            pkb = -math.log10(kb) if kb > 0 else 0
        else:
            pkb = st.number_input("pKb:", value=4.74, key="ph_weak_pkb")
            kb = 10 ** (-pkb) if pkb >= 0 else 0
    
    if st.button("Calculate pH", type="primary", key="ph_weak_calc"):
        try:
            if mode == "Weak Acid":
                # HA ⇌ H+ + A-
                # Ka = x² / (C - x)
                # Using quadratic: x² + Ka·x - Ka·C = 0
                
                pka = -math.log10(ka)
                discriminant = ka**2 + 4 * ka * concentration
                x = (-ka + math.sqrt(discriminant)) / 2
                
                h3o = x
                ph = -math.log10(h3o)
                poh = 14 - ph
                oh = 1.0e-14 / h3o
                
                st.success(f"✅ **pH = {ph:.3f}**")
                st.markdown("---")
                
                col_res1, col_res2 = st.columns(2)
                with col_res1:
                    st.markdown(f"**[H₃O⁺] = {h3o:.2e} M**")
                    st.markdown(f"**[OH⁻] = {oh:.2e} M**")
                with col_res2:
                    st.markdown(f"**pKa = {pka:.3f}**")
                    st.markdown(f"**pOH = {poh:.3f}**")
                
                with st.expander("🔍 Vis trin"):
                    st.markdown("**Weak Acid Equilibrium:**")
                    st.markdown(f"HA ⇌ H₃O⁺ + A⁻")
                    st.markdown(f"Initial (M): {concentration:.2e} | 0 | 0")
                    st.markdown(f"Change (M):    -x      | +x | +x")
                    st.markdown(f"Equilibrium:   {concentration:.2e}-x | x | x")
                    
                    st.markdown(f"\nKa = [H₃O⁺][A⁻]/[HA] = {ka:.2e}")
                    st.markdown(f"Ka = x² / ({concentration:.2e} - x) = {ka:.2e}")
                    
                    st.markdown(f"\nSolving the quadratic equation:")
                    st.markdown(f"x² + {ka:.2e}·x - {ka*concentration:.2e} = 0")
                    st.markdown(f"**x = [H₃O⁺] = {h3o:.2e} M**")
                    
                    st.markdown(f"\npH = -log₁₀[H₃O⁺] = -log₁₀({h3o:.2e}) = **{ph:.3f}**")
                    
                    # Check if approximation would work
                    if x / concentration < 0.05:
                        x_approx = math.sqrt(ka * concentration)
                        ph_approx = -math.log10(x_approx)
                        st.markdown(f"\n**Approximation Check:**")
                        st.markdown(f"Since x/C = {x/concentration:.2%} < 5%, approximation is valid:")
                        st.markdown(f"x ≈ √(Ka·C) = √({ka:.2e} × {concentration:.2e}) = {x_approx:.2e} M")
                        st.markdown(f"pH ≈ {ph_approx:.3f} (vs exact: {ph:.3f})")
            
            else:  # Weak Base
                # B + H2O ⇌ BH+ + OH-
                # Kb = x² / (C - x)
                
                pkb = -math.log10(kb)
                pka_conj = 14 - pkb
                
                discriminant = kb**2 + 4 * kb * concentration
                x = (-kb + math.sqrt(discriminant)) / 2
                
                oh = x
                poh = -math.log10(oh)
                ph = 14 - poh
                h3o = 1.0e-14 / oh
                
                st.success(f"✅ **pH = {ph:.3f}**")
                st.markdown("---")
                
                col_res1, col_res2 = st.columns(2)
                with col_res1:
                    st.markdown(f"**[OH⁻] = {oh:.2e} M**")
                    st.markdown(f"**[H₃O⁺] = {h3o:.2e} M**")
                with col_res2:
                    st.markdown(f"**pKb = {pkb:.3f}**")
                    st.markdown(f"**pKa(conj. acid) = {pka_conj:.3f}**")
                
                with st.expander("🔍 Vis trin"):
                    st.markdown("**Weak Base Equilibrium:**")
                    st.markdown(f"B + H₂O ⇌ BH⁺ + OH⁻")
                    st.markdown(f"Initial (M): {concentration:.2e} | 0 | 0")
                    st.markdown(f"Change (M):    -x      | +x | +x")
                    st.markdown(f"Equilibrium:   {concentration:.2e}-x | x | x")
                    
                    st.markdown(f"\nKb = [BH⁺][OH⁻]/[B] = {kb:.2e}")
                    st.markdown(f"Kb = x² / ({concentration:.2e} - x) = {kb:.2e}")
                    
                    st.markdown(f"\nSolving the quadratic equation:")
                    st.markdown(f"x² + {kb:.2e}·x - {kb*concentration:.2e} = 0")
                    st.markdown(f"**x = [OH⁻] = {oh:.2e} M**")
                    
                    st.markdown(f"\npOH = -log₁₀[OH⁻] = -log₁₀({oh:.2e}) = **{poh:.3f}**")
                    st.markdown(f"pH = 14.00 - pOH = 14.00 - {poh:.3f} = **{ph:.3f}**")
        
        except Exception as e:
            st.error(f"❌ **Fejl**: {str(e)}")


def show_pH_ksp_solubility_tab():
    """Ksp solubility pH calculator."""
    st.markdown("### 🧂 Ksp Solubility pH")
    st.markdown("Calculate pH from slightly soluble salts like Mg(OH)₂.")
    
    st.markdown("**Example: Mg(OH)₂ ⇌ Mg²⁺ + 2OH⁻, Ksp = [Mg²⁺][OH⁻]²**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        ksp = st.number_input(
            "Ksp value:",
            value=1.8e-11,
            format="%.2e",
            help="Solubility product constant",
            key="ph_ksp_value"
        )
    
    with col2:
        st.markdown("**Ion coefficients in Ksp expression**")
        num_cations = st.number_input("Number of cations (M):", value=1, min_value=1, max_value=5, key="ph_ksp_cations")
        num_anions = st.number_input("Number of anions (X):", value=2, min_value=1, max_value=5, key="ph_ksp_anions")
        anion_charge = st.number_input("Anion charge (for OH⁻ use -1):", value=-1, key="ph_ksp_anion_charge")
    
    if st.button("Calculate pH", type="primary", key="ph_ksp_calc"):
        try:
            # MxXy ⇌ x·M^n+ + y·X^m-
            # Ksp = [M^n+]^x · [X^m-]^y = (x·s)^x · (y·s)^y = x^x · y^y · s^(x+y)
            # s = (Ksp / (x^x · y^y))^(1/(x+y))
            
            denominator = (num_cations ** num_cations) * (num_anions ** num_anions)
            exponent = num_cations + num_anions
            solubility = (ksp / denominator) ** (1 / exponent)
            
            # Calculate [OH-] from solubility
            oh_concentration = num_anions * solubility
            
            # Calculate pH
            poh = -math.log10(oh_concentration)
            ph = 14 - poh
            h3o = 1.0e-14 / oh_concentration
            
            st.success(f"✅ **pH = {ph:.3f}**")
            st.markdown("---")
            
            col_res1, col_res2 = st.columns(2)
            with col_res1:
                st.markdown(f"**Solubility (s) = {solubility:.2e} M**")
                st.markdown(f"**[OH⁻] = {oh_concentration:.2e} M**")
            with col_res2:
                st.markdown(f"**[H₃O⁺] = {h3o:.2e} M**")
                st.markdown(f"**pOH = {poh:.3f}**")
            
            with st.expander("🔍 Vis trin"):
                st.markdown("**Solubility Equilibrium:**")
                st.markdown(f"M{num_cations}X{num_anions} ⇌ {num_cations}M⁺ + {num_anions}X⁻")
                st.markdown(f"(where M = cation, X = anion)")
                
                st.markdown(f"\nKsp = [M]^{num_cations} × [X]^{num_anions} = {ksp:.2e}")
                st.markdown(f"If solubility = s, then:")
                st.markdown(f"[M] = {num_cations}s and [X] = {num_anions}s")
                
                st.markdown(f"\nKsp = ({num_cations}s)^{num_cations} × ({num_anions}s)^{num_anions}")
                st.markdown(f"Ksp = {num_cations}^{num_cations} × {num_anions}^{num_anions} × s^{exponent}")
                st.markdown(f"Ksp = {denominator:.2e} × s^{exponent}")
                
                st.markdown(f"\nSolving for s:")
                st.markdown(f"s = (Ksp / ({num_cations}^{num_cations} × {num_anions}^{num_anions}))^(1/{exponent})")
                st.markdown(f"s = ({ksp:.2e} / {denominator:.2e})^(1/{exponent})")
                st.markdown(f"**s = {solubility:.2e} M**")
                
                st.markdown(f"\n[X⁻] = {num_anions} × s = {num_anions} × {solubility:.2e} = **{oh_concentration:.2e} M**")
                st.markdown(f"\npOH = -log₁₀[OH⁻] = **{poh:.3f}**")
                st.markdown(f"pH = 14.00 - pOH = **{ph:.3f}**")
        
        except Exception as e:
            st.error(f"❌ **Fejl**: {str(e)}")


def show_pH_buffer_tab():
    """Buffer Henderson-Hasselbalch calculator."""
    st.markdown("### 🧂 Buffer Henderson-Hasselbalch")
    st.markdown("Calculate pH of a buffer using the Henderson-Hasselbalch equation:")
    st.markdown("**pH = pKa + log₁₀([A⁻]/[HA])**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        pka = st.number_input("pKa:", value=4.74, key="ph_buffer_pka")
    
    with col2:
        conc_ha = st.number_input(
            "[HA] (acid concentration, M):",
            value=0.1,
            min_value=1e-10,
            format="%.2e",
            key="ph_buffer_ha"
        )
    
    with col3:
        conc_a = st.number_input(
            "[A⁻] (conjugate base concentration, M):",
            value=0.1,
            min_value=1e-10,
            format="%.2e",
            key="ph_buffer_a"
        )
    
    if st.button("Calculate pH", type="primary", key="ph_buffer_calc"):
        try:
            ratio = conc_a / conc_ha
            log_ratio = math.log10(ratio)
            ph = pka + log_ratio
            
            st.success(f"✅ **pH = {ph:.3f}**")
            st.markdown("---")
            
            col_res1, col_res2 = st.columns(2)
            with col_res1:
                st.markdown(f"**[HA] = {conc_ha:.2e} M**")
                st.markdown(f"**[A⁻] = {conc_a:.2e} M**")
            with col_res2:
                st.markdown(f"**Ratio [A⁻]/[HA] = {ratio:.3f}**")
                st.markdown(f"**pKa = {pka:.3f}**")
            
            with st.expander("🔍 Vis trin"):
                st.markdown("**Henderson-Hasselbalch Equation:**")
                st.markdown(f"pH = pKa + log₁₀([A⁻]/[HA])")
                st.markdown(f"pH = {pka:.3f} + log₁₀({conc_a:.2e} / {conc_ha:.2e})")
                st.markdown(f"pH = {pka:.3f} + log₁₀({ratio:.3f})")
                st.markdown(f"pH = {pka:.3f} + {log_ratio:.3f}")
                st.markdown(f"**pH = {ph:.3f}**")
                
                if abs(conc_a - conc_ha) < 1e-10:
                    st.markdown(f"\n**Special Case:** [A⁻] = [HA]")
                    st.markdown(f"When the acid and conjugate base concentrations are equal:")
                    st.markdown(f"log₁₀(1) = 0, so **pH = pKa = {pka:.3f}**")
        
        except Exception as e:
            st.error(f"❌ **Fejl**: {str(e)}")


def show_pH_buffer_addition_tab():
    """Buffer after addition of strong acid/base."""
    st.markdown("### 🧂 Buffer After Addition")
    st.markdown("Calculate pH after adding strong acid or base to a buffer.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        pka = st.number_input("pKa of buffer system:", value=4.74, key="ph_buf_add_pka")
        conc_ha_initial = st.number_input(
            "Initial [HA] (M):",
            value=0.1,
            min_value=1e-10,
            format="%.2e",
            key="ph_buf_add_ha"
        )
    
    with col2:
        conc_a_initial = st.number_input(
            "Initial [A⁻] (M):",
            value=0.1,
            min_value=1e-10,
            format="%.2e",
            key="ph_buf_add_a"
        )
    
    st.markdown("**Added Reagent:**")
    col3, col4, col5 = st.columns(3)
    
    with col3:
        added_type = st.radio("Add:", ["HCl (acid)", "NaOH (base)"], key="ph_buf_add_type")
    
    with col4:
        added_conc = st.number_input(
            "Concentration of added reagent (M):",
            value=0.1,
            min_value=1e-10,
            format="%.2e",
            key="ph_buf_add_conc"
        )
    
    with col5:
        added_volume = st.number_input(
            "Volume added (mL):",
            value=10.0,
            min_value=0.1,
            key="ph_buf_add_vol"
        )
    
    st.markdown("**Initial Buffer Volume (mL):**")
    buffer_volume = st.number_input("Buffer volume:", value=100.0, min_value=1.0, key="ph_buf_add_buf_vol")
    
    if st.button("Calculate pH", type="primary", key="ph_buf_add_calc"):
        try:
            # Calculate moles
            moles_ha = conc_ha_initial * (buffer_volume / 1000)
            moles_a = conc_a_initial * (buffer_volume / 1000)
            moles_added = added_conc * (added_volume / 1000)
            
            # Initial pH
            ratio_initial = moles_a / moles_ha
            ph_initial = pka + math.log10(ratio_initial)
            
            # After addition
            if added_type == "HCl (acid)":
                # HCl reacts with A-: A- + H+ -> HA
                moles_ha_final = moles_ha + moles_added
                moles_a_final = moles_a - moles_added
                
                if moles_a_final < 0:
                    st.error("❌ **Fejl**: Added acid exceeds conjugate base. Buffer capacity exceeded!")
                    return
            
            else:  # NaOH
                # NaOH reacts with HA: HA + OH- -> A- + H2O
                moles_ha_final = moles_ha - moles_added
                moles_a_final = moles_a + moles_added
                
                if moles_ha_final < 0:
                    st.error("❌ **Fejl**: Added base exceeds weak acid. Buffer capacity exceeded!")
                    return
            
            # Total volume after addition
            total_volume = buffer_volume + added_volume
            
            # New concentrations
            conc_ha_final = moles_ha_final / (total_volume / 1000)
            conc_a_final = moles_a_final / (total_volume / 1000)
            
            # Final pH
            ratio_final = conc_a_final / conc_ha_final
            ph_final = pka + math.log10(ratio_final)
            
            # pH change
            delta_ph = ph_final - ph_initial
            
            st.success(f"✅ **Final pH = {ph_final:.3f}**")
            st.markdown("---")
            
            col_res1, col_res2, col_res3 = st.columns(3)
            with col_res1:
                st.markdown(f"**Initial pH = {ph_initial:.3f}**")
                st.markdown(f"**Final pH = {ph_final:.3f}**")
            with col_res2:
                st.markdown(f"**ΔpH = {delta_ph:+.3f}**")
                st.markdown(f"**pH Change direction:** {'↑ More basic' if delta_ph > 0 else '↓ More acidic'}")
            with col_res3:
                st.markdown(f"**[HA] → [A⁻]**")
                st.markdown(f"**{conc_ha_final:.2e} → {conc_a_final:.2e}**")
            
            with st.expander("🔍 Vis trin"):
                st.markdown("**Step 1: Calculate initial moles**")
                st.markdown(f"n(HA) = {conc_ha_initial:.2e} M × {buffer_volume:.1f} mL = **{moles_ha:.2e} mol**")
                st.markdown(f"n(A⁻) = {conc_a_initial:.2e} M × {buffer_volume:.1f} mL = **{moles_a:.2e} mol**")
                
                st.markdown(f"\n**Step 2: Calculate initial pH**")
                st.markdown(f"pH = pKa + log₁₀([A⁻]/[HA])")
                st.markdown(f"pH = {pka:.3f} + log₁₀({ratio_initial:.3f}) = **{ph_initial:.3f}**")
                
                st.markdown(f"\n**Step 3: Calculate moles added**")
                st.markdown(f"n(added) = {added_conc:.2e} M × {added_volume:.1f} mL = **{moles_added:.2e} mol**")
                
                if added_type == "HCl (acid)":
                    st.markdown(f"\n**Step 4: Reaction with HCl**")
                    st.markdown(f"A⁻ + H⁺ → HA")
                    st.markdown(f"n(HA) = {moles_ha:.2e} + {moles_added:.2e} = **{moles_ha_final:.2e} mol**")
                    st.markdown(f"n(A⁻) = {moles_a:.2e} - {moles_added:.2e} = **{moles_a_final:.2e} mol**")
                else:
                    st.markdown(f"\n**Step 4: Reaction with NaOH**")
                    st.markdown(f"HA + OH⁻ → A⁻ + H₂O")
                    st.markdown(f"n(HA) = {moles_ha:.2e} - {moles_added:.2e} = **{moles_ha_final:.2e} mol**")
                    st.markdown(f"n(A⁻) = {moles_a:.2e} + {moles_added:.2e} = **{moles_a_final:.2e} mol**")
                
                st.markdown(f"\n**Step 5: Calculate new concentrations**")
                st.markdown(f"Total volume = {buffer_volume:.1f} + {added_volume:.1f} = **{total_volume:.1f} mL**")
                st.markdown(f"[HA]ₙₑw = {moles_ha_final:.2e} mol / {total_volume/1000:.3f} L = **{conc_ha_final:.2e} M**")
                st.markdown(f"[A⁻]ₙₑw = {moles_a_final:.2e} mol / {total_volume/1000:.3f} L = **{conc_a_final:.2e} M**")
                
                st.markdown(f"\n**Step 6: Calculate final pH**")
                st.markdown(f"pH = {pka:.3f} + log₁₀({conc_a_final:.2e}/{conc_ha_final:.2e})")
                st.markdown(f"pH = {pka:.3f} + log₁₀({ratio_final:.3f}) = **{ph_final:.3f}**")
                
                st.markdown(f"\n**Step 7: Calculate change**")
                st.markdown(f"ΔpH = {ph_final:.3f} - {ph_initial:.3f} = **{delta_ph:+.3f}**")
        
        except Exception as e:
            st.error(f"❌ **Fejl**: {str(e)}")


def show_equilibrium_page():
    """Display the equilibrium calculator page."""
    st.title("⚗️ Ligevægt")
    st.markdown("---")

    subpage_labels = [
        "⚖️ Le Chateliers princip",
        "🔢 Oxidationstrin",
        "🧊 ICE Table",
        "🔄 Kc/Kp konvertering",
        "📊 Reaktionskvotient Q",
        "💧 Opløselighed (Ksp)",
    ]
    subpage_to_query = {
        "⚖️ Le Chateliers princip": "le-chatelier",
        "🔢 Oxidationstrin":         "oxidation",
        "🧊 ICE Table":              "ice",
        "🔄 Kc/Kp konvertering":    "kc-kp",
        "📊 Reaktionskvotient Q":    "qvsK",
        "💧 Opløselighed (Ksp)":    "ksp",
    }
    query_to_subpage = {v: k for k, v in subpage_to_query.items()}

    if "nav_ligevaegt" in st.session_state:
        _nav_target = st.session_state.pop("nav_ligevaegt")
        if _nav_target in subpage_labels:
            st.session_state["eq_subpage"] = _nav_target

    query_sub_raw = st.query_params.get("eq_tab")
    if isinstance(query_sub_raw, list):
        query_sub_raw = query_sub_raw[0] if query_sub_raw else None
    query_sub = str(query_sub_raw).strip() if query_sub_raw else ""
    if "eq_subpage" not in st.session_state and query_sub in query_to_subpage:
        st.session_state["eq_subpage"] = query_to_subpage[query_sub]

    st.markdown(
        """
<style>
.st-key-eq_subpage label[data-testid="stWidgetLabel"] {
    position: absolute; width: 1px; height: 1px; padding: 0;
    margin: -1px; overflow: hidden; clip: rect(0,0,0,0); border: 0;
}
.st-key-eq_subpage [data-testid="stRadio"] div[role="radiogroup"] {
    display: flex; flex-wrap: wrap; gap: 0.35rem;
    border-bottom: 1px solid #e2e8f0; margin-bottom: 0.8rem;
}
.st-key-eq_subpage [data-testid="stRadio"] label[data-baseweb="radio"] {
    margin: 0; padding: 0.35rem 0.05rem 0.55rem 0.05rem;
    border-bottom: 2px solid transparent; background: transparent; min-height: 0;
}
.st-key-eq_subpage [data-testid="stRadio"] label[data-baseweb="radio"] > div:first-child {
    display: none !important;
}
.st-key-eq_subpage [data-testid="stRadio"] label[data-baseweb="radio"] p {
    margin: 0; font-size: 1.02rem; color: #0f172a;
}
.st-key-eq_subpage [data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) {
    border-bottom-color: #ff4b4b;
}
.st-key-eq_subpage [data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) p {
    color: #ff4b4b; font-weight: 600;
}
</style>
        """,
        unsafe_allow_html=True,
    )

    active_subpage = st.radio(
        "EqSubpageNav",
        subpage_labels,
        key="eq_subpage",
        horizontal=True,
        label_visibility="collapsed",
    )

    sel_q = subpage_to_query[active_subpage]
    if st.query_params.get("eq_tab") != sel_q:
        st.query_params["eq_tab"] = sel_q

    if active_subpage == "⚖️ Le Chateliers princip":
        render_le_chatelier_tab()
    elif active_subpage == "🔢 Oxidationstrin":
        render_oxidation_states_tab()
    elif active_subpage == "🧊 ICE Table":
        show_ice_table_tab()
    elif active_subpage == "🔄 Kc/Kp konvertering":
        show_kc_kp_conversion_tab()
    elif active_subpage == "📊 Reaktionskvotient Q":
        show_reaction_quotient_tab()
    elif active_subpage == "💧 Opløselighed (Ksp)":
        show_solubility_tab()


def show_ice_table_tab():
    """Display the ICE table solver tab."""
    st.markdown("### 🧊 ICE Table Solver")
    
    st.markdown("""
    Solve equilibrium problems using ICE (Initial, Change, Equilibrium) tables.
    
    Enter a balanced chemical reaction and initial concentrations.
    """)
    
    # Input section
    reaction = st.text_input(
        "Chemical Reaction:",
        placeholder="e.g., A + B -> C",
        help="Enter a balanced chemical reaction",
        key="eq_ice_reaction"
    )
    
    if reaction:
        try:
            # Parse the reaction to get species
            from core.reaction import parse_reaction_equation
            parsed = parse_reaction_equation(reaction)
            all_species = parsed['reactants'] + parsed['products']
            
            st.markdown(f"**Species:** {', '.join(all_species)}")
            
            # Initial concentrations
            st.markdown("#### Initial Concentrations (M)")
            initial_concentrations = {}
            
            for species in all_species:
                value = st.number_input(
                    f"[{species}]₀:",
                    value=0.0,
                    step=0.01,
                    min_value=0.0,
                    key=f"ice_initial_{species}"
                )
                initial_concentrations[species] = value
            
            # Equilibrium constant
            kc = st.number_input(
                "Kc value:",
                value=1.0,
                step=0.1,
                min_value=1e-20,
                format="%.2e"
            )
            
            # Calculate button
            if st.button("Solve ICE Table", type="primary"):
                try:
                    with st.spinner("Solving..."):
                        result, steps, metadata = solve_ice_table_with_steps(
                            reaction, initial_concentrations, kc
                        )
                    
                    st.success("✅ **ICE Table Solved!**")
                    
                    # Results
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Extent of reaction:** {result['extent']:.6f}")
                        st.markdown(f"**Direction:** {result['direction']}")
                    
                    with col2:
                        st.markdown("**Equilibrium concentrations:**")
                        for species, conc in result['equilibrium_concentrations'].items():
                            st.markdown(f"- [{species}] = {conc:.6f} M")
                    
                    # Steps section
                    with st.expander("🔍 Vis trin", expanded=False):
                        for step in steps:
                            st.markdown(step)
                
                except Exception as e:
                    st.error(f"❌ **Fejl**: {str(e)}")
        
        except Exception as e:
            st.error(f"❌ **Error parsing reaction**: {str(e)}")


def show_kc_kp_conversion_tab():
    """Display the Kc/Kp conversion tab."""
    st.markdown("### 🔄 Kc ↔ Kp Conversion")
    
    st.markdown("""
    Convert between concentration-based (Kc) and pressure-based (Kp) equilibrium constants.
    
    **Formula:** Kp = Kc × (RT)^Δn
    """)
    
    # Input section
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Known value:**")
        known_type = st.radio(
            "Convert from:",
            ["Kc to Kp", "Kp to Kc"],
            horizontal=True
        )
        
        if known_type == "Kc to Kp":
            kc = st.number_input("Kc value:", value=1.0, step=0.1, format="%.2e")
            kp = None
        else:
            kp = st.number_input("Kp value:", value=24.47, step=0.1, format="%.2e")
            kc = None
    
    with col2:
        st.markdown("**Conditions:**")
        temperature = st.number_input("Temperature (K):", value=298.15, step=1.0, min_value=0.1)
        delta_n = st.number_input("Δn (gas moles):", value=1, step=1, help="Change in gas moles: products - reactants")
    
    # Calculate button
    if st.button("Convert", type="primary"):
        try:
            with st.spinner("Converting..."):
                result, steps, metadata = convert_equilibrium_constants_with_steps(
                    kc=kc, kp=kp, temperature=temperature, delta_n=delta_n
                )
            
            st.success("✅ **Conversion Complete!**")
            
            # Results
            if known_type == "Kc to Kp":
                st.markdown(f"**Kp = {result['kp']:.6f}**")
            else:
                st.markdown(f"**Kc = {result['kc']:.6f}**")
            
            st.info(f"**Temperature:** {temperature:.1f} K, **Δn:** {delta_n}")
            
            # Steps section
            with st.expander("🔍 Vis trin", expanded=False):
                for step in steps:
                    st.markdown(step)
        
        except Exception as e:
            st.error(f"❌ **Fejl**: {str(e)}")


def show_reaction_quotient_tab():
    """Display the reaction quotient tab."""
    st.markdown("### 📊 Reaction Quotient (Q)")
    
    st.markdown("""
    Calculate the reaction quotient Q and compare it to the equilibrium constant K.
    
    **Q < K:** Reaction proceeds to products (right)
    **Q > K:** Reaction proceeds to reactants (left)
    **Q = K:** System is at equilibrium
    """)
    
    # Input section
    reaction = st.text_input(
        "Chemical Reaction:",
        placeholder="e.g., A + B -> C",
        help="Enter a balanced chemical reaction",
        key="eq_Q_reaction"
    )
    
    if reaction:
        try:
            # Parse the reaction to get species
            from core.reaction import parse_reaction_equation
            parsed = parse_reaction_equation(reaction)
            all_species = parsed['reactants'] + parsed['products']
            
            st.markdown(f"**Species:** {', '.join(all_species)}")
            
            # Current concentrations
            st.markdown("#### Current Concentrations (M)")
            current_concentrations = {}
            
            for species in all_species:
                value = st.number_input(
                    f"[{species}]:",
                    value=1.0,
                    step=0.1,
                    min_value=0.0,
                    key=f"quotient_current_{species}"
                )
                current_concentrations[species] = value
            
            # Equilibrium constant
            k = st.number_input(
                "Equilibrium constant K:",
                value=1.0,
                step=0.1,
                min_value=1e-20,
                format="%.2e"
            )
            
            # Calculate button
            if st.button("Calculate Q", type="primary"):
                try:
                    with st.spinner("Calculating..."):
                        result, steps, metadata = calculate_reaction_quotient_with_steps(
                            reaction, current_concentrations, k
                        )
                    
                    st.success("✅ **Reaction Quotient Calculated!**")
                    
                    # Results
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Q = {result['Q']:.6f}**")
                        st.markdown(f"**K = {k:.6f}**")
                    
                    with col2:
                        st.markdown(f"**Comparison:** {result['comparison']}")
                        st.markdown(f"**Direction:** {result['direction']}")
                    
                    # Steps section
                    with st.expander("🔍 Vis trin", expanded=False):
                        for step in steps:
                            st.markdown(step)
                
                except Exception as e:
                    st.error(f"❌ **Fejl**: {str(e)}")
        
        except Exception as e:
            st.error(f"❌ **Error parsing reaction**: {str(e)}")


def show_solubility_tab():
    """Display the solubility tab."""
    st.markdown("### 💧 Solubility Calculations")
    
    # Mode selection
    mode = st.radio(
        "Beregningstype:",
        ["Opløselighed fra Ksp", "Ksp fra opløselighed", "⚠️ Fældes der bundfald?"],
        horizontal=True,
    )
    _sol_help = {
        "Opløselighed fra Ksp": "💡 **Hvornår?** Du kender Ksp og vil finde molar opløselighed s (mol/L).",
        "Ksp fra opløselighed": "💡 **Hvornår?** Du kender opløseligheden (fra eksperiment) og vil beregne Ksp.",
        "⚠️ Fældes der bundfald?": "💡 **Hvornår?** To opløsninger blandes – dannes der bundfald? Beregn Q og sammenlign med Ksp.",
    }
    st.info(_sol_help[mode])

    if mode == "Opløselighed fra Ksp":
        st.markdown("#### Beregn molar opløselighed fra Ksp")
        
        salt_formula = st.text_input(
            "Salt formula:",
            placeholder="e.g., AgCl, Ca(OH)2",
            help="Enter the chemical formula of the salt",
            key="eq_solubility_formula1"
        )
        
        if salt_formula:
            ksp = st.number_input(
                "Ksp value:",
                value=1.8e-10,
                step=1e-11,
                min_value=1e-30,
                format="%.2e"
            )
            
            # Common ion effect
            st.markdown("**Common ion concentrations (optional):**")
            common_ion_input = st.text_input(
                "Common ions:",
                placeholder="e.g., Cl-:0.1, Na+:0.05",
                help="Format: ion:concentration, separate with commas"
            )
            
            common_ion_concentrations = {}
            if common_ion_input:
                try:
                    for pair in common_ion_input.split(','):
                        if ':' in pair:
                            ion, conc = pair.strip().split(':')
                            common_ion_concentrations[ion.strip()] = float(conc)
                except:
                    st.warning("Invalid common ion format. Using no common ions.")
            
            if st.button("Calculate Solubility", type="primary"):
                try:
                    with st.spinner("Calculating..."):
                        result, steps, metadata = calculate_solubility_with_steps(
                            salt_formula, ksp, common_ion_concentrations
                        )
                    
                    st.success("✅ **Solubility Calculated!**")

                    # Results
                    s = result['solubility']
                    s_fmt = f"{s:.4e}" if s < 1e-3 else f"{s:.6f}"
                    st.markdown(f"**Molar solubility:** {s_fmt} M")

                    st.markdown("**Equilibrium concentrations:**")
                    for species, conc in result['equilibrium_concentrations'].items():
                        c_fmt = f"{conc:.4e}" if conc < 1e-3 else f"{conc:.6f}"
                        st.markdown(f"- [{species}] = {c_fmt} M")
                    
                    # Steps section
                    with st.expander("🔍 Vis trin", expanded=False):
                        for step in steps:
                            st.markdown(step)
                
                except Exception as e:
                    st.error(f"❌ **Fejl**: {str(e)}")
    
    elif mode == "Ksp fra opløselighed":
        st.markdown("#### Beregn Ksp fra opløselighed")
        
        salt_formula = st.text_input(
            "Salt formula:",
            placeholder="e.g., AgCl, Ca(OH)2",
            help="Enter the chemical formula of the salt",
            key="eq_solubility_formula2"
        )
        
        if salt_formula:
            solubility = st.number_input(
                "Solubility (M):",
                value=1.34e-5,
                step=1e-6,
                min_value=1e-20,
                format="%.2e"
            )
            
            if st.button("Calculate Ksp", type="primary"):
                try:
                    with st.spinner("Calculating..."):
                        result, steps, metadata = calculate_solubility_product_with_steps(
                            salt_formula, solubility
                        )
                    
                    st.success("✅ **Ksp Calculated!**")
                    
                    # Results
                    st.markdown(f"**Ksp = {result['ksp']:.2e}**")
                    
                    # Steps section
                    with st.expander("🔍 Vis trin", expanded=False):
                        for step in steps:
                            st.markdown(step)
                
                except Exception as e:
                    st.error(f"❌ **Fejl**: {str(e)}")

    else:  # Fælding check
        import math
        st.markdown("#### ⚠️ Fældes der bundfald? (Q vs. Ksp)")
        st.latex(r"Q = [M^{n+}]^x \cdot [X^{m-}]^y")
        st.markdown(
            "Bland to opløsninger og beregn ionprodukt Q. Sammenlign med Ksp:  \n"
            "- **Q < Ksp** → ingen fældning (umættet)  \n"
            "- **Q = Ksp** → præcis ved mætning  \n"
            "- **Q > Ksp** → bundfald dannes (overmættet)"
        )

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Opløsning 1 (kation)**")
            kation = st.text_input("Kation (fx Ag⁺, Ca²⁺):", value="Ag⁺", key="ppt_cat")
            c_cat = st.number_input("Koncentration kation (M):", value=0.010, min_value=0.0, format="%.4f", key="ppt_ccat")
            V1 = st.number_input("Volumen V₁ (mL):", value=50.0, min_value=0.0, key="ppt_V1")
            z_cat = st.number_input("Ladning kation |z|:", value=1, min_value=1, max_value=4, key="ppt_zcat")
            nu_cat = st.number_input("Koefficient kation (x):", value=1, min_value=1, max_value=4, key="ppt_nucat")
        with col2:
            st.markdown("**Opløsning 2 (anion)**")
            anion = st.text_input("Anion (fx Cl⁻, SO₄²⁻):", value="Cl⁻", key="ppt_an")
            c_an = st.number_input("Koncentration anion (M):", value=0.020, min_value=0.0, format="%.4f", key="ppt_can")
            V2 = st.number_input("Volumen V₂ (mL):", value=50.0, min_value=0.0, key="ppt_V2")
            z_an = st.number_input("Ladning anion |z|:", value=1, min_value=1, max_value=4, key="ppt_zan")
            nu_an = st.number_input("Koefficient anion (y):", value=1, min_value=1, max_value=4, key="ppt_nuan")

        ksp_val = st.number_input("Ksp:", value=1.8e-10, min_value=1e-40, format="%.2e", key="ppt_ksp")

        if st.button("Tjek fældning", type="primary", key="ppt_calc"):
            V_total = V1 + V2
            c_cat_mix = c_cat * V1 / V_total
            c_an_mix = c_an * V2 / V_total
            Q = (c_cat_mix ** nu_cat) * (c_an_mix ** nu_an)

            st.success(f"**Q = {Q:.3e}**  |  **Ksp = {ksp_val:.3e}**")

            if Q < ksp_val * 0.9999:
                st.info(f"✅ **Q < Ksp** → Ingen fældning. Opløsningen er umættet.")
            elif Q > ksp_val * 1.0001:
                st.error(f"⚠️ **Q > Ksp** → **Bundfald dannes!** Opløsningen er overmættet.")
            else:
                st.warning("≈ Q ≈ Ksp → Præcis ved mætningspunktet.")

            with st.expander("🔍 Trin-for-trin", expanded=True):
                st.markdown(f"""
1. **Fortynding ved blanding** (total volumen = {V1:.1f} + {V2:.1f} = {V_total:.1f} mL):
   - [{kation}]_blandet = {c_cat:.4f} × {V1:.1f}/{V_total:.1f} = **{c_cat_mix:.4e} M**
   - [{anion}]_blandet = {c_an:.4f} × {V2:.1f}/{V_total:.1f} = **{c_an_mix:.4e} M**
2. **Ionprodukt Q:**
   Q = [{kation}]^{nu_cat} × [{anion}]^{nu_an}
   Q = {c_cat_mix:.4e}^{nu_cat} × {c_an_mix:.4e}^{nu_an} = **{Q:.3e}**
3. **Sammenlign med Ksp = {ksp_val:.3e}:**
   Q/Ksp = {Q/ksp_val:.2f} → {"Q > Ksp: fælder" if Q > ksp_val else "Q < Ksp: ingen fældning"}
""")

        st.markdown("---")
        st.markdown("**Referencetabel – Ksp for udvalgte salte ved 25°C:**")
        import pandas as pd
        ksp_ref = {
            "Salt": ["AgCl", "AgBr", "AgI", "BaSO₄", "CaCO₃", "CaF₂", "PbSO₄", "Mg(OH)₂", "Fe(OH)₃"],
            "Ksp": ["1,8×10⁻¹⁰", "5,0×10⁻¹³", "8,3×10⁻¹⁷", "1,1×10⁻¹⁰", "3,3×10⁻⁹", "3,9×10⁻¹¹",
                    "1,6×10⁻⁸", "5,6×10⁻¹²", "2,8×10⁻³⁹"],
        }
        st.dataframe(pd.DataFrame(ksp_ref), hide_index=True, use_container_width=True)


def show_gas_laws_page():
    """Display the gas laws calculator page."""
    st.title("📊 Gases Calculator")
    st.markdown("---")
    
    # Import gas laws functions
    from calculators.gases import (
        calculate_ideal_gas_law_with_steps,
        calculate_dalton_law_with_steps,
        calculate_gas_stoichiometry_with_steps,
        calculate_van_der_waals_with_steps
    )
    
    def convert_pressure(value: float, from_unit: str, to_unit: str) -> float:
        factors_to_pa = {
            "Pa": 1.0,
            "hPa": 100.0,
            "kPa": 1000.0,
            "MPa": 1000000.0,
            "atm": 101325.0,
            "bar": 100000.0,
            "mmHg": 133.322
        }
        base_pa = value * factors_to_pa[from_unit]
        return base_pa / factors_to_pa[to_unit]

    def convert_volume(value: float, from_unit: str, to_unit: str) -> float:
        factors_to_l = {
            "mL": 0.001,
            "cL": 0.01,
            "dL": 0.1,
            "L": 1.0,
            "m^3": 1000.0
        }
        base_l = value * factors_to_l[from_unit]
        return base_l / factors_to_l[to_unit]

    def convert_length(value: float, from_unit: str, to_unit: str) -> float:
        """Convert between common length units using meters as the base."""
        factors_to_m = {
            "nm": 1e-9,
            "μm": 1e-6,
            "um": 1e-6,
            "mm": 1e-3,
            "cm": 1e-2,
            "dm": 1e-1,
            "m": 1.0,
            "km": 1000.0,
        }
        # Accept both 'μm' and 'um' keys; prefer canonical forms for output
        if from_unit not in factors_to_m:
            raise ValueError(f"Unknown length unit: {from_unit}")
        if to_unit not in factors_to_m:
            raise ValueError(f"Unknown length unit: {to_unit}")
        base_m = value * factors_to_m[from_unit]
        return base_m / factors_to_m[to_unit]

    def convert_temperature(value: float, from_unit: str, to_unit: str) -> float:
        if from_unit == to_unit:
            return value
        if from_unit == "Celsius":
            temp_k = value + 273.15
        elif from_unit == "Fahrenheit":
            temp_k = (value - 32.0) * 5.0 / 9.0 + 273.15
        else:
            temp_k = value

        if to_unit == "Celsius":
            return temp_k - 273.15
        if to_unit == "Fahrenheit":
            return (temp_k - 273.15) * 9.0 / 5.0 + 32.0
        return temp_k

    def convert_gas_constant(value: float, from_unit: str, to_unit: str) -> float:
        """Convert gas constant R between common chemistry units via J/(mol·K)."""
        factors_to_j_per_mol_k = {
            "J/(mol·K)": 1.0,
            "kJ/(mol·K)": 1000.0,
            "cal/(mol·K)": 4.184,
            "L·kPa/(mol·K)": 1.0,
            "L·bar/(mol·K)": 100.0,
            "L·atm/(mol·K)": 101.325,
            "m³·Pa/(mol·K)": 1.0,
        }
        base_j_per_mol_k = value * factors_to_j_per_mol_k[from_unit]
        return base_j_per_mol_k / factors_to_j_per_mol_k[to_unit]

    def convert_mass(value: float, from_unit: str, to_unit: str) -> float:
        factors_to_g = {
            "μg": 1e-6,
            "mg": 0.001,
            "g": 1.0,
            "kg": 1000.0,
            "t": 1_000_000.0,
        }
        base_g = value * factors_to_g[from_unit]
        return base_g / factors_to_g[to_unit]

    def get_mass_unit_symbol(unit_label: str) -> str:
        return unit_label.split(" ", 1)[0]

    def convert_moles(value: float, from_unit: str, to_unit: str) -> float:
        """Convert between mole units."""
        factors_to_mol = {
            "μmol": 1e-6,
            "nmol": 1e-9,
            "pmol": 1e-12,
            "mmol": 1e-3,
            "mol": 1.0,
            "kmol": 1000.0,
        }
        base_mol = value * factors_to_mol[from_unit]
        return base_mol / factors_to_mol[to_unit]

    _gas_options = [
        "Enhedsomregning", "Ideel gaslov", "🔬 M fra densitet", "Daltons lov",
        "Gasstoichiometri", "van der Waals", "💨 Grahams lov", "🔁 Kombineret gaslov",
    ]
    _gas_active = _render_styled_tab_nav(_gas_options, key="gases_tab", nav_key="nav_gases")

    if _gas_active == "Enhedsomregning":
        st.markdown("### 🔁 Unit Conversion")
        st.markdown("Convert between pressure, volume, and temperature units.")

        subtab1, subtab2, subtab3, subtab4, subtab5, subtab6, subtab7 = st.tabs(["Pressure", "Volume", "Temperature", "Weight/Mass", "Gas Constant (R)", "Length", "Moles"])

        with subtab1:
            st.caption("Standardenhed for tryk: Pascal (Pa).")
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                pressure_value = st.number_input("Pressure value:", value=1.0, key="gas_conv_pressure_value")
            with col2:
                pressure_from = st.selectbox(
                    "From:",
                    ["atm", "Pa", "kPa", "MPa", "bar", "hPa", "mmHg"],
                    key="gas_conv_pressure_from"
                )
            with col3:
                pressure_to = st.selectbox(
                    "To:",
                    ["atm", "Pa", "kPa", "MPa", "bar", "hPa", "mmHg"],
                    index=1,
                    key="gas_conv_pressure_to"
                )

            if st.button("Convert Pressure", type="primary", key="gas_conv_pressure_btn"):
                try:
                    result = convert_pressure(pressure_value, pressure_from, pressure_to)
                    st.success(f"✅ **Resultat**: {result:.6g} {pressure_to}")
                except Exception as e:
                    st.error(f"❌ **Fejl**: {str(e)}")

        with subtab2:
            st.caption("Standardenhed for volumen: m^3.")
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                volume_value = st.number_input("Volume value:", value=1.0, key="gas_conv_volume_value")
            with col2:
                volume_from = st.selectbox(
                    "From:",
                    ["mL", "cL", "dL", "L", "m^3"],
                    key="gas_conv_volume_from"
                )
            with col3:
                volume_to = st.selectbox(
                    "To:",
                    ["mL", "cL", "dL", "L", "m^3"],
                    index=4,
                    key="gas_conv_volume_to"
                )

            if st.button("Convert Volume", type="primary", key="gas_conv_volume_btn"):
                try:
                    result = convert_volume(volume_value, volume_from, volume_to)
                    st.success(f"✅ **Resultat**: {result:.6g} {volume_to}")
                except Exception as e:
                    st.error(f"❌ **Fejl**: {str(e)}")

        with subtab3:
            st.caption("Standardenhed for temperatur: Kelvin (K).")
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                temperature_value = st.number_input("Temperature value:", value=298.15, key="gas_conv_temp_value")
            with col2:
                temperature_from = st.selectbox(
                    "From:",
                    ["Kelvin", "Celsius", "Fahrenheit"],
                    index=1,
                    key="gas_conv_temp_from"
                )
            with col3:
                temperature_to = st.selectbox(
                    "To:",
                    ["Kelvin", "Celsius", "Fahrenheit"],
                    index=0,
                    key="gas_conv_temp_to"
                )

            if st.button("Convert Temperature", type="primary", key="gas_conv_temp_btn"):
                try:
                    result = convert_temperature(temperature_value, temperature_from, temperature_to)
                    st.success(f"✅ **Resultat**: {result:.6g} {temperature_to}")
                except Exception as e:
                    st.error(f"❌ **Fejl**: {str(e)}")

        with subtab4:
            st.caption("Standardenhed for masse: g.")
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                mass_value = st.number_input(
                    "Mass value:",
                    value=1.0,
                    min_value=0.0,
                    format="%.10g",
                    key="gas_conv_mass_value"
                )
            with col2:
                mass_from = st.selectbox(
                    "From:",
                    ["μg (mikrogram)", "mg (milligram)", "g (gram)", "kg (kilogram)", "t (ton)"],
                    index=2,
                    key="gas_conv_mass_from"
                )
            with col3:
                mass_to = st.selectbox(
                    "To:",
                    ["μg (mikrogram)", "mg (milligram)", "g (gram)", "kg (kilogram)", "t (ton)"],
                    index=1,
                    key="gas_conv_mass_to"
                )

            if st.button("Convert Mass", type="primary", key="gas_conv_mass_btn"):
                try:
                    mass_from_unit = get_mass_unit_symbol(mass_from)
                    mass_to_unit = get_mass_unit_symbol(mass_to)
                    result = convert_mass(mass_value, mass_from_unit, mass_to_unit)
                    st.success(f"✅ **Resultat**: {result:.10g} {mass_to_unit}")
                except Exception as e:
                    st.error(f"❌ **Fejl**: {str(e)}")

        with subtab5:
            st.markdown("Konverter gaskonstanten R mellem almindelige kemi-enheder.")
            st.caption("Standardenhed for gaskonstanten R: J/(mol·K).")
            st.caption("Reference: R = 8.314462618 J/(mol·K) = 0.082057 L·atm/(mol·K)")

            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                gas_constant_value = st.number_input("R value:", value=8.314462618, key="gas_conv_r_value")
            with col2:
                gas_constant_from = st.selectbox(
                    "From:",
                    [
                        "J/(mol·K)",
                        "kJ/(mol·K)",
                        "cal/(mol·K)",
                        "L·kPa/(mol·K)",
                        "L·bar/(mol·K)",
                        "L·atm/(mol·K)",
                        "m³·Pa/(mol·K)",
                    ],
                    key="gas_conv_r_from"
                )
            with col3:
                gas_constant_to = st.selectbox(
                    "To:",
                    [
                        "J/(mol·K)",
                        "kJ/(mol·K)",
                        "cal/(mol·K)",
                        "L·kPa/(mol·K)",
                        "L·bar/(mol·K)",
                        "L·atm/(mol·K)",
                        "m³·Pa/(mol·K)",
                    ],
                    index=0,
                    key="gas_conv_r_to"
                )

            if st.button("Convert Gas Constant", type="primary", key="gas_conv_r_btn"):
                try:
                    result = convert_gas_constant(gas_constant_value, gas_constant_from, gas_constant_to)
                    st.success(f"✅ **Resultat**: {result:.10g} {gas_constant_to}")
                except Exception as e:
                    st.error(f"❌ **Fejl**: {str(e)}")

        with subtab6:
            st.caption("Standardenhed for længde: meter (m).")
            st.caption(
                "**μm** = micrometer (mikrometer) = 10⁻⁶ m  |  "
                "**nm** = nanometer = 10⁻⁹ m  |  "
                "**mm** = millimeter = 10⁻³ m  |  "
                "**cm** = centimeter = 10⁻² m"
            )
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                length_value = st.number_input("Length value:", value=1.0, key="gas_conv_length_value")
            with col2:
                length_from = st.selectbox(
                    "From:",
                    ["nm", "μm", "mm", "cm", "dm", "m", "km"],
                    index=5,
                    key="gas_conv_length_from"
                )
            with col3:
                length_to = st.selectbox(
                    "To:",
                    ["nm", "μm", "mm", "cm", "dm", "m", "km"],
                    index=5,
                    key="gas_conv_length_to"
                )

            if st.button("Convert Length", type="primary", key="gas_conv_length_btn"):
                try:
                    # Accept either 'um' or 'μm' in conversion helper
                    result = convert_length(length_value, length_from, length_to)
                    st.success(f"✅ **Resultat**: {result:.6g} {length_to}")
                except Exception as e:
                    st.error(f"❌ **Fejl**: {str(e)}")

        with subtab7:
            st.caption("Standardenhed for mængde: mol.")
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                moles_value = st.number_input(
                    "Mole value:",
                    value=1.0,
                    min_value=0.0,
                    format="%.10g",
                    key="gas_conv_moles_value"
                )
            with col2:
                moles_from = st.selectbox(
                    "From:",
                    ["pmol (picomol)", "nmol (nanomol)", "μmol (micromol)", "mmol (millimol)", "mol (mol)", "kmol (kilomol)"],
                    index=4,
                    key="gas_conv_moles_from"
                )
            with col3:
                moles_to = st.selectbox(
                    "To:",
                    ["pmol (picomol)", "nmol (nanomol)", "μmol (micromol)", "mmol (millimol)", "mol (mol)", "kmol (kilomol)"],
                    index=3,
                    key="gas_conv_moles_to"
                )

            if st.button("Convert Moles", type="primary", key="gas_conv_moles_btn"):
                try:
                    moles_from_unit = moles_from.split(" ", 1)[0]
                    moles_to_unit = moles_to.split(" ", 1)[0]
                    result = convert_moles(moles_value, moles_from_unit, moles_to_unit)
                    st.success(f"✅ **Resultat**: {result:.10g} {moles_to_unit}")
                except Exception as e:
                    st.error(f"❌ **Fejl**: {str(e)}")

    elif _gas_active == "Ideel gaslov":
        st.markdown("### 🎈 Ideel gaslov: PV = nRT")
        st.markdown("Beregn én ubekendt ud fra de tre kendte.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Kendte størrelser:**")
            pressure = st.number_input(
                "Tryk:",
                value=None,
                placeholder="Indtast tryk (lad stå tom for at beregne)",
                help="Pressure value",
                key="gas_ideal_pressure"
            )
            volume = st.number_input(
                "Volumen:",
                value=None,
                placeholder="Indtast volumen (lad stå tom for at beregne)",
                help="Volume value",
                key="gas_ideal_volume"
            )
        
        with col2:
            moles = st.number_input(
                "Mol (n):",
                value=None,
                placeholder="Indtast mol (lad stå tom for at beregne)",
                help="Number of moles",
                key="gas_ideal_moles"
            )
            temperature = st.number_input(
                "Temperatur:",
                value=None,
                placeholder="Indtast temperatur",
                help="Temperature value",
                key="gas_ideal_temperature"
            )
        
        # Unit selection
        col1, col2, col3 = st.columns(3)
        with col1:
            pressure_unit = st.selectbox("Tryksenhed:", ["atm", "bar", "kPa", "MPa", "Pa"], key="gas_ideal_punit")
        with col2:
            volume_unit = st.selectbox("Volumenenhed:", ["L", "mL", "m³"], key="gas_ideal_vunit")
        with col3:
            temperature_unit = st.selectbox("Temperaturenhed:", ["K", "°C"], key="gas_ideal_tunit")
        
        if st.button("Beregn", type="primary"):
            try:
                # Count provided variables
                provided_vars = sum(1 for var in [pressure, volume, moles, temperature] if var is not None)
                if provided_vars != 3:
                    st.error("❌ **Fejl**: Exactly three variables must be provided to calculate the fourth.")
                else:
                    with st.spinner("Calculating..."):
                        result = calculate_ideal_gas_law_with_steps(
                            pressure=pressure, volume=volume, moles=moles, temperature=temperature,
                            pressure_unit=pressure_unit, volume_unit=volume_unit, temperature_unit=temperature_unit
                        )
                    
                    st.success(f"✅ **Resultat**: {result['result']:.4g} {result['unit']}")
                    
                    # Steps section
                    with st.expander("🔍 Vis trin", expanded=False):
                        st.markdown(result['steps'])
            
            except Exception as e:
                st.error(f"❌ **Fejl**: {str(e)}")

        _quick_links([
            ("🔬 M fra densitet", "gases", "🔬 M fra densitet"),
            ("⚖️ Molarmasse", "atoms-molar", None),
            ("📊 Gasstoichiometri", "gases", "Gasstoichiometri"),
        ])

    elif _gas_active == "🔬 M fra densitet":
        st.markdown("### 🔬 Find molarmasse fra densitet")
        st.markdown(
            "**Formel:** M = ρRT / P  \n"
            "Bruges når du kender tryk, temperatur og densitet (g/L) – typisk til at identificere en ukendt gas."
        )
        st.info(
            "**Eksempel (som på billedet):** T = 100 °C, P = 1,0 atm, ρ = 3,0 g/L  \n"
            "→ M = (3,0 × 0,08206 × 373) / 1,0 ≈ **91,8 g/mol** → N₂O₄ (M = 92,01 g/mol) ✓"
        )
        col1, col2 = st.columns(2)
        with col1:
            density = st.number_input("Densitet ρ (g/L)", value=3.0, min_value=0.001, format="%.4f", key="mfd_density")
            pressure_mfd = st.number_input("Tryk P", value=1.0, min_value=1e-9, format="%.4f", key="mfd_pressure")
            pressure_unit_mfd = st.selectbox("Tryksenhed", ["atm", "bar", "kPa", "Pa"], key="mfd_punit")
        with col2:
            temp_mfd = st.number_input("Temperatur T", value=100.0, format="%.2f", key="mfd_temp")
            temp_unit_mfd = st.selectbox("Temperaturenhed", ["°C", "K"], key="mfd_tunit")

        if st.button("Beregn molarmasse", type="primary", key="mfd_btn"):
            R = 0.08206  # L·atm/(mol·K)
            T_K = temp_mfd + 273.15 if temp_unit_mfd == "°C" else temp_mfd
            p_atm = pressure_mfd
            unit_factors = {"atm": 1.0, "bar": 1.0 / 1.01325, "kPa": 1.0 / 101.325, "Pa": 1.0 / 101325.0}
            p_atm = pressure_mfd * unit_factors[pressure_unit_mfd]
            M = density * R * T_K / p_atm
            st.success(f"**M ≈ {M:.2f} g/mol**")
            st.markdown(f"""
**Trin-for-trin:**

1. Omarranger PV = nRT: da n = m/M og ρ = m/V gælder **M = ρRT/P**
2. Omregn temperatur: T = {temp_mfd} {temp_unit_mfd} = **{T_K:.2f} K**
3. Omregn tryk til atm: P = {pressure_mfd} {pressure_unit_mfd} = **{p_atm:.4f} atm**
4. Indsæt:
   M = ({density:.4f} g/L × 0,08206 L·atm/mol·K × {T_K:.2f} K) / {p_atm:.4f} atm
   **M = {M:.2f} g/mol**
""")
            st.caption("💡 Sammenlign med kendte molarmasser: NO = 30, NO₂ = 46, N₂O = 44, N₂O₄ = 92, N₂O₅ = 108 g/mol")

        _quick_links([
            ("⚖️ Molarmasse", "atoms-molar", None),
            ("🎈 Ideel gaslov", "gases", "Ideel gaslov"),
            ("📊 Gasstoichiometri", "gases", "Gasstoichiometri"),
        ])

    elif _gas_active == "Daltons lov":
        st.markdown("### 🌊 Daltons lov – partialtryk")
        st.markdown("Beregn partialtryk ud fra mol eller molfraktioner.")
        
        input_method = st.radio(
            "Inputmetode:",
            ["Moles", "Mole Fractions"], key="gas_dalton_mode"
        )
        _dalton_help = {
            "Moles": "💡 **Hvornår?** Du kender antallet af mol af hvert stof – beregner molfraktion og partialtryk automatisk.",
            "Mole Fractions": "💡 **Hvornår?** Du kender allerede molfraktionerne (summen skal = 1). Angiv blot det samlede tryk.",
        }
        st.info(_dalton_help[input_method])

        if input_method == "Moles":
            st.markdown("**Enter species with moles:**")
            num_species = st.number_input("Number of species:", min_value=1, max_value=10, value=2, key="gas_dalton_n_moles")
            
            species_data = []
            for i in range(num_species):
                col1, col2 = st.columns(2)
                with col1:
                    name = st.text_input(f"Species {i+1} name:", value=f"Gas{i+1}", key=f"gas_dalton_name_{i}")
                with col2:
                    moles = st.number_input(f"Moles of species {i+1}:", value=1.0, min_value=0.0, key=f"gas_dalton_moles_{i}")
                species_data.append({"name": name, "moles": moles})
        else:
            st.markdown("**Enter species with mole fractions:**")
            num_species = st.number_input("Number of species:", min_value=1, max_value=10, value=2, key="gas_dalton_n_frac")
            
            species_data = []
            for i in range(num_species):
                col1, col2 = st.columns(2)
                with col1:
                    name = st.text_input(f"Species {i+1} name:", value=f"Gas{i+1}", key=f"gas_dalton_name_frac_{i}")
                with col2:
                    fraction = st.number_input(f"Mole fraction of species {i+1}:", value=0.5, min_value=0.0, max_value=1.0, key=f"gas_dalton_x_{i}")
                species_data.append({"name": name, "mole_fraction": fraction})
        
        total_pressure = st.number_input("Total pressure:", value=1.0, min_value=0.0, key="gas_dalton_ptot")
        pressure_unit = st.selectbox("Tryksenhed:", ["atm", "bar", "kPa", "Pa"], key="gas_dalton_punit")
        
        # Collected over water option
        collected_over_water = st.checkbox("Collected over water")
        water_vapor_pressure = None
        if collected_over_water:
            water_vapor_pressure = st.number_input("Water vapor pressure:", value=0.05, min_value=0.0)
        
        if st.button("Calculate Partial Pressures", type="primary"):
            try:
                with st.spinner("Calculating..."):
                    result = calculate_dalton_law_with_steps(
                        species_data=species_data,
                        total_pressure=total_pressure,
                        pressure_unit=pressure_unit,
                        collected_over_water=collected_over_water,
                        water_vapor_pressure=water_vapor_pressure
                    )
                
                st.success("✅ **Partial Pressures Calculated!**")
                
                # Results
                st.markdown("**Partial Pressures:**")
                for pp in result['partial_pressures']:
                    st.markdown(f"- {pp['name']}: {pp['partial_pressure']:.4f} {pressure_unit}")
                
                if collected_over_water:
                    st.markdown(f"**Gas pressure (excluding water vapor)**: {result['gas_pressure']:.4f} {pressure_unit}")
                
                # Steps section
                with st.expander("🔍 Vis trin", expanded=False):
                    st.markdown(result['steps'])
            
            except Exception as e:
                st.error(f"❌ **Fejl**: {str(e)}")
    
    elif _gas_active == "Gasstoichiometri":
        st.markdown("### ⚗️ Gas Stoichiometry")
        st.markdown("Calculate limiting reagent and theoretical gas product volume.")
        
        reaction = st.text_input(
            "Chemical Reaction:",
            placeholder="e.g., 2 H2 + O2 -> 2 H2O(g)",
            help="Enter the balanced chemical reaction",
            key="gas_stoich_rxn"
        )
        
        if reaction:
            st.markdown("**Reactant Information:**")
            num_reactants = st.number_input("Number of reactants:", min_value=1, max_value=5, value=2, key="gas_stoich_n")
            
            reactant_data = []
            for i in range(num_reactants):
                col1, col2, col3 = st.columns(3)
                with col1:
                    formula = st.text_input(f"Reactant {i+1} formula:", value=f"R{i+1}", key=f"gas_stoich_formula_{i}")
                with col2:
                    input_type = st.selectbox(f"Input type for reactant {i+1}:", ["Volume", "Mass"], key=f"gas_stoich_type_{i}")
                with col3:
                    if input_type == "Volume":
                        value = st.number_input(f"Volume of reactant {i+1}:", value=1.0, min_value=0.0, key=f"gas_stoich_vol_{i}")
                        reactant_data.append({"formula": formula, "volume": value})
                    else:
                        value = st.number_input(f"Mass of reactant {i+1} (g):", value=1.0, min_value=0.0, key=f"gas_stoich_mass_{i}")
                        reactant_data.append({"formula": formula, "mass": value})
            
            col1, col2, col3 = st.columns(3)
            with col1:
                temperature = st.number_input("Temperatur:", value=298.15, min_value=0.0, key="gas_stoich_T")
            with col2:
                pressure = st.number_input("Tryk:", value=1.0, min_value=0.0, key="gas_stoich_P")
            with col3:
                temperature_unit = st.selectbox("Temperaturenhed:", ["K", "°C"], key="gas_stoich_Tunit")
            
            pressure_unit = st.selectbox("Tryksenhed:", ["atm", "bar", "kPa", "Pa"], key="gas_stoich_Punit")
            volume_unit = st.selectbox("Volumenenhed:", ["L", "mL", "m³"], key="gas_stoich_Vunit")
            
            if st.button("Calculate Stoichiometry", type="primary"):
                try:
                    with st.spinner("Calculating..."):
                        result = calculate_gas_stoichiometry_with_steps(
                            reaction=reaction,
                            reactant_data=reactant_data,
                            temperature=temperature,
                            pressure=pressure,
                            temperature_unit=temperature_unit,
                            pressure_unit=pressure_unit,
                            volume_unit=volume_unit
                        )
                    
                    st.success("✅ **Stoichiometry Calculated!**")
                    
                    # Results
                    st.markdown(f"**Limiting Reactant**: {result['limiting_reactant']['formula']}")
                    st.markdown(f"**Product Moles**: {result['product_moles']:.4f} mol")
                    st.markdown(f"**Product Volume**: {result['product_volume']:.4f} {volume_unit}")
                    
                    # Steps section
                    with st.expander("🔍 Vis trin", expanded=False):
                        st.markdown(result['steps'])
                
                except Exception as e:
                    st.error(f"❌ **Fejl**: {str(e)}")
    
    elif _gas_active == "van der Waals":
        st.markdown("### 🔬 van der Waals Equation")
        st.markdown("Calculate pressure using the van der Waals equation for real gases.")
        
        # Load available gases
        try:
            import pandas as pd
            vdw_path = Path(__file__).parent / "data" / "vdw_constants.csv"
            vdw_data = pd.read_csv(vdw_path)
            available_gases = vdw_data['gas'].tolist()
        except:
            available_gases = ["CO2", "N2", "O2"]
        
        col1, col2 = st.columns(2)
        
        with col1:
            gas = st.selectbox("Gas:", available_gases)
            moles = st.number_input("Mol (n):", value=1.0, min_value=0.0)
            volume = st.number_input("Volumen:", value=1.0, min_value=0.0)
        
        with col2:
            temperature = st.number_input("Temperatur:", value=298.15, min_value=0.0)
            volume_unit = st.selectbox("Volumenenhed:", ["L", "mL", "m³"])
            temperature_unit = st.selectbox("Temperaturenhed:", ["K", "°C"])
        
        pressure_unit = st.selectbox("Tryksenhed:", ["atm", "bar", "kPa", "Pa"])
        
        if st.button("Calculate van der Waals Pressure", type="primary"):
            try:
                with st.spinner("Calculating..."):
                    result = calculate_van_der_waals_with_steps(
                        gas=gas,
                        moles=moles,
                        volume=volume,
                        temperature=temperature,
                        volume_unit=volume_unit,
                        temperature_unit=temperature_unit,
                        pressure_unit=pressure_unit
                    )
                
                st.success("✅ **van der Waals Pressure Calculated!**")
                
                # Results
                st.markdown(f"**van der Waals Pressure**: {result['pressure_vdw']:.4f} {pressure_unit}")
                st.markdown(f"**Ideal Gas Pressure**: {result['pressure_ideal']:.4f} {pressure_unit}")
                st.markdown(f"**Compressibility Factor (Z)**: {result['compressibility_factor']:.4f}")
                
                # Steps section
                with st.expander("🔍 Vis trin", expanded=False):
                    st.markdown(result['steps'])
            
            except Exception as e:
                st.error(f"❌ **Fejl**: {str(e)}")

    elif _gas_active == "💨 Grahams lov":
        render_graham_tab()
    elif _gas_active == "🔁 Kombineret gaslov":
        _render_combined_gas_law_tab()


def _render_combined_gas_law_tab():
    """Combined / Boyle's / Charles's / Gay-Lussac gas law tab."""
    st.markdown("## 🔁 Kombineret gaslov")
    st.markdown(
        r"$$\frac{P_1 V_1}{T_1} = \frac{P_2 V_2}{T_2}$$"
    )
    st.markdown(
        "Angiv **tilstand 1** og to af tre variabler i **tilstand 2**. "
        "Lad det ubekendte felt stå på 0 (beregnes automatisk). "
        "Sæt en variabel til **ens** i begge tilstande for at simulere Boyles, Charles' eller Gay-Lussacs lov."
    )
    st.markdown("---")

    col1, col2 = st.columns(2, gap="large")

    p_units = {"atm": 1.0, "kPa": 101.325, "Pa": 101325.0, "bar": 101.325 / 1.01325, "mmHg": 760.0}
    v_units = {"L": 1.0, "mL": 0.001, "m³": 1000.0, "dL": 0.1, "cL": 0.01}

    def to_atm(p, unit): return p / p_units[unit]
    def from_atm(p, unit): return p * p_units[unit]
    def to_L(v, unit): return v * v_units[unit]
    def from_L(v, unit): return v / v_units[unit]
    def to_K(t, unit): return t + 273.15 if unit == "°C" else t

    with col1:
        st.markdown("### Tilstand 1")
        p1_val = st.number_input("P₁:", value=1.0, min_value=0.0, key="cg_p1")
        p1_u   = st.selectbox("Enhed P₁:", list(p_units.keys()), key="cg_p1u")
        v1_val = st.number_input("V₁:", value=2.0, min_value=0.0, key="cg_v1")
        v1_u   = st.selectbox("Enhed V₁:", list(v_units.keys()), key="cg_v1u")
        t1_val = st.number_input("T₁:", value=25.0, key="cg_t1")
        t1_u   = st.selectbox("Enhed T₁:", ["°C", "K"], key="cg_t1u")

    with col2:
        st.markdown("### Tilstand 2 (0 = ubekendt)")
        p2_val = st.number_input("P₂ (0 = ubekendt):", value=2.0, min_value=0.0, key="cg_p2")
        p2_u   = st.selectbox("Enhed P₂:", list(p_units.keys()), key="cg_p2u")
        v2_val = st.number_input("V₂ (0 = ubekendt):", value=0.0, min_value=0.0, key="cg_v2")
        v2_u   = st.selectbox("Enhed V₂:", list(v_units.keys()), key="cg_v2u")
        t2_val = st.number_input("T₂ (0 = ubekendt):", value=100.0, key="cg_t2")
        t2_u   = st.selectbox("Enhed T₂:", ["°C", "K"], key="cg_t2u")

    if st.button("Beregn", type="primary", key="cg_run"):
        # Convert to base units: atm, L, K
        P1 = to_atm(p1_val, p1_u)
        V1 = to_L(v1_val, v1_u)
        T1 = to_K(t1_val, t1_u)

        P2_in = to_atm(p2_val, p2_u) if p2_val != 0 else None
        V2_in = to_L(v2_val, v2_u)   if v2_val != 0 else None
        T2_in = to_K(t2_val, t2_u)   if t2_val != 0 else None

        # Safety
        if T1 <= 0:
            st.error("T₁ skal være > 0 K.")
            st.stop()

        unknowns = [x for x in [P2_in, V2_in, T2_in] if x is None]
        if len(unknowns) > 1:
            st.error("Angiv mindst 2 kendte værdier i tilstand 2 (lad kun ét felt stå på 0).")
            st.stop()

        # P1V1/T1 = P2V2/T2  →  solve for missing
        lhs = P1 * V1 / T1   # constant

        steps = []
        steps.append(f"**P₁ = {p1_val} {p1_u} = {P1:.4f} atm**")
        steps.append(f"**V₁ = {v1_val} {v1_u} = {V1:.4f} L**")
        steps.append(f"**T₁ = {t1_val} {t1_u} = {T1:.2f} K**")
        steps.append(f"P₁V₁/T₁ = {P1:.4f} × {V1:.4f} / {T1:.2f} = **{lhs:.6f} atm·L/K**")

        if P2_in is None:
            # P2 = lhs × T2 / V2
            T2 = T2_in; V2 = V2_in
            P2 = lhs * T2 / V2
            result_label = f"P₂ = {from_atm(P2, p2_u):.4g} {p2_u}"
            steps.append(f"P₂ = (P₁V₁/T₁) × T₂/V₂ = {lhs:.6f} × {T2:.2f} / {V2:.4f} = {P2:.4f} atm = **{from_atm(P2, p2_u):.4g} {p2_u}**")
        elif V2_in is None:
            T2 = T2_in; P2 = P2_in
            V2 = lhs * T2 / P2
            result_label = f"V₂ = {from_L(V2, v2_u):.4g} {v2_u}"
            steps.append(f"V₂ = (P₁V₁/T₁) × T₂/P₂ = {lhs:.6f} × {T2:.2f} / {P2:.4f} = {V2:.4f} L = **{from_L(V2, v2_u):.4g} {v2_u}**")
        else:
            P2 = P2_in; V2 = V2_in
            T2 = P2 * V2 / lhs
            t2_display = T2 - 273.15 if t2_u == "°C" else T2
            result_label = f"T₂ = {t2_display:.2f} {t2_u} ({T2:.2f} K)"
            steps.append(f"T₂ = P₂V₂ / (P₁V₁/T₁) = {P2:.4f} × {V2:.4f} / {lhs:.6f} = {T2:.2f} K = **{t2_display:.2f} {t2_u}**")

        st.success(f"### {result_label}")
        with st.expander("📋 Vis udledning", expanded=False):
            for s in steps:
                st.markdown(s)

    st.markdown("---")
    with st.expander("📚 Specialtilfælde", expanded=False):
        st.markdown("""
| Lov | Fast variabel | Relation |
|-----|--------------|----------|
| **Boyles lov** | T konstant | P₁V₁ = P₂V₂ |
| **Charles' lov** | P konstant | V₁/T₁ = V₂/T₂ |
| **Gay-Lussacs lov** | V konstant | P₁/T₁ = P₂/T₂ |
| **Kombineret** | n konstant | P₁V₁/T₁ = P₂V₂/T₂ |

**OBS:** T skal altid angives i **Kelvin** (K = °C + 273.15) — kalkulatoren konverterer automatisk.
        """)


def show_solutions_page():
    """Display the solutions calculator page."""
    st.title("⚗️ Solutions")
    st.markdown("---")
    from calculators.solutions import (
        solve_molarity, grams_for_solution, volume_stock_for_dilution,
        solve_molality, percent_w_w, percent_v_v, percent_w_v,
        ppm_general, ppm_aqueous_from_mg_per_L, mix_solutions,
        mole_fraction_from_masses, mole_fraction_from_moles, ionic_strength
    )

    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "Molarity", "Make Solution", "Molality", "Percent", "ppm/ppb",
        "Mixing", "Mole Fraction", "Ionic Strength"
    ])

    with tab1:
        st.markdown("#### Molarity: M = n/V")
        unknown = st.selectbox("Ubekendt", ["M", "n", "V"], index=0)
        M = st.number_input("M (mol/L)", value=0.500)
        n = st.number_input("n (mol)", value=0.250)
        V = st.number_input("V (L)", value=0.500)
        if unknown == "M":
            M = None
        elif unknown == "n":
            n = None
        else:
            V = None
        if st.button("Solve Molarity", type="primary"):
            try:
                res, steps = solve_molarity(M, n, V)
                key = list(res.keys())[0]
                st.success(f"{key} = {res[key]:.6g}")
                with st.expander("Vis trin"):
                    st.markdown(steps)
            except Exception as e:
                st.error(str(e))

    with tab2:
        st.markdown("#### Make a solution (from solid / from stock)")
        col1, col2 = st.columns(2)
        with col1:
            formula = st.text_input("Formula (solid)", value="NaCl")
            M_t = st.number_input("Target M (mol/L)", value=0.1000, format="%.4f")
            V_f = st.number_input("Final volume (L)", value=1.00, format="%.3f")
            if st.button("Grams from solid", type="primary"):
                try:
                    g, steps = grams_for_solution(formula, M_t, V_f)
                    st.success(f"grams = {g:.4g} g")
                    with st.expander("Vis trin"):
                        st.markdown(steps)
                except Exception as e:
                    st.error(str(e))
        with col2:
            M_stock = st.number_input("Stock M (mol/L)", value=2.00, format="%.3f")
            if st.button("V_stock for dilution", type="primary"):
                try:
                    V1, steps = volume_stock_for_dilution(M_stock, M_t, V_f)
                    st.success(f"V_stock = {V1:.6g} L")
                    with st.expander("Vis trin"):
                        st.markdown(steps)
                except Exception as e:
                    st.error(str(e))

    with tab3:
        st.markdown("#### Molality: m = n / kg_solvent")
        unknown = st.selectbox("Unknown (molality)", ["m", "n_mol", "m_solvent_kg"], index=0)
        m = st.number_input("m (mol/kg)", value=1.0)
        n = st.number_input("n (mol)", value=0.1)
        kg = st.number_input("kg solvent", value=0.1)
        if unknown == "m":
            m = None
        elif unknown == "n_mol":
            n = None
        else:
            kg = None
        if st.button("Solve Molality", type="primary"):
            try:
                res, steps = solve_molality(m, n, kg)
                key = list(res.keys())[0]
                st.success(f"{key} = {res[key]:.6g}")
                with st.expander("Vis trin"):
                    st.markdown(steps)
            except Exception as e:
                st.error(str(e))

    with tab4:
        st.markdown("#### Percent concentration")
        mode = st.selectbox("Mode", ["w/w", "v/v", "w/v"]) 
        if mode == "w/w":
            unknown = st.selectbox("Ubekendt", ["%", "m_solute", "m_total"]) 
            a = st.number_input("m_solute (g) or %", value=10.0)
            b = st.number_input("m_total (g) or %", value=110.0)
            if st.button("Compute w/w%", type="primary"):
                try:
                    val, steps = percent_w_w(a, b, unknown)
                    st.success(f"Result = {val:.6g}")
                    with st.expander("Vis trin"):
                        st.markdown(steps)
                except Exception as e:
                    st.error(str(e))
        elif mode == "v/v":
            unknown = st.selectbox("Ubekendt", ["%", "V_solute", "V_total"]) 
            a = st.number_input("V_solute (mL) or %", value=10.0)
            b = st.number_input("V_total (mL) or %", value=100.0)
            if st.button("Compute v/v%", type="primary"):
                try:
                    val, steps = percent_v_v(a, b, unknown)
                    st.success(f"Result = {val:.6g}")
                    with st.expander("Vis trin"):
                        st.markdown(steps)
                except Exception as e:
                    st.error(str(e))
        else:
            unknown = st.selectbox("Ubekendt", ["%", "m_solute", "V_solution"]) 
            a = st.number_input("m_solute (g) or %", value=5.0)
            b = st.number_input("V_solution (mL) or %", value=100.0)
            if st.button("Compute w/v%", type="primary"):
                try:
                    val, steps = percent_w_v(a, b, unknown)
                    st.success(f"Result = {val:.6g}")
                    with st.expander("Vis trin"):
                        st.markdown(steps)
                except Exception as e:
                    st.error(str(e))

    with tab5:
        st.markdown("#### ppm / ppb")
        basis = st.selectbox("Basis", ["mass", "volume"]) 
        sol = st.number_input("amount solute (same basis)", value=0.0500)
        tot = st.number_input("amount total (same basis)", value=2.00)
        unit = st.selectbox("Unit", ["ppm", "ppb"], index=0)
        if st.button("Compute ppm/ppb", type="primary"):
            try:
                val, steps = ppm_general(sol, tot, basis, unit)
                st.success(f"{unit} = {val:.6g}")
                with st.expander("Vis trin"):
                    st.markdown(steps)
            except Exception as e:
                st.error(str(e))
        st.markdown("Aqueous shortcut: ppm ≈ mg/L")
        mgL = st.number_input("mg/L", value=25.0)
        if st.button("ppm from mg/L", type="primary"):
            try:
                val, steps = ppm_aqueous_from_mg_per_L(mgL)
                st.success(f"ppm = {val:.6g}")
                with st.expander("Vis trin"):
                    st.markdown(steps)
            except Exception as e:
                st.error(str(e))

    with tab6:
        st.markdown("#### Mixing same-solute solutions")
        V1 = st.number_input("V1 (L)", value=0.100)
        M1 = st.number_input("M1 (mol/L)", value=1.000)
        V2 = st.number_input("V2 (L)", value=0.400)
        M2 = st.number_input("M2 (mol/L)", value=0.200)
        if st.button("Mix", type="primary"):
            try:
                Mf, steps = mix_solutions([V1, V2], [M1, M2])
                st.success(f"M_final = {Mf:.6g} M")
                with st.expander("Vis trin"):
                    st.markdown(steps)
            except Exception as e:
                st.error(str(e))

    with tab7:
        st.markdown("#### Mole fraction (binary)")
        mode = st.selectbox("Input mode", ["masses+formulas", "moles"], index=0)
        if mode == "masses+formulas":
            formulaA = st.text_input("Formula A", value="NaCl")
            mA = st.number_input("m_A (g)", value=10.0)
            formulaB = st.text_input("Formula B", value="H2O")
            mB = st.number_input("m_B (g)", value=100.0)
            if st.button("Compute x", type="primary"):
                try:
                    xA, xB, steps = mole_fraction_from_masses(formulaA, mA, formulaB, mB)
                    st.success(f"x_A = {xA:.6g}, x_B = {xB:.6g}")
                    with st.expander("Vis trin"):
                        st.markdown(steps)
                except Exception as e:
                    st.error(str(e))
        else:
            nA = st.number_input("n_A (mol)", value=0.171)
            nB = st.number_input("n_B (mol)", value=5.55)
            if st.button("Compute x from moles", type="primary"):
                from core.solutions import mole_fraction_from_moles
                try:
                    xA, xB, steps = mole_fraction_from_moles(nA, nB)
                    st.success(f"x_A = {xA:.6g}, x_B = {xB:.6g}")
                    with st.expander("Vis trin"):
                        st.markdown(steps)
                except Exception as e:
                    st.error(str(e))

    with tab8:
        st.markdown("#### Ionic strength")
        name1 = st.text_input("Species 1 name", value="Na+")
        c1 = st.number_input("c1 (M)", value=0.200)
        z1 = st.number_input("z1 (charge)", value=1, step=1)
        name2 = st.text_input("Species 2 name", value="SO4^2-")
        c2 = st.number_input("c2 (M)", value=0.100)
        z2 = st.number_input("z2 (charge)", value=-2, step=1)
        if st.button("Compute I", type="primary"):
            try:
                I, steps = ionic_strength([(name1, c1, int(z1)), (name2, c2, int(z2))])
                st.success(f"I = {I:.6g}")
                with st.expander("Vis trin"):
                    st.markdown(steps)
            except Exception as e:
                st.error(str(e))

def show_kinetics_page():
    """Display Kinetics calculators."""
    st.title("⚡ Kinetik")
    st.markdown("---")
    from calculators.kinetics import (
        calculate_integrated_rate_with_steps,
        calculate_half_life_with_steps,
        calculate_determine_order_k_with_steps,
        calculate_arrhenius_forward_with_steps,
        calculate_arrhenius_two_point_Ea_with_steps,
    )

    _kin_options = ["Integreret hastighedslov", "📊 Halvliv", "Bestem orden & k", "📋 Initial rates", "Arrhenius", "Hastighedsrelationer"]
    _kin_active = _render_styled_tab_nav(_kin_options, key="kinetics_tab", nav_key="nav_kinetics")

    if _kin_active == "Integreret hastighedslov":
        st.markdown("#### Integreret hastighedslov")
        st.caption("💡 Brug dette til at beregne koncentration eller tid for en reaktion af 0., 1. eller 2. orden.")
        order = st.selectbox("Orden", [0, 1, 2], index=1)
        unknown = st.selectbox("Ubekendt", ["Ct", "C0", "k", "t"], index=0)
        C0 = st.number_input("C0 (M)", value=0.100, min_value=0.0)
        Ct = st.number_input("Ct (M)", value=0.010, min_value=0.0)
        k = st.number_input("k (units depend on order)", value=0.350, min_value=0.0)
        t = st.number_input("t (s)", value=10.0, min_value=0.0)
        if unknown == "Ct":
            Ct = None
        elif unknown == "C0":
            C0 = None
        elif unknown == "k":
            k = None
        else:
            t = None
        if st.button("Beregn", type="primary"):
            try:
                val, steps, meta = calculate_integrated_rate_with_steps(order, C0, Ct, k, t)
                st.success(f"{unknown} = {val:.6g}")
                with st.expander("Vis trin"):
                    for s in steps:
                        st.markdown(s)
            except Exception as e:
                st.error(str(e))
        _quick_links([
            ("📊 Halvliv", "kinetics", "📊 Halvliv"),
            ("Bestem orden & k", "kinetics", "Bestem orden & k"),
            ("Arrhenius", "kinetics", "Arrhenius"),
        ])

    elif _kin_active == "📊 Halvliv":
        import math
        st.markdown("#### 📊 Halvliv – t½ for reaktioner af 0., 1. og 2. orden")
        st.markdown("Halvliv er den tid det tager for koncentrationen at falde til det halve.")

        col1, col2 = st.columns(2)
        with col1:
            hl_order = st.selectbox("Reaktionsorden:", [0, 1, 2], index=1, key="hl_order")
            hl_k = st.number_input("Hastighedskonstant k:", value=0.350, min_value=1e-12, format="%.4e", key="hl_k",
                                   help="Enheder: M·s⁻¹ (0. orden), s⁻¹ (1. orden), M⁻¹·s⁻¹ (2. orden)")
        with col2:
            if hl_order in [0, 2]:
                hl_C0 = st.number_input("[A]₀ (M):", value=0.100, min_value=1e-12, key="hl_C0")
            else:
                hl_C0 = None
                st.markdown("*[A]₀ ikke nødvendig for 1. orden*")

        formulas = {
            0: (r"t_{1/2} = \frac{[A]_0}{2k}", "t½ = [A]₀ / (2k)"),
            1: (r"t_{1/2} = \frac{\ln 2}{k}", "t½ = ln2 / k"),
            2: (r"t_{1/2} = \frac{1}{k[A]_0}", "t½ = 1 / (k·[A]₀)"),
        }
        st.latex(formulas[hl_order][0])

        if st.button("Beregn t½", type="primary", key="hl_calc"):
            if hl_order == 0:
                t_half = hl_C0 / (2 * hl_k)
                steps = [
                    f"**0. orden:** t½ = [A]₀ / (2k)",
                    f"t½ = {hl_C0:.4f} / (2 × {hl_k:.4e}) = **{t_half:.4f} s**",
                ]
            elif hl_order == 1:
                t_half = math.log(2) / hl_k
                steps = [
                    f"**1. orden:** t½ = ln2 / k",
                    f"t½ = {math.log(2):.6f} / {hl_k:.4e} = **{t_half:.4f} s**",
                    f"Bemærk: halvliv er **uafhængigt af [A]₀** for 1. orden.",
                ]
            else:
                t_half = 1.0 / (hl_k * hl_C0)
                steps = [
                    f"**2. orden:** t½ = 1 / (k·[A]₀)",
                    f"t½ = 1 / ({hl_k:.4e} × {hl_C0:.4f}) = **{t_half:.4f} s**",
                    f"Bemærk: halvliv **afhænger af [A]₀** for 2. orden — det stiger over tid!",
                ]

            st.success(f"✅ **t½ = {t_half:.4f} s**  ({t_half/60:.3f} min)")
            with st.expander("🔍 Trin-for-trin", expanded=True):
                for s in steps:
                    st.markdown(s)

        st.markdown("---")
        st.markdown("**Sammenligning af halvliv:**")
        import pandas as pd
        df_hl = pd.DataFrame({
            "Orden": ["0. orden", "1. orden", "2. orden"],
            "Formel": ["t½ = [A]₀/(2k)", "t½ = ln2/k", "t½ = 1/(k[A]₀)"],
            "Afhænger af [A]₀?": ["Ja", "Nej", "Ja"],
            "t½ over tid": ["Falder", "Konstant", "Stiger"],
        })
        st.dataframe(df_hl, hide_index=True, use_container_width=True)
        _quick_links([
            ("Integreret hastighedslov", "kinetics", "Integreret hastighedslov"),
            ("Bestem orden & k", "kinetics", "Bestem orden & k"),
            ("☢️ Nuklear halvliv", "nuklear", None),
        ])

    elif _kin_active == "Bestem orden & k":
        st.markdown("#### Determine Order & k (two-point)")
        col1, col2 = st.columns(2)
        with col1:
            t1 = st.number_input("t1 (s)", value=0.0, min_value=0.0)
            C1 = st.number_input("C1 (M)", value=0.100, min_value=1e-12, format="%.6f")
        with col2:
            t2 = st.number_input("t2 (s)", value=10.0, min_value=0.0)
            C2 = st.number_input("C2 (M)", value=0.003, min_value=1e-12, format="%.6f")
        if st.button("Beregn", type="primary"):
            try:
                res, steps, meta = calculate_determine_order_k_with_steps(t1, C1, t2, C2)
                st.success(f"Order = {res['order']}, k = {res['k']:.6g}, residual = {res['residual']:.3e}")
                with st.expander("Vis trin"):
                    for s in steps:
                        st.markdown(s)
            except Exception as e:
                st.error(str(e))

    elif _kin_active == "📋 Initial rates":
        import math, pandas as pd
        st.markdown("#### 📋 Initial rates-metoden – bestem reaktionsorden fra eksperimenter")
        st.latex(r"\text{Hastighedslov: } r = k[A]^m[B]^n")
        st.markdown(
            "Angiv mindst 3 eksperimenter. Metoden finder ordenen for hvert reaktant ved at sammenligne "
            "to eksperimenter hvor kun ét reaktant ændres (**ceteris paribus**)."
        )
        st.info("💡 Typisk eksamen: du får en tabel med [A], [B] og initial rate – find m, n og k.")

        n_reactants = st.radio("Antal reaktanter:", [1, 2], index=1, horizontal=True, key="ir_nreact")
        n_exp = st.number_input("Antal eksperimenter:", value=3, min_value=2, max_value=6, step=1, key="ir_nexp")

        headers = ["Eksperiment"] + (["[A] (M)", "[B] (M)"] if n_reactants == 2 else ["[A] (M)"]) + ["Initial rate (M/s)"]
        defaults = {
            2: [
                [1, 0.10, 0.10, 1.2e-4],
                [2, 0.20, 0.10, 4.8e-4],
                [3, 0.10, 0.20, 2.4e-4],
            ],
            1: [
                [1, 0.10, 1.2e-4],
                [2, 0.20, 9.6e-4],
                [3, 0.40, 7.7e-3],
            ],
        }[n_reactants]

        rows = []
        for i in range(int(n_exp)):
            d = defaults[i] if i < len(defaults) else ([i+1] + [0.10]*n_reactants + [1e-5])
            cols_row = st.columns(len(headers))
            row = [i + 1]
            cols_row[0].markdown(f"**Exp {i+1}**")
            if n_reactants == 2:
                row.append(cols_row[1].number_input("", value=float(d[1]), min_value=1e-9, format="%.4f", key=f"ir_A_{i}", label_visibility="collapsed"))
                row.append(cols_row[2].number_input("", value=float(d[2]), min_value=1e-9, format="%.4f", key=f"ir_B_{i}", label_visibility="collapsed"))
                row.append(cols_row[3].number_input("", value=float(d[3]), min_value=1e-20, format="%.3e", key=f"ir_r_{i}", label_visibility="collapsed"))
            else:
                row.append(cols_row[1].number_input("", value=float(d[1]), min_value=1e-9, format="%.4f", key=f"ir_A_{i}", label_visibility="collapsed"))
                row.append(cols_row[2].number_input("", value=float(d[2]), min_value=1e-20, format="%.3e", key=f"ir_r_{i}", label_visibility="collapsed"))
            rows.append(row)

        if st.button("Beregn orden og k", type="primary", key="ir_calc"):
            try:
                data = rows
                steps_out = []

                # Find order m for A: find two rows where B is same
                if n_reactants == 2:
                    # Find pairs where B is same (within 1%)
                    pair_A = None
                    for i in range(len(data)):
                        for j in range(i+1, len(data)):
                            if abs(data[i][2] - data[j][2]) / data[i][2] < 0.02:
                                if abs(data[i][1] - data[j][1]) / data[i][1] > 0.05:
                                    pair_A = (i, j)
                                    break
                        if pair_A:
                            break
                    pair_B = None
                    for i in range(len(data)):
                        for j in range(i+1, len(data)):
                            if abs(data[i][1] - data[j][1]) / data[i][1] < 0.02:
                                if abs(data[i][2] - data[j][2]) / data[i][2] > 0.05:
                                    pair_B = (i, j)
                                    break
                        if pair_B:
                            break

                    if pair_A:
                        i, j = pair_A
                        ratio_r = data[j][3] / data[i][3]
                        ratio_A = data[j][1] / data[i][1]
                        m_raw = math.log(ratio_r) / math.log(ratio_A)
                        m = round(m_raw)
                        steps_out.append(f"**Orden for A (m):** Exp {i+1} og {j+1} (samme [B])")
                        steps_out.append(f"r{j+1}/r{i+1} = ([A]{j+1}/[A]{i+1})^m → {ratio_r:.4f} = {ratio_A:.4f}^m → m = ln({ratio_r:.4f})/ln({ratio_A:.4f}) = **{m_raw:.3f} ≈ {m}**")
                    else:
                        m = None
                        steps_out.append("⚠️ Kunne ikke finde eksperimentpar med samme [B] – juster input.")

                    if pair_B:
                        i, j = pair_B
                        ratio_r = data[j][3] / data[i][3]
                        ratio_B = data[j][2] / data[i][2]
                        n_raw = math.log(ratio_r) / math.log(ratio_B)
                        n_ord = round(n_raw)
                        steps_out.append(f"**Orden for B (n):** Exp {i+1} og {j+1} (samme [A])")
                        steps_out.append(f"r{j+1}/r{i+1} = ([B]{j+1}/[B]{i+1})^n → {ratio_r:.4f} = {ratio_B:.4f}^n → n = **{n_raw:.3f} ≈ {n_ord}**")
                    else:
                        n_ord = None
                        steps_out.append("⚠️ Kunne ikke finde eksperimentpar med samme [A] – juster input.")

                    if m is not None and n_ord is not None:
                        k_vals = [row[3] / (row[1]**m * row[2]**n_ord) for row in data]
                        k_avg = sum(k_vals) / len(k_vals)
                        steps_out.append(f"**Beregn k** for hvert eksperiment (k = r / ([A]^{m}·[B]^{n_ord})):")
                        for idx, (row, kv) in enumerate(zip(data, k_vals)):
                            steps_out.append(f"  Exp {idx+1}: k = {row[3]:.3e} / ({row[1]:.4f}^{m} × {row[2]:.4f}^{n_ord}) = **{kv:.4e}**")
                        steps_out.append(f"**k (gennemsnit) = {k_avg:.4e} M^(1−m−n)·s⁻¹**")
                        st.success(f"✅ **r = k·[A]^{m}·[B]^{n_ord}**   med  k = {k_avg:.4e}")
                    else:
                        st.warning("Kunne ikke bestemme begge ordener automatisk.")

                else:  # single reactant
                    all_m = []
                    for i in range(len(data)):
                        for j in range(i+1, len(data)):
                            ratio_r = data[j][2] / data[i][2]
                            ratio_A = data[j][1] / data[i][1]
                            m_raw = math.log(ratio_r) / math.log(ratio_A)
                            all_m.append(m_raw)
                            steps_out.append(f"Exp {i+1}→{j+1}: m = ln(r{j+1}/r{i+1})/ln([A]{j+1}/[A]{i+1}) = {m_raw:.3f}")
                    m = round(sum(all_m) / len(all_m))
                    steps_out.append(f"**m ≈ {m}** (gennemsnit af {len(all_m)} par)")
                    k_vals = [row[2] / row[1]**m for row in data]
                    k_avg = sum(k_vals) / len(k_vals)
                    steps_out.append(f"**k (gennemsnit) = {k_avg:.4e}**")
                    st.success(f"✅ **r = k·[A]^{m}**   med  k = {k_avg:.4e}")

                with st.expander("🔍 Trin-for-trin", expanded=True):
                    for s in steps_out:
                        st.markdown(s)
            except Exception as e:
                st.error(f"Fejl: {e}")
        _quick_links([
            ("📊 Halvliv", "kinetics", "📊 Halvliv"),
            ("Integreret hastighedslov", "kinetics", "Integreret hastighedslov"),
            ("Arrhenius", "kinetics", "Arrhenius"),
        ])

    elif _kin_active == "Arrhenius":
        st.markdown("#### Arrhenius")
        st.caption("💡 **Fremad:** du kender k₁ ved T₁ og Eₐ → beregn k₂ ved T₂. **Baglæns:** du kender k₁ og k₂ → beregn Eₐ.")
        st.markdown("Forlæns (én måling)")
        k1 = st.number_input("k1 (s^-1)", value=1.0e-3, format="%.6e")
        T1 = st.number_input("T1 (K)", value=298.15)
        T2 = st.number_input("T2 (K)", value=308.15)
        Ea = st.number_input("Ea (kJ/mol)", value=50.0)
        if st.button("Beregn k₂", type="primary"):
            try:
                k2, steps, _ = calculate_arrhenius_forward_with_steps(k1, T1, T2, Ea)
                st.success(f"k2 = {k2:.6g} s^-1")
                with st.expander("Vis trin"):
                    for s in steps:
                        st.markdown(s)
            except Exception as e:
                st.error(str(e))
        st.markdown("Baglæns – find Eₐ (to målinger)")
        k2v = st.number_input("k2 (s^-1)", value=3.0e-3, format="%.6e")
        if st.button("Beregn Eₐ", type="primary"):
            try:
                Ea_kJ, steps, _ = calculate_arrhenius_two_point_Ea_with_steps(k1, T1, k2v, T2)
                st.success(f"Ea = {Ea_kJ:.4g} kJ/mol")
                with st.expander("Vis trin"):
                    for s in steps:
                        st.markdown(s)
            except Exception as e:
                st.error(str(e))

    elif _kin_active == "Hastighedsrelationer":
        st.markdown("#### Hastighedsrelationer ud fra støkiometri")
        st.info("Given a balanced reaction aA + bB -> cC + dD, rates relate as −(1/a)d[A]/dt = −(1/b)d[B]/dt = (1/c)d[C]/dt …")


def show_electrochemistry_page():
    st.title("🔋 Elektrokemi")
    st.markdown("---")
    from calculators.electrochemistry import (
        calculate_standard_cell_with_steps,
        calculate_nernst_with_steps,
        calculate_deltaG_from_E_with_steps,
        calculate_K_from_E0_with_steps,
        calculate_daniell_Q,
        calculate_e_cell_from_half_potentials_with_steps,
        calculate_e_cell_from_gibbs_with_steps,
        calculate_unknown_potential_from_gibbs_with_steps,
        calculate_k_from_gibbs_with_steps,
        calculate_gibbs_from_k_with_steps,
        calculate_k_from_e_cell_with_steps,
        calculate_gibbs_from_e_cell_with_steps,
        calculate_e_cell_from_k_with_steps,
        match_candidate_potential_value,
    )

    _ec_options = ["Byg en celle", "Nernst", "ΔG og K", "Redoks termodynamik", "⚡ Faradays lov"]
    _ec_active = _render_styled_tab_nav(_ec_options, key="electro_tab", nav_key="nav_electrochemistry")

    if _ec_active == "Byg en celle":
        from core.electrochem import load_reduction_potentials
        df = load_reduction_potentials()
        cath = st.selectbox("Katode (reduktion)", df['half_reaction'].tolist(), key="electro_cath")
        an = st.selectbox("Anode (reduktion)", df['half_reaction'].tolist(), key="electro_an")
        if st.button("Beregn E°celle", type="primary", key="electro_cell_btn"):
            try:
                res, steps, _ = calculate_standard_cell_with_steps(cath, an)
                st.success(f"E°cell = {res['E0_cell_V']:.4g} V, n = {res['n']}")
                with st.expander("Vis trin"):
                    for s in steps:
                        st.markdown(s)
            except Exception as e:
                st.error(str(e))

        _quick_links([
            ("Nernst", "electrochemistry", "Nernst"),
            ("ΔG og K", "electrochemistry", "ΔG og K"),
            ("🔋 Redoxafstemning", "stoichiometry", "🔋 Redoxafstemning"),
        ])

    elif _ec_active == "Nernst":
        st.markdown("#### Nernst-beregner")
        E0 = st.number_input("E°cell (V)", value=1.10, key="nernst_E0")
        n = st.number_input("n (electrons)", value=2, min_value=1, key="nernst_n")
        T = st.number_input("T (K)", value=298.15, min_value=0.0, key="nernst_T")
        st.markdown("Quick Daniell helper: Q = [Zn2+]/[Cu2+]")
        Zn2 = st.number_input("[Zn2+] (M)", value=0.10, min_value=1e-12, format="%.4f", key="nernst_Zn2")
        Cu2 = st.number_input("[Cu2+] (M)", value=1.00, min_value=1e-12, format="%.4f", key="nernst_Cu2")
        Q = calculate_daniell_Q(Zn2, Cu2)
        st.info(f"Q = {Q:.6g}")
        if st.button("Beregn E", type="primary", key="nernst_btn"):
            try:
                E, steps, _ = calculate_nernst_with_steps(E0, int(n), T, Q)
                st.success(f"E = {E:.6g} V")
                with st.expander("Vis trin"):
                    for s in steps:
                        st.markdown(s)
            except Exception as e:
                st.error(str(e))

    elif _ec_active == "ΔG og K":
        st.markdown("#### ΔG° og K")
        n = st.number_input("n (electrons)", value=2, min_value=1, key="g_n")
        E0 = st.number_input("E°cell (V)", value=1.10, format="%.4f", key="g_E0")
        if st.button("Beregn ΔG°", type="primary", key="dg_btn"):
            try:
                dG_kJ, steps, _ = calculate_deltaG_from_E_with_steps(int(n), E0)
                st.success(f"ΔG° = {dG_kJ:.4g} kJ/mol")
                with st.expander("Vis trin"):
                    for s in steps:
                        st.markdown(s)
            except Exception as e:
                st.error(str(e))
        st.markdown("---")
        T = st.number_input("T (K)", value=298.15, key="g_T")
        if st.button("Beregn K", key="K_btn"):
            try:
                K, log10K, steps, _ = calculate_K_from_E0_with_steps(int(n), E0, T)
                st.success(f"K = {K:.3g} (log10K = {log10K:.3f})")
                with st.expander("Vis trin"):
                    for s in steps:
                        st.markdown(s)
            except Exception as e:
                st.error(str(e))
        _quick_links([
            ("Byg en celle", "electrochemistry", "Byg en celle"),
            ("Nernst", "electrochemistry", "Nernst"),
            ("⚗️ Kc/Kp", "ligevaegt", "🔄 Kc/Kp konvertering"),
        ])

    elif _ec_active == "Redoks termodynamik":
        st.markdown("### Redox, ΔG°, E°cell and K")
        st.caption("Eksamensvenlig redox-termokemi med tydelige mellemregninger og enhedskontrol.")

        def render_step_block(given, formula, substitution, result, interpretation):
            st.markdown("**Given**")
            for line in given:
                st.markdown(f"- {line}")
            st.markdown("**Formula used**")
            for line in formula:
                st.markdown(f"- {line}")
            st.markdown("**Substitution**")
            for line in substitution:
                st.markdown(f"- {line}")
            st.markdown("**Result**")
            for line in result:
                st.markdown(f"- {line}")
            st.markdown("**Interpretation**")
            for line in interpretation:
                st.markdown(f"- {line}")

        # Section 1
        st.markdown("---")
        st.subheader("1) Find E°cell ud fra halvcellereaktioner")
        c1, c2 = st.columns(2)
        with c1:
            cathode_E = st.number_input("Cathode potential (V)", value=1.087, format="%.4f", key="rt_cath_E")
            cathode_type_label = st.selectbox(
                "Cathode potential type",
                ["Reduction potential (E°red)", "Oxidation potential (E°ox)", "Actual half-reaction direction"],
                key="rt_cath_type",
            )
        with c2:
            anode_E = st.number_input("Anode potential (V)", value=0.762, format="%.4f", key="rt_anode_E")
            anode_type_label = st.selectbox(
                "Anode potential type",
                ["Reduction potential (E°red)", "Oxidation potential (E°ox)", "Actual half-reaction direction"],
                index=1,
                key="rt_anode_type",
            )

        type_map = {
            "Reduction potential (E°red)": "red",
            "Oxidation potential (E°ox)": "ox",
            "Actual half-reaction direction": "actual",
        }
        cath_type = type_map[cathode_type_label]
        an_type = type_map[anode_type_label]

        if st.button("Beregn E°cell", type="primary", key="rt_e_cell_calc"):
            try:
                res, steps, _ = calculate_e_cell_from_half_potentials_with_steps(
                    cathode_E, cath_type, anode_E, an_type
                )
                for warning in res.get("warnings", []):
                    st.warning(warning)

                given = [
                    f"E°cathode = {cathode_E:.4g} V ({cathode_type_label})",
                    f"E°anode = {anode_E:.4g} V ({anode_type_label})",
                ]
                formula = [res["formula"], "Do not multiply E° by stoichiometric coefficients."]
                substitution = [
                    f"E°cathode(actual) = {res['cathode_actual_V']:.4g} V",
                    f"E°anode(actual) = {res['anode_actual_V']:.4g} V",
                    f"E°cell = {res['cathode_actual_V']:.4g} + {res['anode_actual_V']:.4g}",
                ]
                result = [f"E°cell = {res['E_cell_V']:.4g} V"]
                interpretation = [
                    "Positive E°cell means a spontaneous redox reaction under standard conditions.",
                ]
                render_step_block(given, formula, substitution, result, interpretation)
            except Exception as exc:
                st.error(str(exc))

        # Section 2
        st.markdown("---")
        st.subheader("2) Find anode/kathode-potentiale ud fra ΔG°")
        g1, g2, g3 = st.columns(3)
        with g1:
            dG_value = st.number_input("ΔG°", value=-356.9, format="%.4f", key="rt_dg_val")
            dG_unit = st.selectbox("ΔG° unit", ["J/mol", "kJ/mol"], index=1, key="rt_dg_unit")
        with g2:
            n_value = st.number_input("n (electrons)", value=2, min_value=1, key="rt_n")
            known_E = st.number_input("Known potential (V)", value=1.087, format="%.4f", key="rt_known_E")
        with g3:
            known_side = st.selectbox("Known electrode", ["cathode", "anode"], key="rt_known_side")
            known_type = st.selectbox(
                "Known potential type",
                ["Reduction potential (E°red)", "Oxidation potential (E°ox)", "Actual half-reaction direction"],
                key="rt_known_type",
            )

        unknown_choice = st.selectbox(
            "Find",
            [
                "anode oxidation potential",
                "anode reduction potential",
                "cathode reduction potential",
                "cathode oxidation potential",
            ],
            key="rt_unknown_choice",
        )

        unknown_map = {
            "anode oxidation potential": ("anode", "ox"),
            "anode reduction potential": ("anode", "red"),
            "cathode reduction potential": ("cathode", "red"),
            "cathode oxidation potential": ("cathode", "ox"),
        }
        unknown_side, unknown_type = unknown_map[unknown_choice]
        known_type_norm = type_map[known_type]

        if "rt_candidates" not in st.session_state:
            st.session_state["rt_candidates"] = []

        st.markdown("#### Candidate options (optional)")
        oc1, oc2, oc3, oc4 = st.columns([2, 1, 1, 1])
        with oc1:
            cand_label = st.text_input("Label", value="Zn(s) -> Zn2+ + 2e-", key="rt_cand_label")
        with oc2:
            cand_value = st.number_input("Potential (V)", value=0.762, format="%.4f", key="rt_cand_value")
        with oc3:
            cand_type = st.selectbox("Type", ["E°ox", "E°red"], key="rt_cand_type")
        with oc4:
            if st.button("Add", key="rt_cand_add"):
                st.session_state["rt_candidates"].append(
                    {
                        "label": cand_label,
                        "value": cand_value,
                        "type": "ox" if cand_type == "E°ox" else "red",
                    }
                )
            if st.button("Clear", key="rt_cand_clear"):
                st.session_state["rt_candidates"] = []

        if st.session_state["rt_candidates"]:
            cand_df = pd.DataFrame(st.session_state["rt_candidates"])
            st.dataframe(cand_df, use_container_width=True, hide_index=True)

        if st.button("Beregn ukendt potentiale", type="primary", key="rt_unknown_calc"):
            try:
                res, steps, _ = calculate_unknown_potential_from_gibbs_with_steps(
                    dG_value,
                    dG_unit,
                    n_value,
                    known_E,
                    known_side,
                    known_type_norm,
                    unknown_side,
                    unknown_type,
                )

                if dG_unit == "kJ/mol":
                    st.warning("ΔG° was entered in kJ/mol and converted to J/mol.")

                given = [
                    f"ΔG° = {dG_value:.6g} {dG_unit}",
                    f"n = {int(n_value)}",
                    f"Known {known_side} = {known_E:.4g} V ({known_type})",
                ]
                formula = ["ΔG° = −n F E°cell", "E°cell = E°cathode(actual) + E°anode(actual)"]
                substitution = [
                    f"E°cell = {res['E_cell_V']:.4g} V",
                    f"Unknown actual = {res['unknown_actual_V']:.4g} V",
                ]
                result = [
                    f"{unknown_choice} = {res['unknown_V']:.4g} V",
                ]
                interpretation = [
                    "If a half-reaction is reversed, the sign of E° changes.",
                ]
                render_step_block(given, formula, substitution, result, interpretation)

                match = {}
                if st.session_state["rt_candidates"]:
                    match = match_candidate_potential_value(
                        res["unknown_V"],
                        unknown_type,
                        st.session_state["rt_candidates"],
                        tolerance=0.005,
                    )
                if match:
                    st.success(f"Correct answer: {match['label']} (Δ = {match['diff']:.4g} V)")
                elif st.session_state["rt_candidates"]:
                    st.info("No candidate matched within ±0.005 V.")
            except Exception as exc:
                st.error(str(exc))

        # Section 3
        st.markdown("---")
        st.subheader("3) Find K, ΔG° eller E°cell")
        target = st.selectbox(
            "Calculation target",
            [
                "find K from ΔG°",
                "find ΔG° from K",
                "find K from E°cell",
                "find E°cell from K",
                "find ΔG° from E°cell",
                "find E°cell from ΔG°",
            ],
            key="rt_target",
        )

        # Initialize all as None; we'll only create widgets for the selected target
        dG_value_3 = None
        dG_unit_3 = None
        e_cell_3 = None
        n_value_3 = None
        t_value_3 = None
        t_unit_3 = None
        k_value_3 = None

        # Use explicit conditional rendering so non-relevant widgets are not created
        if target in {"find K from ΔG°", "find E°cell from ΔG°"}:
            t1, t2 = st.columns(2)
            with t1:
                dG_value_3 = st.number_input("ΔG°", value=-50.0, format="%.4f", key="rt_dg_val_3")
                dG_unit_3 = st.selectbox("ΔG° unit", ["J/mol", "kJ/mol"], key="rt_dg_unit_3")
            with t2:
                if target == "find E°cell from ΔG°":
                    n_value_3 = st.number_input("n", value=1, min_value=1, key="rt_n_3")
                else:
                    t_value_3 = st.number_input("Temperature", value=298.15, format="%.4f", key="rt_t_3")
                    t_unit_3 = st.selectbox("Temp unit", ["K", "°C"], key="rt_t_unit_3")

        elif target in {"find ΔG° from K", "find E°cell from K"}:
            # Only K and Temperature (and maybe n) are shown for these targets
            t1, t2 = st.columns(2)
            with t1:
                k_value_3 = st.number_input("K", value=1.0, format="%.4e", key="rt_k_3")
            with t2:
                t_value_3 = st.number_input("Temperature", value=298.15, format="%.4f", key="rt_t_3")
                t_unit_3 = st.selectbox("Temp unit", ["K", "°C"], key="rt_t_unit_3")
            if target == "find E°cell from K":
                n_value_3 = st.number_input("n", value=1, min_value=1, key="rt_n_3")

        elif target == "find K from E°cell":
            # For K from E°cell we only need E°, n and Temperature
            t1, t2, t3 = st.columns(3)
            with t1:
                e_cell_3 = st.number_input("E°cell (V)", value=0.585, format="%.4f", key="rt_e_cell_3")
            with t2:
                n_value_3 = st.number_input("n", value=1, min_value=1, key="rt_n_3")
            with t3:
                t_value_3 = st.number_input("Temperature", value=298.15, format="%.4f", key="rt_t_3")
                t_unit_3 = st.selectbox("Temp unit", ["K", "°C"], key="rt_t_unit_3")

        elif target == "find ΔG° from E°cell":
            t1, t2 = st.columns(2)
            with t1:
                e_cell_3 = st.number_input("E°cell (V)", value=0.585, format="%.4f", key="rt_e_cell_3")
            with t2:
                n_value_3 = st.number_input("n", value=1, min_value=1, key="rt_n_3")

        if st.button("Beregn", type="primary", key="rt_target_calc"):
            try:
                if t_unit_3 == "°C":
                    st.warning("Temperature was entered in °C and converted to K.")
                if dG_unit_3 == "kJ/mol":
                    st.warning("ΔG° was entered in kJ/mol and converted to J/mol.")

                if target == "find K from ΔG°":
                    res, steps, _ = calculate_k_from_gibbs_with_steps(dG_value_3, dG_unit_3, t_value_3, t_unit_3)
                    result_value = f"K = {res['K']:.6g}"
                    dG_J = res["dG_J"]
                    e_cell_val = None
                elif target == "find ΔG° from K":
                    res, steps, _ = calculate_gibbs_from_k_with_steps(k_value_3, t_value_3, t_unit_3)
                    result_value = f"ΔG° = {res['dG_J']:.6g} J/mol"
                    dG_J = res["dG_J"]
                    e_cell_val = None
                elif target == "find K from E°cell":
                    res, steps, _ = calculate_k_from_e_cell_with_steps(n_value_3, e_cell_3, t_value_3, t_unit_3)
                    result_value = f"K = {res['K']:.6g}"
                    dG_J = None
                    e_cell_val = e_cell_3
                elif target == "find E°cell from K":
                    res, steps, _ = calculate_e_cell_from_k_with_steps(n_value_3, k_value_3, t_value_3, t_unit_3)
                    result_value = f"E°cell = {res['E_cell_V']:.6g} V"
                    dG_J = None
                    e_cell_val = res["E_cell_V"]
                elif target == "find ΔG° from E°cell":
                    res, steps, _ = calculate_gibbs_from_e_cell_with_steps(n_value_3, e_cell_3)
                    result_value = f"ΔG° = {res['dG_J']:.6g} J/mol"
                    dG_J = res["dG_J"]
                    e_cell_val = e_cell_3
                else:
                    res, steps, _ = calculate_e_cell_from_gibbs_with_steps(dG_value_3, dG_unit_3, n_value_3)
                    result_value = f"E°cell = {res['E_cell_V']:.6g} V"
                    dG_J = res["dG_J"]
                    e_cell_val = res["E_cell_V"]

                given = [f"Target: {target}"]
                if dG_value_3 is not None and dG_unit_3 is not None:
                    given.append(f"ΔG° = {dG_value_3:.6g} {dG_unit_3}")
                if e_cell_3 is not None:
                    given.append(f"E°cell = {e_cell_3:.6g} V")
                if n_value_3 is not None:
                    given.append(f"n = {int(n_value_3)}")
                if t_value_3 is not None and t_unit_3 is not None:
                    given.append(f"T = {t_value_3:.6g} {t_unit_3}")
                if k_value_3 is not None:
                    given.append(f"K = {k_value_3:.6g}")
                formula = ["ΔG° = −n F E°cell", "ΔG° = −R T ln(K)", "E°cell = (R T / n F) ln(K)"]
                substitution = steps
                result = [result_value]

                interpretation = []
                if dG_J is not None:
                    if abs(dG_J) < 1e-9:
                        interpretation.append("ΔG° ≈ 0 → equilibrium.")
                    elif dG_J < 0:
                        interpretation.append("ΔG° < 0 → spontaneous under standard conditions.")
                    else:
                        interpretation.append("ΔG° > 0 → non-spontaneous under standard conditions.")
                if e_cell_val is not None:
                    if abs(e_cell_val) < 1e-9:
                        interpretation.append("E°cell ≈ 0 → equilibrium.")
                    elif e_cell_val > 0:
                        interpretation.append("E°cell > 0 → spontaneous under standard conditions.")
                    else:
                        interpretation.append("E°cell < 0 → non-spontaneous under standard conditions.")

                render_step_block(given, formula, substitution, result, interpretation)
            except Exception as exc:
                st.error(str(exc))

    elif _ec_active == "⚡ Faradays lov":
        _render_faraday_tab()


def _render_faraday_tab():
    """Faraday's law of electrolysis tab."""
    import math as _math
    F_CONST = 96485.0  # C/mol

    st.markdown("## ⚡ Faradays lov – Elektrolyse")
    st.markdown(
        r"$$m = \frac{M \cdot I \cdot t}{n \cdot F}$$"
    )
    st.markdown(
        "Beregn den masse der afsættes (eller opløses) ved elektrolyse, "
        "eller find strøm/tid ud fra ønsket masse."
    )
    st.markdown("---")

    col1, col2 = st.columns([3, 2], gap="large")

    COMMON_METALS = {
        "Cu (kobber, Cu²⁺→Cu)":   ("Cu",  63.55,  2),
        "Ag (sølv, Ag⁺→Ag)":      ("Ag",  107.87, 1),
        "Au (guld, Au³⁺→Au)":     ("Au",  196.97, 3),
        "Zn (zink, Zn²⁺→Zn)":     ("Zn",  65.38,  2),
        "Ni (nikkel, Ni²⁺→Ni)":   ("Ni",  58.69,  2),
        "Al (aluminium, Al³⁺→Al)":("Al",  26.98,  3),
        "Fe (jern, Fe²⁺→Fe)":     ("Fe",  55.85,  2),
        "Fe (jern, Fe³⁺→Fe)":     ("Fe",  55.85,  3),
        "Pb (bly, Pb²⁺→Pb)":      ("Pb",  207.2,  2),
        "Cr (krom, Cr³⁺→Cr)":     ("Cr",  52.00,  3),
        "H₂ (brint, 2H⁺→H₂)":    ("H2",  2.016,  1),
        "Cl₂ (klor, 2Cl⁻→Cl₂)":  ("Cl2", 70.90,  1),
    }

    with col1:
        st.markdown("### Input")

        preset = st.selectbox(
            "Vælg metal/stof (udfylder M og n automatisk):",
            ["Manuel input"] + list(COMMON_METALS.keys()),
            key="far_preset",
        )

        if preset != "Manuel input":
            sym, M_preset, n_preset = COMMON_METALS[preset]
        else:
            M_preset, n_preset = 63.55, 2

        c_m, c_n = st.columns(2)
        with c_m:
            M = st.number_input("Molarmasse M (g/mol):", value=float(M_preset), min_value=0.1, key="far_M")
        with c_n:
            n_e = st.number_input("Elektroner per ion n:", value=int(n_preset), min_value=1, step=1, key="far_n")

        unknown = st.radio(
            "Hvad vil du beregne?",
            ["m — masse afsat (g)", "I — strøm (A)", "t — tid"],
            key="far_unknown",
            horizontal=True,
        )
        _far_help = {
            "m — masse afsat (g)": "💡 Brug Faradays lov: m = (I · t · M) / (n · F). Du kender strøm, tid og stof.",
            "I — strøm (A)": "💡 Omvendt beregning – du kender masse, tid og stof, finder strømmen.",
            "t — tid": "💡 Omvendt beregning – du kender masse, strøm og stof, finder den nødvendige tid.",
        }
        st.caption(_far_help[unknown])

        c1, c2 = st.columns(2)
        with c1:
            if "I" not in unknown:
                I_val = st.number_input("Strøm I (A):", value=2.0, min_value=0.0, key="far_I")
            else:
                I_val = None
            if "t" not in unknown:
                t_val_raw = st.number_input("Tid:", value=3600.0, min_value=0.0, key="far_t")
                t_unit = st.selectbox("Tidsenhed:", ["s", "min", "h"], key="far_t_unit")
                t_s = t_val_raw * {"s": 1, "min": 60, "h": 3600}[t_unit]
            else:
                t_val_raw = None; t_s = None; t_unit = "s"
        with c2:
            if "m" not in unknown:
                m_val = st.number_input("Masse m (g):", value=2.37, min_value=0.0, key="far_m")
            else:
                m_val = None

        run = st.button("Beregn", type="primary", key="far_run")

    with col2:
        st.markdown("### Formel og konstanter")
        st.markdown(r"""
**Faradays lov:**
$$m = \frac{M \cdot I \cdot t}{n \cdot F}$$

| Symbol | Betydning | Enhed |
|--------|-----------|-------|
| m | Masse afsat | g |
| M | Molarmasse | g/mol |
| I | Strømstyrke | A |
| t | Tid | s |
| n | Elektroner per ion | — |
| F | Faradays konstant | 96485 C/mol |

**Ladning:** Q = I × t (coulomb)

**Mol elektroner:** $n_e = Q / F$

**Mol stof:** $n_{stof} = n_e / n$
        """)
        st.info(f"F = {F_CONST:.0f} C/mol")

    if run:
        steps = []
        steps.append(f"**M = {M:.3f} g/mol,  n = {n_e},  F = {F_CONST:.0f} C/mol**")

        try:
            if "m" in unknown:
                Q = I_val * t_s
                mol_e = Q / F_CONST
                mol_sub = mol_e / n_e
                m_result = mol_sub * M
                steps.append(f"Q = I × t = {I_val} × {t_s:.0f} = {Q:.2f} C")
                steps.append(f"mol e⁻ = Q/F = {Q:.2f}/{F_CONST:.0f} = {mol_e:.5f} mol")
                steps.append(f"mol stof = mol e⁻ / n = {mol_e:.5f} / {n_e} = {mol_sub:.5f} mol")
                steps.append(f"**m = mol × M = {mol_sub:.5f} × {M:.3f} = {m_result:.4f} g**")
                st.success(f"### m = {m_result:.4f} g")

            elif "I" in unknown:
                Q_needed = (m_val * n_e * F_CONST) / M
                I_result = Q_needed / t_s
                steps.append(f"Q = m × n × F / M = {m_val} × {n_e} × {F_CONST:.0f} / {M:.3f} = {Q_needed:.2f} C")
                steps.append(f"**I = Q / t = {Q_needed:.2f} / {t_s:.0f} = {I_result:.4f} A**")
                st.success(f"### I = {I_result:.4f} A")

            else:  # t unknown
                Q_needed = (m_val * n_e * F_CONST) / M
                t_result_s = Q_needed / I_val
                t_display = t_result_s / 3600 if t_result_s > 3600 else (t_result_s / 60 if t_result_s > 120 else t_result_s)
                t_unit_out = "h" if t_result_s > 3600 else ("min" if t_result_s > 120 else "s")
                steps.append(f"Q = m × n × F / M = {m_val} × {n_e} × {F_CONST:.0f} / {M:.3f} = {Q_needed:.2f} C")
                steps.append(f"**t = Q / I = {Q_needed:.2f} / {I_val} = {t_result_s:.2f} s = {t_display:.3f} {t_unit_out}**")
                st.success(f"### t = {t_result_s:.2f} s  ({t_display:.3f} {t_unit_out})")

        except Exception as e:
            st.error(str(e))
            st.stop()

        with st.expander("📋 Vis udledning trin for trin", expanded=False):
            for s in steps:
                st.markdown(s)

    st.markdown("---")
    with st.expander("💡 Eksempler fra eksamen", expanded=False):
        st.markdown("""
**Eksempel 1:** 2.00 A i 1.00 time → masse Cu afsat (Cu²⁺, M=63.55, n=2)?

Q = 2.00 × 3600 = 7200 C
mol e⁻ = 7200 / 96485 = 0.07462 mol
mol Cu = 0.07462 / 2 = 0.03731 mol
m = 0.03731 × 63.55 = **2.37 g Cu**

---

**Eksempel 2:** Afsæt 1.00 g Ag (Ag⁺, M=107.87, n=1) med 0.500 A. Hvor lang tid?

Q = 1.00 × 1 × 96485 / 107.87 = 894.6 C
t = 894.6 / 0.500 = **1789 s ≈ 29.8 min**

---

**Eksempel 3:** Produktion af Al fra Al₂O₃ (Al³⁺, n=3, M=26.98). 1000 A i 24 h?

Q = 1000 × 86400 = 8.64×10⁷ C
mol Al = 8.64×10⁷ / (96485 × 3) = 298.5 mol
m = 298.5 × 26.98 = **8055 g ≈ 8.06 kg**
        """)


def show_thermochemistry_page():
    """Display new Thermochemistry calculators (Part 4)."""
    st.title("🔥 Termokemi")
    st.markdown("---")

    from calculators.thermochemistry import (
        calculate_calorimetry_with_steps,
        calculate_heating_curve_water_with_steps,
    )
    from core.reaction_enthalpy import (
        parseReaction,
        computeRxnEnthalpy,
        balanceReaction,
        isReactionBalanced,
    )
    from core.dhf_database import load_dhf_database, add_to_dhf_database, getDhf, normalizeSpeciesKey
    from core.hess_solver import solve_hess_problem

    tab_enthalpy, tab_gibbs, tab_calorimetry, tab_heating, tab_vanthoff, tab_kirchhoff, tab_bornhaber = st.tabs([
        "Enthalpi (ΔH°)",
        "Gibbs (ΔG)",
        "Kalorimetri (q = mcΔT)",
        "Opvarmningskurve",
        "📈 Van't Hoff-plot",
        "🌡️ Kirchhoffs lov",
        "🔷 Born-Haber",
    ])

    with tab_gibbs:
        _render_gibbs_calculator(include_page_header=False)

    with tab_calorimetry:
        st.markdown("#### Kalorimetri")
        col1, col2 = st.columns(2)
        with col1:
            mass_g = st.number_input("Mass (g)", value=100.0, min_value=0.0)
            preset = st.selectbox("Preset", ["water_ice", "water_liquid", "water_steam"], index=1, key="thermo_cal_preset")
            c_custom = st.number_input("Specific heat c (J/(g·K)) [optional]", value=0.0, min_value=0.0)
            c_val = None if c_custom == 0.0 else c_custom
        with col2:
            mode = st.radio("Temperature input", ["ΔT (K)", "T_initial/T_final (°C)"])
            _cal_help = {
                "ΔT (K)": "💡 Brug denne hvis du allerede kender temperaturforskellen direkte.",
                "T_initial/T_final (°C)": "💡 Brug denne hvis du har start- og sluttemperatur – ΔT beregnes automatisk.",
            }
            st.caption(_cal_help[mode])
            if mode == "ΔT (K)":
                deltaT = st.number_input("ΔT (K)", value=25.0)
                T_i = None
                T_f = None
            else:
                T_i = st.number_input("T_initial (°C)", value=20.0)
                T_f = st.number_input("T_final (°C)", value=45.0)
                deltaT = None
            out_unit = st.selectbox("Output unit", ["kJ", "J"], index=0, key="thermo_cal_unit")

        if st.button("Beregn q", type="primary"):
            try:
                q_val, steps, meta = calculate_calorimetry_with_steps(
                    mass_g=mass_g,
                    delta_T_K=deltaT,
                    T_initial_C=T_i,
                    T_final_C=T_f,
                    c_J_per_gK=c_val,
                    preset=preset,
                    output_unit=out_unit,
                )
                st.success(f"q = {q_val:.4g} {out_unit}")
                with st.expander("Vis trin"):
                    for s in steps:
                        st.markdown(s)
            except Exception as e:
                st.error(str(e))
        _quick_links([
            ("Enthalpi (ΔH°)", "thermochemistry", None),
            ("Gibbs (ΔG)", "thermochemistry", None),
        ], ctx="thermo_cal")

    with tab_heating:
        st.markdown("#### Opvarmningskurve (vand)")
        mass_g = st.number_input("Mass (g)", value=10.0, min_value=0.0, key="hc_mass")
        T_i = st.number_input("T_initial (°C)", value=-10.0, key="hc_ti")
        T_f = st.number_input("T_final (°C)", value=110.0, key="hc_tf")
        if st.button("Beregn opvarmningskurve", type="primary"):
            try:
                q_kJ, steps, meta = calculate_heating_curve_water_with_steps(mass_g, T_i, T_f)
                st.success(f"Total q = {q_kJ:.4g} kJ")
                with st.expander("Vis trin"):
                    for s in steps:
                        st.markdown(s)
            except Exception as e:
                st.error(str(e))

    with tab_enthalpy:
        enthalpy_tab1, enthalpy_tab2 = st.tabs([
            "ΔH° med dannelsesentalpier",
            "Hess Solver",
        ])

    with enthalpy_tab1:
        st.markdown("#### Reaktionsenthalpi (ΔH°)")
        st.markdown("Hess' lov: ΔH°_rxn = Σ(ν·ΔH_f° produkter) − Σ(ν·ΔH_f° reaktanter)")

        if "thermo_rxn_input" not in st.session_state:
            st.session_state["thermo_rxn_input"] = "N2(g) + 3 H2(g) -> 2 NH3(g)"
        if "thermo_rxn_input_pending" not in st.session_state:
            st.session_state["thermo_rxn_input_pending"] = None
        if "thermo_dhf_add_pending" not in st.session_state:
            st.session_state["thermo_dhf_add_pending"] = None

        # Apply pending input update before creating text_input widget
        pending_rxn = st.session_state.get("thermo_rxn_input_pending")
        if pending_rxn:
            st.session_state["thermo_rxn_input"] = pending_rxn
            st.session_state["thermo_rxn_input_pending"] = None

        rxn = st.text_input(
            "Reaktion (brug ->, => eller =)",
            key="thermo_rxn_input",
            help="Eksempel: N2(g) + 3 H2(g) -> 2 NH3(g)",
        )

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            do_balance = st.button("Balancer reaktion", key="thermo_balance_btn")
        with col_btn2:
            do_compute = st.button("Beregn ΔH°", type="primary", key="thermo_compute_btn")

        try:
            ast = parseReaction(rxn)
            st.caption(f"Parsed: {ast['equation_str']}")
            for warning in ast.get("warnings", []):
                st.warning(warning)

            if do_balance:
                try:
                    balanced_result = balanceReaction(ast)
                    st.session_state["thermo_rxn_input_pending"] = balanced_result["equation_str"]
                    st.success(f"Afstemt reaktion: {balanced_result['equation_str']}")
                    st.rerun()
                except Exception as balance_error:
                    st.error(f"Kunne ikke afstemme reaktionen: {balance_error}")

            db = load_dhf_database()
            species_items = []
            seen_species = set()
            for item in ast["reactants"] + ast["products"]:
                species_key = item["species_key"]
                if species_key not in seen_species:
                    seen_species.add(species_key)
                    species_items.append(
                        {
                            "species_key": species_key,
                            "lookup_raw": item.get("lookup_key_raw", species_key),
                        }
                    )

            override_rows = []
            default_overrides = st.session_state.get("thermo_dhf_overrides", {})
            for species_item in species_items:
                species_key = species_item["species_key"]
                lookup = getDhf(species_item["lookup_raw"], overrides={}, db=db)
                existing = default_overrides.get(species_key)
                override_rows.append(
                    {
                        "Species": species_key,
                        "In database": bool(lookup["found"] and lookup["source"] != "override"),
                        "Override ΔHf° (kJ/mol)": "" if existing is None else existing,
                    }
                )

            override_df = pd.DataFrame(override_rows)
            edited_overrides = st.data_editor(
                override_df,
                use_container_width=True,
                key="thermo_dhf_override_editor",
                disabled=["Species", "In database"],
                hide_index=True,
            )

            overrides = {}
            for _, row in edited_overrides.iterrows():
                raw_value = row["Override ΔHf° (kJ/mol)"]
                if raw_value == "" or pd.isna(raw_value):
                    continue
                try:
                    overrides[normalizeSpeciesKey(row["Species"])] = float(raw_value)
                except Exception:
                    st.error(f"Ugyldig override-værdi for {row['Species']}: {raw_value}")

            st.session_state["thermo_dhf_overrides"] = overrides

            balanced, imbalance = isReactionBalanced(ast)
            if not balanced:
                imbalance_text = ", ".join([f"{el}: {val:g}" for el, val in imbalance.items()])
                st.warning(f"Reaktionen er ikke afstemt. Beregner med de indtastede koefficienter. Ubalance: {imbalance_text}")

            details = computeRxnEnthalpy(ast, db, overrides)

            display_rows = []
            for row in details["rows"]:
                dhf_display = row["dhf_kj_per_mol"] if row["dhf_kj_per_mol"] is not None else "Missing ΔHf°"
                subtotal_display = row["subtotal_kj_per_mol"] if row["subtotal_kj_per_mol"] is not None else "—"
                display_rows.append(
                    {
                        "Side": "Produkt" if row["side"] == "product" else "Reaktant",
                        "Stof": row["species"],
                        "ν": row["coefficient"],
                        "ΔHf° (kJ/mol)": dhf_display,
                        "Kilde": row["source"],
                        "Subtotal ν·ΔHf° (kJ/mol)": subtotal_display,
                    }
                )

            st.dataframe(pd.DataFrame(display_rows), use_container_width=True, hide_index=True)

            if details["missing_species"]:
                st.error("Mangler ΔHf° for: " + ", ".join(details["missing_species"]))
                if do_compute:
                    st.error("Calculate ΔH° er blokeret indtil alle manglende ΔHf° er udfyldt via override eller database.")
            if details["delta_h_rxn_kj_per_mol"] is not None and not details["missing_species"]:
                st.info(f"Σ produkter = {details['sum_products_kj_per_mol']:.6g} kJ/mol")
                st.info(f"Σ reaktanter = {details['sum_reactants_kj_per_mol']:.6g} kJ/mol")
                if do_compute:
                    st.success(f"ΔH°_rxn = {details['delta_h_rxn_kj_per_mol']:.6g} kJ/mol reaktion")

            addable_species = [
                species_item["species_key"]
                for species_item in species_items
                if species_item["species_key"] in overrides
                and not getDhf(species_item["lookup_raw"], overrides={}, db=db)["found"]
            ]

            if addable_species:
                st.markdown("##### Add to database")
                species_to_add = st.multiselect(
                    "Vælg override-værdier der skal gemmes permanent",
                    options=addable_species,
                    key="thermo_dhf_add_species",
                )
                source_text = st.text_input(
                    "Kilde/kommentar",
                    value="User-added override",
                    key="thermo_dhf_add_source",
                )

                if st.button("Add to database", key="thermo_dhf_add_btn"):
                    if not species_to_add:
                        st.warning("Vælg mindst ét stof at gemme.")
                    else:
                        st.session_state["thermo_dhf_add_pending"] = {
                            "entries": {k: overrides[k] for k in species_to_add},
                            "source": source_text,
                        }

            pending = st.session_state.get("thermo_dhf_add_pending")
            if pending:
                st.warning("Bekræft gemning til data/dhf.json")
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    if st.button("Confirm save", type="primary", key="thermo_dhf_confirm_btn"):
                        add_to_dhf_database(pending["entries"], pending["source"])
                        st.session_state["thermo_dhf_add_pending"] = None
                        st.success("ΔHf°-værdier gemt i data/dhf.json")
                        st.rerun()
                with col_c2:
                    if st.button("Cancel", key="thermo_dhf_cancel_btn"):
                        st.session_state["thermo_dhf_add_pending"] = None
                        st.info("Gemning annulleret")

        except Exception as e:
            st.error(str(e))

    with enthalpy_tab2:
        st.markdown("#### Hess Solver")
        st.markdown("Find en linearkombination af kendte reaktioner, så summen matcher målereaktionen eksakt (Hess' lov).")

        target_rxn = st.text_input(
            "Target reaction",
            value="N2(g) + 3H2(g) -> 2NH3(g)",
            key="hess_target_rxn",
            help="Understøtter -> eller → samt koefficienter som 1/2 og ½.",
        )

        known_block = st.text_area(
            "Known reactions (one per line: reaction ; dH)",
            value=(
                "N2(g) + O2(g) -> 2 NO(g) ; 180.8\n"
                "H2(g) + 1/2 O2(g) -> H2O(g) ; -241.8\n"
                "4 NH3(g) + 5 O2(g) -> 4 NO(g) + 6 H2O(g) ; -904.0"
            ),
            height=180,
            key="hess_known_block",
        )

        if st.button("Solve", type="primary", key="hess_solve_btn"):
            try:
                result = solve_hess_problem(target_rxn, known_block)
                if not result.get("ok"):
                    st.error(result.get("error", "Kunne ikke løse Hess-problemet."))
                    if result.get("reason"):
                        st.info(result["reason"])
                    if result.get("inconsistent_species_rows"):
                        st.warning("Inkonsekvente species-rækker: " + ", ".join(result["inconsistent_species_rows"]))
                    diagnostics = result.get("diagnostics") or {}
                    missing_species = diagnostics.get("missing_target_species") or []
                    if missing_species:
                        st.warning("Species i target som ikke kan dannes af kendte reaktioner: " + ", ".join(missing_species))
                else:
                    st.markdown("##### Selected combination")
                    combo_rows = []
                    for entry in result["selected_combination"]:
                        combo_rows.append(
                            {
                                "Line": entry["input_index"],
                                "Factor": entry["factor_str"],
                                "Reversed": "Yes" if entry["is_reversed"] else "No",
                                "Reaction": entry["reaction"],
                                "ΔH° (kJ/mol)": entry["delta_h_str"],
                            }
                        )
                    if combo_rows:
                        st.dataframe(pd.DataFrame(combo_rows), use_container_width=True, hide_index=True)
                    else:
                        st.info("Ingen reaktioner blev brugt (alle faktorer = 0).")

                    scaled = result.get("scaled_integer_presentation", {})
                    scaled_factors = scaled.get("factors") or []
                    scaled_scale = scaled.get("scale", 1)
                    if scaled_factors:
                        st.caption(
                            "Skaleret heltalsvisning (samme løsning): "
                            + ", ".join(str(v) for v in scaled_factors)
                            + f"  (svarer til target ganget med {scaled_scale})"
                        )

                    st.markdown("##### Summed reaction")
                    st.code(result["summed_reaction"])
                    st.caption(f"Target: {result['target']['equation']}")

                    st.markdown("##### ΔH° calculation")
                    if result["delta_h_terms"]:
                        expression = " ".join(result["delta_h_terms"])
                    else:
                        expression = "0"
                    if expression.startswith("+"):
                        expression = expression[2:]
                    st.write(f"{expression} = {result['delta_h_total_str']} kJ/mol")
                    st.success(f"ΔH°target = {result['delta_h_total_float']:.6g} kJ/mol")

                    st.markdown("##### Validation")
                    validation = result.get("validation", {})
                    if validation.get("residual_zero") and validation.get("matches_target_exactly"):
                        st.success("OK: A·x = b eksakt. Summen matcher target præcist.")
                    else:
                        st.error("Fejl: residual er ikke nul eller summen matcher ikke target.")
                        st.json(validation)

            except Exception as e:
                st.error(str(e))

    with tab_vanthoff:
        _show_vanthoff_tab()

    with tab_kirchhoff:
        _show_kirchhoff_tab()

    with tab_bornhaber:
        _show_born_haber_tab()


def _show_vanthoff_tab():
    """Van't Hoff-plot: ΔH° og ΔS° fra ligevægtskonstanter ved forskellige temperaturer."""
    import math

    R = 8.314  # J/(mol·K)

    st.markdown("### 📈 Van't Hoff-plot")
    st.latex(r"\ln K = -\frac{\Delta H°}{R} \cdot \frac{1}{T} + \frac{\Delta S°}{R}")
    st.markdown(
        "Bruges til at bestemme **ΔH°** og **ΔS°** fra ligevægtskonstanter målt ved forskellige temperaturer. "
        "Hældningen i et lnK vs. 1/T-plot er −ΔH°/R, og skæringspunktet er ΔS°/R."
    )

    mode = st.radio(
        "Beregningsmode:",
        ["To-punkts (2 K-værdier)", "Find K ved ny temperatur"],
        horizontal=True, key="vh_mode",
    )

    if mode == "To-punkts (2 K-værdier)":
        st.markdown("#### To-punkts Van't Hoff")
        st.caption(
            "Givet K₁ ved T₁ og K₂ ved T₂ – beregner ΔH° fra hældning og ΔS° fra skæringspunkt."
        )
        col1, col2 = st.columns(2)
        with col1:
            T1 = st.number_input("T₁ (K):", value=298.15, min_value=1.0, key="vh_T1")
            K1 = st.number_input("K₁:", value=1.0e-5, min_value=1e-30, format="%.3e", key="vh_K1")
        with col2:
            T2 = st.number_input("T₂ (K):", value=373.15, min_value=1.0, key="vh_T2")
            K2 = st.number_input("K₂:", value=1.0e-3, min_value=1e-30, format="%.3e", key="vh_K2")

        temp_unit = st.radio("Temperaturenhed (input):", ["K", "°C"], horizontal=True, key="vh_tunit")
        if temp_unit == "°C":
            T1 += 273.15
            T2 += 273.15

        if st.button("Beregn ΔH° og ΔS°", type="primary", key="vh_btn"):
            try:
                if abs(T1 - T2) < 0.01:
                    st.error("T₁ og T₂ må ikke være identiske.")
                else:
                    lnK1 = math.log(K1)
                    lnK2 = math.log(K2)
                    inv_T1 = 1.0 / T1
                    inv_T2 = 1.0 / T2

                    # slope = -ΔH°/R = Δ(lnK) / Δ(1/T)
                    slope = (lnK2 - lnK1) / (inv_T2 - inv_T1)
                    dH_J = -slope * R
                    dH_kJ = dH_J / 1000

                    # intercept = ΔS°/R → ΔS° = R × (lnK - slope/T)
                    dS_J = R * (lnK1 - slope * inv_T1)

                    # ΔG° at T1 and T2
                    dG1 = -R * T1 * lnK1 / 1000
                    dG2 = -R * T2 * lnK2 / 1000

                    st.success(f"**ΔH° = {dH_kJ:.2f} kJ/mol**  |  **ΔS° = {dS_J:.2f} J/(mol·K)**")

                    st.markdown(f"""
**Trin-for-trin:**

1. lnK₁ = ln({K1:.3e}) = **{lnK1:.4f}**
2. lnK₂ = ln({K2:.3e}) = **{lnK2:.4f}**
3. Hældning = Δ(lnK) / Δ(1/T) = ({lnK2:.4f} − {lnK1:.4f}) / (1/{T2:.2f} − 1/{T1:.2f})
   = {lnK2-lnK1:.4f} / {inv_T2-inv_T1:.6f} = **{slope:.2f} K**
4. ΔH° = −hældning × R = −{slope:.2f} × 8.314 = **{dH_J:.0f} J/mol = {dH_kJ:.2f} kJ/mol**
5. ΔS° = R × (lnK₁ − hældning × 1/T₁) = 8.314 × ({lnK1:.4f} − {slope:.2f} × {inv_T1:.6f})
   = **{dS_J:.2f} J/(mol·K)**
6. Kontrol – ΔG°(T₁) = −RT₁lnK₁ = **{dG1:.2f} kJ/mol**
7. Kontrol – ΔG°(T₂) = −RT₂lnK₂ = **{dG2:.2f} kJ/mol**
""")

                    exo_endo = "eksoterm (ΔH° < 0)" if dH_kJ < 0 else "endoterm (ΔH° > 0)"
                    k_temp = "K falder med stigende T" if dH_kJ < 0 else "K stiger med stigende T"
                    st.info(f"📌 Reaktionen er **{exo_endo}** → {k_temp} (Le Chatelier)")

            except Exception as exc:
                st.error(f"Fejl: {exc}")

    else:  # Find K ved ny temperatur
        st.markdown("#### Find K ved ny temperatur")
        st.caption(
            "Givet ΔH° og én K-måling – beregn K ved en anden temperatur. "
            "Eller: givet ΔH° og ΔS° – beregn K ved vilkårlig T."
        )
        method = st.radio(
            "Input:", ["ΔH° + én K-måling", "ΔH° og ΔS°"], horizontal=True, key="vh_pred_method"
        )
        col1, col2 = st.columns(2)
        with col1:
            dH_input = st.number_input("ΔH° (kJ/mol):", value=-92.0, key="vh_pred_dH")
            T_new = st.number_input("Ny temperatur T (K):", value=500.0, min_value=1.0, key="vh_pred_Tnew")
        with col2:
            if method == "ΔH° + én K-måling":
                T_ref = st.number_input("Referencetemperatur T₁ (K):", value=298.15, min_value=1.0, key="vh_pred_Tref")
                K_ref = st.number_input("K₁ ved T₁:", value=977.0, min_value=1e-30, format="%.4e", key="vh_pred_K1")
            else:
                dS_input = st.number_input("ΔS° (J/(mol·K)):", value=-198.0, key="vh_pred_dS")

        if st.button("Find K(T)", type="primary", key="vh_pred_btn"):
            try:
                dH_J = dH_input * 1000
                if method == "ΔH° + én K-måling":
                    lnK_new = math.log(K_ref) + (-dH_J / R) * (1.0 / T_new - 1.0 / T_ref)
                else:
                    lnK_new = (-dH_J / (R * T_new)) + dS_input / R

                K_new = math.exp(lnK_new)
                dG_new = -R * T_new * lnK_new / 1000

                st.success(f"**K({T_new:.1f} K) = {K_new:.4e}**  |  ΔG° = {dG_new:.2f} kJ/mol")
                if method == "ΔH° + én K-måling":
                    st.markdown(f"""
**Beregning:**

ln(K₂/K₁) = −ΔH°/R × (1/T₂ − 1/T₁)

lnK₂ = lnK₁ + (−ΔH°/R) × (1/T₂ − 1/T₁)
= {math.log(K_ref):.4f} + ({-dH_J/R:.2f}) × ({1/T_new:.6f} − {1/T_ref:.6f})
= {math.log(K_ref):.4f} + {(-dH_J/R)*(1/T_new - 1/T_ref):.4f}
= **{lnK_new:.4f}**

K₂ = e^{lnK_new:.4f} = **{K_new:.4e}**
""")
            except Exception as exc:
                st.error(f"Fejl: {exc}")

    _quick_links([
        ("Gibbs (ΔG)", "thermochemistry", None),
        ("Ligevægt / ICE", "ligevaegt", "🧊 ICE Table"),
        ("Kc/Kp", "ligevaegt", "🔄 Kc/Kp konvertering"),
    ], ctx="vanthoff")


def _show_kirchhoff_tab():
    """Kirchhoffs lov: ΔH°(T₂) = ΔH°(T₁) + ΔCp × (T₂ − T₁)."""
    st.markdown("### 🌡️ Kirchhoffs lov")
    st.latex(r"\Delta H°(T_2) = \Delta H°(T_1) + \Delta C_p \cdot (T_2 - T_1)")
    st.markdown(
        "Bruges til at korrigere reaktionsentalpien til en anden temperatur end standardbetingelserne (298 K). "
        "Gyldigt når ΔCp er konstant over det givne temperaturinterval."
    )
    st.info(
        "**ΔCp** = Σ(νᵢ × Cp,i produkter) − Σ(νᵢ × Cp,i reaktanter)  \n"
        "Typiske Cp-værdier: H₂(g)≈28,8 J/mol·K, O₂(g)≈29,4, N₂(g)≈29,1, "
        "H₂O(g)≈33,6, CO₂(g)≈37,1, NH₃(g)≈35,1"
    )

    mode = st.radio(
        "Input-mode:",
        ["Direkte ΔCp", "Beregn ΔCp fra Cp for hvert stof"],
        horizontal=True, key="kh_mode",
    )

    col1, col2 = st.columns(2)
    with col1:
        dH_ref = st.number_input("ΔH°(T₁) (kJ/mol):", value=-92.38, key="kh_dH_ref")
        T1 = st.number_input("T₁ (K):", value=298.15, min_value=1.0, key="kh_T1")
        T2 = st.number_input("T₂ (K):", value=500.0, min_value=1.0, key="kh_T2")

    with col2:
        if mode == "Direkte ΔCp":
            dCp = st.number_input(
                "ΔCp (J/(mol·K)):", value=-58.6, format="%.2f", key="kh_dCp",
                help="Positiv: produkter har højere Cp. Negativ: reaktanter har højere Cp."
            )
        else:
            st.markdown("**Cp-tabel (J/(mol·K))**")
            n_prod = st.number_input("Antal produkter:", min_value=1, max_value=6, value=2, step=1, key="kh_np")
            n_react = st.number_input("Antal reaktanter:", min_value=1, max_value=6, value=2, step=1, key="kh_nr")

            products = []
            for i in range(int(n_prod)):
                c1, c2, c3 = st.columns(3)
                with c1:
                    name = st.text_input(f"Produkt {i+1}:", key=f"kh_pname_{i}", placeholder="NH₃(g)")
                with c2:
                    nu = st.number_input("ν:", value=1.0, min_value=0.0, key=f"kh_pnu_{i}")
                with c3:
                    cp = st.number_input("Cp:", value=35.1, key=f"kh_pcp_{i}")
                products.append((nu, cp))

            reactants = []
            for i in range(int(n_react)):
                c1, c2, c3 = st.columns(3)
                with c1:
                    name = st.text_input(f"Reaktant {i+1}:", key=f"kh_rname_{i}", placeholder="N₂(g)")
                with c2:
                    nu = st.number_input("ν:", value=1.0, min_value=0.0, key=f"kh_rnu_{i}")
                with c3:
                    cp = st.number_input("Cp:", value=29.1, key=f"kh_rcp_{i}")
                reactants.append((nu, cp))

            dCp = sum(nu * cp for nu, cp in products) - sum(nu * cp for nu, cp in reactants)
            st.metric("Beregnet ΔCp (J/(mol·K)):", f"{dCp:.2f}")

    if st.button("Beregn ΔH°(T₂)", type="primary", key="kh_btn"):
        dT = T2 - T1
        correction_kJ = dCp * dT / 1000  # convert J → kJ
        dH_T2 = dH_ref + correction_kJ

        st.success(f"**ΔH°({T2:.1f} K) = {dH_T2:.4f} kJ/mol**")
        st.markdown(f"""
**Trin-for-trin:**

1. ΔH°({T1:.1f} K) = **{dH_ref:.4f} kJ/mol** (standard)
2. ΔCp = **{dCp:.2f} J/(mol·K)**
3. ΔT = T₂ − T₁ = {T2:.1f} − {T1:.1f} = **{dT:.1f} K**
4. Korrektionsled: ΔCp × ΔT = {dCp:.2f} × {dT:.1f} = **{dCp*dT:.2f} J/mol = {correction_kJ:.4f} kJ/mol**
5. ΔH°({T2:.1f} K) = {dH_ref:.4f} + {correction_kJ:.4f} = **{dH_T2:.4f} kJ/mol**
""")

        change_pct = abs(correction_kJ / dH_ref * 100) if dH_ref != 0 else 0
        if change_pct < 5:
            st.info(f"✅ Korrektionen er kun {change_pct:.1f}% – Kirchhoff-korrektionen er lille ved dette interval.")
        else:
            st.warning(f"⚠️ Korrektionen er {change_pct:.1f}% – temperaturkorrektionen er signifikant.")

    st.markdown("---")
    st.caption(
        "💡 Eksempel (N₂ + 3H₂ → 2NH₃): ΔCp = 2×35,1 − (29,1 + 3×28,8) = 70,2 − 115,5 = −45,3 J/mol·K  \n"
        "ΔH°(500K) = −92,38 + (−45,3 × 202)/1000 = −92,38 − 9,15 = −101,5 kJ/mol"
    )

    _quick_links([
        ("Enthalpi ΔH°", "thermochemistry", None),
        ("Gibbs (ΔG)", "thermochemistry", None),
        ("📈 Van't Hoff-plot", "thermochemistry", None),
    ], ctx="kirchhoff")


def _show_born_haber_tab():
    """Born-Haber cyklus – gitterenthalpi for ioniske forbindelser."""
    st.markdown("### 🔷 Born-Haber cyklus – Gitterenthalpi")
    st.markdown(
        "Born-Haber cyklussen anvender **Hess' lov** til at beregne gitterentalpien (ΔH_latt) "
        "for ioniske salte, som ikke kan måles direkte. Alle trin summerer til ΔH_f° for saltet."
    )
    st.latex(
        r"\Delta H_f° = \Delta H_{sub} + \Delta H_{ion} + \frac{1}{2}\Delta H_{diss} + \Delta H_{ea} + \Delta H_{latt}"
    )
    st.info(
        "**Trin i Born-Haber cyklussen (eksempel NaCl):**\n"
        "1. **Sublimation** af metallet: Na(s) → Na(g)  \n"
        "2. **Ionisering** af metalatom: Na(g) → Na⁺(g) + e⁻  \n"
        "3. **Dissociation** af halvmolekyle: ½Cl₂(g) → Cl(g)  \n"
        "4. **Elektronaffinitet** for ikke-metallet: Cl(g) + e⁻ → Cl⁻(g)  \n"
        "5. **Gitterenthalpi**: Na⁺(g) + Cl⁻(g) → NaCl(s)  \n"
        "→ ΔH_latt = ΔH_f° − (ΔH_sub + ΔH_ion + ½ΔH_diss + ΔH_ea)"
    )

    salt_type = st.radio(
        "Forbindelsestype:",
        ["MX (fx NaCl, KF, LiI)", "MX₂ (fx CaCl₂, MgO)", "Tilpasset"],
        horizontal=True, key="bh_salt_type",
    )

    if salt_type == "MX (fx NaCl, KF, LiI)":
        diss_factor = 0.5
        ion_factor = 1
        ea_factor = 1
    elif salt_type == "MX₂ (fx CaCl₂, MgO)":
        diss_factor = 1.0
        ion_factor = 2
        ea_factor = 2
        st.info("For MX₂: inkludér 1. og 2. ioniseringsenergi i ΔH_ion (sum), og 2 × ΔH_ea")
    else:
        diss_factor = st.number_input("Faktor for dissociation (fx 0,5 for ½X₂):", value=0.5, step=0.5, min_value=0.0, key="bh_diss_fac")
        ion_factor = 1
        ea_factor = 1

    col1, col2 = st.columns(2)
    with col1:
        dH_f = st.number_input("ΔH_f° (dannelsesenthalpi, kJ/mol):", value=-411.2, step=1.0, key="bh_dhf",
                                help="Standard dannelsesenthalpi for saltet (negativ for stabile salte)")
        dH_sub = st.number_input("ΔH_sub (sublimationsenthalpi, kJ/mol):", value=107.3, step=1.0, key="bh_sub",
                                  help="Sublimation af fast metal til gasatom: M(s) → M(g), altid positiv")
        dH_ion = st.number_input(
            f"ΔH_ion (ioniseringsenergi, kJ/mol):", value=495.8, step=1.0, key="bh_ion",
            help="Sum af ioniseringsenergier (1. og 2. IE for M²⁺)")
    with col2:
        dH_diss = st.number_input("ΔH_diss (dissociationsenthalpi, kJ/mol for X₂):", value=242.0, step=1.0, key="bh_diss",
                                   help="X₂(g) → 2X(g). Bruges med faktor (½ for NaCl, 1 for CaCl₂)")
        dH_ea = st.number_input(
            f"ΔH_ea (elektronaffinitet, kJ/mol):", value=-349.0, step=1.0, key="bh_ea",
            help="Negativ for de fleste halogener (energi frigives). For O²⁻: 2. EA er positiv!")
        unknown = st.radio("Hvad skal beregnes?", ["ΔH_latt (gitterenthalpi)", "ΔH_f° (dannelse)"], key="bh_unknown")

    if st.button("Beregn", type="primary", key="bh_calc"):
        contrib_sub = dH_sub
        contrib_ion = dH_ion * ion_factor
        contrib_diss = dH_diss * diss_factor
        contrib_ea = dH_ea * ea_factor
        sum_others = contrib_sub + contrib_ion + contrib_diss + contrib_ea

        if unknown == "ΔH_latt (gitterenthalpi)":
            result = dH_f - sum_others
            st.success(f"✅ **ΔH_latt = {result:.1f} kJ/mol**")
            result_label = "ΔH_latt"
        else:
            result = sum_others + st.session_state.get("bh_latt_override", -788.0)
            result_label = "ΔH_f°"
            st.warning("Vælg 'ΔH_latt' for den normale beregning; her estimeres ΔH_f° fra alle led + antaget gitterenthalpi.")

        if unknown == "ΔH_latt (gitterenthalpi)":
            with st.expander("🔍 Trin-for-trin", expanded=True):
                st.markdown(f"""
**Hess' lov:** ΔH_latt = ΔH_f° − (ΔH_sub + ΔH_ion + {diss_factor}·ΔH_diss + ΔH_ea)

| Trin | Enthalpi |
|------|---------|
| ΔH_f° (dannelsesenthalpi) | **{dH_f:+.1f} kJ/mol** |
| − ΔH_sub | −{contrib_sub:+.1f} kJ/mol |
| − ΔH_ion (×{ion_factor}) | −{contrib_ion:+.1f} kJ/mol |
| − {diss_factor}·ΔH_diss | −{contrib_diss:+.1f} kJ/mol |
| − ΔH_ea (×{ea_factor}) | −{contrib_ea:+.1f} kJ/mol |
| **= ΔH_latt** | **{result:+.1f} kJ/mol** |

ΔH_latt er typisk **stærkt negativ** (energi frigives ved gitterdannelse).
{"✅ Rimelig gitterenthalpi for et 1:1 salt." if result < -300 else "⚠️ Tjek fortegn på ΔH_ea – EA for halogener er negativ."}
""")

    st.markdown("---")
    st.markdown("**Referencetabel – typiske Born-Haber-værdier:**")
    bh_ref = {
        "Salt": ["NaCl", "KCl", "MgO", "CaF₂", "LiF"],
        "ΔH_f° (kJ/mol)": [-411, -437, -602, -1228, -616],
        "ΔH_latt (kJ/mol)": [-788, -717, -3791, -2630, -1037],
    }
    import pandas as pd
    st.dataframe(pd.DataFrame(bh_ref), hide_index=True, use_container_width=True)

    _quick_links([
        ("Enthalpi ΔH°", "thermochemistry", None),
        ("Gibbs (ΔG)", "thermochemistry", None),
        ("🌡️ Kirchhoffs lov", "thermochemistry", None),
    ], ctx="bornhaber")


def show_colligatives_page():
    """Display Colligative Properties calculators (Part 4)."""
    st.title("🧪 Colligative Properties")
    st.markdown("---")

    from calculators.colligatives import (
        freezing_boiling_with_steps,
        osmotic_pressure_with_steps,
        raoult_nonvolatile_with_steps,
        raoult_binary_with_steps,
    )

    tab1, tab2, tab3, tab4 = st.tabs([
        "ΔTf / ΔTb",
        "Osmotic Pressure",
        "Raoult's Law",
        "🔬 M fra kolligative egenskaber",
    ])

    with tab1:
        st.markdown("#### Freezing depression / Boiling elevation")
        i = st.number_input("van't Hoff factor i", value=1.0, min_value=0.0)
        mode = st.radio("Solute input", ["moles", "mass + molar mass"], horizontal=True)
        if mode == "moles":
            moles = st.number_input("Moles solute (mol)", value=1.0, min_value=0.0)
            mass = None
            mm = None
        else:
            mass = st.number_input("Mass solute (g)", value=58.44, min_value=0.0)
            mm = st.number_input("Molar mass (g/mol)", value=58.44, min_value=0.0)
            moles = None
        mass_solvent = st.number_input("Mass solvent (g)", value=1000.0, min_value=0.0)
        if st.button("Calculate ΔT", type="primary"):
            try:
                res, steps, meta = freezing_boiling_with_steps(
                    solvent="water",
                    moles_solute=moles,
                    mass_solute_g=mass,
                    molar_mass_solute_g_per_mol=mm,
                    mass_solvent_g=mass_solvent,
                    i=i,
                )
                st.success(f"ΔTf = {res['deltaTf_C']:.4g} °C, Tf = {res['Tf_C']:.4g} °C")
                st.success(f"ΔTb = {res['deltaTb_C']:.4g} °C, Tb = {res['Tb_C']:.4g} °C")
                with st.expander("Vis trin"):
                    for s in steps:
                        st.markdown(s)
            except Exception as e:
                st.error(str(e))

    with tab2:
        st.markdown("#### Osmotic Pressure")
        mode = st.radio("Concentration input", ["Molarity", "moles + volume"], horizontal=True, key="osm_mode")
        if mode == "Molarity":
            M = st.number_input("Molarity (M)", value=0.100, min_value=0.0, key="osm_M")
            moles = None
            vol = None
        else:
            moles = st.number_input("Moles solute (mol)", value=0.010, min_value=0.0, key="osm_mol")
            vol = st.number_input("Solution volume (L)", value=0.100, min_value=0.0, key="osm_vol")
            M = None
        T = st.number_input("Temperature (K)", value=298.15)
        i = st.number_input("van't Hoff i", value=1.0, min_value=0.0, key="osm_i")
        if st.button("Calculate π", type="primary"):
            try:
                pi_atm, steps, meta = osmotic_pressure_with_steps(M, moles, vol, T, i)
                st.success(f"π = {pi_atm:.4g} atm")
                with st.expander("Vis trin"):
                    for s in steps:
                        st.markdown(s)
            except Exception as e:
                st.error(str(e))

    with tab3:
        st.markdown("#### Raoult's Law")
        mode = st.radio("Case", ["Nonvolatile solute", "Volatile binary"], horizontal=True, key="ra_mode")
        if mode == "Nonvolatile solute":
            x_s = st.number_input("x_solvent", value=0.900, min_value=0.0, max_value=1.0)
            P_star = st.number_input("P*_solvent (kPa)", value=100.0, min_value=0.0)
            if st.button("Calculate P_solution", type="primary"):
                try:
                    P, steps, meta = raoult_nonvolatile_with_steps(x_s, P_star)
                    st.success(f"P_solution = {P:.4g} kPa")
                    with st.expander("Vis trin"):
                        for s in steps:
                            st.markdown(s)
                except Exception as e:
                    st.error(str(e))
        else:
            x_A = st.number_input("x_A", value=0.500, min_value=0.0, max_value=1.0)
            P_A = st.number_input("P*_A (kPa)", value=80.0, min_value=0.0)
            x_B = 1.0 - x_A
            st.info(f"x_B auto = {x_B:.4f}")
            P_B = st.number_input("P*_B (kPa)", value=60.0, min_value=0.0)
            if st.button("Calculate P_total", type="primary"):
                try:
                    from calculators.colligatives import raoult_binary_with_steps
                    res, steps, meta = raoult_binary_with_steps(x_A, P_A, x_B, P_B)
                    st.success(f"P_total = {res['P_total']:.4g} kPa")
                    st.info(f"P_A = {res['P_A']:.4g} kPa, P_B = {res['P_B']:.4g} kPa")
                    with st.expander("Vis trin"):
                        for s in steps:
                            st.markdown(s)
                except Exception as e:
                    st.error(str(e))

    with tab4:
        _show_molar_mass_from_colligatives()


def _show_molar_mass_from_colligatives():
    """Baglæns kolligative egenskaber: find molarmasse af opløst stof."""
    import math

    R = 0.08206   # L·atm/(mol·K)
    Kf_water = 1.86   # °C·kg/mol
    Kb_water = 0.512  # °C·kg/mol

    st.markdown("### 🔬 Find molarmasse fra kolligative egenskaber")
    st.markdown(
        "Givet et eksperimentelt målt ΔTf, ΔTb eller osmotisk tryk – find molarmassen af det opløste stof. "
        "Klassisk DTU-opgave ved karakterisering af ukendte forbindelser."
    )

    method = st.radio(
        "Metode:",
        ["ΔTf – frysepunktssænkning", "ΔTb – kogepunktselevering", "π – osmotisk tryk"],
        horizontal=True, key="mcol_method",
    )

    col1, col2 = st.columns(2)
    with col1:
        mass_solute = st.number_input("Masse af opløst stof (g):", value=5.0, min_value=0.0,
                                       format="%.4f", key="mcol_mass")
        i = st.number_input("Van't Hoff faktor i:", value=1.0, min_value=0.1,
                             help="i=1 for ikke-elektrolytter. NaCl→i≈2, CaCl₂→i≈3",
                             key="mcol_i")

    with col2:
        if method in ["ΔTf – frysepunktssænkning", "ΔTb – kogepunktselevering"]:
            dT_obs = st.number_input(
                "Målt |ΔT| (°C):", value=0.372, min_value=0.0, format="%.4f", key="mcol_dT",
                help="Angiv den observerede temperaturændring som positivt tal."
            )
            mass_solvent = st.number_input("Masse af opløsningsmiddel (g):", value=100.0,
                                            min_value=0.1, key="mcol_msolvent")
            custom_K = st.checkbox("Brug andet opløsningsmiddel (andet Kf/Kb)", key="mcol_custom_K")
            if custom_K:
                Kf_use = st.number_input("Kf eller Kb (°C·kg/mol):", value=Kf_water, key="mcol_Kuse")
            else:
                Kf_use = Kf_water if "ΔTf" in method else Kb_water
                label = "Kf(vand) = 1,86 °C·kg/mol" if "ΔTf" in method else "Kb(vand) = 0,512 °C·kg/mol"
                st.info(f"Bruger: {label}")
        else:  # osmotisk tryk
            pi_atm = st.number_input("Osmotisk tryk π (atm):", value=2.47, min_value=0.0,
                                      format="%.4f", key="mcol_pi")
            V_L = st.number_input("Opløsningsvolumen V (L):", value=0.100, min_value=0.001,
                                   key="mcol_V")
            T_K = st.number_input("Temperatur T (K):", value=298.15, min_value=1.0, key="mcol_T")

    if st.button("Beregn molarmasse", type="primary", key="mcol_btn"):
        try:
            if method in ["ΔTf – frysepunktssænkning", "ΔTb – kogepunktselevering"]:
                # ΔT = i × K × m,  m = molalitet = mol/kg_solvent
                # mol = m × kg_solvent = ΔT × kg_solvent / (i × K)
                # M = mass_solute / mol
                kg_solvent = mass_solvent / 1000.0
                mol_solute = dT_obs * kg_solvent / (i * Kf_use)
                M_calc = mass_solute / mol_solute
                m_calc = mol_solute / kg_solvent

                K_label = "Kf" if "ΔTf" in method else "Kb"
                prop_label = "frysepunktssænkning" if "ΔTf" in method else "kogepunktselevering"

                st.success(f"**M ≈ {M_calc:.2f} g/mol**")
                st.markdown(f"""
**Trin-for-trin ({prop_label}):**

Formel: ΔT = i × {K_label} × m  →  m = ΔT / (i × {K_label})

1. Molalitet: m = {dT_obs:.4f} / ({i:.1f} × {Kf_use:.3f}) = **{m_calc:.4f} mol/kg**
2. Mol opløst stof: n = m × kg_solvent = {m_calc:.4f} × {kg_solvent:.4f} = **{mol_solute:.6f} mol**
3. Molarmasse: M = masse / n = {mass_solute:.4f} g / {mol_solute:.6f} mol = **{M_calc:.2f} g/mol**
""")

            else:  # osmotisk tryk
                # π = i × (n/V) × R × T  →  n = π×V / (i×R×T)
                # M = mass / n
                n_solute = (pi_atm * V_L) / (i * R * T_K)
                M_calc = mass_solute / n_solute
                c_calc = n_solute / V_L

                st.success(f"**M ≈ {M_calc:.2f} g/mol**")
                st.markdown(f"""
**Trin-for-trin (osmotisk tryk):**

Formel: π = i × c × R × T  →  c = π / (i × R × T)

1. Koncentration: c = {pi_atm:.4f} / ({i:.1f} × 0,08206 × {T_K:.2f}) = **{c_calc:.6f} mol/L**
2. Mol: n = c × V = {c_calc:.6f} × {V_L:.4f} = **{n_solute:.6f} mol**
3. Molarmasse: M = {mass_solute:.4f} / {n_solute:.6f} = **{M_calc:.2f} g/mol**
""")
                st.caption("💡 Osmotisk tryk giver ofte den mest præcise molarmasse ved høj M (biopolymerer, proteiner).")

        except Exception as exc:
            st.error(f"Fejl: {exc}")

    st.markdown("---")
    ex_col1, ex_col2 = st.columns(2)
    with ex_col1:
        st.caption("**Eksempel (ΔTf):** 5,00 g ukendt stof i 100 g benzol (Kf=5,12). ΔTf = 0,740°C → M = 5,12×0,1/0,740 / 0,100 = 346 g/mol")
    with ex_col2:
        st.caption("**Eksempel (osmose):** 1,00 g protein i 100 mL vand giver π = 2,73 mmHg ved 25°C → c = 2,73/760/(0,08206×298) = 1,47×10⁻⁴ M → M = 1,00/0,0147 = 68.000 g/mol")

    _quick_links([
        ("Kogepunkt/frysepunkt", "koge-fryse", None),
        ("Osmotisk tryk", "koge-fryse", None),
        ("⚖️ Molarmasse", "atoms-molar", "⚖️ Molar Mass"),
    ])


# ---------------------------------------------------------------------------
# MOLEKYLE DATABASE PAGE
# ---------------------------------------------------------------------------

_CATEGORY_ICONS = {
    "syre": "🧪",
    "base": "⚗️",
    "salt": "🧂",
    "ion": "⚡",
    "molekyle": "🔬",
    "oxid": "💨",
    "organisk": "🌿",
    "andet": "❓",
}

_CATEGORY_LABELS_DA = {
    "syre": "Syre",
    "base": "Base",
    "salt": "Salt",
    "ion": "Ion",
    "molekyle": "Molekyle",
    "oxid": "Oxid",
    "organisk": "Organisk",
    "andet": "Andet",
}

_FILTER_OPTIONS = ["Alle"] + [
    "Syre", "Base", "Salt", "Ion", "Molekyle", "Oxid", "Organisk"
]

_FILTER_TO_CATEGORY = {
    "Alle": None,
    "Syre": "syre",
    "Base": "base",
    "Salt": "salt",
    "Ion": "ion",
    "Molekyle": "molekyle",
    "Oxid": "oxid",
    "Organisk": "organisk",
}


@st.cache_data(ttl=24 * 60 * 60, show_spinner=False)
def _resolve_structure_image(name_da: str, name_en: str, formula: str) -> dict:
    """Resolve a structure image URL from web sources (Wikipedia -> PubChem)."""
    wikipedia_api = "https://en.wikipedia.org/w/api.php"
    wikipedia_summary = "https://en.wikipedia.org/api/rest_v1/page/summary/"

    search_terms = []
    if name_en:
        search_terms.append(name_en)
        search_terms.append(f"{name_en} molecule")
    if name_da:
        search_terms.append(name_da)
    search_terms.append(formula)

    for term in search_terms:
        try:
            search_resp = requests.get(
                wikipedia_api,
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": f"{term} chemistry",
                    "format": "json",
                    "utf8": 1,
                    "srlimit": 1,
                },
                timeout=5,
            )
            search_resp.raise_for_status()
            data = search_resp.json()
            hits = data.get("query", {}).get("search", [])
            if not hits:
                continue

            title = hits[0].get("title")
            if not title:
                continue

            summary_resp = requests.get(
                wikipedia_summary + quote(title),
                timeout=5,
            )
            summary_resp.raise_for_status()
            summary_data = summary_resp.json()
            thumb_url = summary_data.get("thumbnail", {}).get("source")
            page_url = summary_data.get("content_urls", {}).get("desktop", {}).get("page")

            if thumb_url:
                return {
                    "url": thumb_url,
                    "caption": f"Strukturillustration fra Wikipedia: {title}",
                    "source": page_url or "https://en.wikipedia.org",
                }
        except Exception:
            continue

    for term in search_terms:
        try:
            pubchem_url = (
                "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/"
                f"{quote(term)}/PNG?image_size=large"
            )
            resp = requests.get(pubchem_url, timeout=5)
            if resp.status_code == 200 and resp.headers.get("Content-Type", "").startswith("image/"):
                return {
                    "url": pubchem_url,
                    "caption": f"2D-struktur fra PubChem: {term}",
                    "source": "https://pubchem.ncbi.nlm.nih.gov",
                }
        except Exception:
            continue

    return {"url": "", "caption": "", "source": ""}


def _render_substance_card(s: Substance) -> None:
    """Render a detailed substance card in Streamlit."""
    def _fmt_constant(value: float) -> str:
        return f"{value:.2e}"

    icon = _CATEGORY_ICONS.get(s.category, "❓")
    cat_label = _CATEGORY_LABELS_DA.get(s.category, s.category.capitalize())

    st.markdown(f"## {icon} {s.name_da}  `{s.formula}`")
    if s.name_en:
        st.caption(f"Engelsk navn: {s.name_en}")

    # ── Grunddata ──────────────────────────────────────────────────────────
    with st.expander("📋 Grunddata", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Navn (DK):** {s.name_da}")
            st.markdown(f"**Formel:** `{s.formula}`")
            st.markdown(f"**Kategori:** {cat_label}")
            if s.subtype:
                st.markdown(f"**Underkategori:** {s.subtype}")
            if s.molar_mass is not None:
                st.markdown(f"**Molarmasse:** {s.molar_mass:.3g} g/mol")
        with col2:
            if s.physical_state:
                st.markdown(f"**Fysisk tilstand (25 °C):** {s.physical_state.capitalize()}")
            if s.polarity:
                st.markdown(f"**Polaritet:** {s.polarity.capitalize()}")
            if s.ion_charge is not None:
                charge_str = f"+{s.ion_charge}" if s.ion_charge > 0 else str(s.ion_charge)
                st.markdown(f"**Ionladning:** {charge_str}")
            if s.solubility_note:
                st.markdown(f"**Opløselighed:** {s.solubility_note}")
        st.markdown(f"**Beskrivelse:** {s.description}")

    # ── Klassifikation ─────────────────────────────────────────────────────
    classification_lines = []
    if s.acid_base_role:
        role_label = {"syre": "Syre", "base": "Base", "amfoter": "Amfoter", "neutral": "Neutral"}.get(
            s.acid_base_role, s.acid_base_role
        )
        classification_lines.append(f"**Syre/base-funktion:** {role_label}")
    if s.acid_strength:
        classification_lines.append(f"**Syrestyrke:** {s.acid_strength.capitalize()} syre")
    if s.base_strength:
        classification_lines.append(f"**Basestyrke:** {s.base_strength.capitalize()} base")

    if classification_lines:
        with st.expander("🏷️ Klassifikation", expanded=True):
            for line in classification_lines:
                st.markdown(line)

    # ── Struktur (VSEPR) og billede ───────────────────────────────────────
    with st.expander("🧩 Struktur (VSEPR)", expanded=True):
        st.markdown(f"**VSEPR-struktur:** {get_vsepr_description(s)}")
        st.markdown(f"**Tetraedrisk type:** {get_vsepr_distortion_label(s)}")
        image_info = _resolve_structure_image(s.name_da, s.name_en or "", s.formula)
        if image_info["url"]:
            try:
                st.image(image_info["url"], caption=image_info["caption"], use_container_width=False)
                st.caption(f"Kilde: {image_info['source']}")
            except AttributeError:
                st.markdown(f"Strukturbillede: {image_info['caption']}")
        else:
            st.info("Intet online struktur-billede fundet automatisk for dette stof.")

    # ── Kemiske egenskaber ─────────────────────────────────────────────────
    chem_lines = []
    if s.conjugate_base:
        chem_lines.append(f"**Konjugeret base:** `{s.conjugate_base}`")
    if s.conjugate_acid:
        chem_lines.append(f"**Konjugeret syre:** `{s.conjugate_acid}`")
    if s.ka is not None:
        chem_lines.append(f"**Ka:** {_fmt_constant(s.ka)}")
    if s.pka is not None:
        chem_lines.append(f"**pKa:** {s.pka:.2f}")
    if s.kb is not None:
        chem_lines.append(f"**Kb:** {_fmt_constant(s.kb)}")
    if s.pkb is not None:
        chem_lines.append(f"**pKb:** {s.pkb:.2f}")
    if s.salt_components:
        chem_lines.append(f"**Ioner i saltet:** {', '.join(f'`{c}`' for c in s.salt_components)}")

    if chem_lines:
        with st.expander("⚗️ Kemiske egenskaber"):
            for line in chem_lines:
                st.markdown(line)

    # ── Eksamensnoter ──────────────────────────────────────────────────────
    if s.common_exam_note:
        with st.expander("📝 Eksamensnoter"):
            st.info(s.common_exam_note)

    # ── Tags ───────────────────────────────────────────────────────────────
    if s.tags:
        st.markdown("**Tags:** " + " · ".join(f"`{t}`" for t in s.tags))

    if s.synonyms:
        st.caption("Synonymer: " + ", ".join(s.synonyms))


def show_organic_chemistry_page():
    """Organisk kemi: funktionelle grupper og reaktionsforudsigelse."""
    import re

    st.title("🧬 Organisk kemi")
    st.markdown("---")

    org_tab = st.radio(
        "Vælg:",
        ["🔍 Funktionelle grupper", "⚗️ Reaktionsforudsigelse", "📚 Reference"],
        horizontal=True,
        key="org_tab",
    )
    st.markdown("---")

    # ── Funktionelle grupper ──────────────────────────────────────────────────
    if org_tab == "🔍 Funktionelle grupper":
        st.markdown("### 🔍 Identificér funktionelle grupper")
        st.markdown(
            "Indtast en **kondenseret formel** (fx `CH3COCH2CHO`) eller et **IUPAC-navn** "
            "(fx `3-methylpentan-2-on`). Calculatoren finder alle funktionelle grupper."
        )

        inp = st.text_input(
            "Formel eller navn:",
            placeholder="fx CH3COCH2CHO, CH3COOCH2CH3, propan-1-ol",
            key="org_fg_input",
        )

        if inp.strip():
            raw = inp.strip()

            # ── Detector helpers ─────────────────────────────────────────────
            _GROUP_COLORS = {
                "Carboxylsyre": "🔴",
                "Ester":        "🟠",
                "Aldehyd":      "🟡",
                "Keton":        "🟣",
                "Alkohol":      "🔵",
                "Amin":         "🟢",
                "Amid":         "⚫",
                "Alken":        "🟤",
                "Alkyn":        "⬜",
                "Aromat":       "🌸",
                "Alkan":        "⚪",
                "Halogenid":    "🧊",
            }

            def _detect_groups(s: str):
                groups = []
                upper = s.upper().replace(" ", "")
                lower = s.lower()

                # ── Condensed formula patterns (order: most specific first) ──
                work = upper

                # Carboxylsyre: COOH
                if re.search(r"COOH", work):
                    groups.append(("Carboxylsyre", "-COOH", "Karbonylgruppe + hydroxyl på samme C"))
                    work = re.sub(r"COOH", "####", work)

                # Ester: COO (not followed by H, already consumed COOH above)
                if re.search(r"COO", work):
                    groups.append(("Ester", "-COO-", "Karbonyl bundet til ether-oxygen"))
                    work = re.sub(r"COO", "###", work)

                # Amid: CONH / CONHCH / CON
                if re.search(r"CO\s*NH|CON", work):
                    groups.append(("Amid", "-CONH-", "Karbonyl bundet til nitrogen"))
                    work = re.sub(r"CONH?2?|CON", "###", work)

                # Aldehyd: CHO (terminal – COOH already removed)
                if re.search(r"CHO", work):
                    groups.append(("Aldehyd", "-CHO", "Karbonyl-H: C=O ved terminalt C"))
                    work = re.sub(r"CHO", "###", work)

                # Keton: CO flanked by C or ) or (
                if re.search(r"[C\)]CO[C\(]|[C\)]CO$|^CO[C\(]", work):
                    groups.append(("Keton", ">C=O", "Karbonyl inde i kæden"))
                    work = re.sub(r"CO", "##", work, count=1)

                # Alkohol: OH (remaining – not part of consumed groups)
                if re.search(r"OH", work):
                    groups.append(("Alkohol", "-OH", "Hydroxylgruppe bundet til sp³-carbon"))
                    work = re.sub(r"OH", "##", work)

                # Amin: NH2, NH, N (not in amid)
                if re.search(r"NH2|NH(?!#)|(?<=[C\d])N(?=[C\d(])", work):
                    groups.append(("Amin", "-NH₂/-NH-", "Nitrogengruppe"))

                # Halogenid: F, CL (not in already found), BR, I
                halo_map = {"CL": "Cl", "BR": "Br", "F": "F", "I": "I"}
                for pat, sym in halo_map.items():
                    if re.search(rf"(?<=[C\d]){pat}|{pat}(?=[C\d#])", work):
                        groups.append(("Halogenid", f"-{sym}", f"Halogensubstituent ({sym})"))
                        break

                # ── IUPAC name patterns ───────────────────────────────────────
                # (supplement condensed-formula detection)
                iupac_hits = set(g[0] for g in groups)

                def _iupac(pattern, name, smarts, note):
                    if name not in iupac_hits and re.search(pattern, lower):
                        groups.append((name, smarts, note))
                        iupac_hits.add(name)

                _iupac(r"syre$|ic acid$|oic acid$|carboxylic", "Carboxylsyre", "-COOH", "Slutning -syre/-ic acid")
                _iupac(r"oat$|anoat|yl .*at$|yl.*ate$", "Ester", "-COO-", "Slutning -oat/-ate")
                _iupac(r"amid$|amide$", "Amid", "-CONH-", "Slutning -amid/-amide")
                _iupac(r"al$|aldehyd", "Aldehyd", "-CHO", "Slutning -al/-aldehyd")
                _iupac(r"on$|one$|anon|ketone|keton(?!s)", "Keton", ">C=O", "Slutning -on/-one/-anon")
                _iupac(r"ol$|alkohol|diol|triol", "Alkohol", "-OH", "Slutning -ol/-alkohol")
                _iupac(r"amin$|amine$|amino", "Amin", "-NH₂", "Slutning -amin/-amine")
                _iupac(r"en$|ene$|alken", "Alken", "C=C", "Slutning -en/-ene")
                _iupac(r"yn$|yne$|alkyn", "Alkyn", "C≡C", "Slutning -yn/-yne")
                _iupac(r"benzen|toluen|phenyl|aromat|anilin", "Aromat", "Ph/Ar", "Benzenring")
                _iupac(r"chlor|brom|fluor|iod|chlorid|bromid|fluorid|iodid", "Halogenid", "-X", "Halogenbetegnelse")

                # If nothing found and looks like formula, try alkane
                if not groups and re.fullmatch(r"[CH0-9\(\)]+", upper):
                    groups.append(("Alkan", "C-C", "Ingen funktionel gruppe – mættet kulbrint"))

                return groups

            found = _detect_groups(raw)

            if found:
                st.markdown(f"**Fundet {len(found)} gruppe(r) i `{raw}`:**")
                for name, smarts, note in found:
                    color = _GROUP_COLORS.get(name, "⚪")
                    st.markdown(
                        f"{color} **{name}** &nbsp;(`{smarts}`)  \n"
                        f"&nbsp;&nbsp;&nbsp;&nbsp;*{note}*"
                    )

                if len(found) >= 2:
                    names = [g[0] for g in found]
                    st.success(f"✅ Forbindelsen indeholder **{' + '.join(names)}**")
            else:
                st.warning("Kunne ikke identificere grupper – tjek formlen eller prøv IUPAC-navn.")

            with st.expander("💡 Eksempler", expanded=False):
                st.markdown(
                    "| Formel | Grupper |\n"
                    "|--------|--------|\n"
                    "| `CH3COCH2CHO` | Keton + Aldehyd |\n"
                    "| `CH3COOCH2CH3` | Ester |\n"
                    "| `CH2OHCH2CH2CHO` | Alkohol + Aldehyd |\n"
                    "| `CH3COCH2COOH` | Keton + Carboxylsyre |\n"
                    "| `CH3CH2OH` | Alkohol |\n"
                    "| `CH3NH2` | Amin |\n"
                    "| `pentan-2-ol` | Alkohol |\n"
                    "| `3-methylpentan-2-on` | Keton |\n"
                )

    # ── Reaktionsforudsigelse ─────────────────────────────────────────────────
    elif org_tab == "⚗️ Reaktionsforudsigelse":
        st.markdown("### ⚗️ Forudsig reaktionsprodukt")

        _REACTIONS = {
            "Alken": {
                "H₂ (katalytisk hydrering)": {
                    "produkt": "Alkan",
                    "type": "Additionsreaktion",
                    "forklaring": (
                        "H₂ adderes over C=C-dobbelthindingen (katalysator: Pt, Pd eller Ni). "
                        "Begge C-atomer i dobbelthindingen får én H tilføjet.  \n"
                        "**Alken + H₂ → Alkan**  \n"
                        "_Eksempel: CH₂=CH₂ + H₂ → CH₃CH₃_"
                    ),
                },
                "Br₂ (halogenering)": {
                    "produkt": "1,2-Dibromoalkan",
                    "type": "Elektrofil addition",
                    "forklaring": (
                        "Br₂ adderes over dobbelthindingen: ét Br til hvert C-atom → vicinal dibromid.  \n"
                        "**Alken + Br₂ → 1,2-dibromoalkan**  \n"
                        "_Eksempel: CH₂=CH₂ + Br₂ → BrCH₂CH₂Br_  \n"
                        "Reaktionen affarver Br₂-opløsning (test for umætning)."
                    ),
                },
                "HBr (Markovnikov)": {
                    "produkt": "Bromoalkan",
                    "type": "Elektrofil addition (Markovnikov)",
                    "forklaring": (
                        "H adderes til det C med **flest H** (Markovnikovs regel), Br til det C med færrest H.  \n"
                        "**Alken + HBr → bromoalkan**  \n"
                        "_Eksempel: CH₃CH=CH₂ + HBr → CH₃CHBrCH₃ (ikke CH₃CH₂CH₂Br)_"
                    ),
                },
                "H₂O / H⁺ (hydratisering)": {
                    "produkt": "Alkohol (Markovnikov)",
                    "type": "Elektrofil addition",
                    "forklaring": (
                        "OH adderes til det C med færrest H (Markovnikov), H til det med flest H.  \n"
                        "**Alken + H₂O → alkohol**  \n"
                        "_Eksempel: CH₃CH=CH₂ + H₂O → CH₃CH(OH)CH₃ (sekundær alkohol)_"
                    ),
                },
            },
            "Alkyn": {
                "H₂ (1 ækvivalent)": {
                    "produkt": "Alken (cis)",
                    "type": "Delvis hydrering",
                    "forklaring": (
                        "Med Lindlar-katalysator (Pd/CaCO₃) dannes *cis*-alken.  \n"
                        "**Alkyn + H₂ (1 ekv.) → cis-alken**  \n"
                        "_Eksempel: CH≡CH + H₂ → CH₂=CH₂_"
                    ),
                },
                "H₂ (overskud / 2 ækvivalenter)": {
                    "produkt": "Alkan",
                    "type": "Fuld hydrering",
                    "forklaring": (
                        "Dobbelthindingen reduceres videre til alkan med overskud H₂.  \n"
                        "**Alkyn + 2 H₂ → alkan**  \n"
                        "_Eksempel: CH≡CH + 2 H₂ → CH₃CH₃_"
                    ),
                },
                "Br₂": {
                    "produkt": "1,1,2,2-Tetrabromoalkan",
                    "type": "Dobbelt addition",
                    "forklaring": (
                        "Br₂ adderes to gange over tredobbelthindingen.  \n"
                        "**Alkyn + 2 Br₂ → tetrabromoalkan**"
                    ),
                },
            },
            "Keton": {
                "H₂ / NaBH₄ (reduktion)": {
                    "produkt": "Sekundær alkohol",
                    "type": "Reduktion",
                    "forklaring": (
                        "Karbonylgruppen (C=O) reduceres til -CHOH.  \n"
                        "**Keton + H₂ → sekundær alkohol**  \n"
                        "_Eksempel: CH₃COCH₃ + H₂ → CH₃CH(OH)CH₃ (propan-2-ol)_"
                    ),
                },
                "KMnO₄ / K₂Cr₂O₇ (oxidation)": {
                    "produkt": "Ingen reaktion (ketoner oxideres ikke)  \n*(tertiær-C ved karbonyl)*",
                    "type": "Ingen reaktion",
                    "forklaring": (
                        "Ketoner mangler C-H ved karbonyl-C, derfor ingen videre oxidation under normale betingelser.  \n"
                        "*(Undtagelse: kraftig oxidation kan spalte kæden)*"
                    ),
                },
            },
            "Aldehyd": {
                "H₂ / NaBH₄ (reduktion)": {
                    "produkt": "Primær alkohol",
                    "type": "Reduktion",
                    "forklaring": (
                        "CHO reduceres til CH₂OH.  \n"
                        "**Aldehyd + H₂ → primær alkohol**  \n"
                        "_Eksempel: CH₃CHO + H₂ → CH₃CH₂OH (ethanol)_"
                    ),
                },
                "KMnO₄ / K₂Cr₂O₇ (mild oxidation)": {
                    "produkt": "Carboxylsyre",
                    "type": "Oxidation",
                    "forklaring": (
                        "CHO oxideres til COOH.  \n"
                        "**Aldehyd + [O] → carboxylsyre**  \n"
                        "_Eksempel: CH₃CHO + [O] → CH₃COOH (eddikesyre)_"
                    ),
                },
            },
            "Primær alkohol": {
                "KMnO₄ / K₂Cr₂O₇ (mild)": {
                    "produkt": "Aldehyd",
                    "type": "Oxidation",
                    "forklaring": (
                        "CH₂OH oxideres til CHO. Stopper ved aldehyd med mild oxidation.  \n"
                        "**Primær alkohol + [O] (mild) → aldehyd**  \n"
                        "_Eksempel: CH₃CH₂OH → CH₃CHO_"
                    ),
                },
                "KMnO₄ / K₂Cr₂O₇ (overskud)": {
                    "produkt": "Carboxylsyre",
                    "type": "Fuld oxidation",
                    "forklaring": (
                        "CH₂OH oxideres videre til COOH med overskud oxidationsmiddel.  \n"
                        "**Primær alkohol + [O] (overskud) → carboxylsyre**  \n"
                        "_Eksempel: CH₃CH₂OH → CH₃COOH_"
                    ),
                },
                "Carboxylsyre + H⁺/Δ (esterifikation)": {
                    "produkt": "Ester + H₂O",
                    "type": "Kondensationsreaktion",
                    "forklaring": (
                        "Fischer-esterifikation: alkohol + carboxylsyre ⇌ ester + vand.  \n"
                        "**R-OH + R'-COOH ⇌ R'-COO-R + H₂O**  \n"
                        "_Eksempel: CH₃CH₂OH + CH₃COOH → CH₃COOCH₂CH₃ + H₂O_"
                    ),
                },
            },
            "Sekundær alkohol": {
                "KMnO₄ / K₂Cr₂O₇": {
                    "produkt": "Keton",
                    "type": "Oxidation",
                    "forklaring": (
                        "CHOH oxideres til C=O.  \n"
                        "**Sekundær alkohol + [O] → keton**  \n"
                        "_Eksempel: CH₃CH(OH)CH₃ → CH₃COCH₃ (acetone)_"
                    ),
                },
            },
            "Tertiær alkohol": {
                "KMnO₄ / K₂Cr₂O₇": {
                    "produkt": "Ingen reaktion",
                    "type": "Ingen reaktion",
                    "forklaring": (
                        "Tertiær alkohol har intet C-H ved OH-C → kan ikke oxideres yderligere.  \n"
                        "*(Stærk syre kan give eliminering til alken)*"
                    ),
                },
            },
            "Carboxylsyre": {
                "Alkohol + H⁺/Δ (esterifikation)": {
                    "produkt": "Ester + H₂O",
                    "type": "Kondensationsreaktion",
                    "forklaring": (
                        "**R-COOH + HO-R' ⇌ R-COO-R' + H₂O**  \n"
                        "_Eksempel: CH₃COOH + CH₃OH → CH₃COOCH₃ + H₂O_"
                    ),
                },
                "LiAlH₄ / NaBH₄ (reduktion)": {
                    "produkt": "Primær alkohol",
                    "type": "Reduktion",
                    "forklaring": (
                        "COOH reduceres til CH₂OH (kræver stærkt reduktionsmiddel som LiAlH₄).  \n"
                        "**Carboxylsyre + [H] → primær alkohol**"
                    ),
                },
            },
            "Ester": {
                "H₂O / H⁺ (syrhydrolyse)": {
                    "produkt": "Carboxylsyre + Alkohol",
                    "type": "Hydrolyse",
                    "forklaring": (
                        "COO-R spaltes med vand under sure betingelser.  \n"
                        "**Ester + H₂O → carboxylsyre + alkohol**  \n"
                        "_Eksempel: CH₃COOCH₂CH₃ + H₂O → CH₃COOH + CH₃CH₂OH_"
                    ),
                },
                "NaOH (forsæbning / saponifikation)": {
                    "produkt": "Natriumcarboxylat (salt) + Alkohol",
                    "type": "Basisk hydrolyse (irreversibel)",
                    "forklaring": (
                        "**Ester + NaOH → R-COO⁻Na⁺ + R'-OH**  \n"
                        "Irreversibel (modsat syrhydrolyse). Bruges ved sæbefremstilling.  \n"
                        "_Eksempel: CH₃COOCH₂CH₃ + NaOH → CH₃COO⁻Na⁺ + CH₃CH₂OH_"
                    ),
                },
            },
        }

        reactant = st.selectbox("Udgangsmateriale:", list(_REACTIONS.keys()), key="org_reactant")
        reagents = list(_REACTIONS[reactant].keys())
        reagent = st.selectbox("Reagent / betingelse:", reagents, key="org_reagent")

        rx = _REACTIONS[reactant][reagent]
        st.markdown("---")
        st.success(f"**{reactant} + {reagent} →** {rx['produkt']}")
        st.markdown(f"**Reaktionstype:** {rx['type']}")
        st.markdown("**Forklaring:**")
        st.info(rx["forklaring"])

    # ── Reference ─────────────────────────────────────────────────────────────
    else:
        st.markdown("### 📚 Reference: Funktionelle grupper & reaktioner")

        with st.expander("🧩 Funktionelle grupper", expanded=True):
            import pandas as pd
            fg_data = [
                ("Alkan",        "C-C",   "-an",       "CH₃CH₃",          "Ingen (mættet)"),
                ("Alken",        "C=C",   "-en/-ene",  "CH₂=CH₂",         "H₂, Br₂, HX, H₂O"),
                ("Alkyn",        "C≡C",   "-yn/-yne",  "CH≡CH",            "H₂ (×1 eller ×2), Br₂"),
                ("Aromat",       "Ph",    "benzen-",   "C₆H₆",             "Elektrofil subst."),
                ("Alkohol",      "-OH",   "-ol",       "CH₃OH",            "Oxidation, Esterifikation"),
                ("Aldehyd",      "-CHO",  "-al",       "HCHO, CH₃CHO",     "Reduktion, Oxidation"),
                ("Keton",        ">C=O",  "-on/-one",  "CH₃COCH₃",         "Reduktion"),
                ("Carboxylsyre", "-COOH", "-syre",     "CH₃COOH",          "Esterifikation, Reduktion"),
                ("Ester",        "-COO-", "-oat/-ate", "CH₃COOCH₂CH₃",     "Hydrolyse (H⁺ eller OH⁻)"),
                ("Amin",         "-NH₂",  "-amin",     "CH₃NH₂",           "Amid-dannelse"),
                ("Amid",         "-CONH-","-amid",     "CH₃CONH₂",         "Hydrolyse"),
                ("Halogenid",    "-X",    "halo-",     "CH₃Cl, CH₃Br",     "Substitution, Eliminering"),
            ]
            df_fg = pd.DataFrame(fg_data, columns=["Gruppe", "SMARTS", "Navnesuffix", "Eksempel", "Vigtige reaktioner"])
            st.dataframe(df_fg, use_container_width=True, hide_index=True)

        with st.expander("⚗️ Vigtige reaktionstyper", expanded=True):
            rx_data = [
                ("Hydrering",         "Alken + H₂",          "Alkan",                "Pd/Pt/Ni kat., tilsættes H₂ over C=C"),
                ("Halogenaddition",   "Alken + Br₂",         "1,2-Dibromoalkan",     "Affarver Br₂ – test for umætning"),
                ("HX-addition",       "Alken + HBr/HCl",     "Haloalkan",            "Markovnikov: H til C med flest H"),
                ("Hydratisering",     "Alken + H₂O",         "Alkohol",              "Markovnikov: OH til C med færrest H"),
                ("Dehydrering",       "Alkohol + H₂SO₄/Δ",   "Alken + H₂O",         "Eliminering; Saytzev: mest substitueret alken"),
                ("Oxidation prim.",   "R-CH₂OH + [O]",       "Aldehyd → Syre",       "Mild: aldehyd; overskud: carboxylsyre"),
                ("Oxidation sek.",    "R-CHOH-R' + [O]",     "Keton",                "KMnO₄ eller K₂Cr₂O₇"),
                ("Reduktion keton",   "Keton + H₂",          "Sekundær alkohol",     "NaBH₄ eller LiAlH₄"),
                ("Reduktion aldehyd", "Aldehyd + H₂",        "Primær alkohol",       "NaBH₄ eller LiAlH₄"),
                ("Esterifikation",    "R-COOH + R'-OH",      "Ester + H₂O",          "H⁺ kat., reversibel ligevægt"),
                ("Hydrolyse (sur)",   "Ester + H₂O/H⁺",      "Syre + Alkohol",       "Reversibel"),
                ("Saponifikation",    "Ester + NaOH",        "Carboxylat + Alkohol", "Irreversibel basisk hydrolyse"),
            ]
            df_rx = pd.DataFrame(rx_data, columns=["Reaktionstype", "Reaktanter", "Produkt", "Note"])
            st.dataframe(df_rx, use_container_width=True, hide_index=True)

        with st.expander("🧪 Oxidationstilstande (carbon)", expanded=False):
            st.markdown(
                "| Forbindelsestype | C-oxidationstrin | Eksempel |\n"
                "|-----------------|-----------------|----------|\n"
                "| Alkan | −4 til +4 (afhænger af binding) | CH₄: C = −4 |\n"
                "| Primær alkohol | Lav | CH₃OH |\n"
                "| Aldehyd | Middel | CH₂O, CH₃CHO |\n"
                "| Carboxylsyre | Høj | HCOOH, CH₃COOH |\n\n"
                "**Generel rækkefølge (stigende oxidation):**  \n"
                "Alkan → Alkohol → Aldehyd/Keton → Carboxylsyre → CO₂"
            )

        with st.expander("🔎 Genkend funktionelle grupper på strukturformel", expanded=True):
            st.caption("Hver gruppe vises som strukturformel-mønster. **R** = resten af molekylet (alkylgruppe).")

            _STRUCT_GROUPS = [
                {
                    "name": "Alkohol",
                    "emoji": "🔵",
                    "suffix": "-ol",
                    "struct": (
                        "    OH\n"
                        "    │\n"
                        "R ─ C ─ R'\n"
                        "    │\n"
                        "    H"
                    ),
                    "condensed": "R-OH  /  -CHOH-  /  -CH₂OH",
                    "kend": "Hydroxylgruppe (-OH) bundet direkte til carbon (ikke karbonyl)",
                    "eksempel": "CH₃CH₂OH (ethanol), propan-2-ol",
                },
                {
                    "name": "Aldehyd",
                    "emoji": "🟡",
                    "suffix": "-al",
                    "struct": (
                        "    O\n"
                        "    ‖\n"
                        "R ─ C ─ H"
                    ),
                    "condensed": "R-CHO  /  -CHO (altid terminal)",
                    "kend": "C=O med én H direkte på karbonyl-C. **Sidder altid for enden** af kæden",
                    "eksempel": "HCHO (methanal), CH₃CHO (ethanal)",
                },
                {
                    "name": "Keton",
                    "emoji": "🟣",
                    "suffix": "-on / -one",
                    "struct": (
                        "    O\n"
                        "    ‖\n"
                        "R ─ C ─ R'"
                    ),
                    "condensed": "R-CO-R'  /  -CO- (inde i kæden)",
                    "kend": "C=O **inde i kæden** (karbonyl-C bundet til to C-atomer, ingen H på C=O)",
                    "eksempel": "CH₃COCH₃ (acetone/propan-2-on)",
                },
                {
                    "name": "Carboxylsyre",
                    "emoji": "🔴",
                    "suffix": "-syre / -ic acid",
                    "struct": (
                        "    O\n"
                        "    ‖\n"
                        "R ─ C ─ OH"
                    ),
                    "condensed": "R-COOH  /  -COOH (terminal)",
                    "kend": "Karbonyl **og** hydroxyl på **samme** C. Let sur smag/lugt i eksempler",
                    "eksempel": "CH₃COOH (eddikesyre), HCOOH (myresyre)",
                },
                {
                    "name": "Ester",
                    "emoji": "🟠",
                    "suffix": "-oat / -ate",
                    "struct": (
                        "    O\n"
                        "    ‖\n"
                        "R ─ C ─ O ─ R'"
                    ),
                    "condensed": "R-COO-R'  /  -COO-",
                    "kend": "Karbonyl efterfulgt af oxygen der er bundet til **endnu et carbon** (ikke H)",
                    "eksempel": "CH₃COOCH₂CH₃ (ethylacetat)",
                },
                {
                    "name": "Amin",
                    "emoji": "🟢",
                    "suffix": "-amin / -amine",
                    "struct": (
                        "R ─ NH₂\n"
                        "\n"
                        "(sekundær: R-NH-R')\n"
                        "(tertiær: R-N(-R')R'')"
                    ),
                    "condensed": "R-NH₂  /  R-NH-R'  /  R₃N",
                    "kend": "Nitrogen bundet til carbon. Primær: -NH₂, Sekundær: -NH-, Tertiær: -N<",
                    "eksempel": "CH₃NH₂ (methylamin), anilin (C₆H₅NH₂)",
                },
                {
                    "name": "Amid",
                    "emoji": "⚫",
                    "suffix": "-amid / -amide",
                    "struct": (
                        "    O\n"
                        "    ‖\n"
                        "R ─ C ─ NH₂"
                    ),
                    "condensed": "R-CONH₂  /  -CONHR-",
                    "kend": "Karbonyl direkte bundet til nitrogen. Kombination af keton-look + NH",
                    "eksempel": "CH₃CONH₂ (acetamid), peptidBindinger er amider",
                },
                {
                    "name": "Alken",
                    "emoji": "🟤",
                    "suffix": "-en / -ene",
                    "struct": (
                        "    H   H\n"
                        "    │   │\n"
                        "R ─ C = C ─ R'"
                    ),
                    "condensed": "R-CH=CH-R'  /  R₂C=CH₂",
                    "kend": "Dobbeltbinding mellem to C (plan geometri, 120°). **Ingen** karbonyl",
                    "eksempel": "CH₂=CH₂ (ethen), 3-methyl-1-penten",
                },
                {
                    "name": "Alkyn",
                    "emoji": "⬜",
                    "suffix": "-yn / -yne",
                    "struct": (
                        "R ─ C ≡ C ─ R'"
                    ),
                    "condensed": "R-C≡C-R'  /  RC≡CH (terminal)",
                    "kend": "Tredobbeltbinding (lineær, 180°). To parallelle π-bindinger",
                    "eksempel": "HC≡CH (acetylen/etyn), propyn",
                },
                {
                    "name": "Halogenid",
                    "emoji": "🧊",
                    "suffix": "halo- / chloro- / bromo-",
                    "struct": (
                        "R ─ C ─ X\n"
                        "    │\n"
                        "   (X = F, Cl, Br, I)"
                    ),
                    "condensed": "R-Cl  /  R-Br  /  R-F  /  R-I",
                    "kend": "Halogenatom (F, Cl, Br, I) direkte bundet til carbon",
                    "eksempel": "CH₃Cl (chlormethan), CH₂BrCH₂Br (1,2-dibromoethan)",
                },
            ]

            # Render 2 cards per row
            for i in range(0, len(_STRUCT_GROUPS), 2):
                row_groups = _STRUCT_GROUPS[i:i+2]
                cols = st.columns(len(row_groups))
                for col, grp in zip(cols, row_groups):
                    with col:
                        st.markdown(
                            f"#### {grp['emoji']} {grp['name']}"
                            f"&nbsp;&nbsp;<small style='color:#888'>({grp['suffix']})</small>",
                            unsafe_allow_html=True,
                        )
                        st.code(grp["struct"], language=None)
                        st.markdown(
                            f"**Kondenseret:** `{grp['condensed']}`  \n"
                            f"**Genkend:** {grp['kend']}  \n"
                            f"**Eksempel:** *{grp['eksempel']}*"
                        )
                st.markdown("---")


def show_molecule_database_page() -> None:
    """Render the Molekyle database page."""
    def _reset_molecule_db_state() -> None:
        st.session_state["moldb_query"] = ""
        st.session_state.pop("moldb_selected_id", None)

    st.title("🔬 Molekyle database")
    st.markdown(
        "Søg efter et stof ved navn eller formel og få en kompakt faglig oversigt."
    )
    st.markdown("---")

    # ── Search bar ────────────────────────────────────────────────────────
    col_search, col_reset = st.columns([5, 1])
    with col_search:
        query = st.text_input(
            label="Søg",
            placeholder="Søg efter navn eller formel, fx HCl, NaOH, svovlsyre, ammoniak",
            key="moldb_query",
            label_visibility="collapsed",
        )
    with col_reset:
        st.button(
            "✖ Nulstil",
            key="moldb_reset",
            on_click=_reset_molecule_db_state,
        )

    # ── Category filter ───────────────────────────────────────────────────
    selected_filter = st.radio(
        "Filtrer:",
        _FILTER_OPTIONS,
        horizontal=True,
        key="moldb_filter",
    )
    category_filter = _FILTER_TO_CATEGORY[selected_filter]

    # ── Search ────────────────────────────────────────────────────────────
    if query.strip():
        results = search_substances(query)
        if category_filter:
            results = [r for r in results if r.category == category_filter]
    else:
        # No query → show all or filtered list
        if category_filter:
            results = [s for s in SUBSTANCES if s.category == category_filter]
        else:
            results = []

    # ── Result list ───────────────────────────────────────────────────────
    if query.strip() and not results:
        st.warning(
            f"Ingen stoffer fundet for søgningen **\"{query.strip()}\"**. "
            "Prøv et andet navn, en formel eller et synonym."
        )
        st.session_state.pop("moldb_selected_id", None)
    elif results:
        st.markdown(f"**{len(results)} resultat(er):**")
        for s in results:
            icon = _CATEGORY_ICONS.get(s.category, "❓")
            cat_label = _CATEGORY_LABELS_DA.get(s.category, s.category.capitalize())
            btn_label = f"{icon} {s.name_da}  ({s.formula})  — {cat_label}"
            if st.button(btn_label, key=f"moldb_btn_{s.id}"):
                st.session_state["moldb_selected_id"] = s.id
    elif not query.strip() and not category_filter:
        st.info(
            "Brug søgefeltet øverst til at finde et stof, "
            "eller vælg en kategori for at se alle stoffer i kategorien."
        )

    # ── Detail card ───────────────────────────────────────────────────────
    selected_id = st.session_state.get("moldb_selected_id")
    if selected_id:
        substance = get_substance_by_id(selected_id)
        if substance:
            st.markdown("---")
            _render_substance_card(substance)

    # ── Footer ────────────────────────────────────────────────────────────
    st.markdown("---")
    st.caption(
        "Databasen er et hurtigt opslagsværk til undervisningsbrug. "
        "Nogle egenskaber afhænger af kontekst, opløsning og betingelser."
    )


if __name__ == "__main__":
    main()
