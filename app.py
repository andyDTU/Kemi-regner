"""
Chemistry Calculator - Streamlit App
A comprehensive chemistry calculator for high school and introductory university students.
"""

import streamlit as st
import pandas as pd
from pathlib import Path

# Import calculators
from calculators.molar_mass import calculate_molar_mass_with_steps, format_composition_table
from calculators.gibbs import calculate_gibbs_free_energy_with_steps, analyze_gibbs_temperature_dependence
from calculators.stoichiometry import calculate_limiting_reagent_with_steps, calculate_dilution_with_steps
from calculators.acids_bases import (
    calculate_strong_acid_ph, calculate_strong_base_ph, calculate_strong_acid_base_mixture,
    calculate_weak_acid_ph, calculate_weak_base_ph, calculate_buffer_ph,
    calculate_buffer_mixing_ph, calculate_target_buffer_ratio,
    calculate_titration_strong_acid_strong_base, calculate_titration_weak_acid_strong_base
)
from calculators.equilibrium import (
    solve_ice_table_with_steps, convert_equilibrium_constants_with_steps,
    calculate_reaction_quotient_with_steps, calculate_solubility_with_steps,
    calculate_solubility_product_with_steps
)
from core.reaction import balance_equation

# Page configuration
st.set_page_config(
    page_title="Chemistry Calculator",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Main application function."""
    
    # Sidebar navigation
    st.sidebar.title("🧪 Chemistry Calculator")
    st.sidebar.markdown("---")
    
    # Navigation options
    page = st.sidebar.radio(
        "Select Calculator:",
         ["🏠 Fundamentals", "⚖️ Atoms & Molar Mass", "🔥 Thermochemistry (Gibbs)", "🌡️ Thermochemistry", 
         "🧮 Stoichiometry", "🧪 Acids & Bases", "⚖️ Equilibrium", 
         "📊 Gases", "🧪 Colligative Properties", "⚗️ Solutions", "⚡ Kinetics", "🔋 Electrochemistry"]
    )
    
    # Main content area
    if page == "🏠 Fundamentals":
        show_fundamentals_page()
    elif page == "⚖️ Atoms & Molar Mass":
        show_molar_mass_page()
    elif page == "🔥 Thermochemistry (Gibbs)":
        show_gibbs_page()
    elif page == "🧮 Stoichiometry":
        show_stoichiometry_page()
    elif page == "🧪 Acids & Bases":
        show_acids_bases_page()
    elif page == "⚖️ Equilibrium":
        show_equilibrium_page()
    elif page == "📊 Gases":
        show_gas_laws_page()
    elif page == "🌡️ Thermochemistry":
        show_thermochemistry_page()
    elif page == "🧪 Colligative Properties":
        show_colligatives_page()
    elif page == "⚗️ Solutions":
        show_solutions_page()
    elif page == "⚗️ Solutions":
        show_solutions_page()
    elif page == "⚡ Kinetics":
        show_kinetics_page()
    elif page == "🔋 Electrochemistry":
        show_electrochemistry_page()

def show_fundamentals_page():
    """Display the fundamentals page."""
    st.title("🏠 Chemistry Calculator Fundamentals")
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ## Welcome to Chemistry Calculator!
        
        This application provides comprehensive tools for chemistry calculations commonly encountered in high school and introductory university courses.
        
        ### Available Calculators:
        
        **⚖️ Atoms & Molar Mass**
        - Calculate molar masses of compounds
        - Determine percentage composition
        - Handle complex formulas with parentheses
        
        **🔥 Thermochemistry (Gibbs)**
        - Calculate Gibbs free energy changes
        - Determine reaction spontaneity
        - Analyze temperature dependence
        
        **🧮 Stoichiometry**
        - Balance chemical equations
        - Calculate limiting reagents and theoretical yields
        - Solve dilution problems
        
        **🧪 Acids & Bases**
        - Strong/weak acid/base pH calculations
        - Buffer solutions and Henderson-Hasselbalch
        - Titration point calculations
        
        **⚖️ Equilibrium**
        - ICE table solver
        - Kc/Kp conversions
        - Reaction quotient and solubility
        
        **📊 Gas Laws** (Coming Soon)
        - Ideal gas law calculations
        - Combined gas law
        - Van der Waals equation
        
        **⚗️ Solutions** (Coming Soon)
        - Molarity calculations
        - Dilution problems
        - Concentration conversions
        
        **⚡ Kinetics** (Coming Soon)
        - Rate law calculations
        - Half-life problems
        - Activation energy
        """)
    
    with col2:
        st.markdown("""
        ### Quick Tips:
        
        - Use the sidebar to navigate between calculators
        - All calculations show step-by-step solutions
        - Units are automatically converted as needed
        - Results are displayed with appropriate significant figures
        
        ### Getting Started:
        
        1. Select a calculator from the sidebar
        2. Enter your values with appropriate units
        3. Click Calculate to see results
        4. Expand "Show Steps" to see detailed work
        """)
        
        # Example calculations
        st.markdown("### Example Calculations:")
        
        if st.button("Calculate H₂O Molar Mass"):
            try:
                result, steps, metadata = calculate_molar_mass_with_steps("H2O")
                st.success(f"H₂O Molar Mass: {result:.3f} g/mol")
            except Exception as e:
                st.error(f"Error: {e}")
        
        if st.button("Calculate Gibbs Example"):
            try:
                result, steps, metadata = calculate_gibbs_free_energy_with_steps(
                    -100, "kJ/mol", 200, "J/(mol·K)", 298.15, "K"
                )
                st.success(f"ΔG: {result:.2f} kJ/mol")
            except Exception as e:
                st.error(f"Error: {e}")

def show_molar_mass_page():
    """Display the molar mass calculator page."""
    st.title("⚖️ Molar Mass Calculator")
    st.markdown("---")
    
    # Input section
    st.markdown("### Enter Chemical Formula")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        formula = st.text_input(
            "Chemical Formula:",
            placeholder="e.g., C6H12O6, Fe2(SO4)3, Ca(OH)2",
            help="Enter a chemical formula. Supports parentheses and subscripts."
        )
    
    with col2:
        st.markdown("### Examples:")
        st.markdown("- **H₂O** (water)")
        st.markdown("- **C₆H₁₂O₆** (glucose)")
        st.markdown("- **Fe₂(SO₄)₃** (iron sulfate)")
        st.markdown("- **Ca(OH)₂** (calcium hydroxide)")
    
    # Calculate button
    if st.button("Calculate Molar Mass", type="primary"):
        if not formula:
            st.error("Please enter a chemical formula.")
        else:
            try:
                with st.spinner("Calculating..."):
                    result, steps, metadata = calculate_molar_mass_with_steps(formula)
                
                # Results section
                st.success(f"✅ **Molar Mass: {result:.3f} g/mol**")
                
                # Composition table
                if 'composition' in metadata:
                    st.markdown("### Elemental Composition")
                    composition_table = format_composition_table(metadata['composition'])
                    st.markdown(composition_table)
                
                # Steps section
                with st.expander("🔍 Show Steps", expanded=False):
                    for step in steps:
                        st.markdown(step)
                
                # Additional information
                if 'element_counts' in metadata:
                    st.markdown("### Element Counts")
                    element_counts_df = pd.DataFrame([
                        {"Element": element, "Count": count}
                        for element, count in metadata['element_counts'].items()
                    ])
                    st.dataframe(element_counts_df, use_container_width=True)
                
            except Exception as e:
                st.error(f"❌ **Error**: {str(e)}")
                st.info("Please check your formula and try again.")

def show_gibbs_page():
    """Display the Gibbs free energy calculator page."""
    st.title("🔥 Gibbs Free Energy Calculator")
    st.markdown("---")
    
    st.markdown("""
    Calculate the Gibbs free energy change (ΔG) for a reaction using the equation:
    
    **ΔG = ΔH - TΔS**
    
    Where:
    - ΔG = Gibbs free energy change
    - ΔH = Enthalpy change
    - T = Temperature
    - ΔS = Entropy change
    """)
    
    # Input section
    st.markdown("### Enter Reaction Parameters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Enthalpy Change (ΔH)")
        delta_h = st.number_input(
            "ΔH Value:",
            value=-100.0,
            step=0.1,
            format="%.1f"
        )
        delta_h_unit = st.selectbox(
            "ΔH Unit:",
            ["kJ/mol", "J/mol", "cal/mol", "kcal/mol"],
            index=0
        )
        
        st.markdown("#### Temperature (T)")
        temperature = st.number_input(
            "Temperature Value:",
            value=298.15,
            step=0.1,
            format="%.3f"
        )
        temp_unit = st.selectbox(
            "Temperature Unit:",
            ["K", "°C"],
            index=0
        )
    
    with col2:
        st.markdown("#### Entropy Change (ΔS)")
        delta_s = st.number_input(
            "ΔS Value:",
            value=200.0,
            step=0.1,
            format="%.1f"
        )
        delta_s_unit = st.selectbox(
            "ΔS Unit:",
            ["J/(mol·K)", "kJ/(mol·K)", "cal/(mol·K)"],
            index=0
        )
        
        st.markdown("#### Quick Examples:")
        if st.button("Example 1: Spontaneous"):
            st.session_state.delta_h = -100.0
            st.session_state.delta_s = 200.0
            st.session_state.temperature = 298.15
            st.rerun()
        
        if st.button("Example 2: Non-spontaneous"):
            st.session_state.delta_h = 40.0
            st.session_state.delta_s = 100.0
            st.session_state.temperature = 298.15
            st.rerun()
    
    # Calculate button
    if st.button("Calculate ΔG", type="primary"):
        try:
            with st.spinner("Calculating..."):
                result, steps, metadata = calculate_gibbs_free_energy_with_steps(
                    delta_h, delta_h_unit, delta_s, delta_s_unit, temperature, temp_unit
                )
            
            # Results section
            st.success(f"✅ **ΔG = {result:.2f} kJ/mol**")
            
            # Spontaneity indicator
            spontaneity = metadata.get('spontaneity', 'unknown')
            if spontaneity == 'spontaneous':
                st.success("🟢 **Reaction is SPONTANEOUS** at this temperature")
            elif spontaneity == 'non-spontaneous':
                st.warning("🔴 **Reaction is NON-SPONTANEOUS** at this temperature")
            else:
                st.info("⚖️ **Reaction is at EQUILIBRIUM** at this temperature")
            
            # Crossover temperature
            if metadata.get('crossover_temperature_k'):
                t_eq = metadata['crossover_temperature_k']
                st.info(f"🌡️ **Crossover Temperature**: {t_eq:.1f} K")
                if t_eq < 1000:
                    st.info(f"🌡️ **Crossover Temperature**: {t_eq - 273.15:.1f}°C")
            
            # Steps section
            with st.expander("🔍 Show Steps", expanded=False):
                for step in steps:
                    st.markdown(step)
            
            # Temperature dependence analysis
            with st.expander("📈 Temperature Dependence Analysis", expanded=False):
                analysis_steps, analysis_metadata = analyze_gibbs_temperature_dependence(
                    delta_h, delta_h_unit, delta_s, delta_s_unit
                )
                for step in analysis_steps:
                    st.markdown(step)
            
        except Exception as e:
            st.error(f"❌ **Error**: {str(e)}")
            st.info("Please check your inputs and try again.")

def show_stoichiometry_page():
    """Display the stoichiometry calculator page."""
    st.title("🧮 Stoichiometry Calculator")
    st.markdown("---")
    
    # Create tabs for different stoichiometry calculations
    tab1, tab2, tab3 = st.tabs(["⚖️ Balance Reaction", "🔬 Limiting Reagent & Yields", "💧 Dilution"])
    
    with tab1:
        show_reaction_balancing_tab()
    
    with tab2:
        show_limiting_reagent_tab()
    
    with tab3:
        show_dilution_tab()


def show_reaction_balancing_tab():
    """Display the reaction balancing tab."""
    st.markdown("### ⚖️ Balance Chemical Reaction")
    
    # Input section
    equation = st.text_input(
        "Chemical Equation:",
        placeholder="e.g., Fe2(SO4)3 + KOH -> Fe(OH)3 + K2SO4",
        help="Enter a chemical equation. Use ->, =>, or = as arrow. Supports + as separator."
    )
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if st.button("Balance Equation", type="primary"):
            if not equation:
                st.error("Please enter a chemical equation.")
            else:
                try:
                    with st.spinner("Balancing equation..."):
                        result = balance_equation(equation)
                    
                    # Results section
                    st.success("✅ **Equation Balanced Successfully!**")
                    
                    # Display balanced equation
                    st.markdown(f"**Balanced Equation:** {result['equation_str']}")
                    
                    # Show coefficients
                    st.markdown("**Coefficients:**")
                    for i, species in enumerate(result['species_order']):
                        coeff = result['coefficients'][i]
                        st.markdown(f"- {species}: {coeff}")
                    
                    # Steps section
                    with st.expander("🔍 Show Steps", expanded=False):
                        for step in result['steps']:
                            st.markdown(step)
                    
                except Exception as e:
                    st.error(f"❌ **Error**: {str(e)}")
                    st.info("Please check your equation and try again.")
    
    with col2:
        st.markdown("### Examples:")
        st.markdown("- **Fe₂(SO₄)₃ + KOH → Fe(OH)₃ + K₂SO₄**")
        st.markdown("- **C₂H₅OH + O₂ → CO₂ + H₂O**")
        st.markdown("- **H₂ + O₂ → H₂O**")
        st.markdown("- **N₂ + H₂ → NH₃**")


def show_limiting_reagent_tab():
    """Display the limiting reagent tab."""
    st.markdown("### 🔬 Limiting Reagent & Theoretical Yield")
    
    # Input section
    equation = st.text_input(
        "Chemical Equation:",
        placeholder="e.g., N2 + H2 -> NH3",
        help="Enter a chemical equation. It will be automatically balanced."
    )
    
    if equation:
        try:
            # Parse the equation to get reactants and products
            from core.reaction import parse_reaction_equation
            parsed = parse_reaction_equation(equation)
            reactants = parsed['reactants']
            products = parsed['products']
            
            st.markdown(f"**Reactants:** {', '.join(reactants)}")
            st.markdown(f"**Products:** {', '.join(products)}")
            
            # Reactant inputs
            st.markdown("#### Reactant Quantities")
            reactant_inputs = []
            
            for i, reactant in enumerate(reactants):
                st.markdown(f"**{reactant}:**")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    mode = st.selectbox(
                        "Mode:",
                        ["mass", "moles", "solution"],
                        key=f"mode_{i}"
                    )
                
                with col2:
                    if mode == "mass":
                        value = st.number_input("Mass (g):", value=10.0, step=0.1, key=f"value_{i}")
                        unit = "g"
                    elif mode == "moles":
                        value = st.number_input("Moles:", value=1.0, step=0.1, key=f"value_{i}")
                        unit = "mol"
                    else:  # solution
                        value = st.number_input("Molarity (M):", value=1.0, step=0.1, key=f"value_{i}")
                        unit = "M"
                
                with col3:
                    if mode == "solution":
                        volume = st.number_input("Volume (mL):", value=100, step=1, key=f"volume_{i}")
                    else:
                        volume = None
                
                with col4:
                    st.markdown("")  # Spacer
                
                reactant_inputs.append({
                    'formula': reactant,
                    'mode': mode,
                    'value': value,
                    'unit': unit,
                    'volume': volume
                })
            
            # Target product selection
            st.markdown("#### Target Product")
            target_product = st.selectbox(
                "Select target product for yield calculation:",
                products,
                key="target_product"
            )
            
            # Actual yield (optional)
            actual_yield = st.number_input(
                "Actual yield (g) - optional:",
                value=None,
                step=0.01,
                help="Leave empty if you only want theoretical yield"
            )
            
            # Calculate button
            if st.button("Calculate Limiting Reagent & Yield", type="primary"):
                try:
                    with st.spinner("Calculating..."):
                        result, steps, metadata = calculate_limiting_reagent_with_steps(
                            equation, reactant_inputs, target_product, actual_yield
                        )
                    
                    # Results section
                    st.success("✅ **Calculation Complete!**")
                    
                    # Key results
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Limiting Reagent:** {result['limiting_reagent']}")
                        st.markdown(f"**Theoretical Yield:** {result['theoretical_yield_moles']:.4f} mol")
                        st.markdown(f"**Theoretical Yield:** {result['theoretical_yield_mass']:.3f} g")
                    
                    with col2:
                        if result['percent_yield']:
                            st.markdown(f"**Percent Yield:** {result['percent_yield']:.1f}%")
                        
                        # Excess reactants
                        if result['excess_data']:
                            st.markdown("**Excess Reactants:**")
                            for reactant, excess in result['excess_data'].items():
                                if excess['moles_excess'] > 0:
                                    st.markdown(f"- {reactant}: {excess['moles_excess']:.4f} mol ({excess['mass_excess']:.3f} g)")
                    
                    # Steps section
                    with st.expander("🔍 Show Steps", expanded=False):
                        for step in steps:
                            st.markdown(step)
                    
                except Exception as e:
                    st.error(f"❌ **Error**: {str(e)}")
                    st.info("Please check your inputs and try again.")
        
        except Exception as e:
            st.error(f"❌ **Error parsing equation**: {str(e)}")


def show_dilution_tab():
    """Display the dilution calculator tab."""
    st.markdown("### 💧 Dilution Calculator (M₁V₁ = M₂V₂)")
    
    st.markdown("""
    Solve for any one variable in the dilution equation: **M₁V₁ = M₂V₂**
    
    Where:
    - M₁ = Initial concentration
    - V₁ = Initial volume
    - M₂ = Final concentration
    - V₂ = Final volume
    """)
    
    # Input section
    st.markdown("#### Select the unknown variable:")
    unknown = st.radio(
        "Unknown:",
        ["M₁ (Initial concentration)", "V₁ (Initial volume)", 
         "M₂ (Final concentration)", "V₂ (Final volume)"],
        horizontal=True
    )
    
    # Create input fields based on selection
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Initial Values:**")
        if unknown != "M₁ (Initial concentration)":
            m1 = st.number_input("M₁ (Initial concentration):", value=2.0, step=0.1)
            m1_unit = st.selectbox("M₁ unit:", ["M", "mM", "μM"], key="m1_unit")
        else:
            m1 = None
            m1_unit = "M"
        
        if unknown != "V₁ (Initial volume)":
            v1 = st.number_input("V₁ (Initial volume):", value=100.0, step=0.1)
            v1_unit = st.selectbox("V₁ unit:", ["mL", "L"], key="v1_unit")
        else:
            v1 = None
            v1_unit = "mL"
    
    with col2:
        st.markdown("**Final Values:**")
        if unknown != "M₂ (Final concentration)":
            m2 = st.number_input("M₂ (Final concentration):", value=0.25, step=0.01)
            m2_unit = st.selectbox("M₂ unit:", ["M", "mM", "μM"], key="m2_unit")
        else:
            m2 = None
            m2_unit = "M"
        
        if unknown != "V₂ (Final volume)":
            v2 = st.number_input("V₂ (Final volume):", value=250.0, step=0.1)
            v2_unit = st.selectbox("V₂ unit:", ["mL", "L"], key="v2_unit")
        else:
            v2 = None
            v2_unit = "L"
    
    # Calculate button
    if st.button("Calculate", type="primary"):
        try:
            with st.spinner("Calculating..."):
                result, steps, metadata = calculate_dilution_with_steps(
                    m1=m1, v1=v1, m2=m2, v2=v2,
                    m1_unit=m1_unit, v1_unit=v1_unit,
                    m2_unit=m2_unit, v2_unit=v2_unit
                )
            
            # Results section
            st.success("✅ **Calculation Complete!**")
            
            # Display result
            unknown_symbol = result['unknown']
            result_value = result['result']
            result_unit = result['result_unit']
            
            st.markdown(f"**{unknown_symbol} = {result_value:.6f} {result_unit}**")
            
            # Steps section
            with st.expander("🔍 Show Steps", expanded=False):
                for step in steps:
                    st.markdown(step)
        
        except Exception as e:
            st.error(f"❌ **Error**: {str(e)}")
            st.info("Please check your inputs and try again.")


def show_acids_bases_page():
    """Display the acids and bases calculator page."""
    st.title("🧪 Acids & Bases Calculator")
    st.markdown("---")
    
    # Create tabs for different calculators
    tab1, tab2, tab3, tab4 = st.tabs([
        "Strong Acids/Bases", "Weak Acids/Bases", "Buffers", "Titrations"
    ])
    
    with tab1:
        show_strong_acids_bases_tab()
    
    with tab2:
        show_weak_acids_bases_tab()
    
    with tab3:
        show_buffers_tab()
    
    with tab4:
        show_titrations_tab()


def show_strong_acids_bases_tab():
    """Display the strong acids/bases tab."""
    st.markdown("### 💪 Strong Acids & Bases")
    
    # Mode selection
    mode = st.radio(
        "Calculation Mode:",
        ["Single strong acid", "Single strong base", "Mixture of strong acid + base"],
        horizontal=True
    )
    
    if mode == "Single strong acid":
        st.markdown("#### Strong Acid pH")
        concentration = st.number_input("Acid concentration (M):", value=0.1, step=0.01, min_value=1e-7)
        volume = st.number_input("Volume (L):", value=1.0, step=0.1, min_value=0.001)
        
        if st.button("Calculate pH", type="primary"):
            try:
                with st.spinner("Calculating..."):
                    ph, steps, metadata = calculate_strong_acid_ph(concentration, volume)
                
                st.success(f"✅ **pH = {ph:.3f}**")
                
                with st.expander("🔍 Show Steps", expanded=False):
                    for step in steps:
                        st.markdown(step)
            
            except Exception as e:
                st.error(f"❌ **Error**: {str(e)}")
    
    elif mode == "Single strong base":
        st.markdown("#### Strong Base pH")
        concentration = st.number_input("Base concentration (M):", value=0.01, step=0.001, min_value=1e-7)
        volume = st.number_input("Volume (L):", value=1.0, step=0.1, min_value=0.001)
        
        if st.button("Calculate pH", type="primary"):
            try:
                with st.spinner("Calculating..."):
                    ph, steps, metadata = calculate_strong_base_ph(concentration, volume)
                
                st.success(f"✅ **pH = {ph:.3f}**")
                
                with st.expander("🔍 Show Steps", expanded=False):
                    for step in steps:
                        st.markdown(step)
            
            except Exception as e:
                st.error(f"❌ **Error**: {str(e)}")
    
    else:  # Mixture
        st.markdown("#### Strong Acid + Base Mixture")
        col1, col2 = st.columns(2)
        
        with col1:
            acid_conc = st.number_input("Acid concentration (M):", value=0.1, step=0.01, min_value=1e-7)
            acid_vol = st.number_input("Acid volume (L):", value=1.0, step=0.1, min_value=0.001)
        
        with col2:
            base_conc = st.number_input("Base concentration (M):", value=0.05, step=0.01, min_value=1e-7)
            base_vol = st.number_input("Base volume (L):", value=1.0, step=0.1, min_value=0.001)
        
        if st.button("Calculate pH", type="primary"):
            try:
                with st.spinner("Calculating..."):
                    ph, steps, metadata = calculate_strong_acid_base_mixture(
                        acid_conc, acid_vol, base_conc, base_vol
                    )
                
                st.success(f"✅ **pH = {ph:.3f}**")
                st.info(f"**Limiting species:** {metadata['limiting_species']}")
                
                with st.expander("🔍 Show Steps", expanded=False):
                    for step in steps:
                        st.markdown(step)
            
            except Exception as e:
                st.error(f"❌ **Error**: {str(e)}")


def show_weak_acids_bases_tab():
    """Display the weak acids/bases tab."""
    st.markdown("### 🥶 Weak Acids & Bases")
    
    # Mode selection
    mode = st.radio(
        "Calculation Mode:",
        ["Weak acid", "Weak base"],
        horizontal=True
    )
    
    if mode == "Weak acid":
        st.markdown("#### Weak Acid pH")
        concentration = st.number_input("Acid concentration (M):", value=0.1, step=0.01, min_value=1e-7)
        ka = st.number_input("Ka value:", value=1.8e-5, step=1e-6, min_value=1e-12, format="%.2e")
        
        if st.button("Calculate pH", type="primary"):
            try:
                with st.spinner("Calculating..."):
                    ph, steps, metadata = calculate_weak_acid_ph(concentration, ka)
                
                st.success(f"✅ **pH = {ph:.3f}**")
                st.info(f"**Percent ionization:** {metadata['percent_ionization']:.2f}%")
                
                with st.expander("🔍 Show Steps", expanded=False):
                    for step in steps:
                        st.markdown(step)
            
            except Exception as e:
                st.error(f"❌ **Error**: {str(e)}")
    
    else:  # Weak base
        st.markdown("#### Weak Base pH")
        concentration = st.number_input("Base concentration (M):", value=0.1, step=0.01, min_value=1e-7)
        
        kb_method = st.radio(
            "Kb input method:",
            ["Direct Kb value", "Ka of conjugate acid"],
            horizontal=True
        )
        
        if kb_method == "Direct Kb value":
            kb = st.number_input("Kb value:", value=1.8e-5, step=1e-6, min_value=1e-12, format="%.2e")
            ka_conjugate = None
        else:
            kb = None
            ka_conjugate = st.number_input("Ka of conjugate acid:", value=5.6e-10, step=1e-11, min_value=1e-12, format="%.2e")
        
        if st.button("Calculate pH", type="primary"):
            try:
                with st.spinner("Calculating..."):
                    ph, steps, metadata = calculate_weak_base_ph(
                        concentration, kb=kb, ka_conjugate=ka_conjugate
                    )
                
                st.success(f"✅ **pH = {ph:.3f}**")
                if 'percent_ionization' in metadata:
                    st.info(f"**Percent ionization:** {metadata['percent_ionization']:.2f}%")
                
                with st.expander("🔍 Show Steps", expanded=False):
                    for step in steps:
                        st.markdown(step)
            
            except Exception as e:
                st.error(f"❌ **Error**: {str(e)}")


def show_buffers_tab():
    """Display the buffers tab."""
    st.markdown("### 🧪 Buffer Solutions")
    
    # Mode selection
    mode = st.radio(
        "Buffer calculation mode:",
        ["Known concentrations", "Mixing solutions", "Target pH"],
        horizontal=True
    )
    
    if mode == "Known concentrations":
        st.markdown("#### Buffer pH from Concentrations")
        col1, col2 = st.columns(2)
        
        with col1:
            conc_a_minus = st.number_input("[A⁻] concentration (M):", value=0.1, step=0.01, min_value=1e-7)
            conc_ha = st.number_input("[HA] concentration (M):", value=0.1, step=0.01, min_value=1e-7)
        
        with col2:
            ka = st.number_input("Ka value:", value=1.8e-5, step=1e-6, min_value=1e-12, format="%.2e")
            pka = st.number_input("pKa value (optional):", value=None, step=0.01, help="Leave empty to calculate from Ka")
        
        if st.button("Calculate pH", type="primary"):
            try:
                with st.spinner("Calculating..."):
                    ph, steps, metadata = calculate_buffer_ph(
                        conc_a_minus, conc_ha, ka, pka
                    )
                
                st.success(f"✅ **pH = {ph:.3f}**")
                
                with st.expander("🔍 Show Steps", expanded=False):
                    for step in steps:
                        st.markdown(step)
            
            except Exception as e:
                st.error(f"❌ **Error**: {str(e)}")
    
    elif mode == "Mixing solutions":
        st.markdown("#### Buffer pH from Mixing")
        col1, col2 = st.columns(2)
        
        with col1:
            acid_conc = st.number_input("Weak acid concentration (M):", value=0.1, step=0.01, min_value=1e-7)
            acid_vol = st.number_input("Acid volume (L):", value=1.0, step=0.1, min_value=0.001)
        
        with col2:
            base_conc = st.number_input("Conjugate base concentration (M):", value=0.1, step=0.01, min_value=1e-7)
            base_vol = st.number_input("Base volume (L):", value=1.0, step=0.1, min_value=0.001)
            ka = st.number_input("Ka value:", value=1.8e-5, step=1e-6, min_value=1e-12, format="%.2e")
        
        if st.button("Calculate pH", type="primary"):
            try:
                with st.spinner("Calculating..."):
                    ph, steps, metadata = calculate_buffer_mixing_ph(
                        acid_conc, acid_vol, base_conc, base_vol, ka
                    )
                
                st.success(f"✅ **pH = {ph:.3f}**")
                
                with st.expander("🔍 Show Steps", expanded=False):
                    for step in steps:
                        st.markdown(step)
            
            except Exception as e:
                st.error(f"❌ **Error**: {str(e)}")
    
    else:  # Target pH
        st.markdown("#### Target Buffer pH")
        target_ph = st.number_input("Target pH:", value=5.0, step=0.1, min_value=0.0, max_value=14.0)
        pka = st.number_input("pKa value:", value=4.74, step=0.01)
        ka = st.number_input("Ka value (optional):", value=None, step=1e-6, format="%.2e", help="Leave empty to calculate from pKa")
        
        if st.button("Calculate Ratio", type="primary"):
            try:
                with st.spinner("Calculating..."):
                    ratio, steps, metadata = calculate_target_buffer_ratio(target_ph, pka, ka)
                
                st.success(f"✅ **[A⁻]/[HA] ratio = {ratio:.3f}**")
                st.info(f"**Target pH:** {target_ph:.1f}, **pKa:** {pka:.2f}")
                
                with st.expander("🔍 Show Steps", expanded=False):
                    for step in steps:
                        st.markdown(step)
            
            except Exception as e:
                st.error(f"❌ **Error**: {str(e)}")


def show_titrations_tab():
    """Display the titrations tab."""
    st.markdown("### 🧪 Titration Calculations")
    
    # Mode selection
    mode = st.radio(
        "Titration type:",
        ["Strong acid + Strong base", "Weak acid + Strong base"],
        horizontal=True
    )
    
    if mode == "Strong acid + Strong base":
        st.markdown("#### Strong Acid + Strong Base")
        col1, col2 = st.columns(2)
        
        with col1:
            acid_conc = st.number_input("Acid concentration (M):", value=0.1, step=0.01, min_value=1e-7)
            acid_vol = st.number_input("Acid volume (L):", value=1.0, step=0.1, min_value=0.001)
        
        with col2:
            base_conc = st.number_input("Base concentration (M):", value=0.1, step=0.01, min_value=1e-7)
            base_vol = st.number_input("Base volume (L):", value=1.0, step=0.1, min_value=0.001)
        
        if st.button("Calculate Titration Point", type="primary"):
            try:
                with st.spinner("Calculating..."):
                    ph, point_type, steps, metadata = calculate_titration_strong_acid_strong_base(
                        acid_conc, acid_vol, base_conc, base_vol
                    )
                
                st.success(f"✅ **pH = {ph:.3f}**")
                st.info(f"**Point type:** {point_type}")
                
                with st.expander("🔍 Show Steps", expanded=False):
                    for step in steps:
                        st.markdown(step)
            
            except Exception as e:
                st.error(f"❌ **Error**: {str(e)}")
    
    else:  # Weak acid + Strong base
        st.markdown("#### Weak Acid + Strong Base")
        col1, col2 = st.columns(2)
        
        with col1:
            acid_conc = st.number_input("Acid concentration (M):", value=0.1, step=0.01, min_value=1e-7)
            acid_vol = st.number_input("Acid volume (L):", value=1.0, step=0.1, min_value=0.001)
            ka = st.number_input("Ka value:", value=1.8e-5, step=1e-6, min_value=1e-12, format="%.2e")
        
        with col2:
            base_conc = st.number_input("Base concentration (M):", value=0.1, step=0.01, min_value=1e-7)
            base_vol = st.number_input("Base volume (L):", value=1.0, step=0.1, min_value=0.001)
        
        if st.button("Calculate Titration Point", type="primary"):
            try:
                with st.spinner("Calculating..."):
                    ph, point_type, steps, metadata = calculate_titration_weak_acid_strong_base(
                        acid_conc, acid_vol, ka, base_conc, base_vol
                    )
                
                st.success(f"✅ **pH = {ph:.3f}**")
                st.info(f"**Point type:** {point_type}")
                
                with st.expander("🔍 Show Steps", expanded=False):
                    for step in steps:
                        st.markdown(step)
            
            except Exception as e:
                st.error(f"❌ **Error**: {str(e)}")


def show_equilibrium_page():
    """Display the equilibrium calculator page."""
    st.title("⚖️ Equilibrium Calculator")
    st.markdown("---")
    
    # Create tabs for different calculators
    tab1, tab2, tab3, tab4 = st.tabs([
        "ICE Table Solver", "Kc/Kp Conversion", "Reaction Quotient", "Solubility"
    ])
    
    with tab1:
        show_ice_table_tab()
    
    with tab2:
        show_kc_kp_conversion_tab()
    
    with tab3:
        show_reaction_quotient_tab()
    
    with tab4:
        show_solubility_tab()


def show_ice_table_tab():
    """Display the ICE table solver tab."""
    st.markdown("### 🧊 ICE Table Solver")
    
    st.markdown("""
    Solve equilibrium problems using ICE (Initial, Change, Equilibrium) tables.
    
    Enter a balanced chemical reaction and initial concentrations.
    """)
    
    # Input section
    reaction = st.text_input(
        "Chemical Reaction:",
        placeholder="e.g., A + B -> C",
        help="Enter a balanced chemical reaction"
    )
    
    if reaction:
        try:
            # Parse the reaction to get species
            from core.reaction import parse_reaction_equation
            parsed = parse_reaction_equation(reaction)
            all_species = parsed['reactants'] + parsed['products']
            
            st.markdown(f"**Species:** {', '.join(all_species)}")
            
            # Initial concentrations
            st.markdown("#### Initial Concentrations (M)")
            initial_concentrations = {}
            
            for species in all_species:
                value = st.number_input(
                    f"[{species}]₀:",
                    value=0.0,
                    step=0.01,
                    min_value=0.0,
                    key=f"ice_initial_{species}"
                )
                initial_concentrations[species] = value
            
            # Equilibrium constant
            kc = st.number_input(
                "Kc value:",
                value=1.0,
                step=0.1,
                min_value=1e-20,
                format="%.2e"
            )
            
            # Calculate button
            if st.button("Solve ICE Table", type="primary"):
                try:
                    with st.spinner("Solving..."):
                        result, steps, metadata = solve_ice_table_with_steps(
                            reaction, initial_concentrations, kc
                        )
                    
                    st.success("✅ **ICE Table Solved!**")
                    
                    # Results
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Extent of reaction:** {result['extent']:.6f}")
                        st.markdown(f"**Direction:** {result['direction']}")
                    
                    with col2:
                        st.markdown("**Equilibrium concentrations:**")
                        for species, conc in result['equilibrium_concentrations'].items():
                            st.markdown(f"- [{species}] = {conc:.6f} M")
                    
                    # Steps section
                    with st.expander("🔍 Show Steps", expanded=False):
                        for step in steps:
                            st.markdown(step)
                
                except Exception as e:
                    st.error(f"❌ **Error**: {str(e)}")
        
        except Exception as e:
            st.error(f"❌ **Error parsing reaction**: {str(e)}")


def show_kc_kp_conversion_tab():
    """Display the Kc/Kp conversion tab."""
    st.markdown("### 🔄 Kc ↔ Kp Conversion")
    
    st.markdown("""
    Convert between concentration-based (Kc) and pressure-based (Kp) equilibrium constants.
    
    **Formula:** Kp = Kc × (RT)^Δn
    """)
    
    # Input section
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Known value:**")
        known_type = st.radio(
            "Convert from:",
            ["Kc to Kp", "Kp to Kc"],
            horizontal=True
        )
        
        if known_type == "Kc to Kp":
            kc = st.number_input("Kc value:", value=1.0, step=0.1, format="%.2e")
            kp = None
        else:
            kp = st.number_input("Kp value:", value=24.47, step=0.1, format="%.2e")
            kc = None
    
    with col2:
        st.markdown("**Conditions:**")
        temperature = st.number_input("Temperature (K):", value=298.15, step=1.0, min_value=0.1)
        delta_n = st.number_input("Δn (gas moles):", value=1, step=1, help="Change in gas moles: products - reactants")
    
    # Calculate button
    if st.button("Convert", type="primary"):
        try:
            with st.spinner("Converting..."):
                result, steps, metadata = convert_equilibrium_constants_with_steps(
                    kc=kc, kp=kp, temperature=temperature, delta_n=delta_n
                )
            
            st.success("✅ **Conversion Complete!**")
            
            # Results
            if known_type == "Kc to Kp":
                st.markdown(f"**Kp = {result['kp']:.6f}**")
            else:
                st.markdown(f"**Kc = {result['kc']:.6f}**")
            
            st.info(f"**Temperature:** {temperature:.1f} K, **Δn:** {delta_n}")
            
            # Steps section
            with st.expander("🔍 Show Steps", expanded=False):
                for step in steps:
                    st.markdown(step)
        
        except Exception as e:
            st.error(f"❌ **Error**: {str(e)}")


def show_reaction_quotient_tab():
    """Display the reaction quotient tab."""
    st.markdown("### 📊 Reaction Quotient (Q)")
    
    st.markdown("""
    Calculate the reaction quotient Q and compare it to the equilibrium constant K.
    
    **Q < K:** Reaction proceeds to products (right)
    **Q > K:** Reaction proceeds to reactants (left)
    **Q = K:** System is at equilibrium
    """)
    
    # Input section
    reaction = st.text_input(
        "Chemical Reaction:",
        placeholder="e.g., A + B -> C",
        help="Enter a balanced chemical reaction"
    )
    
    if reaction:
        try:
            # Parse the reaction to get species
            from core.reaction import parse_reaction_equation
            parsed = parse_reaction_equation(reaction)
            all_species = parsed['reactants'] + parsed['products']
            
            st.markdown(f"**Species:** {', '.join(all_species)}")
            
            # Current concentrations
            st.markdown("#### Current Concentrations (M)")
            current_concentrations = {}
            
            for species in all_species:
                value = st.number_input(
                    f"[{species}]:",
                    value=1.0,
                    step=0.1,
                    min_value=0.0,
                    key=f"quotient_current_{species}"
                )
                current_concentrations[species] = value
            
            # Equilibrium constant
            k = st.number_input(
                "Equilibrium constant K:",
                value=1.0,
                step=0.1,
                min_value=1e-20,
                format="%.2e"
            )
            
            # Calculate button
            if st.button("Calculate Q", type="primary"):
                try:
                    with st.spinner("Calculating..."):
                        result, steps, metadata = calculate_reaction_quotient_with_steps(
                            reaction, current_concentrations, k
                        )
                    
                    st.success("✅ **Reaction Quotient Calculated!**")
                    
                    # Results
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Q = {result['Q']:.6f}**")
                        st.markdown(f"**K = {k:.6f}**")
                    
                    with col2:
                        st.markdown(f"**Comparison:** {result['comparison']}")
                        st.markdown(f"**Direction:** {result['direction']}")
                    
                    # Steps section
                    with st.expander("🔍 Show Steps", expanded=False):
                        for step in steps:
                            st.markdown(step)
                
                except Exception as e:
                    st.error(f"❌ **Error**: {str(e)}")
        
        except Exception as e:
            st.error(f"❌ **Error parsing reaction**: {str(e)}")


def show_solubility_tab():
    """Display the solubility tab."""
    st.markdown("### 💧 Solubility Calculations")
    
    # Mode selection
    mode = st.radio(
        "Calculation mode:",
        ["Solubility from Ksp", "Ksp from solubility"],
        horizontal=True
    )
    
    if mode == "Solubility from Ksp":
        st.markdown("#### Calculate Solubility from Ksp")
        
        salt_formula = st.text_input(
            "Salt formula:",
            placeholder="e.g., AgCl, Ca(OH)2",
            help="Enter the chemical formula of the salt"
        )
        
        if salt_formula:
            ksp = st.number_input(
                "Ksp value:",
                value=1.8e-10,
                step=1e-11,
                min_value=1e-30,
                format="%.2e"
            )
            
            # Common ion effect
            st.markdown("**Common ion concentrations (optional):**")
            common_ion_input = st.text_input(
                "Common ions:",
                placeholder="e.g., Cl-:0.1, Na+:0.05",
                help="Format: ion:concentration, separate with commas"
            )
            
            common_ion_concentrations = {}
            if common_ion_input:
                try:
                    for pair in common_ion_input.split(','):
                        if ':' in pair:
                            ion, conc = pair.strip().split(':')
                            common_ion_concentrations[ion.strip()] = float(conc)
                except:
                    st.warning("Invalid common ion format. Using no common ions.")
            
            if st.button("Calculate Solubility", type="primary"):
                try:
                    with st.spinner("Calculating..."):
                        result, steps, metadata = calculate_solubility_with_steps(
                            salt_formula, ksp, common_ion_concentrations
                        )
                    
                    st.success("✅ **Solubility Calculated!**")
                    
                    # Results
                    st.markdown(f"**Molar solubility:** {result['solubility']:.6f} M")
                    
                    st.markdown("**Equilibrium concentrations:**")
                    for species, conc in result['equilibrium_concentrations'].items():
                        st.markdown(f"- [{species}] = {conc:.6f} M")
                    
                    # Steps section
                    with st.expander("🔍 Show Steps", expanded=False):
                        for step in steps:
                            st.markdown(step)
                
                except Exception as e:
                    st.error(f"❌ **Error**: {str(e)}")
    
    else:  # Ksp from solubility
        st.markdown("#### Calculate Ksp from Solubility")
        
        salt_formula = st.text_input(
            "Salt formula:",
            placeholder="e.g., AgCl, Ca(OH)2",
            help="Enter the chemical formula of the salt"
        )
        
        if salt_formula:
            solubility = st.number_input(
                "Solubility (M):",
                value=1.34e-5,
                step=1e-6,
                min_value=1e-20,
                format="%.2e"
            )
            
            if st.button("Calculate Ksp", type="primary"):
                try:
                    with st.spinner("Calculating..."):
                        result, steps, metadata = calculate_solubility_product_with_steps(
                            salt_formula, solubility
                        )
                    
                    st.success("✅ **Ksp Calculated!**")
                    
                    # Results
                    st.markdown(f"**Ksp = {result['ksp']:.2e}**")
                    
                    # Steps section
                    with st.expander("🔍 Show Steps", expanded=False):
                        for step in steps:
                            st.markdown(step)
                
                except Exception as e:
                    st.error(f"❌ **Error**: {str(e)}")


def show_gas_laws_page():
    """Display the gas laws calculator page."""
    st.title("📊 Gases Calculator")
    st.markdown("---")
    
    # Import gas laws functions
    from calculators.gases import (
        calculate_ideal_gas_law_with_steps,
        calculate_dalton_law_with_steps,
        calculate_gas_stoichiometry_with_steps,
        calculate_van_der_waals_with_steps
    )
    
    # Sidebar for calculator selection
    calculator = st.sidebar.selectbox(
        "Select Calculator:",
        ["Ideal Gas Law", "Dalton's Law", "Gas Stoichiometry", "van der Waals"]
    )
    
    if calculator == "Ideal Gas Law":
        st.markdown("### 🎈 Ideal Gas Law: PV = nRT")
        st.markdown("Calculate any one variable given the other three.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Input Variables:**")
            pressure = st.number_input(
                "Pressure:",
                value=None,
                placeholder="Enter pressure (leave empty to calculate)",
                help="Pressure value"
            )
            volume = st.number_input(
                "Volume:",
                value=None,
                placeholder="Enter volume (leave empty to calculate)",
                help="Volume value"
            )
        
        with col2:
            moles = st.number_input(
                "Moles:",
                value=None,
                placeholder="Enter moles (leave empty to calculate)",
                help="Number of moles"
            )
            temperature = st.number_input(
                "Temperature:",
                value=None,
                placeholder="Enter temperature",
                help="Temperature value"
            )
        
        # Unit selection
        col1, col2, col3 = st.columns(3)
        with col1:
            pressure_unit = st.selectbox("Pressure Unit:", ["atm", "bar", "kPa", "Pa"])
        with col2:
            volume_unit = st.selectbox("Volume Unit:", ["L", "mL", "m³"])
        with col3:
            temperature_unit = st.selectbox("Temperature Unit:", ["K", "°C"])
        
        if st.button("Calculate", type="primary"):
            try:
                # Count provided variables
                provided_vars = sum(1 for var in [pressure, volume, moles, temperature] if var is not None)
                if provided_vars != 3:
                    st.error("❌ **Error**: Exactly three variables must be provided to calculate the fourth.")
                else:
                    with st.spinner("Calculating..."):
                        result = calculate_ideal_gas_law_with_steps(
                            pressure=pressure, volume=volume, moles=moles, temperature=temperature,
                            pressure_unit=pressure_unit, volume_unit=volume_unit, temperature_unit=temperature_unit
                        )
                    
                    st.success(f"✅ **Result**: {result['result']:.4g} {result['unit']}")
                    
                    # Steps section
                    with st.expander("🔍 Show Steps", expanded=False):
                        st.markdown(result['steps'])
            
            except Exception as e:
                st.error(f"❌ **Error**: {str(e)}")
    
    elif calculator == "Dalton's Law":
        st.markdown("### 🌊 Dalton's Law of Partial Pressures")
        st.markdown("Calculate partial pressures from moles or mole fractions.")
        
        # Input method selection
        input_method = st.radio(
            "Input Method:",
            ["Moles", "Mole Fractions"]
        )
        
        if input_method == "Moles":
            st.markdown("**Enter species with moles:**")
            num_species = st.number_input("Number of species:", min_value=1, max_value=10, value=2)
            
            species_data = []
            for i in range(num_species):
                col1, col2 = st.columns(2)
                with col1:
                    name = st.text_input(f"Species {i+1} name:", value=f"Gas{i+1}")
                with col2:
                    moles = st.number_input(f"Moles of {name}:", value=1.0, min_value=0.0)
                species_data.append({"name": name, "moles": moles})
        else:
            st.markdown("**Enter species with mole fractions:**")
            num_species = st.number_input("Number of species:", min_value=1, max_value=10, value=2)
            
            species_data = []
            for i in range(num_species):
                col1, col2 = st.columns(2)
                with col1:
                    name = st.text_input(f"Species {i+1} name:", value=f"Gas{i+1}")
                with col2:
                    fraction = st.number_input(f"Mole fraction of {name}:", value=0.5, min_value=0.0, max_value=1.0)
                species_data.append({"name": name, "mole_fraction": fraction})
        
        total_pressure = st.number_input("Total pressure:", value=1.0, min_value=0.0)
        pressure_unit = st.selectbox("Pressure Unit:", ["atm", "bar", "kPa", "Pa"])
        
        # Collected over water option
        collected_over_water = st.checkbox("Collected over water")
        water_vapor_pressure = None
        if collected_over_water:
            water_vapor_pressure = st.number_input("Water vapor pressure:", value=0.05, min_value=0.0)
        
        if st.button("Calculate Partial Pressures", type="primary"):
            try:
                with st.spinner("Calculating..."):
                    result = calculate_dalton_law_with_steps(
                        species_data=species_data,
                        total_pressure=total_pressure,
                        pressure_unit=pressure_unit,
                        collected_over_water=collected_over_water,
                        water_vapor_pressure=water_vapor_pressure
                    )
                
                st.success("✅ **Partial Pressures Calculated!**")
                
                # Results
                st.markdown("**Partial Pressures:**")
                for pp in result['partial_pressures']:
                    st.markdown(f"- {pp['name']}: {pp['partial_pressure']:.4f} {pressure_unit}")
                
                if collected_over_water:
                    st.markdown(f"**Gas pressure (excluding water vapor)**: {result['gas_pressure']:.4f} {pressure_unit}")
                
                # Steps section
                with st.expander("🔍 Show Steps", expanded=False):
                    st.markdown(result['steps'])
            
            except Exception as e:
                st.error(f"❌ **Error**: {str(e)}")
    
    elif calculator == "Gas Stoichiometry":
        st.markdown("### ⚗️ Gas Stoichiometry")
        st.markdown("Calculate limiting reagent and theoretical gas product volume.")
        
        reaction = st.text_input(
            "Chemical Reaction:",
            placeholder="e.g., 2 H2 + O2 -> 2 H2O(g)",
            help="Enter the balanced chemical reaction"
        )
        
        if reaction:
            st.markdown("**Reactant Information:**")
            num_reactants = st.number_input("Number of reactants:", min_value=1, max_value=5, value=2)
            
            reactant_data = []
            for i in range(num_reactants):
                col1, col2, col3 = st.columns(3)
                with col1:
                    formula = st.text_input(f"Reactant {i+1} formula:", value=f"R{i+1}")
                with col2:
                    input_type = st.selectbox(f"Input type for {formula}:", ["Volume", "Mass"], key=f"type_{i}")
                with col3:
                    if input_type == "Volume":
                        value = st.number_input(f"Volume of {formula}:", value=1.0, min_value=0.0)
                        reactant_data.append({"formula": formula, "volume": value})
                    else:
                        value = st.number_input(f"Mass of {formula} (g):", value=1.0, min_value=0.0)
                        reactant_data.append({"formula": formula, "mass": value})
            
            col1, col2, col3 = st.columns(3)
            with col1:
                temperature = st.number_input("Temperature:", value=298.15, min_value=0.0)
            with col2:
                pressure = st.number_input("Pressure:", value=1.0, min_value=0.0)
            with col3:
                temperature_unit = st.selectbox("Temperature Unit:", ["K", "°C"])
            
            pressure_unit = st.selectbox("Pressure Unit:", ["atm", "bar", "kPa", "Pa"])
            volume_unit = st.selectbox("Volume Unit:", ["L", "mL", "m³"])
            
            if st.button("Calculate Stoichiometry", type="primary"):
                try:
                    with st.spinner("Calculating..."):
                        result = calculate_gas_stoichiometry_with_steps(
                            reaction=reaction,
                            reactant_data=reactant_data,
                            temperature=temperature,
                            pressure=pressure,
                            temperature_unit=temperature_unit,
                            pressure_unit=pressure_unit,
                            volume_unit=volume_unit
                        )
                    
                    st.success("✅ **Stoichiometry Calculated!**")
                    
                    # Results
                    st.markdown(f"**Limiting Reactant**: {result['limiting_reactant']['formula']}")
                    st.markdown(f"**Product Moles**: {result['product_moles']:.4f} mol")
                    st.markdown(f"**Product Volume**: {result['product_volume']:.4f} {volume_unit}")
                    
                    # Steps section
                    with st.expander("🔍 Show Steps", expanded=False):
                        st.markdown(result['steps'])
                
                except Exception as e:
                    st.error(f"❌ **Error**: {str(e)}")
    
    elif calculator == "van der Waals":
        st.markdown("### 🔬 van der Waals Equation")
        st.markdown("Calculate pressure using the van der Waals equation for real gases.")
        
        # Load available gases
        try:
            import pandas as pd
            vdw_path = Path(__file__).parent / "data" / "vdw_constants.csv"
            vdw_data = pd.read_csv(vdw_path)
            available_gases = vdw_data['gas'].tolist()
        except:
            available_gases = ["CO2", "N2", "O2"]
        
        col1, col2 = st.columns(2)
        
        with col1:
            gas = st.selectbox("Gas:", available_gases)
            moles = st.number_input("Moles:", value=1.0, min_value=0.0)
            volume = st.number_input("Volume:", value=1.0, min_value=0.0)
        
        with col2:
            temperature = st.number_input("Temperature:", value=298.15, min_value=0.0)
            volume_unit = st.selectbox("Volume Unit:", ["L", "mL", "m³"])
            temperature_unit = st.selectbox("Temperature Unit:", ["K", "°C"])
        
        pressure_unit = st.selectbox("Pressure Unit:", ["atm", "bar", "kPa", "Pa"])
        
        if st.button("Calculate van der Waals Pressure", type="primary"):
            try:
                with st.spinner("Calculating..."):
                    result = calculate_van_der_waals_with_steps(
                        gas=gas,
                        moles=moles,
                        volume=volume,
                        temperature=temperature,
                        volume_unit=volume_unit,
                        temperature_unit=temperature_unit,
                        pressure_unit=pressure_unit
                    )
                
                st.success("✅ **van der Waals Pressure Calculated!**")
                
                # Results
                st.markdown(f"**van der Waals Pressure**: {result['pressure_vdw']:.4f} {pressure_unit}")
                st.markdown(f"**Ideal Gas Pressure**: {result['pressure_ideal']:.4f} {pressure_unit}")
                st.markdown(f"**Compressibility Factor (Z)**: {result['compressibility_factor']:.4f}")
                
                # Steps section
                with st.expander("🔍 Show Steps", expanded=False):
                    st.markdown(result['steps'])
            
            except Exception as e:
                st.error(f"❌ **Error**: {str(e)}")

def show_solutions_page():
    """Display the solutions calculator page."""
    st.title("⚗️ Solutions")
    st.markdown("---")
    from calculators.solutions import (
        solve_molarity, grams_for_solution, volume_stock_for_dilution,
        solve_molality, percent_w_w, percent_v_v, percent_w_v,
        ppm_general, ppm_aqueous_from_mg_per_L, mix_solutions,
        mole_fraction_from_masses, mole_fraction_from_moles, ionic_strength
    )

    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "Molarity", "Make Solution", "Molality", "Percent", "ppm/ppb",
        "Mixing", "Mole Fraction", "Ionic Strength"
    ])

    with tab1:
        st.markdown("#### Molarity: M = n/V")
        unknown = st.selectbox("Unknown", ["M", "n", "V"], index=0)
        M = st.number_input("M (mol/L)", value=0.500)
        n = st.number_input("n (mol)", value=0.250)
        V = st.number_input("V (L)", value=0.500)
        if unknown == "M":
            M = None
        elif unknown == "n":
            n = None
        else:
            V = None
        if st.button("Solve Molarity", type="primary"):
            try:
                res, steps = solve_molarity(M, n, V)
                key = list(res.keys())[0]
                st.success(f"{key} = {res[key]:.6g}")
                with st.expander("Show steps"):
                    st.markdown(steps)
            except Exception as e:
                st.error(str(e))

    with tab2:
        st.markdown("#### Make a solution (from solid / from stock)")
        col1, col2 = st.columns(2)
        with col1:
            formula = st.text_input("Formula (solid)", value="NaCl")
            M_t = st.number_input("Target M (mol/L)", value=0.1000, format="%.4f")
            V_f = st.number_input("Final volume (L)", value=1.00, format="%.3f")
            if st.button("Grams from solid", type="primary"):
                try:
                    g, steps = grams_for_solution(formula, M_t, V_f)
                    st.success(f"grams = {g:.4g} g")
                    with st.expander("Show steps"):
                        st.markdown(steps)
                except Exception as e:
                    st.error(str(e))
        with col2:
            M_stock = st.number_input("Stock M (mol/L)", value=2.00, format="%.3f")
            if st.button("V_stock for dilution", type="primary"):
                try:
                    V1, steps = volume_stock_for_dilution(M_stock, M_t, V_f)
                    st.success(f"V_stock = {V1:.6g} L")
                    with st.expander("Show steps"):
                        st.markdown(steps)
                except Exception as e:
                    st.error(str(e))

    with tab3:
        st.markdown("#### Molality: m = n / kg_solvent")
        unknown = st.selectbox("Unknown (molality)", ["m", "n_mol", "m_solvent_kg"], index=0)
        m = st.number_input("m (mol/kg)", value=1.0)
        n = st.number_input("n (mol)", value=0.1)
        kg = st.number_input("kg solvent", value=0.1)
        if unknown == "m":
            m = None
        elif unknown == "n_mol":
            n = None
        else:
            kg = None
        if st.button("Solve Molality", type="primary"):
            try:
                res, steps = solve_molality(m, n, kg)
                key = list(res.keys())[0]
                st.success(f"{key} = {res[key]:.6g}")
                with st.expander("Show steps"):
                    st.markdown(steps)
            except Exception as e:
                st.error(str(e))

    with tab4:
        st.markdown("#### Percent concentration")
        mode = st.selectbox("Mode", ["w/w", "v/v", "w/v"]) 
        if mode == "w/w":
            unknown = st.selectbox("Unknown", ["%", "m_solute", "m_total"]) 
            a = st.number_input("m_solute (g) or %", value=10.0)
            b = st.number_input("m_total (g) or %", value=110.0)
            if st.button("Compute w/w%", type="primary"):
                try:
                    val, steps = percent_w_w(a, b, unknown)
                    st.success(f"Result = {val:.6g}")
                    with st.expander("Show steps"):
                        st.markdown(steps)
                except Exception as e:
                    st.error(str(e))
        elif mode == "v/v":
            unknown = st.selectbox("Unknown", ["%", "V_solute", "V_total"]) 
            a = st.number_input("V_solute (mL) or %", value=10.0)
            b = st.number_input("V_total (mL) or %", value=100.0)
            if st.button("Compute v/v%", type="primary"):
                try:
                    val, steps = percent_v_v(a, b, unknown)
                    st.success(f"Result = {val:.6g}")
                    with st.expander("Show steps"):
                        st.markdown(steps)
                except Exception as e:
                    st.error(str(e))
        else:
            unknown = st.selectbox("Unknown", ["%", "m_solute", "V_solution"]) 
            a = st.number_input("m_solute (g) or %", value=5.0)
            b = st.number_input("V_solution (mL) or %", value=100.0)
            if st.button("Compute w/v%", type="primary"):
                try:
                    val, steps = percent_w_v(a, b, unknown)
                    st.success(f"Result = {val:.6g}")
                    with st.expander("Show steps"):
                        st.markdown(steps)
                except Exception as e:
                    st.error(str(e))

    with tab5:
        st.markdown("#### ppm / ppb")
        basis = st.selectbox("Basis", ["mass", "volume"]) 
        sol = st.number_input("amount solute (same basis)", value=0.0500)
        tot = st.number_input("amount total (same basis)", value=2.00)
        unit = st.selectbox("Unit", ["ppm", "ppb"], index=0)
        if st.button("Compute ppm/ppb", type="primary"):
            try:
                val, steps = ppm_general(sol, tot, basis, unit)
                st.success(f"{unit} = {val:.6g}")
                with st.expander("Show steps"):
                    st.markdown(steps)
            except Exception as e:
                st.error(str(e))
        st.markdown("Aqueous shortcut: ppm ≈ mg/L")
        mgL = st.number_input("mg/L", value=25.0)
        if st.button("ppm from mg/L", type="primary"):
            try:
                val, steps = ppm_aqueous_from_mg_per_L(mgL)
                st.success(f"ppm = {val:.6g}")
                with st.expander("Show steps"):
                    st.markdown(steps)
            except Exception as e:
                st.error(str(e))

    with tab6:
        st.markdown("#### Mixing same-solute solutions")
        V1 = st.number_input("V1 (L)", value=0.100)
        M1 = st.number_input("M1 (mol/L)", value=1.000)
        V2 = st.number_input("V2 (L)", value=0.400)
        M2 = st.number_input("M2 (mol/L)", value=0.200)
        if st.button("Mix", type="primary"):
            try:
                Mf, steps = mix_solutions([V1, V2], [M1, M2])
                st.success(f"M_final = {Mf:.6g} M")
                with st.expander("Show steps"):
                    st.markdown(steps)
            except Exception as e:
                st.error(str(e))

    with tab7:
        st.markdown("#### Mole fraction (binary)")
        mode = st.selectbox("Input mode", ["masses+formulas", "moles"], index=0)
        if mode == "masses+formulas":
            formulaA = st.text_input("Formula A", value="NaCl")
            mA = st.number_input("m_A (g)", value=10.0)
            formulaB = st.text_input("Formula B", value="H2O")
            mB = st.number_input("m_B (g)", value=100.0)
            if st.button("Compute x", type="primary"):
                try:
                    xA, xB, steps = mole_fraction_from_masses(formulaA, mA, formulaB, mB)
                    st.success(f"x_A = {xA:.6g}, x_B = {xB:.6g}")
                    with st.expander("Show steps"):
                        st.markdown(steps)
                except Exception as e:
                    st.error(str(e))
        else:
            nA = st.number_input("n_A (mol)", value=0.171)
            nB = st.number_input("n_B (mol)", value=5.55)
            if st.button("Compute x from moles", type="primary"):
                from core.solutions import mole_fraction_from_moles
                try:
                    xA, xB, steps = mole_fraction_from_moles(nA, nB)
                    st.success(f"x_A = {xA:.6g}, x_B = {xB:.6g}")
                    with st.expander("Show steps"):
                        st.markdown(steps)
                except Exception as e:
                    st.error(str(e))

    with tab8:
        st.markdown("#### Ionic strength")
        name1 = st.text_input("Species 1 name", value="Na+")
        c1 = st.number_input("c1 (M)", value=0.200)
        z1 = st.number_input("z1 (charge)", value=1, step=1)
        name2 = st.text_input("Species 2 name", value="SO4^2-")
        c2 = st.number_input("c2 (M)", value=0.100)
        z2 = st.number_input("z2 (charge)", value=-2, step=1)
        if st.button("Compute I", type="primary"):
            try:
                I, steps = ionic_strength([(name1, c1, int(z1)), (name2, c2, int(z2))])
                st.success(f"I = {I:.6g}")
                with st.expander("Show steps"):
                    st.markdown(steps)
            except Exception as e:
                st.error(str(e))

def show_kinetics_page():
    """Display Kinetics calculators."""
    st.title("⚡ Kinetics")
    st.markdown("---")
    from calculators.kinetics import (
        calculate_integrated_rate_with_steps,
        calculate_half_life_with_steps,
        calculate_determine_order_k_with_steps,
        calculate_arrhenius_forward_with_steps,
        calculate_arrhenius_two_point_Ea_with_steps,
    )

    tab1, tab2, tab3, tab4 = st.tabs([
        "Integrated Rate Law",
        "Determine Order & k",
        "Arrhenius",
        "Rate Relationships",
    ])

    with tab1:
        st.markdown("#### Integrated Rate Law")
        order = st.selectbox("Order", [0, 1, 2], index=1)
        unknown = st.selectbox("Unknown", ["Ct", "C0", "k", "t"], index=0)
        C0 = st.number_input("C0 (M)", value=0.100, min_value=0.0)
        Ct = st.number_input("Ct (M)", value=0.010, min_value=0.0)
        k = st.number_input("k (units depend on order)", value=0.350, min_value=0.0)
        t = st.number_input("t (s)", value=10.0, min_value=0.0)
        if unknown == "Ct":
            Ct = None
        elif unknown == "C0":
            C0 = None
        elif unknown == "k":
            k = None
        else:
            t = None
        if st.button("Solve", type="primary"):
            try:
                val, steps, meta = calculate_integrated_rate_with_steps(order, C0, Ct, k, t)
                st.success(f"{unknown} = {val:.6g}")
                with st.expander("Show steps"):
                    for s in steps:
                        st.markdown(s)
            except Exception as e:
                st.error(str(e))

    with tab2:
        st.markdown("#### Determine Order & k (two-point)")
        col1, col2 = st.columns(2)
        with col1:
            t1 = st.number_input("t1 (s)", value=0.0, min_value=0.0)
            C1 = st.number_input("C1 (M)", value=0.100, min_value=1e-12, format="%.6f")
        with col2:
            t2 = st.number_input("t2 (s)", value=10.0, min_value=0.0)
            C2 = st.number_input("C2 (M)", value=0.003, min_value=1e-12, format="%.6f")
        if st.button("Determine", type="primary"):
            try:
                res, steps, meta = calculate_determine_order_k_with_steps(t1, C1, t2, C2)
                st.success(f"Order = {res['order']}, k = {res['k']:.6g}, residual = {res['residual']:.3e}")
                with st.expander("Show steps"):
                    for s in steps:
                        st.markdown(s)
            except Exception as e:
                st.error(str(e))

    with tab3:
        st.markdown("#### Arrhenius")
        st.markdown("Single-point forward")
        k1 = st.number_input("k1 (s^-1)", value=1.0e-3, format="%.6e")
        T1 = st.number_input("T1 (K)", value=298.15)
        T2 = st.number_input("T2 (K)", value=308.15)
        Ea = st.number_input("Ea (kJ/mol)", value=50.0)
        if st.button("Compute k2", type="primary"):
            try:
                k2, steps, _ = calculate_arrhenius_forward_with_steps(k1, T1, T2, Ea)
                st.success(f"k2 = {k2:.6g} s^-1")
                with st.expander("Show steps"):
                    for s in steps:
                        st.markdown(s)
            except Exception as e:
                st.error(str(e))
        st.markdown("Two-point Ea")
        k2v = st.number_input("k2 (s^-1)", value=3.0e-3, format="%.6e")
        if st.button("Compute Ea", type="primary"):
            try:
                Ea_kJ, steps, _ = calculate_arrhenius_two_point_Ea_with_steps(k1, T1, k2v, T2)
                st.success(f"Ea = {Ea_kJ:.4g} kJ/mol")
                with st.expander("Show steps"):
                    for s in steps:
                        st.markdown(s)
            except Exception as e:
                st.error(str(e))

    with tab4:
        st.markdown("#### Rate Relationships by Stoichiometry")
        st.info("Given a balanced reaction aA + bB -> cC + dD, rates relate as −(1/a)d[A]/dt = −(1/b)d[B]/dt = (1/c)d[C]/dt …")


def show_electrochemistry_page():
    st.title("🔋 Electrochemistry")
    st.markdown("---")
    from calculators.electrochemistry import (
        calculate_standard_cell_with_steps,
        calculate_nernst_with_steps,
        calculate_deltaG_from_E_with_steps,
        calculate_K_from_E0_with_steps,
        calculate_daniell_Q,
    )

    tab1, tab2, tab3 = st.tabs([
        "Build a Cell",
        "Nernst",
        "ΔG and K",
    ])

    with tab1:
        import pandas as pd
        from core.electrochem import load_reduction_potentials
        df = load_reduction_potentials()
        cath = st.selectbox("Cathode (reduction)", df['half_reaction'].tolist())
        an = st.selectbox("Anode (reduction)", df['half_reaction'].tolist())
        if st.button("Compute E°cell", type="primary"):
            try:
                res, steps, _ = calculate_standard_cell_with_steps(cath, an)
                st.success(f"E°cell = {res['E0_cell_V']:.4g} V, n = {res['n']}")
                with st.expander("Show steps"):
                    for s in steps:
                        st.markdown(s)
            except Exception as e:
                st.error(str(e))

    with tab2:
        st.markdown("#### Nernst Calculator")
        E0 = st.number_input("E°cell (V)", value=1.10)
        n = st.number_input("n (electrons)", value=2, min_value=1)
        T = st.number_input("T (K)", value=298.15, min_value=0.0)
        st.markdown("Quick Daniell helper: Q = [Zn2+]/[Cu2+]")
        Zn2 = st.number_input("[Zn2+] (M)", value=0.10, min_value=1e-12, format="%.4f")
        Cu2 = st.number_input("[Cu2+] (M)", value=1.00, min_value=1e-12, format="%.4f")
        Q = calculate_daniell_Q(Zn2, Cu2)
        st.info(f"Q = {Q:.6g}")
        if st.button("Compute E", type="primary"):
            try:
                E, steps, _ = calculate_nernst_with_steps(E0, int(n), T, Q)
                st.success(f"E = {E:.6g} V")
                with st.expander("Show steps"):
                    for s in steps:
                        st.markdown(s)
            except Exception as e:
                st.error(str(e))

    with tab3:
        st.markdown("#### ΔG and K relations")
        n = st.number_input("n", value=2, min_value=1, key="g_n")
        E0 = st.number_input("E° (V)", value=1.10, key="g_E0")
        T = st.number_input("T (K)", value=298.15, key="g_T")
        if st.button("Compute ΔG° and K", type="primary"):
            try:
                dG_kJ, _, _ = calculate_deltaG_from_E_with_steps(int(n), E0)
                K, log10K, steps, _ = calculate_K_from_E0_with_steps(int(n), E0, T)
                st.success(f"ΔG° = {dG_kJ:.4g} kJ/mol, log10 K = {log10K:.4g}")
                with st.expander("Show steps"):
                    for s in steps:
                        st.markdown(s)
            except Exception as e:
                st.error(str(e))

def show_thermochemistry_page():
    """Display new Thermochemistry calculators (Part 4)."""
    st.title("🌡️ Thermochemistry")
    st.markdown("---")

    from calculators.thermochemistry import (
        calculate_calorimetry_with_steps,
        calculate_heating_curve_water_with_steps,
        calculate_reaction_enthalpy_from_formation_with_steps,
        calculate_clausius_clapeyron_with_steps,
    )

    tab1, tab2, tab3, tab4 = st.tabs([
        "Calorimetry (q = m c ΔT)",
        "Heating/Cooling Curve",
        "ΔH from ΔHf° table",
        "Clausius–Clapeyron",
    ])

    with tab1:
        st.markdown("#### Calorimetry")
        col1, col2 = st.columns(2)
        with col1:
            mass_g = st.number_input("Mass (g)", value=100.0, min_value=0.0)
            preset = st.selectbox("Preset", ["water_ice", "water_liquid", "water_steam"], index=1)
            c_custom = st.number_input("Specific heat c (J/(g·K)) [optional]", value=0.0, min_value=0.0)
            c_val = None if c_custom == 0.0 else c_custom
        with col2:
            mode = st.radio("Temperature input", ["ΔT (K)", "T_initial/T_final (°C)"])
            if mode == "ΔT (K)":
                deltaT = st.number_input("ΔT (K)", value=25.0)
                T_i = None
                T_f = None
            else:
                T_i = st.number_input("T_initial (°C)", value=20.0)
                T_f = st.number_input("T_final (°C)", value=45.0)
                deltaT = None
            out_unit = st.selectbox("Output unit", ["kJ", "J"], index=0)

        if st.button("Calculate q", type="primary"):
            try:
                q_val, steps, meta = calculate_calorimetry_with_steps(
                    mass_g=mass_g,
                    delta_T_K=deltaT,
                    T_initial_C=T_i,
                    T_final_C=T_f,
                    c_J_per_gK=c_val,
                    preset=preset,
                    output_unit=out_unit,
                )
                st.success(f"q = {q_val:.4g} {out_unit}")
                with st.expander("Show steps"):
                    for s in steps:
                        st.markdown(s)
            except Exception as e:
                st.error(str(e))

    with tab2:
        st.markdown("#### Heating/Cooling Curve (Water)")
        mass_g = st.number_input("Mass (g)", value=10.0, min_value=0.0, key="hc_mass")
        T_i = st.number_input("T_initial (°C)", value=-10.0, key="hc_ti")
        T_f = st.number_input("T_final (°C)", value=110.0, key="hc_tf")
        if st.button("Calculate heating curve", type="primary"):
            try:
                q_kJ, steps, meta = calculate_heating_curve_water_with_steps(mass_g, T_i, T_f)
                st.success(f"Total q = {q_kJ:.4g} kJ")
                with st.expander("Show steps"):
                    for s in steps:
                        st.markdown(s)
            except Exception as e:
                st.error(str(e))

    with tab3:
        st.markdown("#### Reaction Enthalpy from ΔHf°")
        rxn = st.text_input("Reaction (balanced or not)", value="CH4 + 2 O2 -> CO2 + 2 H2O(l)")
        if st.button("Calculate ΔH_rxn", type="primary"):
            try:
                val, steps, meta = calculate_reaction_enthalpy_from_formation_with_steps(rxn)
                st.success(f"ΔH_rxn = {val:.4g} kJ/mol")
                with st.expander("Show steps"):
                    for s in steps:
                        st.markdown(s)
            except Exception as e:
                st.error(str(e))

    with tab4:
        st.markdown("#### Clausius–Clapeyron (two-point)")
        P1 = st.number_input("P1 (atm)", value=1.0)
        T1 = st.number_input("T1 (K)", value=373.15)
        T2 = st.number_input("T2 (K)", value=353.15)
        dHvap = st.number_input("ΔHvap (kJ/mol)", value=40.65)
        if st.button("Calculate P2", type="primary"):
            try:
                P2, steps, meta = calculate_clausius_clapeyron_with_steps(P1, T1, T2, dHvap)
                st.success(f"P2 = {P2:.4g} atm")
                with st.expander("Show steps"):
                    for s in steps:
                        st.markdown(s)
            except Exception as e:
                st.error(str(e))


def show_colligatives_page():
    """Display Colligative Properties calculators (Part 4)."""
    st.title("🧪 Colligative Properties")
    st.markdown("---")

    from calculators.colligatives import (
        freezing_boiling_with_steps,
        osmotic_pressure_with_steps,
        raoult_nonvolatile_with_steps,
        raoult_binary_with_steps,
    )

    tab1, tab2, tab3 = st.tabs([
        "ΔTf / ΔTb",
        "Osmotic Pressure",
        "Raoult's Law",
    ])

    with tab1:
        st.markdown("#### Freezing depression / Boiling elevation")
        i = st.number_input("van't Hoff factor i", value=1.0, min_value=0.0)
        mode = st.radio("Solute input", ["moles", "mass + molar mass"], horizontal=True)
        if mode == "moles":
            moles = st.number_input("Moles solute (mol)", value=1.0, min_value=0.0)
            mass = None
            mm = None
        else:
            mass = st.number_input("Mass solute (g)", value=58.44, min_value=0.0)
            mm = st.number_input("Molar mass (g/mol)", value=58.44, min_value=0.0)
            moles = None
        mass_solvent = st.number_input("Mass solvent (g)", value=1000.0, min_value=0.0)
        if st.button("Calculate ΔT", type="primary"):
            try:
                res, steps, meta = freezing_boiling_with_steps(
                    solvent="water",
                    moles_solute=moles,
                    mass_solute_g=mass,
                    molar_mass_solute_g_per_mol=mm,
                    mass_solvent_g=mass_solvent,
                    i=i,
                )
                st.success(f"ΔTf = {res['deltaTf_C']:.4g} °C, Tf = {res['Tf_C']:.4g} °C")
                st.success(f"ΔTb = {res['deltaTb_C']:.4g} °C, Tb = {res['Tb_C']:.4g} °C")
                with st.expander("Show steps"):
                    for s in steps:
                        st.markdown(s)
            except Exception as e:
                st.error(str(e))

    with tab2:
        st.markdown("#### Osmotic Pressure")
        mode = st.radio("Concentration input", ["Molarity", "moles + volume"], horizontal=True, key="osm_mode")
        if mode == "Molarity":
            M = st.number_input("Molarity (M)", value=0.100, min_value=0.0, key="osm_M")
            moles = None
            vol = None
        else:
            moles = st.number_input("Moles solute (mol)", value=0.010, min_value=0.0, key="osm_mol")
            vol = st.number_input("Solution volume (L)", value=0.100, min_value=0.0, key="osm_vol")
            M = None
        T = st.number_input("Temperature (K)", value=298.15)
        i = st.number_input("van't Hoff i", value=1.0, min_value=0.0, key="osm_i")
        if st.button("Calculate π", type="primary"):
            try:
                pi_atm, steps, meta = osmotic_pressure_with_steps(M, moles, vol, T, i)
                st.success(f"π = {pi_atm:.4g} atm")
                with st.expander("Show steps"):
                    for s in steps:
                        st.markdown(s)
            except Exception as e:
                st.error(str(e))

    with tab3:
        st.markdown("#### Raoult's Law")
        mode = st.radio("Case", ["Nonvolatile solute", "Volatile binary"], horizontal=True, key="ra_mode")
        if mode == "Nonvolatile solute":
            x_s = st.number_input("x_solvent", value=0.900, min_value=0.0, max_value=1.0)
            P_star = st.number_input("P*_solvent (kPa)", value=100.0, min_value=0.0)
            if st.button("Calculate P_solution", type="primary"):
                try:
                    P, steps, meta = raoult_nonvolatile_with_steps(x_s, P_star)
                    st.success(f"P_solution = {P:.4g} kPa")
                    with st.expander("Show steps"):
                        for s in steps:
                            st.markdown(s)
                except Exception as e:
                    st.error(str(e))
        else:
            x_A = st.number_input("x_A", value=0.500, min_value=0.0, max_value=1.0)
            P_A = st.number_input("P*_A (kPa)", value=80.0, min_value=0.0)
            x_B = 1.0 - x_A
            st.info(f"x_B auto = {x_B:.4f}")
            P_B = st.number_input("P*_B (kPa)", value=60.0, min_value=0.0)
            if st.button("Calculate P_total", type="primary"):
                try:
                    from calculators.colligatives import raoult_binary_with_steps
                    res, steps, meta = raoult_binary_with_steps(x_A, P_A, x_B, P_B)
                    st.success(f"P_total = {res['P_total']:.4g} kPa")
                    st.info(f"P_A = {res['P_A']:.4g} kPa, P_B = {res['P_B']:.4g} kPa")
                    with st.expander("Show steps"):
                        for s in steps:
                            st.markdown(s)
                except Exception as e:
                    st.error(str(e))

if __name__ == "__main__":
    main()
