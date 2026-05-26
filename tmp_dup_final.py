from collections import Counter
from core.molecule_db import SUBSTANCES
ids = [s.id for s in SUBSTANCES]
forms = [s.formula.replace(' ','') for s in SUBSTANCES]
print('dup_ids', sum(v-1 for v in Counter(ids).values() if v>1))
print('dup_formulas', sum(v-1 for v in Counter(forms).values() if v>1))
