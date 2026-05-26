from core.molecule_db import SUBSTANCES
from collections import Counter
print('TOTAL', len(SUBSTANCES))
c = Counter(s.category for s in SUBSTANCES)
print('syre', c['syre'], 'base', c['base'])
print('stark_values', sorted({s.acid_strength for s in SUBSTANCES if s.acid_strength is not None})[:5], sorted({s.base_strength for s in SUBSTANCES if s.base_strength is not None})[:5])
