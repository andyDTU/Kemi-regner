from core.molecule_db import SUBSTANCES
import requests

existing_formulas = {s.formula.replace(' ', '').lower() for s in SUBSTANCES}
existing_names = {s.name_da.lower() for s in SUBSTANCES}
existing_names_en = {s.name_en.lower() for s in SUBSTANCES if s.name_en}

candidates = [
    ("Hydrogen peroxide", "H2O2", "Brintoverilte", "oxid"),
    ("Ozone", "O3", "Ozon", "molekyle"),
    ("Chlorine", "Cl2", "Klor", "molekyle"),
    ("Fluorine", "F2", "Fluor", "molekyle"),
    ("Bromine", "Br2", "Brom", "molekyle"),
    ("Iodine", "I2", "Iod", "molekyle"),
    ("Nitrous acid", "HNO2", "Salpetersyrling", "syre"),
    ("Perchloric acid", "HClO4", "Perchlorsyre", "syre"),
    ("Hypochlorous acid", "HClO", "Hypochlorsyre", "syre"),
    ("Hydrogen cyanide", "HCN", "Hydrogencyanid", "syre"),
    ("Sodium hypochlorite", "NaClO", "Natriumhypochlorit", "salt"),
    ("Potassium permanganate", "KMnO4", "Kaliumpermanganat", "salt"),
    ("Potassium dichromate", "K2Cr2O7", "Kaliumdichromat", "salt"),
    ("Sodium thiosulfate", "Na2S2O3", "Natriumthiosulfat", "salt"),
    ("Silver nitrate", "AgNO3", "Solvnitrat", "salt"),
    ("Calcium nitrate", "Ca(NO3)2", "Calciumnitrat", "salt"),
    ("Ammonium sulfate", "(NH4)2SO4", "Ammoniumsulfat", "salt"),
    ("Sodium acetate", "CH3COONa", "Natriumacetat", "salt"),
    ("Hydrazine", "N2H4", "Hydrazin", "organisk"),
    ("Acetone", "C3H6O", "Acetone", "organisk"),
    ("Benzene", "C6H6", "Benzen", "organisk"),
    ("Toluene", "C7H8", "Toluen", "organisk"),
    ("Phenol", "C6H6O", "Phenol", "organisk"),
    ("Formaldehyde", "CH2O", "Formaldehyd", "organisk"),
    ("Urea", "CH4N2O", "Urea", "organisk"),
]

missing = []
for en_name, formula, da_name, category in candidates:
    formula_key = formula.replace(' ', '').lower()
    if formula_key in existing_formulas:
        continue
    if da_name.lower() in existing_names or en_name.lower() in existing_names_en:
        continue

    cid = None
    try:
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{requests.utils.quote(en_name)}/property/Title/JSON"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            props = data.get("PropertyTable", {}).get("Properties", [])
            if props:
                cid = props[0].get("CID")
    except Exception:
        pass

    missing.append((da_name, en_name, formula, category, cid))

order = {"oxid": 0, "syre": 1, "base": 2, "salt": 3, "molekyle": 4, "organisk": 5}
missing.sort(key=lambda x: (order.get(x[3], 99), x[0]))

for da_name, en_name, formula, category, cid in missing:
    print(f"{da_name} | {en_name} | {formula} | {category} | CID={cid}")
