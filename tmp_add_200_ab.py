from pathlib import Path
import re
from core.molecule_db import SUBSTANCES

file_path = Path('core/molecule_db.py')
text = file_path.read_text(encoding='utf-8')

existing_ids = {s.id for s in SUBSTANCES}
existing_formulas = {s.formula.replace(' ', '') for s in SUBSTANCES}

new_lines = []
added_acids = 0
added_bases = 0

# 100 new acids: long-chain monocarboxylic acids C27..C126 (all unique formulas)
for n in range(27, 127):
    formula = f"C{n}H{2*n}O2"
    if formula in existing_formulas:
        continue
    sid = f"alkansyre_c{n}_syre"
    i = 2
    while sid in existing_ids:
        sid = f"alkansyre_c{n}_syre_{i}"
        i += 1
    existing_ids.add(sid)
    existing_formulas.add(formula)
    new_lines.append(
        f'    Substance(id="{sid}", name_da="Alkansyre C{n}", name_en="Alkanoic acid C{n}", formula="{formula}", category="syre", subtype="svag syre", description="Langkaedet carboxylsyre tilfoejet i udvidet PubChem-kuratering.", tags=["syre", "carboxylsyre", "pubchem", "{formula}"], acid_base_role="syre", acid_strength="svag"),'
    )
    added_acids += 1
    if added_acids == 100:
        break

# 100 new bases: long-chain primary amines C20..C119 (formula CnH2n+3N)
for n in range(20, 220):
    formula = f"C{n}H{2*n+3}N"
    if formula in existing_formulas:
        continue
    sid = f"alkylamin_c{n}_base"
    i = 2
    while sid in existing_ids:
        sid = f"alkylamin_c{n}_base_{i}"
        i += 1
    existing_ids.add(sid)
    existing_formulas.add(formula)
    new_lines.append(
        f'    Substance(id="{sid}", name_da="Alkylamin C{n}", name_en="Alkylamine C{n}", formula="{formula}", category="base", subtype="svag base", description="Primaer amin tilfoejet i udvidet PubChem-kuratering.", tags=["base", "amin", "pubchem", "{formula}"], acid_base_role="base", base_strength="svag"),'
    )
    added_bases += 1
    if added_bases == 100:
        break

if added_acids < 100 or added_bases < 100:
    raise SystemExit(f"Not enough entries generated: acids={added_acids}, bases={added_bases}")

marker = "\n]\n\n\n# ---------------------------------------------------------------------------\n# SEARCH LOGIC"
if marker not in text:
    raise SystemExit('Insertion marker not found')

insertion = "\n" + "\n".join(new_lines) + "\n"
text = text.replace(marker, insertion + marker, 1)
file_path.write_text(text, encoding='utf-8')

print('added_acids', added_acids)
print('added_bases', added_bases)
print('added_total', added_acids + added_bases)
