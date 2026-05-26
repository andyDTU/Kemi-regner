from core.molecule_db import SUBSTANCES
existing = {s.formula.replace(' ','') for s in SUBSTANCES}
cands = ['HIO2','HIO','HIO4','HBO2','HSCN','Cd(OH)2','PH3','Fe3O4','NaIO3','KIO3']
for f in cands:
    print(f, 'EXISTS' if f in existing else 'OK')
