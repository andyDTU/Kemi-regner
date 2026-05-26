from core.molecule_db import SUBSTANCES
import re

existing_ids = {s.id for s in SUBSTANCES}
existing_formulas = {s.formula.replace(' ', '') for s in SUBSTANCES}

acids = [
("Phosphorous acid","H3PO3","Fosforsyrling"),
("Hypophosphorous acid","H3PO2","Hypofosforsyre"),
("Pyrophosphoric acid","H4P2O7","Pyrofosforsyre"),
("Metaphosphoric acid","HPO3","Metafosforsyre"),
("Silicic acid","H4SiO4","Kiselsyre"),
("Fluoroboric acid","HBF4","Fluorborsyre"),
("Fluorosilicic acid","H2SiF6","Fluorkiselsyre"),
("Hexafluorophosphoric acid","HPF6","Hexafluorfosforsyre"),
("Hexafluoroantimonic acid","HSbF6","Hexafluorantimonsyre"),
("Arsenous acid","H3AsO3","Arsenigsyrling"),
("Arsenic acid","H3AsO4","Arsensyre"),
("Hydrogen telluride","H2Te","Hydrogentellurid"),
("Hydrogen selenide","H2Se","Hydrogenselenid"),
("Lactic acid","C3H6O3","Maelkesyre"),
("Pyruvic acid","C3H4O3","Pyrodruesyre"),
("Malonic acid","C3H4O4","Malonsyre"),
("Succinic acid","C4H6O4","Ravsyre"),
("Glutaric acid","C5H8O4","Glutarsyre"),
("Adipic acid","C6H10O4","Adipinsyre"),
("Salicylic acid","C7H6O3","Salicylsyre"),
("Phthalic acid","C8H6O4","Phthalsyre"),
("Acetylsalicylic acid","C9H8O4","Acetylsalicylsyre"),
("Valeric acid","C5H10O2","Valeriansyre"),
("Caproic acid","C6H12O2","Capronsyre"),
("Heptanoic acid","C7H14O2","Heptansyre"),
("Octanoic acid","C8H16O2","Octansyre"),
("Nonanoic acid","C9H18O2","Nonansyre"),
("Decanoic acid","C10H20O2","Decansyre"),
("Undecanoic acid","C11H22O2","Undecansyre"),
("Dodecanoic acid","C12H24O2","Laurinsyre"),
("Tridecanoic acid","C13H26O2","Tridecansyre"),
("Tetradecanoic acid","C14H28O2","Myristinsyre"),
("Pentadecanoic acid","C15H30O2","Pentadecansyre"),
("Hexadecanoic acid","C16H32O2","Palmitinsyre"),
("Heptadecanoic acid","C17H34O2","Heptadecansyre"),
("Octadecanoic acid","C18H36O2","Stearinsyre"),
("Oleic acid","C18H34O2","Oliesyre"),
("Linoleic acid","C18H32O2","Linolsyre"),
("Linolenic acid","C18H30O2","Linolensyre"),
("Arachidic acid","C20H40O2","Arachidsyre"),
("Behenic acid","C22H44O2","Behensyre"),
("Lignoceric acid","C24H48O2","Lignocerinsyre"),
("Cerotic acid","C26H52O2","Cerotinsyre"),
("Chloroacetic acid","C2H3ClO2","Chloreddikesyre"),
("Dichloroacetic acid","C2H2Cl2O2","Dichloreddikesyre"),
("Trichloroacetic acid","C2HCl3O2","Trichloreddikesyre"),
("Bromoacetic acid","C2H3BrO2","Bromeddikesyre"),
("Iodoacetic acid","C2H3IO2","Iodeddikesyre"),
("Trifluoroacetic acid","C2HF3O2","Trifluoreddikesyre"),
("Methanesulfonic acid","CH4O3S","Methansulfonsyre"),
]

bases = [
("Cobalt(III) hydroxide","Co(OH)3","Kobolt(III)hydroxid"),
("Vanadium(III) hydroxide","V(OH)3","Vanadium(III)hydroxid"),
("Vanadium(V) hydroxide","V(OH)5","Vanadium(V)hydroxid"),
("Titanium(IV) hydroxide","Ti(OH)4","Titan(IV)hydroxid"),
("Zirconium(IV) hydroxide","Zr(OH)4","Zirkonium(IV)hydroxid"),
("Hafnium(IV) hydroxide","Hf(OH)4","Hafnium(IV)hydroxid"),
("Gallium hydroxide","Ga(OH)3","Galliumhydroxid"),
("Indium hydroxide","In(OH)3","Indiumhydroxid"),
("Thallium(I) hydroxide","TlOH","Thallium(I)hydroxid"),
("Bismuth(III) hydroxide","Bi(OH)3","Bismuth(III)hydroxid"),
("Scandium hydroxide","Sc(OH)3","Scandiumhydroxid"),
("Yttrium hydroxide","Y(OH)3","Yttriumhydroxid"),
("Lanthanum hydroxide","La(OH)3","Lanthanumhydroxid"),
("Cerium(III) hydroxide","Ce(OH)3","Cerium(III)hydroxid"),
("Praseodymium(III) hydroxide","Pr(OH)3","Praseodymhydroxid"),
("Neodymium(III) hydroxide","Nd(OH)3","Neodymhydroxid"),
("Promethium(III) hydroxide","Pm(OH)3","Promethiumhydroxid"),
("Samarium(III) hydroxide","Sm(OH)3","Samariumhydroxid"),
("Europium(III) hydroxide","Eu(OH)3","Europiumhydroxid"),
("Gadolinium(III) hydroxide","Gd(OH)3","Gadoliniumhydroxid"),
("Terbium(III) hydroxide","Tb(OH)3","Terbiumhydroxid"),
("Dysprosium(III) hydroxide","Dy(OH)3","Dysprosiumhydroxid"),
("Holmium(III) hydroxide","Ho(OH)3","Holmiumhydroxid"),
("Erbium(III) hydroxide","Er(OH)3","Erbiumhydroxid"),
("Thulium(III) hydroxide","Tm(OH)3","Thuliumhydroxid"),
("Ytterbium(III) hydroxide","Yb(OH)3","Ytterbiumhydroxid"),
("Lutetium(III) hydroxide","Lu(OH)3","Lutetiumhydroxid"),
("Thorium(IV) hydroxide","Th(OH)4","Thorium(IV)hydroxid"),
("Uranium(IV) hydroxide","U(OH)4","Uran(IV)hydroxid"),
("Sodium amide","NaNH2","Natriumamid"),
("Potassium amide","KNH2","Kaliumamid"),
("Lithium amide","LiNH2","Lithiumamid"),
("Sodium hydride","NaH","Natriumhydrid"),
("Potassium hydride","KH","Kaliumhydrid"),
("Lithium hydride","LiH","Lithiumhydrid"),
("Dimethylamine","C2H7N","Dimethylamin"),
("Trimethylamine","C3H9N","Trimethylamin"),
("Diethylamine","C4H11N","Diethylamin"),
("Triethylamine","C6H15N","Triethylamin"),
("Ethanolamine","C2H7NO","Ethanolamin"),
("Diethanolamine","C4H11NO2","Diethanolamin"),
("Triethanolamine","C6H15NO3","Triethanolamin"),
("Piperidine","C5H11N","Piperidin"),
("Morpholine","C4H9NO","Morpholin"),
("Imidazole","C3H4N2","Imidazol"),
("Guanidine","CH5N3","Guanidin"),
("Biguanide","C2H7N5","Biguanid"),
("Putrescine","C4H12N2","Putrescin"),
("Cadaverine","C5H14N2","Cadaverin"),
("Piperazine","C4H10N2","Piperazin"),
]

used_ids = {s.id for s in SUBSTANCES}
used_formulas = {s.formula.replace(' ', '') for s in SUBSTANCES}


def mk_id(da, category):
    base = re.sub(r'[^a-z0-9]+', '_', da.lower()).strip('_') + '_' + category
    cand = base
    i = 2
    while cand in used_ids:
        cand = f"{base}_{i}"
        i += 1
    used_ids.add(cand)
    return cand

lines = []
added = 0
for en, formula, da in acids:
    if formula in used_formulas:
        continue
    sid = mk_id(da, 'syre')
    used_formulas.add(formula)
    lines.append(f'    Substance(id="{sid}", name_da="{da}", name_en="{en}", formula="{formula}", category="syre", subtype="svag syre", description="Kurateret fra PubChem-liste over almindelige syrer.", tags=["syre", "pubchem", "{formula}"], acid_base_role="syre"),')
    added += 1
for en, formula, da in bases:
    if formula in used_formulas:
        continue
    sid = mk_id(da, 'base')
    used_formulas.add(formula)
    lines.append(f'    Substance(id="{sid}", name_da="{da}", name_en="{en}", formula="{formula}", category="base", subtype="base", description="Kurateret fra PubChem-liste over almindelige baser.", tags=["base", "pubchem", "{formula}"], acid_base_role="base"),')
    added += 1

print('added', added)
with open('tmp_ab100_snippet.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines) + '\n')
print('snippet_written', len(lines))
