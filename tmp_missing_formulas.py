from core.molecule_db import SUBSTANCES
existing_formulas = {s.formula.replace(' ', '') for s in SUBSTANCES}
candidates = ['HClO','H2C2O4','HCOOH','C6H8O7','C6H5COOH','RbOH','CsOH','Sr(OH)2','Ba(OH)2','Cl2','F2','Br2','I2','O3','H2','P4','S8','SO','N2O','N2O4','ClO2','NH2-','CN-','MnO4-','Cr2O7^2-','ClO-','ClO3-','ClO4-','CH3COO-','HS-','SO3^2-','S2O3^2-','Al3+','Cu2+','Zn2+','Mn2+','Pb2+','Ni2+','C2H6','C3H8','C4H10','C2H4','C2H2','CH3CHO','CH3COCH3','C6H6','C7H8','C6H6O','CH2O','CH4N2O','NaClO','KMnO4','K2Cr2O7','Na2S2O3','AgNO3','Ca(NO3)2','(NH4)2SO4','CH3COONa','H2O2']
for f in candidates:
    if f not in existing_formulas:
        print(f)
