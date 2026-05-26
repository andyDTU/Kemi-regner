from collections import Counter
from core.molecule_db import SUBSTANCES
from collections import Counter
cats = Counter(s.category for s in SUBSTANCES)
print('TOTAL', len(SUBSTANCES))
print('syre', cats['syre'])
print('base', cats['base'])
ids = [s.id for s in SUBSTANCES]
formulas = [s.formula.replace(' ','') for s in SUBSTANCES]
print('dup_ids', sum(v-1 for v in Counter(ids).values() if v>1))
print('dup_formulas', sum(v-1 for v in Counter(formulas).values() if v>1))
