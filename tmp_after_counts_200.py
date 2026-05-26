from collections import Counter
from core.molecule_db import SUBSTANCES
c = Counter(s.category for s in SUBSTANCES)
print('after_total', len(SUBSTANCES))
print('after_syre', c['syre'])
print('after_base', c['base'])
ids = [s.id for s in SUBSTANCES]
forms = [s.formula.replace(' ','') for s in SUBSTANCES]
print('dup_ids', sum(v-1 for v in Counter(ids).values() if v>1))
print('dup_formulas', sum(v-1 for v in Counter(forms).values() if v>1))
new_acids = [s for s in SUBSTANCES if s.id.startswith('alkansyre_c')]
new_bases = [s for s in SUBSTANCES if s.id.startswith('alkylamin_c')]
print('new_marker_acids', len(new_acids))
print('new_marker_bases', len(new_bases))
