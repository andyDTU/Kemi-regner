from core.molecule_db import SUBSTANCES
existing_ids = {s.id for s in SUBSTANCES}
existing_formulas = {s.formula.replace(' ', '') for s in SUBSTANCES}
print('ids', len(existing_ids), 'formulas', len(existing_formulas))
checks = ['HClO4','HNO2','HClO','HClO2','HClO3','H2SO3','H2C2O4','HCOOH','C6H8O7','C6H5COOH',
'RbOH','CsOH','Sr(OH)2','Ba(OH)2','Al(OH)3','Fe(OH)3','Cu(OH)2','Cl2','F2','Br2','I2','O3','H2','P4','S8','SO','N2O','NO2','N2O4','ClO2','NH2-','CN-','MnO4-','Cr2O7^2-','ClO-','ClO3-','ClO4-','CH3COO-','HCO3-','HS-','SO3^2-','S2O3^2-','Al3+','Cu2+','Zn2+','Mn2+','Pb2+','Ni2+','CH3OH','C3H8','C4H10','C2H4','C2H2','CH3CHO','CH3COCH3','C6H6','C7H8','C6H6O','C6H12O6']
for f in checks:
    if f in existing_formulas:
        print('HAS', f)
