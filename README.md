# 🧪 Chemistry Calculator

A comprehensive chemistry calculator built with Streamlit, designed for high school and introductory university students. This application provides step-by-step solutions for common chemistry calculations with a focus on learning and understanding.

## ✨ Features

### 🎯 Implemented Calculators
- **⚖️ Molar Mass**: Calculate molar masses and composition breakdown
- **⚛️ Electron Configuration**: Parse element/ion input and compute orbital electron configuration (long + noble-gas notation)
- **🔥 Gibbs Free Energy**: ΔG, spontaneity, and temperature dependence
- **📊 Gases**: Ideal gas law, Dalton’s law, gas stoichiometry, van der Waals (with thermo-derived a,b when available)
- **🌡️ Thermochemistry**: Calorimetry, heating/cooling curves, ΔH from ΔHf°, Clausius–Clapeyron
- **🧪 Colligative Properties**: ΔTf/ΔTb, osmotic pressure, Raoult’s law
- **⚡ Kinetics**: Integrated rate laws (0/1/2), two-point order/k, Arrhenius (forward/two-point)
- **🔋 Electrochemistry**: E°cell from half-reactions, Nernst, ΔG and K

## 🏗️ Architecture

```
chem_calc/
├── app.py                 # Main Streamlit application
├── core/                  # Core utilities
│   ├── units.py          # Pint UnitRegistry + unit helpers
│   ├── data.py           # Periodic table & constants loading
│   ├── formatting.py     # Significant figures & value formatting
│   └── solver.py         # Shared solve pattern & step rendering
├── calculators/          # Calculator implementations
│   ├── molar_mass.py     # Molar mass calculator
│   ├── gibbs.py          # Gibbs free energy calculator
│   ├── gases.py          # Gas laws (ideal, Dalton, stoichiometry, vdW)
│   ├── thermochemistry.py# Thermochemistry tools
│   ├── colligatives.py   # Colligative properties
│   ├── kinetics.py       # Kinetics tools
│   └── electrochemistry.py # Electrochemistry tools
├── data/                 # Data files
│   ├── constants.json    # Physical constants (R, F, water props)
│   ├── thermo_tables.csv # ΔHf° baseline (CSV preferred for tests; augmented by thermo)
│   └── reduction_potentials.csv # Standard reduction potentials (baseline; optional)
├── tests/                # Test files
│   ├── test_molar_mass.py
│   └── test_gibbs.py
└── requirements.txt      # Python dependencies
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Installation

1. **Clone or download the repository**
   ```bash
   git clone <repository-url>
   cd chem_calc
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\activate
   
   # macOS/Linux
   python -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

5. **Open your browser**
   - The app will automatically open at `http://localhost:8501`
   - If it doesn't open automatically, navigate to the URL shown in your terminal

## 🧪 Using the Calculators

### Molar Mass Calculator
- **Input**: Chemical formula (e.g., `H2O`, `C6H12O6`, `Fe2(SO4)3`)
- **Features**:
  - Handles complex formulas with parentheses
  - Shows element-by-element breakdown
  - Calculates percentage composition
  - Step-by-step solution display

**Example**: Calculate the molar mass of glucose (`C6H12O6`)
- Expected result: ~180.156 g/mol
- Shows contribution of each element: C (6 × 12.011), H (12 × 1.008), O (6 × 15.999)

### Electron Configuration Calculator
- Open **⚖️ Atoms & Molar Mass** → **⚛️ Elektronkonfiguration**.
- Input supports symbol or atomic number with optional charge:
   - `Na`, `B`, `O2-`, `O^2-`, `Fe3+`, `Fe2+`, `Cl-`, `Br1-`, `Cu+`, `Cr`, `Cr2+`
- Charge formats supported: `2+`, `+2`, `2-`, `-2`, `+`, `-`, `0`.
- Output includes:
   - Total electrons (`electrons = Z - charge`)
   - Long notation (e.g. `1s2 2s2 2p6 3s1`)
   - Noble-gas notation (e.g. `[Ne] 3s1`)
   - Orbital distribution (Hund + Pauli) for relevant outer subshells
   - Radius line with explicit type (`atomradius (neutral)` / `ionradius (kation)` / `ionradius (anion)`)
- Radius standard (explicit, fixed by config):
   - Neutral atoms: **covalent radius** (Pyykkö single-bond)
   - Ions: **ionic radius**
- Radius data is lookup-based only (no numeric trend-guess fallback when data is missing).
- Local data files:
   - `data/radii.atomic.json` (neutral atomic radii, default unit pm)
   - `data/radii.ionic.json` (ionic radii by ion key, default unit pm)
- Source notes for radius data (also shown in-app on result):
   - Neutral: mendeleev dataset (Pyykkö covalent radii)
   - Ionic: Shannon-like ionic radius reference values for common ions (school level)
- Transition-metal cations remove electrons from highest principal quantum number first (e.g. Fe²⁺ removes 4s before 3d).
- Ground-state exception table currently includes Cr and Cu and is easy to extend.
- Orbital distribution rules and format:
   - Follows **Hund's rule** (single occupancy with parallel spins first) and **Pauli** (max 2 per orbital with opposite spin)
   - Unpaired electrons are rendered as `↑`, paired as `↑↓`
   - Deterministic orbital ordering:
      - `p`: `px`, `py`, `pz`
      - `d`: `dxy`, `dyz`, `dxz`, `dx2−y2`, `dz2`
   - Example style: `3p: px [↑]  py [↑]  pz [↑]`

### Gibbs Free Energy Calculator
### Kinetics (examples)
- First-order decay: C0=0.100 M, k=0.350 s⁻¹, t=10.0 s → Ct ≈ 0.00302 M
- Arrhenius forward: k1=1.00e-3 s⁻¹ at 298.15 K, Ea=50.0 kJ/mol, T2=308.15 K → k2 ≈ 1.9243e-3 s⁻¹

### Electrochemistry (examples)
- Standard Daniell cell: E°cell = E°(Cu²⁺/Cu) − E°(Zn²⁺/Zn) = 0.34 − (−0.76) ≈ 1.10 V
- Nernst at 298.15 K with [Zn²⁺]=0.10 M, [Cu²⁺]=1.00 M → E ≈ 1.1296 V
- **Inputs**: ΔH (enthalpy change), ΔS (entropy change), T (temperature)
- **Features**:
  - Automatic unit conversion
  - Spontaneity determination
  - Crossover temperature calculation
  - Temperature dependence analysis

**Example**: ΔH = -100 kJ/mol, ΔS = 200 J/(mol·K), T = 298.15 K
- Expected result: ΔG ≈ -159.63 kJ/mol
- Conclusion: Reaction is **spontaneous** at this temperature

### Reaction Enthalpy (ΔH°) under Thermochemistry
- Open **🌡️ Thermochemistry** → **Reaction Enthalpy (ΔH°)**.
- Enter a reaction like `N2(g) + 3 H2(g) -> 2 NH3(g)` or use `=` as arrow.
- Parser supports:
   - Explicit or implicit coefficients (implicit = 1)
   - Parentheses formulas like `Ca(OH)2`, `(NH4)2SO4`
   - Phases `(s)`, `(l)`, `(g)`, `(aq)`
- If phase is omitted, the app defaults to `(g)` and shows a warning.
- The app shows per-species table rows with coefficient ν, ΔHf°, source, and subtotal ν·ΔHf°.
- The result is reported as `ΔH°_rxn` in `kJ/mol reaktion`.
- A **Balance reaction** button attempts integer stoichiometric balancing by linear algebra.

#### Local ΔHf° databases (`data/dhf.openstax.tableG1.json` + `data/dhf.exampack.json` + `data/dhf.json`)
- `data/dhf.openstax.tableG1.json` is generated from OpenStax Appendix G Table G1 and provides broad offline baseline coverage.
- `data/dhf.exampack.json` is an offline **exam pack** with curated overrides for common exam species.
- The database key format is `FORMULA(PHASE)`, for example `H2O(g)`.
- You can extend the dataset by adding more entries to JSON (same key/value structure).
- Missing species are highlighted in the UI and can be provided as temporary overrides.
- Use **Add to database** to persist selected overrides to `data/dhf.json` (user layer).
- Saving requires explicit confirmation in the UI before writing the file.
- Aqueous standards follow the common convention `H+(aq) = 0` in the exam pack.
- Merge priority is: `dhf.json` (user) > `dhf.exampack.json` (exam pack) > `dhf.openstax.tableG1.json` (generated OpenStax base).

### Hess Solver under Thermochemistry
- Open **🌡️ Thermochemistry** → **Hess Solver**.
- Enter a target reaction and known reactions line-by-line as:
   - `reaction ; dH`
   - Example: `H2(g) + 1/2 O2(g) -> H2O(g) ; -241.8`
- Parser supports:
   - `->` and `→`
   - implicit coefficient `1`
   - fractions (`1/2`, `½`)
   - phases `(s)`, `(l)`, `(g)`, `(aq)`
- The solver builds and solves `A*x=b` with exact rational arithmetic (`Fraction`), then validates residual `b-A*x = 0` before showing ΔH°.
- Output shows selected reaction combination (factor + reverse), summed reaction, symbolic ΔH° sum, and exact validation status.

Build/refresh OpenStax baseline:
```bash
npm run build:dhf
```

## 🧪 Running Tests

To ensure everything is working correctly, run the test suite:

```bash
# Run all tests
pytest

# Run tests with more detail
pytest -v

# Run specific test file
pytest tests/test_molar_mass.py
pytest tests/test_gibbs.py
```

### Test Coverage
- **Molar Mass**: H₂O ≈ 18.015 g/mol, C₆H₁₂O₆ ≈ 180.156 g/mol
- **Gibbs**: ΔH = -100 kJ/mol, ΔS = 200 J/(mol·K), T = 298.15 K → ΔG ≈ -159.63 kJ/mol

## 🔧 Technical Details

### Core Technologies
- **Streamlit**: Web application framework
- **Pint**: Unit handling and dimensional analysis
- **PeriodicTable**: Comprehensive periodic table data library
- **NumPy**: Numerical computations
- **Pytest**: Testing framework

### Key Features
- **Type Hints**: Full type annotations for better code quality
- **Error Handling**: Comprehensive error messages and validation
- **Unit Conversion**: Automatic conversion between common chemistry units
- **Significant Figures**: Consistent rounding and display formatting
- **Step-by-Step Solutions**: Educational approach with detailed work shown

### Data Sources
- **Periodic Table**: `periodictable` for atomic masses and formula parsing
- **thermo**: Used to augment ΔHf° values and derive van der Waals a,b from critical constants when CSV does not provide them. See `thermo` on PyPI: https://pypi.org/project/thermo/
- **Constants**: R (J/mol·K), R (L·atm/mol·K), Faraday constant F stored in `data/constants.json`

## 📚 Educational Value

This calculator is designed to help students:
- **Understand the process**: See step-by-step solutions
- **Learn unit conversions**: Automatic handling of different units
- **Practice with real examples**: Use actual chemical formulas and values
- **Build intuition**: Visual feedback on reaction spontaneity and temperature dependence

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure you're in the correct directory (`chem_calc`)
   - Check that all dependencies are installed: `pip list`

2. **Data File Errors**
   - Verify `data/constants.json` exists
   - Check file permissions

3. **Streamlit Issues**
   - Update Streamlit: `pip install --upgrade streamlit`
   - Clear Streamlit cache: `streamlit cache clear`

### Getting Help
- Check the test files for examples of correct usage
- Verify your Python environment has all required packages
- Ensure you're using Python 3.8+ for type hint compatibility

## 🔮 Future Enhancements

### Planned Features
- **Gas Laws Calculator**: PV=nRT, combined gas law, real gas equations
- **Solutions Calculator**: Molarity, molality, dilution problems
- **Kinetics Calculator**: Rate laws, half-life, Arrhenius equation
- **Equilibrium Calculator**: Kc, Kp, ICE tables
- **Electrochemistry**: Nernst equation, cell potentials

### Contributing
This project is designed to be educational and extensible. Feel free to:
- Add new calculators
- Improve existing calculations
- Enhance the user interface
- Add more test cases

## 📄 License

This project is open source and available under the MIT License.

---

**Happy Calculating! 🧪✨**
