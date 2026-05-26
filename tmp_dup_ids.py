from collections import Counter
from core.molecule_db import SUBSTANCES
ids = [s.id for s in SUBSTANCES]
c = Counter(ids)
dups = [(k,v) for k,v in c.items() if v>1]
print('duplicate_ids', len(dups))
for k,v in sorted(dups):
    print(k, v)
