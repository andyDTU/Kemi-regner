from collections import Counter
from core.molecule_db import SUBSTANCES
c = Counter(s.id for s in SUBSTANCES)
dups = [k for k,v in c.items() if v>1]
print('duplicate_ids', len(dups))
if dups:
    print('\n'.join(sorted(dups)))
