from pathlib import Path
p = Path('core/molecule_db.py')
text = p.read_text(encoding='utf-8')
fixed = text.encode('latin1', errors='ignore').decode('utf-8', errors='ignore')
p.write_text(fixed, encoding='utf-8')
print('rewritten')
