from core.molecule_db import SUBSTANCES
from collections import Counter

existing_ids = {s.id for s in SUBSTANCES}
existing_formulas = {s.formula.replace(' ', '') for s in SUBSTANCES}
acid_count = sum(1 for s in SUBSTANCES if s.category == 'syre')
base_count = sum(1 for s in SUBSTANCES if s.category == 'base')
print('acid_count', acid_count)
print('base_count', base_count)
print('total', len(SUBSTANCES))
print('ids', len(existing_ids), 'formulas', len(existing_formulas))
