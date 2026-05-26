from collections import Counter
from core.molecule_db import SUBSTANCES
c = Counter(s.category for s in SUBSTANCES)
print('before_total', len(SUBSTANCES))
print('before_syre', c['syre'])
print('before_base', c['base'])
