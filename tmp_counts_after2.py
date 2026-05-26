from collections import Counter
from core.molecule_db import SUBSTANCES
counts = Counter(s.category for s in SUBSTANCES)
print('TOTAL', len(SUBSTANCES))
for k in sorted(counts):
    print(f'{k}: {counts[k]}')
