from core.molecule_db import SUBSTANCES
existing = {s.formula.replace(' ','') for s in SUBSTANCES}
for f in ['H2SO5','H2S2O8']:
    print(f, 'EXISTS' if f in existing else 'OK')
