import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext, messagebox

# Reuse existing calculation logic from the project
from calculators.molar_mass import (
    calculate_molar_mass_with_steps,
)
from calculators.gibbs import (
    calculate_gibbs_free_energy_with_steps,
)
from calculators.stoichiometry import (
    calculate_limiting_reagent_with_steps,
    calculate_dilution_with_steps,
)
from calculators.redox_balance import (
    balance_redox_with_steps,
)
from calculators.acids_bases import (
    calculate_strong_acid_ph,
    calculate_strong_base_ph,
    calculate_strong_acid_base_mixture,
    calculate_weak_acid_ph,
    calculate_weak_base_ph,
    calculate_buffer_ph,
    calculate_buffer_mixing_ph,
    calculate_target_buffer_ratio,
    calculate_titration_strong_acid_strong_base,
    calculate_titration_weak_acid_strong_base,
)
from calculators.gases import (
    calculate_ideal_gas_law_with_steps,
    calculate_dalton_law_with_steps,
    calculate_gas_stoichiometry_with_steps,
    calculate_van_der_waals_with_steps,
)
from pathlib import Path
import pandas as pd
import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image, ImageTk


def render_latex_to_photoimage(latex: str, fontsize: int = 18, dpi: int = 200) -> ImageTk.PhotoImage:
    """Render a LaTeX math string to a Tkinter PhotoImage using matplotlib and Pillow.

    Returns an ImageTk.PhotoImage which can be attached to a `ttk.Label` or similar.
    """
    fig = plt.figure()
    fig.text(0, 0, latex, fontsize=fontsize)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight", pad_inches=0.05, transparent=True)
    plt.close(fig)
    buf.seek(0)
    img = Image.open(buf)
    return ImageTk.PhotoImage(img)
from calculators.equilibrium import (
    solve_ice_table_with_steps,
    convert_equilibrium_constants_with_steps,
    calculate_reaction_quotient_with_steps,
    calculate_solubility_with_steps,
    calculate_solubility_product_with_steps,
)
from core.reaction import parse_reaction_equation, balance_equation
from calculators.thermochemistry import (
    calculate_calorimetry_with_steps,
    calculate_heating_curve_water_with_steps,
    calculate_reaction_enthalpy_from_formation_with_steps,
    calculate_clausius_clapeyron_with_steps,
)
from calculators.colligatives import (
    freezing_boiling_with_steps,
    osmotic_pressure_with_steps,
    raoult_nonvolatile_with_steps,
    raoult_binary_with_steps,
)
from calculators.solutions import (
    solve_molarity,
    grams_for_solution,
    volume_stock_for_dilution,
    solve_molality,
    percent_w_w,
    percent_v_v,
    percent_w_v,
    ppm_general,
    ppm_aqueous_from_mg_per_L,
    mix_solutions,
    mole_fraction_from_masses,
    mole_fraction_from_moles,
    ionic_strength,
)
from calculators.kinetics import (
    calculate_integrated_rate_with_steps,
    calculate_half_life_with_steps,
    calculate_determine_order_k_with_steps,
    calculate_arrhenius_forward_with_steps,
    calculate_arrhenius_two_point_Ea_with_steps,
)
from calculators.electrochemistry import (
    calculate_standard_cell_with_steps,
    calculate_nernst_with_steps,
    calculate_deltaG_from_E_with_steps,
    calculate_K_from_E0_with_steps,
    calculate_daniell_Q,
)


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Chemistry Calculator (Tkinter)")
        self.geometry("1100x720")

        # Root grid layout: sidebar (col 0) + content (col 1)
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self.sidebar = ttk.Frame(self, padding=12)
        self.sidebar.grid(row=0, column=0, sticky="ns")

        self.content = ttk.Frame(self, padding=12)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.rowconfigure(0, weight=1)
        self.content.columnconfigure(0, weight=1)

        # Register pages here: map name -> class
        self.pages: dict[str, type[ttk.Frame]] = {
            "🏠 Fundamentals": FundamentalsPage,
            "⚖️ Molar Mass": MolarMassPage,
            "🔥 Gibbs": GibbsPage,
            "🧪 Acids & Bases": AcidsBasesPage,
            "📊 Gases": GasesPage,
            "⚖️ Equilibrium": EquilibriumPage,
            "🌡️ Thermochemistry": ThermochemistryPage,
            "🧪 Colligative Properties": ColligativesPage,
            "⚗️ Solutions": SolutionsPage,
            "⚡ Kinetics": KineticsPage,
            "🔋 Electrochemistry": ElectrochemistryPage,
            # Extend incrementally:
            "🧮 Stoichiometry": StoichiometryPage,
            # "🧪 Acids & Bases": AcidsBasesPage,
            # "⚖️ Equilibrium": EquilibriumPage,
            # "📊 Gases": GasesPage,
            # "⚗️ Solutions": SolutionsPage,
            # "⚡ Kinetics": KineticsPage,
            # "🔋 Electrochemistry": ElectrochemistryPage,
        }

        self._build_sidebar()
        self.show_page("🏠 Fundamentals")

    def _build_sidebar(self) -> None:
        title = ttk.Label(
            self.sidebar,
            text="🧪 Chemistry Calculator",
            font=("Segoe UI", 12, "bold"),
        )
        title.pack(anchor="w", pady=(0, 8))

        for name in self.pages.keys():
            button = ttk.Button(self.sidebar, text=name, command=lambda n=name: self.show_page(n))
            button.pack(fill="x", pady=3)

        ttk.Separator(self.sidebar, orient="horizontal").pack(fill="x", pady=8)
        ttk.Label(self.sidebar, text="Tkinter prototype using existing engines", wraplength=200).pack(anchor="w")

    def show_page(self, name: str) -> None:
        # Clear current content
        for child in self.content.winfo_children():
            child.destroy()

        # Instantiate and show the requested page
        page_class = self.pages[name]
        page_instance = page_class(self.content)
        page_instance.grid(row=0, column=0, sticky="nsew")


class FundamentalsPage(ttk.Frame):
    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent)
        header = ttk.Label(self, text="🏠 Chemistry Calculator Fundamentals", font=("Segoe UI", 14, "bold"))
        header.pack(anchor="w")
        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=8)

        intro = (
            "This Tkinter version reuses the same calculation engine from calculators/core.\n"
            "Use the sidebar to switch between pages. Results and steps appear below inputs."
        )
        ttk.Label(self, text=intro, justify="left", wraplength=900).pack(anchor="w")

        # Render Hess' law using matplotlib mathtext and show as an image
        try:
            latex = r"$\Delta H^\circ_{\mathrm{rxn}} = \sum_i \nu_i\,\Delta H^\circ_{f,\mathrm{produkt}_i} - \sum_j \nu_j\,\Delta H^\circ_{f,\mathrm{reaktant}_j}$"
            img = render_latex_to_photoimage(latex, fontsize=20, dpi=200)
            lbl = ttk.Label(self, image=img)
            lbl.image = img
            lbl.pack(anchor="w", pady=(8, 12))
        except Exception:
            # Fail silently if rendering isn't available in the environment
            pass


class MolarMassPage(ttk.Frame):
    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent)
        header = ttk.Label(self, text="⚖️ Molar Mass Calculator", font=("Segoe UI", 14, "bold"))
        header.pack(anchor="w")
        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=8)

        form = ttk.Frame(self)
        form.pack(fill="x", pady=4)

        ttk.Label(form, text="Chemical Formula:").grid(row=0, column=0, sticky="w")
        self.formula_var = tk.StringVar()
        entry = ttk.Entry(form, textvariable=self.formula_var, width=40)
        entry.grid(row=0, column=1, padx=8, sticky="w")

        calc_btn = ttk.Button(form, text="Calculate Molar Mass", command=self._on_calculate)
        calc_btn.grid(row=0, column=2, padx=8)

        # Extended analysis options
        ext = ttk.LabelFrame(self, text="Extended Analysis (optional)")
        ext.pack(fill="x", pady=(6, 4))
        ttk.Label(ext, text="Sample mass (g):").grid(row=0, column=0, sticky="w")
        self.mm_sample_mass = tk.StringVar(value="")
        ttk.Entry(ext, textvariable=self.mm_sample_mass, width=12).grid(row=0, column=1, padx=6)
        self.mm_show_percent = tk.BooleanVar(value=True)
        ttk.Checkbutton(ext, text="Show percent composition", variable=self.mm_show_percent).grid(row=0, column=2, padx=8, sticky="w")

        self.result_var = tk.StringVar()
        ttk.Label(self, textvariable=self.result_var, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(12, 4))

        # Summary frame for percentages, masses, moles per element
        summ = ttk.LabelFrame(self, text="Composition Summary")
        summ.pack(fill="x", pady=(4, 6))
        self.mm_tree = ttk.Treeview(summ, columns=("element","percent","mass","moles"), show="headings", height=6)
        self.mm_tree.heading("element", text="Element")
        self.mm_tree.heading("percent", text="% by mass")
        self.mm_tree.heading("mass", text="Mass (g)")
        self.mm_tree.heading("moles", text="Moles (mol)")
        self.mm_tree.column("element", width=100, anchor="center")
        self.mm_tree.column("percent", width=100, anchor="e")
        self.mm_tree.column("mass", width=120, anchor="e")
        self.mm_tree.column("moles", width=120, anchor="e")
        self.mm_tree.pack(fill="x", padx=4, pady=4)

        ttk.Label(self, text="Steps:").pack(anchor="w")
        self.steps_box = scrolledtext.ScrolledText(self, height=16, wrap="word")
        self.steps_box.pack(fill="both", expand=True)

    def _on_calculate(self) -> None:
        formula = self.formula_var.get().strip()
        if not formula:
            messagebox.showerror("Input Error", "Please enter a chemical formula.")
            return
        try:
            result, steps, _meta = calculate_molar_mass_with_steps(formula)
            
            # Calculate total moles if sample mass is provided
            sample_mass_txt = self.mm_sample_mass.get().strip()
            print(f"Debug: sample_mass_txt = '{sample_mass_txt}'")  # Debug line
            sample_mass = None
            if sample_mass_txt:
                try:
                    sample_mass = float(sample_mass_txt)
                    print(f"Debug: sample_mass = {sample_mass}")  # Debug line
                except ValueError:
                    print(f"Debug: Could not convert '{sample_mass_txt}' to float")  # Debug line
                    sample_mass = None
            
            total_moles = None
            if sample_mass is not None and sample_mass > 0:
                total_moles = sample_mass / result
                print(f"Debug: total_moles = {total_moles}")  # Debug line
            
            # Display molar mass and total moles
            if total_moles is not None:
                result_text = f"Molar Mass: {result:.3f} g/mol | Total Moles: {total_moles:.6g} mol"
                print(f"Debug: Setting result to: {result_text}")  # Debug line
                self.result_var.set(result_text)
            else:
                result_text = f"Molar Mass: {result:.3f} g/mol"
                print(f"Debug: Setting result to: {result_text}")  # Debug line
                self.result_var.set(result_text)

            self.steps_box.configure(state="normal")
            self.steps_box.delete("1.0", "end")
            for s in steps:
                self.steps_box.insert("end", f"{s}\n")
            self.steps_box.see("end")
            self.steps_box.configure(state="normal")

            # Populate composition summary
            try:
                from core.formula import get_formula_metadata
                md = get_formula_metadata(formula)
                composition = md.get("composition", {})  # element -> %
                counts = md.get("element_counts", {})
                molar_mass = md.get("molar_mass", result)
                # sample_mass is already calculated above

                # Clear table
                for item in self.mm_tree.get_children():
                    self.mm_tree.delete(item)

                # Show rows per element if requested, and compute per-element mass and moles when sample mass provided
                for el in sorted(composition.keys()):
                    pct = composition[el] if self.mm_show_percent.get() else None
                    mass_g = (pct/100.0 * sample_mass) if (sample_mass is not None and pct is not None) else None
                    # moles of element atoms in the total sample
                    moles_total_compound = (sample_mass / molar_mass) if sample_mass is not None else None
                    moles_element_atoms = (moles_total_compound * counts.get(el, 0)) if moles_total_compound is not None else None

                    pct_str = f"{pct:.2f}%" if pct is not None else ""
                    mass_str = f"{mass_g:.6g}" if mass_g is not None else ""
                    mols_str = f"{moles_element_atoms:.6g}" if moles_element_atoms is not None else ""
                    self.mm_tree.insert("", "end", values=(el, pct_str, mass_str, mols_str))
            except Exception:
                # Fail-soft; keep the main result available
                pass
        except Exception as exc:
            messagebox.showerror("Error", str(exc))


class AcidsBasesPage(ttk.Frame):
    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent)
        header = ttk.Label(self, text="🧪 Acids & Bases", font=("Segoe UI", 14, "bold"))
        header.pack(anchor="w")
        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=8)

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        self.strong_tab = ttk.Frame(notebook)
        self.weak_tab = ttk.Frame(notebook)
        self.buffer_tab = ttk.Frame(notebook)
        self.titration_tab = ttk.Frame(notebook)
        notebook.add(self.strong_tab, text="Strong")
        notebook.add(self.weak_tab, text="Weak")
        notebook.add(self.buffer_tab, text="Buffers")
        notebook.add(self.titration_tab, text="Titrations")

        self._build_strong_tab()
        self._build_weak_tab()
        self._build_buffer_tab()
        self._build_titration_tab()

    # --- Strong acids/bases ---
    def _build_strong_tab(self) -> None:
        c = self.strong_tab
        mode_row = ttk.Frame(c)
        mode_row.pack(anchor="w", pady=(0, 6))
        ttk.Label(mode_row, text="Mode:").pack(side="left")
        self.strong_mode = tk.StringVar(value="acid")
        ttk.Radiobutton(mode_row, text="Single strong acid", value="acid", variable=self.strong_mode).pack(side="left", padx=6)
        ttk.Radiobutton(mode_row, text="Single strong base", value="base", variable=self.strong_mode).pack(side="left", padx=6)
        ttk.Radiobutton(mode_row, text="Mixture (acid + base)", value="mix", variable=self.strong_mode).pack(side="left", padx=6)

        self.strong_stack = ttk.Frame(c)
        self.strong_stack.pack(fill="x")

        # Acid inputs
        self._strong_acid_frame = ttk.Frame(self.strong_stack)
        ttk.Label(self._strong_acid_frame, text="Concentration (M):").grid(row=0, column=0, sticky="w")
        self.sa_conc = tk.StringVar(value="0.10")
        ttk.Entry(self._strong_acid_frame, textvariable=self.sa_conc, width=12).grid(row=0, column=1, padx=6)
        ttk.Label(self._strong_acid_frame, text="Volume (L):").grid(row=0, column=2, sticky="w")
        self.sa_vol = tk.StringVar(value="1.0")
        ttk.Entry(self._strong_acid_frame, textvariable=self.sa_vol, width=12).grid(row=0, column=3, padx=6)
        ttk.Button(self._strong_acid_frame, text="Calculate pH", command=self._on_strong_acid).grid(row=0, column=4, padx=8)

        # Base inputs
        self._strong_base_frame = ttk.Frame(self.strong_stack)
        ttk.Label(self._strong_base_frame, text="Concentration (M):").grid(row=0, column=0, sticky="w")
        self.sb_conc = tk.StringVar(value="0.010")
        ttk.Entry(self._strong_base_frame, textvariable=self.sb_conc, width=12).grid(row=0, column=1, padx=6)
        ttk.Label(self._strong_base_frame, text="Volume (L):").grid(row=0, column=2, sticky="w")
        self.sb_vol = tk.StringVar(value="1.0")
        ttk.Entry(self._strong_base_frame, textvariable=self.sb_vol, width=12).grid(row=0, column=3, padx=6)
        ttk.Button(self._strong_base_frame, text="Calculate pH", command=self._on_strong_base).grid(row=0, column=4, padx=8)

        # Mixture inputs
        self._strong_mix_frame = ttk.Frame(self.strong_stack)
        ttk.Label(self._strong_mix_frame, text="Acid conc (M):").grid(row=0, column=0, sticky="w")
        self.mx_acid_conc = tk.StringVar(value="0.10")
        ttk.Entry(self._strong_mix_frame, textvariable=self.mx_acid_conc, width=10).grid(row=0, column=1, padx=4)
        ttk.Label(self._strong_mix_frame, text="Acid vol (L):").grid(row=0, column=2, sticky="w")
        self.mx_acid_vol = tk.StringVar(value="1.0")
        ttk.Entry(self._strong_mix_frame, textvariable=self.mx_acid_vol, width=10).grid(row=0, column=3, padx=4)
        ttk.Label(self._strong_mix_frame, text="Base conc (M):").grid(row=1, column=0, sticky="w")
        self.mx_base_conc = tk.StringVar(value="0.05")
        ttk.Entry(self._strong_mix_frame, textvariable=self.mx_base_conc, width=10).grid(row=1, column=1, padx=4)
        ttk.Label(self._strong_mix_frame, text="Base vol (L):").grid(row=1, column=2, sticky="w")
        self.mx_base_vol = tk.StringVar(value="1.0")
        ttk.Entry(self._strong_mix_frame, textvariable=self.mx_base_vol, width=10).grid(row=1, column=3, padx=4)
        ttk.Button(self._strong_mix_frame, text="Calculate pH", command=self._on_strong_mix).grid(row=0, column=4, rowspan=2, padx=8)

        # Result and steps
        self.strong_result = tk.StringVar()
        ttk.Label(c, textvariable=self.strong_result, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(10, 2))
        ttk.Label(c, text="Steps:").pack(anchor="w")
        self.strong_steps = scrolledtext.ScrolledText(c, height=14, wrap="word")
        self.strong_steps.pack(fill="both", expand=True)

        # Bind mode switching
        def update_mode(*_):
            for child in self.strong_stack.winfo_children():
                child.grid_remove()
                child.pack_forget()
            sel = self.strong_mode.get()
            if sel == "acid":
                self._strong_acid_frame.grid(row=0, column=0, sticky="w")
            elif sel == "base":
                self._strong_base_frame.grid(row=0, column=0, sticky="w")
            else:
                self._strong_mix_frame.grid(row=0, column=0, sticky="w")
        self.strong_mode.trace_add("write", update_mode)
        update_mode()

    def _on_strong_acid(self) -> None:
        try:
            conc = float(self.sa_conc.get())
            vol = float(self.sa_vol.get())
            ph, steps, _ = calculate_strong_acid_ph(conc, vol)
            self.strong_result.set(f"pH = {ph:.3f}")
            self._write_steps(self.strong_steps, steps)
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _on_strong_base(self) -> None:
        try:
            conc = float(self.sb_conc.get())
            vol = float(self.sb_vol.get())
            ph, steps, _ = calculate_strong_base_ph(conc, vol)
            self.strong_result.set(f"pH = {ph:.3f}")
            self._write_steps(self.strong_steps, steps)
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _on_strong_mix(self) -> None:
        try:
            aC = float(self.mx_acid_conc.get()); aV = float(self.mx_acid_vol.get())
            bC = float(self.mx_base_conc.get()); bV = float(self.mx_base_vol.get())
            ph, steps, meta = calculate_strong_acid_base_mixture(aC, aV, bC, bV)
            lim = meta.get("limiting")
            extra = f" | Limiting: {lim}" if lim else ""
            self.strong_result.set(f"pH = {ph:.3f}{extra}")
            self._write_steps(self.strong_steps, steps)
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    # --- Weak acids/bases ---
    def _build_weak_tab(self) -> None:
        c = self.weak_tab
        mode_row = ttk.Frame(c)
        mode_row.pack(anchor="w", pady=(0, 6))
        ttk.Label(mode_row, text="Mode:").pack(side="left")
        self.weak_mode = tk.StringVar(value="acid")
        ttk.Radiobutton(mode_row, text="Weak acid", value="acid", variable=self.weak_mode).pack(side="left", padx=6)
        ttk.Radiobutton(mode_row, text="Weak base", value="base", variable=self.weak_mode).pack(side="left", padx=6)

        self.weak_stack = ttk.Frame(c)
        self.weak_stack.pack(fill="x")

        # Weak acid inputs
        self._weak_acid_frame = ttk.Frame(self.weak_stack)
        ttk.Label(self._weak_acid_frame, text="[HA] (M):").grid(row=0, column=0, sticky="w")
        self.wa_C = tk.StringVar(value="0.10")
        ttk.Entry(self._weak_acid_frame, textvariable=self.wa_C, width=10).grid(row=0, column=1, padx=4)
        ttk.Label(self._weak_acid_frame, text="Ka:").grid(row=0, column=2, sticky="w")
        self.wa_Ka = tk.StringVar(value="1.8e-5")
        ttk.Entry(self._weak_acid_frame, textvariable=self.wa_Ka, width=12).grid(row=0, column=3, padx=4)
        ttk.Button(self._weak_acid_frame, text="Calculate pH", command=self._on_weak_acid).grid(row=0, column=4, padx=8)

        # Weak base inputs
        self._weak_base_frame = ttk.Frame(self.weak_stack)
        ttk.Label(self._weak_base_frame, text="[B] (M):").grid(row=0, column=0, sticky="w")
        self.wb_C = tk.StringVar(value="0.10")
        ttk.Entry(self._weak_base_frame, textvariable=self.wb_C, width=10).grid(row=0, column=1, padx=4)
        self.wb_method = tk.StringVar(value="Kb")
        ttk.Radiobutton(self._weak_base_frame, text="Direct Kb", value="Kb", variable=self.wb_method).grid(row=1, column=0, columnspan=2, sticky="w")
        ttk.Radiobutton(self._weak_base_frame, text="Ka of conjugate acid", value="Ka", variable=self.wb_method).grid(row=1, column=2, columnspan=2, sticky="w")
        ttk.Label(self._weak_base_frame, text="Kb (if chosen):").grid(row=2, column=0, sticky="w")
        self.wb_Kb = tk.StringVar(value="1.8e-5")
        ttk.Entry(self._weak_base_frame, textvariable=self.wb_Kb, width=12).grid(row=2, column=1, padx=4)
        ttk.Label(self._weak_base_frame, text="Ka (if chosen):").grid(row=2, column=2, sticky="w")
        self.wb_Ka = tk.StringVar(value="5.6e-10")
        ttk.Entry(self._weak_base_frame, textvariable=self.wb_Ka, width=12).grid(row=2, column=3, padx=4)
        ttk.Button(self._weak_base_frame, text="Calculate pH", command=self._on_weak_base).grid(row=0, column=4, rowspan=3, padx=8)

        # Result and steps
        self.weak_result = tk.StringVar()
        ttk.Label(c, textvariable=self.weak_result, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(10, 2))
        ttk.Label(c, text="Steps:").pack(anchor="w")
        self.weak_steps = scrolledtext.ScrolledText(c, height=14, wrap="word")
        self.weak_steps.pack(fill="both", expand=True)

        def update_mode(*_):
            for child in self.weak_stack.winfo_children():
                child.grid_remove()
                child.pack_forget()
            if self.weak_mode.get() == "acid":
                self._weak_acid_frame.grid(row=0, column=0, sticky="w")
            else:
                self._weak_base_frame.grid(row=0, column=0, sticky="w")
        self.weak_mode.trace_add("write", update_mode)
        update_mode()

    def _on_weak_acid(self) -> None:
        try:
            C = float(self.wa_C.get())
            Ka = float(self.wa_Ka.get())
            ph, steps, meta = calculate_weak_acid_ph(C, Ka)
            extra = f" | % ionization = {meta.get('percent_ionization', 0.0):.2f}%"
            self.weak_result.set(f"pH = {ph:.3f}{extra}")
            self._write_steps(self.weak_steps, steps)
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _on_weak_base(self) -> None:
        try:
            C = float(self.wb_C.get())
            if self.wb_method.get() == "Kb":
                Kb = float(self.wb_Kb.get())
                Ka_conj = None
            else:
                Kb = None
                Ka_conj = float(self.wb_Ka.get())
            ph, steps, meta = calculate_weak_base_ph(C, kb=Kb, ka_conjugate=Ka_conj)
            pi = meta.get('percent_ionization')
            extra = f" | % ionization = {pi:.2f}%" if pi is not None else ""
            self.weak_result.set(f"pH = {ph:.3f}{extra}")
            self._write_steps(self.weak_steps, steps)
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    # --- Buffers ---
    def _build_buffer_tab(self) -> None:
        c = self.buffer_tab
        mode_row = ttk.Frame(c)
        mode_row.pack(anchor="w", pady=(0, 6))
        ttk.Label(mode_row, text="Mode:").pack(side="left")
        self.buf_mode = tk.StringVar(value="known")
        ttk.Radiobutton(mode_row, text="Known concentrations", value="known", variable=self.buf_mode).pack(side="left", padx=6)
        ttk.Radiobutton(mode_row, text="Mixing solutions", value="mix", variable=self.buf_mode).pack(side="left", padx=6)
        ttk.Radiobutton(mode_row, text="Target pH", value="target", variable=self.buf_mode).pack(side="left", padx=6)

        self.buf_stack = ttk.Frame(c)
        self.buf_stack.pack(fill="x")

        # Known concentrations
        self._buf_known = ttk.Frame(self.buf_stack)
        ttk.Label(self._buf_known, text="[A-] (M):").grid(row=0, column=0, sticky="w")
        self.bk_A = tk.StringVar(value="0.10")
        ttk.Entry(self._buf_known, textvariable=self.bk_A, width=10).grid(row=0, column=1, padx=4)
        ttk.Label(self._buf_known, text="[HA] (M):").grid(row=0, column=2, sticky="w")
        self.bk_HA = tk.StringVar(value="0.10")
        ttk.Entry(self._buf_known, textvariable=self.bk_HA, width=10).grid(row=0, column=3, padx=4)
        ttk.Label(self._buf_known, text="Ka:").grid(row=1, column=0, sticky="w")
        self.bk_Ka = tk.StringVar(value="1.8e-5")
        ttk.Entry(self._buf_known, textvariable=self.bk_Ka, width=12).grid(row=1, column=1, padx=4)
        ttk.Label(self._buf_known, text="pKa (optional):").grid(row=1, column=2, sticky="w")
        self.bk_pKa = tk.StringVar(value="")
        ttk.Entry(self._buf_known, textvariable=self.bk_pKa, width=10).grid(row=1, column=3, padx=4)
        ttk.Button(self._buf_known, text="Calculate pH", command=self._on_buf_known).grid(row=0, column=4, rowspan=2, padx=8)

        # Mixing solutions
        self._buf_mix = ttk.Frame(self.buf_stack)
        ttk.Label(self._buf_mix, text="[HA] (M):").grid(row=0, column=0, sticky="w")
        self.bm_HA = tk.StringVar(value="0.10")
        ttk.Entry(self._buf_mix, textvariable=self.bm_HA, width=10).grid(row=0, column=1, padx=4)
        ttk.Label(self._buf_mix, text="V_HA (L):").grid(row=0, column=2, sticky="w")
        self.bm_VHA = tk.StringVar(value="1.0")
        ttk.Entry(self._buf_mix, textvariable=self.bm_VHA, width=10).grid(row=0, column=3, padx=4)
        ttk.Label(self._buf_mix, text="[A-] (M):").grid(row=1, column=0, sticky="w")
        self.bm_A = tk.StringVar(value="0.10")
        ttk.Entry(self._buf_mix, textvariable=self.bm_A, width=10).grid(row=1, column=1, padx=4)
        ttk.Label(self._buf_mix, text="V_A- (L):").grid(row=1, column=2, sticky="w")
        self.bm_VA = tk.StringVar(value="1.0")
        ttk.Entry(self._buf_mix, textvariable=self.bm_VA, width=10).grid(row=1, column=3, padx=4)
        ttk.Label(self._buf_mix, text="Ka:").grid(row=2, column=0, sticky="w")
        self.bm_Ka = tk.StringVar(value="1.8e-5")
        ttk.Entry(self._buf_mix, textvariable=self.bm_Ka, width=12).grid(row=2, column=1, padx=4)
        ttk.Button(self._buf_mix, text="Calculate pH", command=self._on_buf_mix).grid(row=0, column=4, rowspan=3, padx=8)

        # Target pH
        self._buf_target = ttk.Frame(self.buf_stack)
        ttk.Label(self._buf_target, text="Target pH:").grid(row=0, column=0, sticky="w")
        self.bt_pH = tk.StringVar(value="5.00")
        ttk.Entry(self._buf_target, textvariable=self.bt_pH, width=10).grid(row=0, column=1, padx=4)
        ttk.Label(self._buf_target, text="pKa:").grid(row=0, column=2, sticky="w")
        self.bt_pKa = tk.StringVar(value="4.74")
        ttk.Entry(self._buf_target, textvariable=self.bt_pKa, width=10).grid(row=0, column=3, padx=4)
        ttk.Label(self._buf_target, text="Ka (optional):").grid(row=1, column=0, sticky="w")
        self.bt_Ka = tk.StringVar(value="")
        ttk.Entry(self._buf_target, textvariable=self.bt_Ka, width=12).grid(row=1, column=1, padx=4)
        ttk.Button(self._buf_target, text="Calculate ratio [A-]/[HA]", command=self._on_buf_target).grid(row=0, column=4, rowspan=2, padx=8)

        # Result and steps
        self.buf_result = tk.StringVar()
        ttk.Label(c, textvariable=self.buf_result, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(10, 2))
        ttk.Label(c, text="Steps:").pack(anchor="w")
        self.buf_steps = scrolledtext.ScrolledText(c, height=14, wrap="word")
        self.buf_steps.pack(fill="both", expand=True)

        def update_mode(*_):
            for child in self.buf_stack.winfo_children():
                child.grid_remove()
                child.pack_forget()
            sel = self.buf_mode.get()
            if sel == "known":
                self._buf_known.grid(row=0, column=0, sticky="w")
            elif sel == "mix":
                self._buf_mix.grid(row=0, column=0, sticky="w")
            else:
                self._buf_target.grid(row=0, column=0, sticky="w")
        self.buf_mode.trace_add("write", update_mode)
        update_mode()

    def _on_buf_known(self) -> None:
        try:
            A = float(self.bk_A.get()); HA = float(self.bk_HA.get())
            Ka = float(self.bk_Ka.get())
            pKa_txt = self.bk_pKa.get().strip()
            pKa = float(pKa_txt) if pKa_txt else None
            ph, steps, _ = calculate_buffer_ph(A, HA, Ka, pKa)
            self.buf_result.set(f"pH = {ph:.3f}")
            self._write_steps(self.buf_steps, steps)
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _on_buf_mix(self) -> None:
        try:
            HA = float(self.bm_HA.get()); VHA = float(self.bm_VHA.get())
            A = float(self.bm_A.get()); VA = float(self.bm_VA.get())
            Ka = float(self.bm_Ka.get())
            ph, steps, _ = calculate_buffer_mixing_ph(HA, VHA, A, VA, Ka)
            self.buf_result.set(f"pH = {ph:.3f}")
            self._write_steps(self.buf_steps, steps)
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _on_buf_target(self) -> None:
        try:
            target_pH = float(self.bt_pH.get())
            pKa = float(self.bt_pKa.get())
            Ka_txt = self.bt_Ka.get().strip()
            Ka = float(Ka_txt) if Ka_txt else None
            ratio, steps, _ = calculate_target_buffer_ratio(target_pH, pKa, Ka)
            self.buf_result.set(f"[A-]/[HA] = {ratio:.3f}")
            self._write_steps(self.buf_steps, steps)
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    # --- Titrations ---
    def _build_titration_tab(self) -> None:
        c = self.titration_tab
        mode_row = ttk.Frame(c)
        mode_row.pack(anchor="w", pady=(0, 6))
        ttk.Label(mode_row, text="Type:").pack(side="left")
        self.tit_mode = tk.StringVar(value="sa_sb")
        ttk.Radiobutton(mode_row, text="Strong acid + Strong base", value="sa_sb", variable=self.tit_mode).pack(side="left", padx=6)
        ttk.Radiobutton(mode_row, text="Weak acid + Strong base", value="wa_sb", variable=self.tit_mode).pack(side="left", padx=6)

        self.tit_stack = ttk.Frame(c)
        self.tit_stack.pack(fill="x")

        # Strong acid + strong base
        self._tit_sasb = ttk.Frame(self.tit_stack)
        ttk.Label(self._tit_sasb, text="Acid conc (M):").grid(row=0, column=0, sticky="w")
        self.ts_aC = tk.StringVar(value="0.10")
        ttk.Entry(self._tit_sasb, textvariable=self.ts_aC, width=10).grid(row=0, column=1, padx=4)
        ttk.Label(self._tit_sasb, text="Acid vol (L):").grid(row=0, column=2, sticky="w")
        self.ts_aV = tk.StringVar(value="1.0")
        ttk.Entry(self._tit_sasb, textvariable=self.ts_aV, width=10).grid(row=0, column=3, padx=4)
        ttk.Label(self._tit_sasb, text="Base conc (M):").grid(row=1, column=0, sticky="w")
        self.ts_bC = tk.StringVar(value="0.10")
        ttk.Entry(self._tit_sasb, textvariable=self.ts_bC, width=10).grid(row=1, column=1, padx=4)
        ttk.Label(self._tit_sasb, text="Base vol (L):").grid(row=1, column=2, sticky="w")
        self.ts_bV = tk.StringVar(value="1.0")
        ttk.Entry(self._tit_sasb, textvariable=self.ts_bV, width=10).grid(row=1, column=3, padx=4)
        ttk.Button(self._tit_sasb, text="Calculate", command=self._on_tit_sasb).grid(row=0, column=4, rowspan=2, padx=8)

        # Weak acid + strong base
        self._tit_wasb = ttk.Frame(self.tit_stack)
        ttk.Label(self._tit_wasb, text="Acid conc (M):").grid(row=0, column=0, sticky="w")
        self.tw_aC = tk.StringVar(value="0.10")
        ttk.Entry(self._tit_wasb, textvariable=self.tw_aC, width=10).grid(row=0, column=1, padx=4)
        ttk.Label(self._tit_wasb, text="Acid vol (L):").grid(row=0, column=2, sticky="w")
        self.tw_aV = tk.StringVar(value="1.0")
        ttk.Entry(self._tit_wasb, textvariable=self.tw_aV, width=10).grid(row=0, column=3, padx=4)
        ttk.Label(self._tit_wasb, text="Ka:").grid(row=1, column=0, sticky="w")
        self.tw_Ka = tk.StringVar(value="1.8e-5")
        ttk.Entry(self._tit_wasb, textvariable=self.tw_Ka, width=12).grid(row=1, column=1, padx=4)
        ttk.Label(self._tit_wasb, text="Base conc (M):").grid(row=1, column=2, sticky="w")
        self.tw_bC = tk.StringVar(value="0.10")
        ttk.Entry(self._tit_wasb, textvariable=self.tw_bC, width=10).grid(row=1, column=3, padx=4)
        ttk.Label(self._tit_wasb, text="Base vol (L):").grid(row=1, column=4, sticky="w")
        self.tw_bV = tk.StringVar(value="1.0")
        ttk.Entry(self._tit_wasb, textvariable=self.tw_bV, width=10).grid(row=1, column=5, padx=4)
        ttk.Button(self._tit_wasb, text="Calculate", command=self._on_tit_wasb).grid(row=0, column=6, rowspan=2, padx=8)

        # Result and steps
        self.tit_result = tk.StringVar()
        ttk.Label(c, textvariable=self.tit_result, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(10, 2))
        ttk.Label(c, text="Steps:").pack(anchor="w")
        self.tit_steps = scrolledtext.ScrolledText(c, height=14, wrap="word")
        self.tit_steps.pack(fill="both", expand=True)

        def update_mode(*_):
            for child in self.tit_stack.winfo_children():
                child.grid_remove()
                child.pack_forget()
            if self.tit_mode.get() == "sa_sb":
                self._tit_sasb.grid(row=0, column=0, sticky="w")
            else:
                self._tit_wasb.grid(row=0, column=0, sticky="w")
        self.tit_mode.trace_add("write", update_mode)
        update_mode()

    def _on_tit_sasb(self) -> None:
        try:
            aC = float(self.ts_aC.get()); aV = float(self.ts_aV.get())
            bC = float(self.ts_bC.get()); bV = float(self.ts_bV.get())
            ph, region, steps, _ = calculate_titration_strong_acid_strong_base(aC, aV, bC, bV)
            self.tit_result.set(f"pH = {ph:.3f} | Region: {region}")
            self._write_steps(self.tit_steps, steps)
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _on_tit_wasb(self) -> None:
        try:
            aC = float(self.tw_aC.get()); aV = float(self.tw_aV.get())
            Ka = float(self.tw_Ka.get())
            bC = float(self.tw_bC.get()); bV = float(self.tw_bV.get())
            ph, region, steps, _ = calculate_titration_weak_acid_strong_base(aC, aV, Ka, bC, bV)
            self.tit_result.set(f"pH = {ph:.3f} | Region: {region}")
            self._write_steps(self.tit_steps, steps)
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    # --- Utils ---
    @staticmethod
    def _write_steps(box: scrolledtext.ScrolledText, steps: list[str]) -> None:
        box.configure(state="normal")
        box.delete("1.0", "end")
        for s in steps:
            box.insert("end", f"{s}\n")
        box.see("end")
        box.configure(state="normal")

    @staticmethod
    def _write_text(box: scrolledtext.ScrolledText, text: str) -> None:
        box.configure(state="normal")
        box.delete("1.0", "end")
        box.insert("end", text)
        box.see("end")
        box.configure(state="normal")


class GasesPage(ttk.Frame):
    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent)
        header = ttk.Label(self, text="📊 Gases", font=("Segoe UI", 14, "bold"))
        header.pack(anchor="w")
        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=8)

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        self.ideal_tab = ttk.Frame(notebook)
        self.dalton_tab = ttk.Frame(notebook)
        self.stoich_tab = ttk.Frame(notebook)
        self.vdw_tab = ttk.Frame(notebook)
        notebook.add(self.ideal_tab, text="Ideal Gas Law")
        notebook.add(self.dalton_tab, text="Dalton's Law")
        notebook.add(self.stoich_tab, text="Gas Stoichiometry")
        notebook.add(self.vdw_tab, text="van der Waals")

        self._build_ideal_tab()
        self._build_dalton_tab()
        self._build_stoich_tab()
        self._build_vdw_tab()

    # --- Ideal Gas Law ---
    def _build_ideal_tab(self) -> None:
        c = self.ideal_tab
        grid = ttk.Frame(c)
        grid.pack(anchor="w", pady=4)

        # Inputs (leave one blank)
        ttk.Label(grid, text="Pressure:").grid(row=0, column=0, sticky="w")
        self.ig_P = tk.StringVar(value="")
        ttk.Entry(grid, textvariable=self.ig_P, width=10).grid(row=0, column=1, padx=4)
        self.ig_P_unit = tk.StringVar(value="atm")
        ttk.Combobox(grid, textvariable=self.ig_P_unit, values=["atm", "bar", "kPa", "Pa"], width=8, state="readonly").grid(row=0, column=2, padx=4)

        ttk.Label(grid, text="Volume:").grid(row=0, column=3, sticky="w")
        self.ig_V = tk.StringVar(value="")
        ttk.Entry(grid, textvariable=self.ig_V, width=10).grid(row=0, column=4, padx=4)
        self.ig_V_unit = tk.StringVar(value="L")
        ttk.Combobox(grid, textvariable=self.ig_V_unit, values=["L", "mL", "m³"], width=6, state="readonly").grid(row=0, column=5, padx=4)

        ttk.Label(grid, text="Moles n:").grid(row=1, column=0, sticky="w")
        self.ig_n = tk.StringVar(value="")
        ttk.Entry(grid, textvariable=self.ig_n, width=10).grid(row=1, column=1, padx=4)

        ttk.Label(grid, text="Temperature:").grid(row=1, column=3, sticky="w")
        self.ig_T = tk.StringVar(value="")
        ttk.Entry(grid, textvariable=self.ig_T, width=10).grid(row=1, column=4, padx=4)
        self.ig_T_unit = tk.StringVar(value="K")
        ttk.Combobox(grid, textvariable=self.ig_T_unit, values=["K", "°C"], width=6, state="readonly").grid(row=1, column=5, padx=4)

        ttk.Button(c, text="Calculate", command=self._on_ideal).pack(anchor="w", pady=8)

        self.ig_result = tk.StringVar()
        ttk.Label(c, textvariable=self.ig_result, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(2, 2))
        ttk.Label(c, text="Steps:").pack(anchor="w")
        self.ig_steps = scrolledtext.ScrolledText(c, height=14, wrap="word")
        self.ig_steps.pack(fill="both", expand=True)

    def _on_ideal(self) -> None:
        def parse_or_none(v: str):
            t = v.strip()
            return None if t == "" else float(t)
        try:
            P = parse_or_none(self.ig_P.get())
            V = parse_or_none(self.ig_V.get())
            n = parse_or_none(self.ig_n.get())
            T = parse_or_none(self.ig_T.get())
            res = calculate_ideal_gas_law_with_steps(
                pressure=P, volume=V, moles=n, temperature=T,
                pressure_unit=self.ig_P_unit.get(), volume_unit=self.ig_V_unit.get(), temperature_unit=self.ig_T_unit.get(),
            )
            self.ig_result.set(f"Result: {res['result']:.6g} {res['unit']}")
            self._write_text(self.ig_steps, res['steps'])
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    # --- Dalton's Law ---
    def _build_dalton_tab(self) -> None:
        c = self.dalton_tab
        mode_row = ttk.Frame(c)
        mode_row.pack(anchor="w", pady=(0, 6))
        ttk.Label(mode_row, text="Input:").pack(side="left")
        self.d_mode = tk.StringVar(value="moles")
        ttk.Radiobutton(mode_row, text="Moles", value="moles", variable=self.d_mode).pack(side="left", padx=6)
        ttk.Radiobutton(mode_row, text="Mole fractions", value="fractions", variable=self.d_mode).pack(side="left", padx=6)

        ctrl = ttk.Frame(c)
        ctrl.pack(anchor="w")
        ttk.Label(ctrl, text="Number of species:").pack(side="left")
        self.d_n = tk.IntVar(value=2)
        self.d_n_spin = ttk.Spinbox(ctrl, from_=1, to=10, textvariable=self.d_n, width=5, command=self._rebuild_dalton_rows)
        self.d_n_spin.pack(side="left", padx=6)

        grid = ttk.Frame(c)
        grid.pack(fill="x", pady=6)
        self.d_grid = grid
        self._dalton_rows: list[dict[str, tk.Variable]] = []
        self._rebuild_dalton_rows()

        # Total pressure and unit
        row2 = ttk.Frame(c)
        row2.pack(anchor="w", pady=4)
        ttk.Label(row2, text="Total pressure:").pack(side="left")
        self.d_Ptot = tk.StringVar(value="1.0")
        ttk.Entry(row2, textvariable=self.d_Ptot, width=10).pack(side="left", padx=4)
        self.d_Punit = tk.StringVar(value="atm")
        ttk.Combobox(row2, textvariable=self.d_Punit, values=["atm", "bar", "kPa", "Pa"], width=8, state="readonly").pack(side="left", padx=4)

        # Over water
        self.d_over_water = tk.BooleanVar(value=False)
        cb = ttk.Checkbutton(c, text="Collected over water", variable=self.d_over_water, command=self._toggle_water)
        cb.pack(anchor="w")
        self.d_Pwater = tk.StringVar(value="0.05")
        self.d_water_entry = ttk.Entry(c, textvariable=self.d_Pwater, width=12)

        ttk.Button(c, text="Calculate Partial Pressures", command=self._on_dalton).pack(anchor="w", pady=8)

        self.d_result = tk.StringVar()
        ttk.Label(c, textvariable=self.d_result, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(2, 2))
        ttk.Label(c, text="Steps:").pack(anchor="w")
        self.d_steps = scrolledtext.ScrolledText(c, height=14, wrap="word")
        self.d_steps.pack(fill="both", expand=True)

        def update_mode(*_):
            self._rebuild_dalton_rows()
        self.d_mode.trace_add("write", update_mode)

    def _rebuild_dalton_rows(self) -> None:
        for child in self.d_grid.winfo_children():
            child.destroy()
        self._dalton_rows.clear()
        headers = ["Name", "Moles" if self.d_mode.get() == "moles" else "Mole fraction"]
        for col, h in enumerate(headers):
            ttk.Label(self.d_grid, text=h, font=("Segoe UI", 10, "bold")).grid(row=0, column=col, padx=4, pady=2, sticky="w")
        for i in range(self.d_n.get()):
            name_v = tk.StringVar(value=f"Gas{i+1}")
            val_v = tk.StringVar(value="1.0" if self.d_mode.get() == "moles" else "0.5")
            ttk.Entry(self.d_grid, textvariable=name_v, width=16).grid(row=i + 1, column=0, padx=4, pady=2, sticky="w")
            ttk.Entry(self.d_grid, textvariable=val_v, width=12).grid(row=i + 1, column=1, padx=4, pady=2, sticky="w")
            self._dalton_rows.append({"name": name_v, "value": val_v})

    def _toggle_water(self) -> None:
        if self.d_over_water.get():
            ttk.Label(self.dalton_tab, text="Water vapor pressure:").pack(anchor="w")
            self.d_water_entry.pack(anchor="w", pady=(0, 6))
        else:
            try:
                self.d_water_entry.pack_forget()
            except Exception:
                pass

    def _on_dalton(self) -> None:
        try:
            species_data = []
            if self.d_mode.get() == "moles":
                for row in self._dalton_rows:
                    species_data.append({"name": row["name"].get(), "moles": float(row["value"].get())})
            else:
                for row in self._dalton_rows:
                    species_data.append({"name": row["name"].get(), "mole_fraction": float(row["value"].get())})

            Ptot = float(self.d_Ptot.get())
            over_water = self.d_over_water.get()
            Pwater = float(self.d_Pwater.get()) if over_water else None
            res = calculate_dalton_law_with_steps(
                species_data=species_data,
                total_pressure=Ptot,
                pressure_unit=self.d_Punit.get(),
                collected_over_water=over_water,
                water_vapor_pressure=Pwater,
            )
            # Compose summary
            summary = []
            if "partial_pressures" in res:
                for pp in res["partial_pressures"]:
                    summary.append(f"{pp['name']}: {pp['partial_pressure']:.4g} {self.d_Punit.get()}")
            if res.get("gas_pressure") is not None:
                summary.append(f"Gas (dry) pressure: {res['gas_pressure']:.4g} {self.d_Punit.get()}")
            self.d_result.set("; ".join(summary))
            self._write_text(self.d_steps, res["steps"])
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    # --- Gas Stoichiometry ---
    def _build_stoich_tab(self) -> None:
        c = self.stoich_tab
        rxn_row = ttk.Frame(c)
        rxn_row.pack(fill="x", pady=4)
        ttk.Label(rxn_row, text="Reaction:").grid(row=0, column=0, sticky="w")
        self.gs_rxn = tk.StringVar(value="2 H2 + O2 -> 2 H2O(g)")
        ttk.Entry(rxn_row, textvariable=self.gs_rxn, width=50).grid(row=0, column=1, padx=6, sticky="w")

        ctrl = ttk.Frame(c)
        ctrl.pack(anchor="w")
        ttk.Label(ctrl, text="Number of reactants:").pack(side="left")
        self.gs_n = tk.IntVar(value=2)
        self.gs_spin = ttk.Spinbox(ctrl, from_=1, to=5, textvariable=self.gs_n, width=5, command=self._rebuild_gs_rows)
        self.gs_spin.pack(side="left", padx=6)

        grid = ttk.Frame(c)
        grid.pack(fill="x", pady=6)
        self.gs_grid = grid
        self._gs_rows: list[dict[str, tk.Variable]] = []
        self._rebuild_gs_rows()

        row2 = ttk.Frame(c)
        row2.pack(fill="x", pady=4)
        ttk.Label(row2, text="Temperature:").grid(row=0, column=0, sticky="w")
        self.gs_T = tk.StringVar(value="298.15")
        ttk.Entry(row2, textvariable=self.gs_T, width=10).grid(row=0, column=1, padx=4)
        self.gs_T_unit = tk.StringVar(value="K")
        ttk.Combobox(row2, textvariable=self.gs_T_unit, values=["K", "°C"], width=6, state="readonly").grid(row=0, column=2, padx=4)
        ttk.Label(row2, text="Pressure:").grid(row=0, column=3, sticky="w")
        self.gs_P = tk.StringVar(value="1.0")
        ttk.Entry(row2, textvariable=self.gs_P, width=10).grid(row=0, column=4, padx=4)
        self.gs_P_unit = tk.StringVar(value="atm")
        ttk.Combobox(row2, textvariable=self.gs_P_unit, values=["atm", "bar", "kPa", "Pa"], width=8, state="readonly").grid(row=0, column=5, padx=4)
        ttk.Label(row2, text="Output V unit:").grid(row=0, column=6, sticky="w")
        self.gs_V_unit = tk.StringVar(value="L")
        ttk.Combobox(row2, textvariable=self.gs_V_unit, values=["L", "mL", "m³"], width=6, state="readonly").grid(row=0, column=7, padx=4)

        ttk.Button(c, text="Calculate Stoichiometry", command=self._on_gs).pack(anchor="w", pady=8)

        self.gs_result = tk.StringVar()
        ttk.Label(c, textvariable=self.gs_result, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(2, 2))
        ttk.Label(c, text="Steps:").pack(anchor="w")
        self.gs_steps = scrolledtext.ScrolledText(c, height=14, wrap="word")
        self.gs_steps.pack(fill="both", expand=True)

    def _rebuild_gs_rows(self) -> None:
        for child in self.gs_grid.winfo_children():
            child.destroy()
        self._gs_rows.clear()
        headers = ["Formula", "Type", "Value"]
        for col, h in enumerate(headers):
            ttk.Label(self.gs_grid, text=h, font=("Segoe UI", 10, "bold")).grid(row=0, column=col, padx=4, pady=2, sticky="w")
        for i in range(self.gs_n.get()):
            f_v = tk.StringVar(value=f"R{i+1}")
            t_v = tk.StringVar(value="Volume")
            val_v = tk.StringVar(value="1.0")
            ttk.Entry(self.gs_grid, textvariable=f_v, width=16).grid(row=i + 1, column=0, padx=4, pady=2, sticky="w")
            ttk.Combobox(self.gs_grid, textvariable=t_v, values=["Volume", "Mass"], width=8, state="readonly").grid(row=i + 1, column=1, padx=4, pady=2, sticky="w")
            ttk.Entry(self.gs_grid, textvariable=val_v, width=12).grid(row=i + 1, column=2, padx=4, pady=2, sticky="w")
            self._gs_rows.append({"formula": f_v, "type": t_v, "value": val_v})

    def _on_gs(self) -> None:
        try:
            rxn = self.gs_rxn.get().strip()
            reactant_data = []
            for row in self._gs_rows:
                val = float(row["value"].get())
                if row["type"].get() == "Volume":
                    reactant_data.append({"formula": row["formula"].get().strip(), "volume": val})
                else:
                    reactant_data.append({"formula": row["formula"].get().strip(), "mass": val})
            res = calculate_gas_stoichiometry_with_steps(
                reaction=rxn,
                reactant_data=reactant_data,
                temperature=float(self.gs_T.get()),
                pressure=float(self.gs_P.get()),
                temperature_unit=self.gs_T_unit.get(),
                pressure_unit=self.gs_P_unit.get(),
                volume_unit=self.gs_V_unit.get(),
            )
            self.gs_result.set(
                f"Limiting: {res['limiting_reactant']['formula']} | n_product = {res['product_moles']:.4g} mol | V_product = {res['product_volume']:.4g} {self.gs_V_unit.get()}"
            )
            self._write_text(self.gs_steps, res["steps"])
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    # --- van der Waals ---
    def _build_vdw_tab(self) -> None:
        c = self.vdw_tab
        # Load available gases for dropdown
        try:
            vdw_path = Path(__file__).parent / "data" / "vdw_constants.csv"
            df = pd.read_csv(vdw_path)
            gases = df["gas"].tolist()
        except Exception:
            gases = ["CO2", "N2", "O2"]

        row1 = ttk.Frame(c)
        row1.pack(fill="x", pady=4)
        ttk.Label(row1, text="Gas:").grid(row=0, column=0, sticky="w")
        self.vdw_gas = tk.StringVar(value=gases[0] if gases else "CO2")
        ttk.Combobox(row1, textvariable=self.vdw_gas, values=gases, width=12, state="readonly").grid(row=0, column=1, padx=4)
        ttk.Label(row1, text="Moles:").grid(row=0, column=2, sticky="w")
        self.vdw_n = tk.StringVar(value="1.0")
        ttk.Entry(row1, textvariable=self.vdw_n, width=10).grid(row=0, column=3, padx=4)
        ttk.Label(row1, text="Volume:").grid(row=0, column=4, sticky="w")
        self.vdw_V = tk.StringVar(value="1.0")
        ttk.Entry(row1, textvariable=self.vdw_V, width=10).grid(row=0, column=5, padx=4)

        row2 = ttk.Frame(c)
        row2.pack(fill="x", pady=4)
        ttk.Label(row2, text="Temperature:").grid(row=0, column=0, sticky="w")
        self.vdw_T = tk.StringVar(value="298.15")
        ttk.Entry(row2, textvariable=self.vdw_T, width=10).grid(row=0, column=1, padx=4)
        self.vdw_V_unit = tk.StringVar(value="L")
        ttk.Label(row2, text="V unit:").grid(row=0, column=2, sticky="w")
        ttk.Combobox(row2, textvariable=self.vdw_V_unit, values=["L", "mL", "m³"], width=6, state="readonly").grid(row=0, column=3, padx=4)
        self.vdw_T_unit = tk.StringVar(value="K")
        ttk.Label(row2, text="T unit:").grid(row=0, column=4, sticky="w")
        ttk.Combobox(row2, textvariable=self.vdw_T_unit, values=["K", "°C"], width=6, state="readonly").grid(row=0, column=5, padx=4)
        self.vdw_P_unit = tk.StringVar(value="atm")
        ttk.Label(row2, text="P unit:").grid(row=0, column=6, sticky="w")
        ttk.Combobox(row2, textvariable=self.vdw_P_unit, values=["atm", "bar", "kPa", "Pa"], width=8, state="readonly").grid(row=0, column=7, padx=4)

        ttk.Button(c, text="Calculate", command=self._on_vdw).pack(anchor="w", pady=8)

        self.vdw_result = tk.StringVar()
        ttk.Label(c, textvariable=self.vdw_result, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(2, 2))
        ttk.Label(c, text="Steps:").pack(anchor="w")
        self.vdw_steps = scrolledtext.ScrolledText(c, height=14, wrap="word")
        self.vdw_steps.pack(fill="both", expand=True)

    def _on_vdw(self) -> None:
        try:
            res = calculate_van_der_waals_with_steps(
                gas=self.vdw_gas.get(),
                moles=float(self.vdw_n.get()),
                volume=float(self.vdw_V.get()),
                temperature=float(self.vdw_T.get()),
                volume_unit=self.vdw_V_unit.get(),
                temperature_unit=self.vdw_T_unit.get(),
                pressure_unit=self.vdw_P_unit.get(),
            )
            self.vdw_result.set(
                f"P_vdW = {res['pressure_vdw']:.4g} {self.vdw_P_unit.get()} | P_ideal = {res['pressure_ideal']:.4g} {self.vdw_P_unit.get()} | Z = {res['compressibility_factor']:.4g}"
            )
            self._write_text(self.vdw_steps, res["steps"])
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    # --- Utils ---
    @staticmethod
    def _write_text(box: scrolledtext.ScrolledText, text: str) -> None:
        box.configure(state="normal")
        box.delete("1.0", "end")
        box.insert("end", text)
        box.see("end")
        box.configure(state="normal")


class EquilibriumPage(ttk.Frame):
    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent)
        header = ttk.Label(self, text="⚖️ Equilibrium", font=("Segoe UI", 14, "bold"))
        header.pack(anchor="w")
        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=8)

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        self.ice_tab = ttk.Frame(notebook)
        self.kckp_tab = ttk.Frame(notebook)
        self.q_tab = ttk.Frame(notebook)
        self.solubility_tab = ttk.Frame(notebook)
        notebook.add(self.ice_tab, text="ICE Table")
        notebook.add(self.kckp_tab, text="Kc/Kp")
        notebook.add(self.q_tab, text="Reaction Quotient")
        notebook.add(self.solubility_tab, text="Solubility")

        self._build_ice_tab()
        self._build_kckp_tab()
        self._build_q_tab()
        self._build_solubility_tab()

    # --- ICE Table ---
    def _build_ice_tab(self) -> None:
        c = self.ice_tab
        rxn_row = ttk.Frame(c)
        rxn_row.pack(fill="x", pady=4)
        ttk.Label(rxn_row, text="Reaction (balanced or not):").grid(row=0, column=0, sticky="w")
        self.ice_rxn = tk.StringVar(value="A + B -> C")
        ttk.Entry(rxn_row, textvariable=self.ice_rxn, width=50).grid(row=0, column=1, padx=6, sticky="w")
        ttk.Button(rxn_row, text="Load species", command=self._ice_load_species).grid(row=0, column=2, padx=8)

        self.ice_grid = ttk.Frame(c)
        self.ice_grid.pack(fill="x", pady=6)
        self._ice_species: list[str] = []
        self._ice_inputs: dict[str, tk.StringVar] = {}

        row2 = ttk.Frame(c)
        row2.pack(fill="x", pady=4)
        ttk.Label(row2, text="Kc:").grid(row=0, column=0, sticky="w")
        self.ice_kc = tk.StringVar(value="1.0")
        ttk.Entry(row2, textvariable=self.ice_kc, width=12).grid(row=0, column=1, padx=4)

        ttk.Button(c, text="Solve ICE Table", command=self._on_ice).pack(anchor="w", pady=8)

        self.ice_result = tk.StringVar()
        ttk.Label(c, textvariable=self.ice_result, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(2, 2))
        ttk.Label(c, text="Steps:").pack(anchor="w")
        self.ice_steps = scrolledtext.ScrolledText(c, height=14, wrap="word")
        self.ice_steps.pack(fill="both", expand=True)

    def _ice_load_species(self) -> None:
        try:
            parsed = parse_reaction_equation(self.ice_rxn.get().strip())
            species = parsed['reactants'] + parsed['products']
            self._ice_species = species
            for child in self.ice_grid.winfo_children():
                child.destroy()
            ttk.Label(self.ice_grid, text="Species", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, padx=4, pady=2, sticky="w")
            ttk.Label(self.ice_grid, text="Initial [ ] (M)", font=("Segoe UI", 10, "bold")).grid(row=0, column=1, padx=4, pady=2, sticky="w")
            self._ice_inputs.clear()
            for i, s in enumerate(species):
                ttk.Label(self.ice_grid, text=s).grid(row=i + 1, column=0, padx=4, pady=2, sticky="w")
                v = tk.StringVar(value="0.0")
                ttk.Entry(self.ice_grid, textvariable=v, width=12).grid(row=i + 1, column=1, padx=4, pady=2, sticky="w")
                self._ice_inputs[s] = v
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _on_ice(self) -> None:
        try:
            if not self._ice_species:
                self._ice_load_species()
            init = {s: float(self._ice_inputs[s].get()) for s in self._ice_species}
            kc = float(self.ice_kc.get())
            res, steps, _ = solve_ice_table_with_steps(self.ice_rxn.get().strip(), init, kc)
            eq = res.get('equilibrium_concentrations', {})
            details = [f"x = {res.get('extent', 0.0):.6g}", f"direction = {res.get('direction','')} "]
            if eq:
                details.append("Equilibrium: " + ", ".join(f"[{k}]={v:.6g} M" for k, v in eq.items()))
            self.ice_result.set(" | ".join(details))
            self._write_text(self.ice_steps, "\n".join(steps))
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    # --- Kc/Kp Conversion ---
    def _build_kckp_tab(self) -> None:
        c = self.kckp_tab
        mode_row = ttk.Frame(c)
        mode_row.pack(anchor="w", pady=(0, 6))
        ttk.Label(mode_row, text="Convert:").pack(side="left")
        self.k_mode = tk.StringVar(value="kc2kp")
        ttk.Radiobutton(mode_row, text="Kc → Kp", value="kc2kp", variable=self.k_mode).pack(side="left", padx=6)
        ttk.Radiobutton(mode_row, text="Kp → Kc", value="kp2kc", variable=self.k_mode).pack(side="left", padx=6)

        grid = ttk.Frame(c)
        grid.pack(anchor="w")

        ttk.Label(grid, text="Temperature (K):").grid(row=0, column=0, sticky="w")
        self.k_T = tk.StringVar(value="298.15")
        ttk.Entry(grid, textvariable=self.k_T, width=12).grid(row=0, column=1, padx=4)
        ttk.Label(grid, text="Δn (gas moles):").grid(row=0, column=2, sticky="w")
        self.k_dn = tk.StringVar(value="1")
        ttk.Entry(grid, textvariable=self.k_dn, width=8).grid(row=0, column=3, padx=4)

        ttk.Label(grid, text="Kc:").grid(row=1, column=0, sticky="w")
        self.k_kc = tk.StringVar(value="1.0")
        ttk.Entry(grid, textvariable=self.k_kc, width=12).grid(row=1, column=1, padx=4)
        ttk.Label(grid, text="Kp:").grid(row=1, column=2, sticky="w")
        self.k_kp = tk.StringVar(value="")
        ttk.Entry(grid, textvariable=self.k_kp, width=12).grid(row=1, column=3, padx=4)

        ttk.Button(c, text="Convert", command=self._on_kckp).pack(anchor="w", pady=8)

        self.k_result = tk.StringVar()
        ttk.Label(c, textvariable=self.k_result, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(2, 2))
        ttk.Label(c, text="Steps:").pack(anchor="w")
        self.k_steps = scrolledtext.ScrolledText(c, height=12, wrap="word")
        self.k_steps.pack(fill="both", expand=True)

    def _on_kckp(self) -> None:
        try:
            T = float(self.k_T.get())
            dn = int(float(self.k_dn.get()))
            if self.k_mode.get() == "kc2kp":
                kc = float(self.k_kc.get())
                kp = None
            else:
                kc = None
                kp = float(self.k_kp.get())
            res, steps, _ = convert_equilibrium_constants_with_steps(kc=kc, kp=kp, temperature=T, delta_n=dn)
            if 'kp' in res and kc is not None:
                self.k_result.set(f"Kp = {res['kp']:.6g} (from Kc = {res['kc']:.6g})")
            else:
                self.k_result.set(f"Kc = {res['kc']:.6g} (from Kp = {res['kp']:.6g})")
            self._write_text(self.k_steps, "\n".join(steps))
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    # --- Reaction Quotient ---
    def _build_q_tab(self) -> None:
        c = self.q_tab
        rxn_row = ttk.Frame(c)
        rxn_row.pack(fill="x", pady=4)
        ttk.Label(rxn_row, text="Reaction (balanced or not):").grid(row=0, column=0, sticky="w")
        self.q_rxn = tk.StringVar(value="A + B -> C")
        ttk.Entry(rxn_row, textvariable=self.q_rxn, width=50).grid(row=0, column=1, padx=6, sticky="w")
        ttk.Button(rxn_row, text="Load species", command=self._q_load_species).grid(row=0, column=2, padx=8)

        self.q_grid = ttk.Frame(c)
        self.q_grid.pack(fill="x", pady=6)
        self._q_species: list[str] = []
        self._q_inputs: dict[str, tk.StringVar] = {}

        row2 = ttk.Frame(c)
        row2.pack(fill="x", pady=4)
        ttk.Label(row2, text="K:").grid(row=0, column=0, sticky="w")
        self.q_K = tk.StringVar(value="1.0")
        ttk.Entry(row2, textvariable=self.q_K, width=12).grid(row=0, column=1, padx=4)

        ttk.Button(c, text="Calculate Q", command=self._on_q).pack(anchor="w", pady=8)

        self.q_result = tk.StringVar()
        ttk.Label(c, textvariable=self.q_result, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(2, 2))
        ttk.Label(c, text="Steps:").pack(anchor="w")
        self.q_steps = scrolledtext.ScrolledText(c, height=12, wrap="word")
        self.q_steps.pack(fill="both", expand=True)

    def _q_load_species(self) -> None:
        try:
            parsed = parse_reaction_equation(self.q_rxn.get().strip())
            species = parsed['reactants'] + parsed['products']
            self._q_species = species
            for child in self.q_grid.winfo_children():
                child.destroy()
            ttk.Label(self.q_grid, text="Species", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, padx=4, pady=2, sticky="w")
            ttk.Label(self.q_grid, text="[ ] (M)", font=("Segoe UI", 10, "bold")).grid(row=0, column=1, padx=4, pady=2, sticky="w")
            self._q_inputs.clear()
            for i, s in enumerate(species):
                ttk.Label(self.q_grid, text=s).grid(row=i + 1, column=0, padx=4, pady=2, sticky="w")
                v = tk.StringVar(value="1.0")
                ttk.Entry(self.q_grid, textvariable=v, width=12).grid(row=i + 1, column=1, padx=4, pady=2, sticky="w")
                self._q_inputs[s] = v
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _on_q(self) -> None:
        try:
            if not self._q_species:
                self._q_load_species()
            curr = {s: float(self._q_inputs[s].get()) for s in self._q_species}
            K = float(self.q_K.get())
            res, steps, _ = calculate_reaction_quotient_with_steps(self.q_rxn.get().strip(), curr, K)
            self.q_result.set(f"Q = {res['Q']:.6g} | {res['comparison']} | {res['direction']}")
            self._write_text(self.q_steps, "\n".join(steps))
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    # --- Solubility ---
    def _build_solubility_tab(self) -> None:
        c = self.solubility_tab
        mode_row = ttk.Frame(c)
        mode_row.pack(anchor="w", pady=(0, 6))
        ttk.Label(mode_row, text="Mode:").pack(side="left")
        self.s_mode = tk.StringVar(value="from_ksp")
        ttk.Radiobutton(mode_row, text="Solubility from Ksp", value="from_ksp", variable=self.s_mode).pack(side="left", padx=6)
        ttk.Radiobutton(mode_row, text="Ksp from solubility", value="from_s", variable=self.s_mode).pack(side="left", padx=6)

        self.s_stack = ttk.Frame(c)
        self.s_stack.pack(fill="x")

        # From Ksp
        self._s_ksp = ttk.Frame(self.s_stack)
        ttk.Label(self._s_ksp, text="Salt formula:").grid(row=0, column=0, sticky="w")
        self.sk_formula = tk.StringVar(value="AgCl")
        ttk.Entry(self._s_ksp, textvariable=self.sk_formula, width=16).grid(row=0, column=1, padx=4)
        ttk.Label(self._s_ksp, text="Ksp:").grid(row=0, column=2, sticky="w")
        self.sk_ksp = tk.StringVar(value="1.8e-10")
        ttk.Entry(self._s_ksp, textvariable=self.sk_ksp, width=12).grid(row=0, column=3, padx=4)
        ttk.Label(self._s_ksp, text="Common ions (ion:conc, comma-separated):").grid(row=1, column=0, sticky="w")
        self.sk_common = tk.StringVar(value="")
        ttk.Entry(self._s_ksp, textvariable=self.sk_common, width=50).grid(row=1, column=1, columnspan=3, padx=4, pady=2, sticky="w")
        ttk.Button(self._s_ksp, text="Calculate", command=self._on_sol_from_ksp).grid(row=0, column=4, rowspan=2, padx=8)

        # From solubility
        self._s_sol = ttk.Frame(self.s_stack)
        ttk.Label(self._s_sol, text="Salt formula:").grid(row=0, column=0, sticky="w")
        self.ss_formula = tk.StringVar(value="AgCl")
        ttk.Entry(self._s_sol, textvariable=self.ss_formula, width=16).grid(row=0, column=1, padx=4)
        ttk.Label(self._s_sol, text="Solubility (M):").grid(row=0, column=2, sticky="w")
        self.ss_s = tk.StringVar(value="1.34e-5")
        ttk.Entry(self._s_sol, textvariable=self.ss_s, width=12).grid(row=0, column=3, padx=4)
        ttk.Button(self._s_sol, text="Calculate", command=self._on_ksp_from_sol).grid(row=0, column=4, padx=8)

        ttk.Button(c, text="Switch Mode", command=self._sol_update_mode).pack(anchor="w", pady=8)

        self.s_result = tk.StringVar()
        ttk.Label(c, textvariable=self.s_result, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(2, 2))
        ttk.Label(c, text="Steps:").pack(anchor="w")
        self.s_steps = scrolledtext.ScrolledText(c, height=12, wrap="word")
        self.s_steps.pack(fill="both", expand=True)

        self._sol_update_mode()

    def _sol_update_mode(self) -> None:
        for child in self.s_stack.winfo_children():
            child.grid_remove()
            child.pack_forget()
        if self.s_mode.get() == "from_ksp":
            self._s_ksp.grid(row=0, column=0, sticky="w")
        else:
            self._s_sol.grid(row=0, column=0, sticky="w")

    def _on_sol_from_ksp(self) -> None:
        try:
            common_raw = self.sk_common.get().strip()
            common: dict[str, float] = {}
            if common_raw:
                for part in common_raw.split(','):
                    if ':' in part:
                        ion, conc = part.split(':', 1)
                        common[ion.strip()] = float(conc.strip())
            res, steps, _ = calculate_solubility_with_steps(
                salt_formula=self.sk_formula.get().strip(),
                ksp=float(self.sk_ksp.get()),
                common_ion_concentrations=common,
            )
            eq = res.get('equilibrium_concentrations', {})
            eq_str = ", ".join(f"[{k}]={v:.6g} M" for k, v in eq.items())
            self.s_result.set(f"s = {res['solubility']:.6g} M | Ksp(calc) = {res['calculated_ksp']:.2e} | {eq_str}")
            self._write_text(self.s_steps, "\n".join(steps))
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _on_ksp_from_sol(self) -> None:
        try:
            res, steps, _ = calculate_solubility_product_with_steps(
                salt_formula=self.ss_formula.get().strip(),
                solubility=float(self.ss_s.get()),
            )
            self.s_result.set(f"Ksp = {res['ksp']:.2e}")
            self._write_text(self.s_steps, "\n".join(steps))
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    # --- Utils ---
    @staticmethod
    def _write_text(box: scrolledtext.ScrolledText, text: str) -> None:
        box.configure(state="normal")
        box.delete("1.0", "end")
        box.insert("end", text)
        box.see("end")
        box.configure(state="normal")


class KineticsPage(ttk.Frame):
    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent)
        header = ttk.Label(self, text="⚡ Kinetics", font=("Segoe UI", 14, "bold"))
        header.pack(anchor="w")
        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=8)

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        self.int_tab = ttk.Frame(notebook)
        self.det_tab = ttk.Frame(notebook)
        self.arr_tab = ttk.Frame(notebook)
        self.rate_tab = ttk.Frame(notebook)
        notebook.add(self.int_tab, text="Integrated Rate Law")
        notebook.add(self.det_tab, text="Determine Order & k")
        notebook.add(self.arr_tab, text="Arrhenius")
        notebook.add(self.rate_tab, text="Rate Relationships")

        self._build_integrated_tab()
        self._build_determine_tab()
        self._build_arrhenius_tab()
        self._build_rate_tab()

    # --- Integrated Rate Law ---
    def _build_integrated_tab(self) -> None:
        c = self.int_tab
        grid = ttk.Frame(c); grid.pack(fill="x", pady=4)
        ttk.Label(grid, text="Order").grid(row=0, column=0, sticky="w")
        self.kr_order = tk.StringVar(value="1"); ttk.Combobox(grid, textvariable=self.kr_order, values=["0","1","2"], width=6, state="readonly").grid(row=0, column=1, padx=4)
        ttk.Label(grid, text="Unknown").grid(row=0, column=2, sticky="w")
        self.kr_unknown = tk.StringVar(value="Ct"); ttk.Combobox(grid, textvariable=self.kr_unknown, values=["Ct","C0","k","t"], width=8, state="readonly").grid(row=0, column=3, padx=4)
        ttk.Label(grid, text="C0 (M)").grid(row=1, column=0, sticky="w"); self.kr_C0 = tk.StringVar(value="0.100"); ttk.Entry(grid, textvariable=self.kr_C0, width=10).grid(row=1, column=1, padx=4)
        ttk.Label(grid, text="Ct (M)").grid(row=1, column=2, sticky="w"); self.kr_Ct = tk.StringVar(value="0.010"); ttk.Entry(grid, textvariable=self.kr_Ct, width=10).grid(row=1, column=3, padx=4)
        ttk.Label(grid, text="k").grid(row=2, column=0, sticky="w"); self.kr_k = tk.StringVar(value="0.350"); ttk.Entry(grid, textvariable=self.kr_k, width=10).grid(row=2, column=1, padx=4)
        ttk.Label(grid, text="t (s)").grid(row=2, column=2, sticky="w"); self.kr_t = tk.StringVar(value="10.0"); ttk.Entry(grid, textvariable=self.kr_t, width=10).grid(row=2, column=3, padx=4)
        ttk.Button(c, text="Solve", command=self._on_integrated).pack(anchor="w", pady=8)
        self.kr_result = tk.StringVar(); ttk.Label(c, textvariable=self.kr_result, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(2,2))
        self.kr_half_life = tk.StringVar(); ttk.Label(c, textvariable=self.kr_half_life, font=("Segoe UI", 10)).pack(anchor="w", pady=(2,2))
        self.kr_steps = scrolledtext.ScrolledText(c, height=12, wrap="word"); self.kr_steps.pack(fill="both", expand=True)

    def _on_integrated(self) -> None:
        try:
            order = int(self.kr_order.get()); unknown = self.kr_unknown.get()
            C0 = None if unknown == "C0" else float(self.kr_C0.get())
            Ct = None if unknown == "Ct" else float(self.kr_Ct.get())
            k = None if unknown == "k" else float(self.kr_k.get())
            t = None if unknown == "t" else float(self.kr_t.get())
            val, steps, _ = calculate_integrated_rate_with_steps(order, C0, Ct, k, t)
            self.kr_result.set(f"{unknown} = {val:.6g}")
            
            # Calculate and display half-life
            try:
                # We need both C0 and k to calculate half-life
                if C0 is not None and k is not None:
                    half_life_val, half_life_steps, _ = calculate_half_life_with_steps(order, C0, k)
                    
                    # Create a nice half-life display with the formula
                    if order == 0:
                        formula = "t₁/₂ = C₀/(2k)"
                    elif order == 1:
                        formula = "t₁/₂ = ln(2)/k"
                    else:  # order == 2
                        formula = "t₁/₂ = 1/(k·C₀)"
                    
                    self.kr_half_life.set(f"Half-life: {half_life_val:.6g} s | Formula: {formula}")
                else:
                    self.kr_half_life.set("Half-life: Requires both C₀ and k values")
            except Exception as half_life_exc:
                self.kr_half_life.set(f"Half-life: Error calculating ({str(half_life_exc)})")
            
            self._write_text(self.kr_steps, "\n".join(steps))
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    # --- Determine Order & k ---
    def _build_determine_tab(self) -> None:
        c = self.det_tab
        grid = ttk.Frame(c); grid.pack(fill="x", pady=4)
        ttk.Label(grid, text="t1 (s)").grid(row=0, column=0, sticky="w"); self.dk_t1 = tk.StringVar(value="0.0"); ttk.Entry(grid, textvariable=self.dk_t1, width=10).grid(row=0, column=1, padx=4)
        ttk.Label(grid, text="C1 (M)").grid(row=0, column=2, sticky="w"); self.dk_C1 = tk.StringVar(value="0.100"); ttk.Entry(grid, textvariable=self.dk_C1, width=10).grid(row=0, column=3, padx=4)
        ttk.Label(grid, text="t2 (s)").grid(row=1, column=0, sticky="w"); self.dk_t2 = tk.StringVar(value="10.0"); ttk.Entry(grid, textvariable=self.dk_t2, width=10).grid(row=1, column=1, padx=4)
        ttk.Label(grid, text="C2 (M)").grid(row=1, column=2, sticky="w"); self.dk_C2 = tk.StringVar(value="0.003"); ttk.Entry(grid, textvariable=self.dk_C2, width=10).grid(row=1, column=3, padx=4)
        ttk.Button(c, text="Determine", command=self._on_determine).pack(anchor="w", pady=8)
        self.dk_result = tk.StringVar(); ttk.Label(c, textvariable=self.dk_result, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(2,2))
        self.dk_steps = scrolledtext.ScrolledText(c, height=12, wrap="word"); self.dk_steps.pack(fill="both", expand=True)

    def _on_determine(self) -> None:
        try:
            res, steps, _ = calculate_determine_order_k_with_steps(float(self.dk_t1.get()), float(self.dk_C1.get()), float(self.dk_t2.get()), float(self.dk_C2.get()))
            self.dk_result.set(f"Order = {res['order']}, k = {res['k']:.6g}, residual = {res['residual']:.3e}")
            self._write_text(self.dk_steps, "\n".join(steps))
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    # --- Arrhenius ---
    def _build_arrhenius_tab(self) -> None:
        c = self.arr_tab
        grid = ttk.Frame(c); grid.pack(fill="x", pady=4)
        ttk.Label(grid, text="k1 (s^-1)").grid(row=0, column=0, sticky="w"); self.ar_k1 = tk.StringVar(value="1.0e-3"); ttk.Entry(grid, textvariable=self.ar_k1, width=12).grid(row=0, column=1, padx=4)
        ttk.Label(grid, text="T1 (K)").grid(row=0, column=2, sticky="w"); self.ar_T1 = tk.StringVar(value="298.15"); ttk.Entry(grid, textvariable=self.ar_T1, width=12).grid(row=0, column=3, padx=4)
        ttk.Label(grid, text="T2 (K)").grid(row=1, column=0, sticky="w"); self.ar_T2 = tk.StringVar(value="308.15"); ttk.Entry(grid, textvariable=self.ar_T2, width=12).grid(row=1, column=1, padx=4)
        ttk.Label(grid, text="Ea (kJ/mol)").grid(row=1, column=2, sticky="w"); self.ar_Ea = tk.StringVar(value="50.0"); ttk.Entry(grid, textvariable=self.ar_Ea, width=12).grid(row=1, column=3, padx=4)
        ttk.Button(c, text="Compute k2", command=self._on_arr_forward).pack(anchor="w", pady=6)
        row2 = ttk.Frame(c); row2.pack(fill="x", pady=4)
        ttk.Label(row2, text="k2 (s^-1)").grid(row=0, column=0, sticky="w"); self.ar_k2 = tk.StringVar(value="3.0e-3"); ttk.Entry(row2, textvariable=self.ar_k2, width=12).grid(row=0, column=1, padx=4)
        ttk.Button(c, text="Compute Ea", command=self._on_arr_two_point).pack(anchor="w", pady=6)
        self.ar_result = tk.StringVar(); ttk.Label(c, textvariable=self.ar_result, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(2,2))
        self.ar_steps = scrolledtext.ScrolledText(c, height=12, wrap="word"); self.ar_steps.pack(fill="both", expand=True)

    def _on_arr_forward(self) -> None:
        try:
            k2, steps, _ = calculate_arrhenius_forward_with_steps(float(self.ar_k1.get()), float(self.ar_T1.get()), float(self.ar_T2.get()), float(self.ar_Ea.get()))
            self.ar_result.set(f"k2 = {k2:.6g} s^-1")
            self._write_text(self.ar_steps, "\n".join(steps))
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _on_arr_two_point(self) -> None:
        try:
            Ea_kJ, steps, _ = calculate_arrhenius_two_point_Ea_with_steps(float(self.ar_k1.get()), float(self.ar_T1.get()), float(self.ar_k2.get()), float(self.ar_T2.get()))
            self.ar_result.set(f"Ea = {Ea_kJ:.6g} kJ/mol")
            self._write_text(self.ar_steps, "\n".join(steps))
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    # --- Rate Relationships ---
    def _build_rate_tab(self) -> None:
        c = self.rate_tab
        ttk.Label(c, text="Given a balanced reaction aA + bB -> cC + dD, rates relate as −(1/a)d[A]/dt = −(1/b)d[B]/dt = (1/c)d[C]/dt …", wraplength=900, justify="left").pack(anchor="w")

    # --- Utils ---
    @staticmethod
    def _write_text(box: scrolledtext.ScrolledText, text: str) -> None:
        box.configure(state="normal")
        box.delete("1.0", "end")
        if isinstance(text, list):
            box.insert("end", "\n".join(text))
        else:
            box.insert("end", str(text))
        box.see("end")
        box.configure(state="normal")


class ElectrochemistryPage(ttk.Frame):
    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent)
        header = ttk.Label(self, text="🔋 Electrochemistry", font=("Segoe UI", 14, "bold"))
        header.pack(anchor="w")
        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=8)

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        self.cell_tab = ttk.Frame(notebook)
        self.nernst_tab = ttk.Frame(notebook)
        self.gk_tab = ttk.Frame(notebook)
        notebook.add(self.cell_tab, text="Build a Cell")
        notebook.add(self.nernst_tab, text="Nernst")
        notebook.add(self.gk_tab, text="ΔG and K")

        self._build_cell_tab()
        self._build_nernst_tab()
        self._build_gk_tab()

    def _build_cell_tab(self) -> None:
        c = self.cell_tab
        # Load reduction potentials
        try:
            df = pd.read_csv(Path(__file__).parent / "data" / "reduction_potentials.csv")
        except Exception:
            from core.electrochem import load_reduction_potentials
            df = load_reduction_potentials()
        opts = df['half_reaction'].tolist() if 'half_reaction' in df.columns else df
        grid = ttk.Frame(c); grid.pack(fill="x", pady=4)
        ttk.Label(grid, text="Cathode (reduction)").grid(row=0, column=0, sticky="w")
        self.ec_cath = tk.StringVar(value=opts[0] if opts else "")
        ttk.Combobox(grid, textvariable=self.ec_cath, values=opts, width=50).grid(row=0, column=1, padx=6)
        ttk.Label(grid, text="Anode (reduction)").grid(row=1, column=0, sticky="w")
        self.ec_an = tk.StringVar(value=opts[1] if len(opts) > 1 else (opts[0] if opts else ""))
        ttk.Combobox(grid, textvariable=self.ec_an, values=opts, width=50).grid(row=1, column=1, padx=6)
        ttk.Button(c, text="Compute E°cell", command=self._on_cell).pack(anchor="w", pady=8)
        self.ec_result = tk.StringVar(); ttk.Label(c, textvariable=self.ec_result, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(2,2))
        self.ec_steps = scrolledtext.ScrolledText(c, height=12, wrap="word"); self.ec_steps.pack(fill="both", expand=True)

    def _on_cell(self) -> None:
        try:
            res, steps, _ = calculate_standard_cell_with_steps(self.ec_cath.get(), self.ec_an.get())
            self.ec_result.set(f"E°cell = {res['E0_cell_V']:.6g} V, n = {res['n']}")
            self._write_text(self.ec_steps, "\n".join(steps))
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _build_nernst_tab(self) -> None:
        c = self.nernst_tab
        grid = ttk.Frame(c); grid.pack(fill="x", pady=4)
        ttk.Label(grid, text="E°cell (V)").grid(row=0, column=0, sticky="w"); self.ne_E0 = tk.StringVar(value="1.10"); ttk.Entry(grid, textvariable=self.ne_E0, width=12).grid(row=0, column=1, padx=4)
        ttk.Label(grid, text="n (e-)").grid(row=0, column=2, sticky="w"); self.ne_n = tk.StringVar(value="2"); ttk.Entry(grid, textvariable=self.ne_n, width=8).grid(row=0, column=3, padx=4)
        ttk.Label(grid, text="T (K)").grid(row=0, column=4, sticky="w"); self.ne_T = tk.StringVar(value="298.15"); ttk.Entry(grid, textvariable=self.ne_T, width=12).grid(row=0, column=5, padx=4)
        ttk.Label(grid, text="Quick Daniell: [Zn2+]").grid(row=1, column=0, sticky="w"); self.ne_Zn2 = tk.StringVar(value="0.10"); ttk.Entry(grid, textvariable=self.ne_Zn2, width=12).grid(row=1, column=1, padx=4)
        ttk.Label(grid, text="[Cu2+]").grid(row=1, column=2, sticky="w"); self.ne_Cu2 = tk.StringVar(value="1.00"); ttk.Entry(grid, textvariable=self.ne_Cu2, width=12).grid(row=1, column=3, padx=4)
        ttk.Button(c, text="Compute Q", command=self._on_daniell).pack(anchor="w", pady=4)
        ttk.Button(c, text="Compute E", command=self._on_nernst).pack(anchor="w", pady=6)
        self.ne_result = tk.StringVar(); ttk.Label(c, textvariable=self.ne_result, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(2,2))
        self.ne_steps = scrolledtext.ScrolledText(c, height=12, wrap="word"); self.ne_steps.pack(fill="both", expand=True)

    def _on_daniell(self) -> None:
        try:
            Q = calculate_daniell_Q(float(self.ne_Zn2.get()), float(self.ne_Cu2.get()))
            self.ne_result.set(f"Q = {Q:.6g}")
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _on_nernst(self) -> None:
        try:
            E, steps, _ = calculate_nernst_with_steps(float(self.ne_E0.get()), int(float(self.ne_n.get())), float(self.ne_T.get()), float(self.ne_Zn2.get())/float(self.ne_Cu2.get()))
            self.ne_result.set(f"E = {E:.6g} V")
            self._write_text(self.ne_steps, "\n".join(steps))
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _build_gk_tab(self) -> None:
        c = self.gk_tab
        grid = ttk.Frame(c); grid.pack(fill="x", pady=4)
        ttk.Label(grid, text="n").grid(row=0, column=0, sticky="w"); self.gk_n = tk.StringVar(value="2"); ttk.Entry(grid, textvariable=self.gk_n, width=8).grid(row=0, column=1, padx=4)
        ttk.Label(grid, text="E° (V)").grid(row=0, column=2, sticky="w"); self.gk_E0 = tk.StringVar(value="1.10"); ttk.Entry(grid, textvariable=self.gk_E0, width=12).grid(row=0, column=3, padx=4)
        ttk.Label(grid, text="T (K)").grid(row=0, column=4, sticky="w"); self.gk_T = tk.StringVar(value="298.15"); ttk.Entry(grid, textvariable=self.gk_T, width=12).grid(row=0, column=5, padx=4)
        ttk.Button(c, text="Compute ΔG° and K", command=self._on_gk).pack(anchor="w", pady=8)
        self.gk_result = tk.StringVar(); ttk.Label(c, textvariable=self.gk_result, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(2,2))
        self.gk_steps = scrolledtext.ScrolledText(c, height=12, wrap="word"); self.gk_steps.pack(fill="both", expand=True)

    def _on_gk(self) -> None:
        try:
            dG_kJ, _, _ = calculate_deltaG_from_E_with_steps(int(float(self.gk_n.get())), float(self.gk_E0.get()))
            K, log10K, steps, _ = calculate_K_from_E0_with_steps(int(float(self.gk_n.get())), float(self.gk_E0.get()), float(self.gk_T.get()))
            self.gk_result.set(f"ΔG° = {dG_kJ:.6g} kJ/mol, log10 K = {log10K:.6g}")
            self._write_text(self.gk_steps, "\n".join(steps))
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    # --- Utils ---
    @staticmethod
    def _write_text(box: scrolledtext.ScrolledText, text: str) -> None:
        box.configure(state="normal")
        box.delete("1.0", "end")
        if isinstance(text, list):
            box.insert("end", "\n".join(text))
        else:
            box.insert("end", str(text))
        box.see("end")
        box.configure(state="normal")


class ThermochemistryPage(ttk.Frame):
    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent)
        header = ttk.Label(self, text="🌡️ Thermochemistry", font=("Segoe UI", 14, "bold"))
        header.pack(anchor="w")
        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=8)

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        self.cal_tab = ttk.Frame(notebook)
        self.hc_tab = ttk.Frame(notebook)
        self.dhf_tab = ttk.Frame(notebook)
        self.cc_tab = ttk.Frame(notebook)
        notebook.add(self.cal_tab, text="Calorimetry")
        notebook.add(self.hc_tab, text="Heating/Cooling")
        notebook.add(self.dhf_tab, text="ΔH from ΔHf°")
        notebook.add(self.cc_tab, text="Clausius–Clapeyron")

        self._build_cal_tab()
        self._build_hc_tab()
        self._build_dhf_tab()
        self._build_cc_tab()

    # --- Calorimetry ---
    def _build_cal_tab(self) -> None:
        c = self.cal_tab
        row1 = ttk.Frame(c)
        row1.pack(fill="x", pady=4)
        ttk.Label(row1, text="Mass (g):").grid(row=0, column=0, sticky="w")
        self.cal_mass = tk.StringVar(value="100.0")
        ttk.Entry(row1, textvariable=self.cal_mass, width=12).grid(row=0, column=1, padx=4)
        ttk.Label(row1, text="Preset:").grid(row=0, column=2, sticky="w")
        self.cal_preset = tk.StringVar(value="water_liquid")
        ttk.Combobox(row1, textvariable=self.cal_preset, values=["water_ice", "water_liquid", "water_steam"], width=14, state="readonly").grid(row=0, column=3, padx=4)
        ttk.Label(row1, text="c (J/(g·K)) [optional]:").grid(row=0, column=4, sticky="w")
        self.cal_c = tk.StringVar(value="")
        ttk.Entry(row1, textvariable=self.cal_c, width=12).grid(row=0, column=5, padx=4)

        row2 = ttk.Frame(c)
        row2.pack(fill="x", pady=4)
        self.cal_mode = tk.StringVar(value="dT")
        ttk.Radiobutton(row2, text="ΔT (K)", value="dT", variable=self.cal_mode).grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(row2, text="T_initial/T_final (°C)", value="TiTf", variable=self.cal_mode).grid(row=0, column=1, sticky="w")
        ttk.Label(row2, text="ΔT (K):").grid(row=1, column=0, sticky="w")
        self.cal_dT = tk.StringVar(value="25.0")
        ttk.Entry(row2, textvariable=self.cal_dT, width=12).grid(row=1, column=1, padx=4)
        ttk.Label(row2, text="T_initial (°C):").grid(row=1, column=2, sticky="w")
        self.cal_Ti = tk.StringVar(value="20.0")
        ttk.Entry(row2, textvariable=self.cal_Ti, width=12).grid(row=1, column=3, padx=4)
        ttk.Label(row2, text="T_final (°C):").grid(row=1, column=4, sticky="w")
        self.cal_Tf = tk.StringVar(value="45.0")
        ttk.Entry(row2, textvariable=self.cal_Tf, width=12).grid(row=1, column=5, padx=4)
        ttk.Label(row2, text="Output unit:").grid(row=1, column=6, sticky="w")
        self.cal_unit = tk.StringVar(value="kJ")
        ttk.Combobox(row2, textvariable=self.cal_unit, values=["kJ", "J"], width=6, state="readonly").grid(row=1, column=7, padx=4)

        ttk.Button(c, text="Calculate q", command=self._on_calorimetry).pack(anchor="w", pady=8)

        self.cal_result = tk.StringVar()
        ttk.Label(c, textvariable=self.cal_result, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(2, 2))
        ttk.Label(c, text="Steps:").pack(anchor="w")
        self.cal_steps = scrolledtext.ScrolledText(c, height=12, wrap="word")
        self.cal_steps.pack(fill="both", expand=True)

    def _on_calorimetry(self) -> None:
        try:
            mass = float(self.cal_mass.get())
            c_val = self.cal_c.get().strip()
            c_opt = None if c_val == "" else float(c_val)
            if self.cal_mode.get() == "dT":
                dT = float(self.cal_dT.get())
                Ti = None
                Tf = None
            else:
                dT = None
                Ti = float(self.cal_Ti.get())
                Tf = float(self.cal_Tf.get())
            q, steps, _ = calculate_calorimetry_with_steps(
                mass_g=mass,
                delta_T_K=dT,
                T_initial_C=Ti,
                T_final_C=Tf,
                c_J_per_gK=c_opt,
                preset=self.cal_preset.get(),
                output_unit=self.cal_unit.get(),
            )
            self.cal_result.set(f"q = {q:.6g} {self.cal_unit.get()}")
            self._write_text(self.cal_steps, "\n".join(steps))
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    # --- Heating/Cooling Curve ---
    def _build_hc_tab(self) -> None:
        c = self.hc_tab
        row = ttk.Frame(c)
        row.pack(fill="x", pady=4)
        ttk.Label(row, text="Mass (g):").grid(row=0, column=0, sticky="w")
        self.hc_mass = tk.StringVar(value="10.0")
        ttk.Entry(row, textvariable=self.hc_mass, width=12).grid(row=0, column=1, padx=4)
        ttk.Label(row, text="T_initial (°C):").grid(row=0, column=2, sticky="w")
        self.hc_Ti = tk.StringVar(value="-10.0")
        ttk.Entry(row, textvariable=self.hc_Ti, width=12).grid(row=0, column=3, padx=4)
        ttk.Label(row, text="T_final (°C):").grid(row=0, column=4, sticky="w")
        self.hc_Tf = tk.StringVar(value="110.0")
        ttk.Entry(row, textvariable=self.hc_Tf, width=12).grid(row=0, column=5, padx=4)
        ttk.Button(c, text="Calculate", command=self._on_hc).pack(anchor="w", pady=8)

        self.hc_result = tk.StringVar()
        ttk.Label(c, textvariable=self.hc_result, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(2, 2))
        ttk.Label(c, text="Steps:").pack(anchor="w")
        self.hc_steps = scrolledtext.ScrolledText(c, height=12, wrap="word")
        self.hc_steps.pack(fill="both", expand=True)

    def _on_hc(self) -> None:
        try:
            q_kJ, steps, _ = calculate_heating_curve_water_with_steps(
                float(self.hc_mass.get()), float(self.hc_Ti.get()), float(self.hc_Tf.get())
            )
            self.hc_result.set(f"Total q = {q_kJ:.6g} kJ")
            self._write_text(self.hc_steps, "\n".join(steps))
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    # --- ΔH from ΔHf° ---
    def _build_dhf_tab(self) -> None:
        c = self.dhf_tab
        row = ttk.Frame(c)
        row.pack(fill="x", pady=4)
        ttk.Label(row, text="Reaction (balanced or not):").grid(row=0, column=0, sticky="w")
        self.dhf_rxn = tk.StringVar(value="CH4 + 2 O2 -> CO2 + 2 H2O(l)")
        ttk.Entry(row, textvariable=self.dhf_rxn, width=60).grid(row=0, column=1, padx=6, sticky="w")
        ttk.Button(c, text="Calculate ΔH_rxn", command=self._on_dhf).pack(anchor="w", pady=8)

        self.dhf_result = tk.StringVar()
        ttk.Label(c, textvariable=self.dhf_result, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(2, 2))
        ttk.Label(c, text="Steps:").pack(anchor="w")
        self.dhf_steps = scrolledtext.ScrolledText(c, height=12, wrap="word")
        self.dhf_steps.pack(fill="both", expand=True)

    def _on_dhf(self) -> None:
        try:
            val, steps, _ = calculate_reaction_enthalpy_from_formation_with_steps(self.dhf_rxn.get().strip())
            self.dhf_result.set(f"ΔH_rxn = {val:.6g} kJ/mol")
            self._write_text(self.dhf_steps, "\n".join(steps))
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    # --- Clausius–Clapeyron ---
    def _build_cc_tab(self) -> None:
        c = self.cc_tab
        row = ttk.Frame(c)
        row.pack(fill="x", pady=4)
        ttk.Label(row, text="P1 (atm):").grid(row=0, column=0, sticky="w")
        self.cc_P1 = tk.StringVar(value="1.0")
        ttk.Entry(row, textvariable=self.cc_P1, width=12).grid(row=0, column=1, padx=4)
        ttk.Label(row, text="T1 (K):").grid(row=0, column=2, sticky="w")
        self.cc_T1 = tk.StringVar(value="373.15")
        ttk.Entry(row, textvariable=self.cc_T1, width=12).grid(row=0, column=3, padx=4)
        ttk.Label(row, text="T2 (K):").grid(row=0, column=4, sticky="w")
        self.cc_T2 = tk.StringVar(value="353.15")
        ttk.Entry(row, textvariable=self.cc_T2, width=12).grid(row=0, column=5, padx=4)
        ttk.Label(row, text="ΔHvap (kJ/mol) [optional]:").grid(row=1, column=0, sticky="w")
        self.cc_dHv = tk.StringVar(value="40.65")
        ttk.Entry(row, textvariable=self.cc_dHv, width=12).grid(row=1, column=1, padx=4)
        ttk.Button(c, text="Calculate P2", command=self._on_cc).pack(anchor="w", pady=8)

        self.cc_result = tk.StringVar()
        ttk.Label(c, textvariable=self.cc_result, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(2, 2))
        ttk.Label(c, text="Steps:").pack(anchor="w")
        self.cc_steps = scrolledtext.ScrolledText(c, height=12, wrap="word")
        self.cc_steps.pack(fill="both", expand=True)

    def _on_cc(self) -> None:
        try:
            P1 = float(self.cc_P1.get())
            T1 = float(self.cc_T1.get())
            T2 = float(self.cc_T2.get())
            dHv_txt = self.cc_dHv.get().strip()
            dHv = None if dHv_txt == "" else float(dHv_txt)
            val, steps, _ = calculate_clausius_clapeyron_with_steps(P1, T1, T2, dHv)
            self.cc_result.set(f"P2 = {val:.6g} atm")
            self._write_text(self.cc_steps, "\n".join(steps))
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    # --- Utils ---
    @staticmethod
    def _write_text(box: scrolledtext.ScrolledText, text: str) -> None:
        box.configure(state="normal")
        box.delete("1.0", "end")
        box.insert("end", text)
        box.see("end")
        box.configure(state="normal")



class ColligativesPage(ttk.Frame):
    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent)
        header = ttk.Label(self, text="🧪 Colligative Properties", font=("Segoe UI", 14, "bold"))
        header.pack(anchor="w")
        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=8)

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        self.dt_tab = ttk.Frame(notebook)
        self.osm_tab = ttk.Frame(notebook)
        self.rao_tab = ttk.Frame(notebook)
        notebook.add(self.dt_tab, text="ΔTf / ΔTb")
        notebook.add(self.osm_tab, text="Osmotic Pressure")
        notebook.add(self.rao_tab, text="Raoult's Law")

        self._build_dt_tab()
        self._build_osm_tab()
        self._build_rao_tab()

    # --- Freezing/Boiling ---
    def _build_dt_tab(self) -> None:
        c = self.dt_tab
        row = ttk.Frame(c)
        row.pack(fill="x", pady=4)
        ttk.Label(row, text="van't Hoff i:").grid(row=0, column=0, sticky="w")
        self.dt_i = tk.StringVar(value="1.0")
        ttk.Entry(row, textvariable=self.dt_i, width=10).grid(row=0, column=1, padx=4)

        mode_row = ttk.Frame(c)
        mode_row.pack(fill="x", pady=4)
        self.dt_mode = tk.StringVar(value="moles")
        ttk.Radiobutton(mode_row, text="Input moles solute", value="moles", variable=self.dt_mode).pack(side="left", padx=6)
        ttk.Radiobutton(mode_row, text="Mass + molar mass", value="mass", variable=self.dt_mode).pack(side="left", padx=6)

        grid = ttk.Frame(c)
        grid.pack(fill="x", pady=2)
        ttk.Label(grid, text="Moles solute (mol):").grid(row=0, column=0, sticky="w")
        self.dt_moles = tk.StringVar(value="1.0")
        ttk.Entry(grid, textvariable=self.dt_moles, width=12).grid(row=0, column=1, padx=4)
        ttk.Label(grid, text="Mass solute (g):").grid(row=1, column=0, sticky="w")
        self.dt_mass = tk.StringVar(value="58.44")
        ttk.Entry(grid, textvariable=self.dt_mass, width=12).grid(row=1, column=1, padx=4)
        ttk.Label(grid, text="Molar mass (g/mol):").grid(row=1, column=2, sticky="w")
        self.dt_mm = tk.StringVar(value="58.44")
        ttk.Entry(grid, textvariable=self.dt_mm, width=12).grid(row=1, column=3, padx=4)
        ttk.Label(grid, text="Mass solvent (g):").grid(row=2, column=0, sticky="w")
        self.dt_msolv = tk.StringVar(value="1000")
        ttk.Entry(grid, textvariable=self.dt_msolv, width=12).grid(row=2, column=1, padx=4)

        ttk.Button(c, text="Calculate ΔT", command=self._on_dt).pack(anchor="w", pady=8)

        self.dt_result = tk.StringVar()
        ttk.Label(c, textvariable=self.dt_result, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(2, 2))
        ttk.Label(c, text="Steps:").pack(anchor="w")
        self.dt_steps = scrolledtext.ScrolledText(c, height=12, wrap="word")
        self.dt_steps.pack(fill="both", expand=True)

    def _on_dt(self) -> None:
        try:
            mode = self.dt_mode.get()
            i_val = float(self.dt_i.get())
            if mode == "moles":
                moles = float(self.dt_moles.get())
                mass = None
                mm = None
            else:
                moles = None
                mass = float(self.dt_mass.get())
                mm = float(self.dt_mm.get())
            res, steps, _ = freezing_boiling_with_steps(
                solvent="water",
                moles_solute=moles,
                mass_solute_g=mass,
                molar_mass_solute_g_per_mol=mm,
                mass_solvent_g=float(self.dt_msolv.get()),
                i=i_val,
            )
            self.dt_result.set(
                f"ΔTf = {res['deltaTf_C']:.6g} °C, Tf = {res['Tf_C']:.6g} °C | ΔTb = {res['deltaTb_C']:.6g} °C, Tb = {res['Tb_C']:.6g} °C"
            )
            self._write_text(self.dt_steps, "\n".join(steps))
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    # --- Osmotic pressure ---
    def _build_osm_tab(self) -> None:
        c = self.osm_tab
        mode_row = ttk.Frame(c)
        mode_row.pack(fill="x", pady=4)
        self.osm_mode = tk.StringVar(value="M")
        ttk.Radiobutton(mode_row, text="Enter Molarity", value="M", variable=self.osm_mode).pack(side="left", padx=6)
        ttk.Radiobutton(mode_row, text="Moles + Volume", value="mv", variable=self.osm_mode).pack(side="left", padx=6)

        grid = ttk.Frame(c)
        grid.pack(fill="x", pady=2)
        ttk.Label(grid, text="M (mol/L):").grid(row=0, column=0, sticky="w")
        self.osm_M = tk.StringVar(value="0.100")
        ttk.Entry(grid, textvariable=self.osm_M, width=12).grid(row=0, column=1, padx=4)
        ttk.Label(grid, text="moles (mol):").grid(row=0, column=2, sticky="w")
        self.osm_mol = tk.StringVar(value="0.010")
        ttk.Entry(grid, textvariable=self.osm_mol, width=12).grid(row=0, column=3, padx=4)
        ttk.Label(grid, text="V (L):").grid(row=0, column=4, sticky="w")
        self.osm_V = tk.StringVar(value="0.100")
        ttk.Entry(grid, textvariable=self.osm_V, width=12).grid(row=0, column=5, padx=4)
        ttk.Label(grid, text="T (K):").grid(row=1, column=0, sticky="w")
        self.osm_T = tk.StringVar(value="298.15")
        ttk.Entry(grid, textvariable=self.osm_T, width=12).grid(row=1, column=1, padx=4)
        ttk.Label(grid, text="i:").grid(row=1, column=2, sticky="w")
        self.osm_i = tk.StringVar(value="1.0")
        ttk.Entry(grid, textvariable=self.osm_i, width=12).grid(row=1, column=3, padx=4)
        ttk.Button(c, text="Calculate π", command=self._on_osm).pack(anchor="w", pady=8)

        self.osm_result = tk.StringVar()
        ttk.Label(c, textvariable=self.osm_result, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(2, 2))
        ttk.Label(c, text="Steps:").pack(anchor="w")
        self.osm_steps = scrolledtext.ScrolledText(c, height=12, wrap="word")
        self.osm_steps.pack(fill="both", expand=True)

    def _on_osm(self) -> None:
        try:
            if self.osm_mode.get() == "M":
                M = float(self.osm_M.get())
                mol = None
                V = None
            else:
                M = None
                mol = float(self.osm_mol.get())
                V = float(self.osm_V.get())
            pi, steps, _ = osmotic_pressure_with_steps(M, mol, V, float(self.osm_T.get()), float(self.osm_i.get()))
            self.osm_result.set(f"π = {pi:.6g} atm")
            self._write_text(self.osm_steps, "\n".join(steps))
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    # --- Raoult's law ---
    def _build_rao_tab(self) -> None:
        c = self.rao_tab
        mode_row = ttk.Frame(c)
        mode_row.pack(fill="x", pady=4)
        self.rao_mode = tk.StringVar(value="nonvolatile")
        ttk.Radiobutton(mode_row, text="Nonvolatile solute", value="nonvolatile", variable=self.rao_mode).pack(side="left", padx=6)
        ttk.Radiobutton(mode_row, text="Volatile binary", value="binary", variable=self.rao_mode).pack(side="left", padx=6)

        grid = ttk.Frame(c)
        grid.pack(fill="x", pady=2)
        # Nonvolatile inputs
        ttk.Label(grid, text="x_solvent:").grid(row=0, column=0, sticky="w")
        self.rao_xs = tk.StringVar(value="0.900")
        ttk.Entry(grid, textvariable=self.rao_xs, width=12).grid(row=0, column=1, padx=4)
        ttk.Label(grid, text="P*_solvent (kPa):").grid(row=0, column=2, sticky="w")
        self.rao_Ps = tk.StringVar(value="100.0")
        ttk.Entry(grid, textvariable=self.rao_Ps, width=12).grid(row=0, column=3, padx=4)
        # Binary inputs
        ttk.Label(grid, text="x_A:").grid(row=1, column=0, sticky="w")
        self.rao_xA = tk.StringVar(value="0.500")
        ttk.Entry(grid, textvariable=self.rao_xA, width=12).grid(row=1, column=1, padx=4)
        ttk.Label(grid, text="P*_A (kPa):").grid(row=1, column=2, sticky="w")
        self.rao_Pa = tk.StringVar(value="80.0")
        ttk.Entry(grid, textvariable=self.rao_Pa, width=12).grid(row=1, column=3, padx=4)
        ttk.Label(grid, text="P*_B (kPa):").grid(row=1, column=4, sticky="w")
        self.rao_Pb = tk.StringVar(value="60.0")
        ttk.Entry(grid, textvariable=self.rao_Pb, width=12).grid(row=1, column=5, padx=4)
        ttk.Button(c, text="Calculate", command=self._on_rao).pack(anchor="w", pady=8)

        self.rao_result = tk.StringVar()
        ttk.Label(c, textvariable=self.rao_result, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(2, 2))
        ttk.Label(c, text="Steps:").pack(anchor="w")
        self.rao_steps = scrolledtext.ScrolledText(c, height=12, wrap="word")
        self.rao_steps.pack(fill="both", expand=True)

    def _on_rao(self) -> None:
        try:
            if self.rao_mode.get() == "nonvolatile":
                P, steps, _ = raoult_nonvolatile_with_steps(float(self.rao_xs.get()), float(self.rao_Ps.get()))
                self.rao_result.set(f"P_solution = {P:.6g} kPa")
                self._write_text(self.rao_steps, "\n".join(steps))
            else:
                xA = float(self.rao_xA.get())
                PA = float(self.rao_Pa.get())
                xB = 1.0 - xA
                PB = float(self.rao_Pb.get())
                res, steps, _ = raoult_binary_with_steps(xA, PA, xB, PB)
                self.rao_result.set(f"P_total = {res['P_total']:.6g} kPa | P_A = {res['P_A']:.6g} kPa | P_B = {res['P_B']:.6g} kPa")
                self._write_text(self.rao_steps, "\n".join(steps))
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    # --- Utils ---
    @staticmethod
    def _write_text(box: scrolledtext.ScrolledText, text: str) -> None:
        box.configure(state="normal")
        box.delete("1.0", "end")
        if isinstance(text, list):
            box.insert("end", "\n".join(text))
        else:
            box.insert("end", str(text))
        box.see("end")
        box.configure(state="normal")


class SolutionsPage(ttk.Frame):
    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent)
        header = ttk.Label(self, text="⚗️ Solutions", font=("Segoe UI", 14, "bold"))
        header.pack(anchor="w")
        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=8)

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        self.molarity_tab = ttk.Frame(notebook)
        self.make_tab = ttk.Frame(notebook)
        self.molality_tab = ttk.Frame(notebook)
        self.percent_tab = ttk.Frame(notebook)
        self.ppm_tab = ttk.Frame(notebook)
        self.mix_tab = ttk.Frame(notebook)
        self.molefrac_tab = ttk.Frame(notebook)
        self.ionic_tab = ttk.Frame(notebook)
        notebook.add(self.molarity_tab, text="Molarity")
        notebook.add(self.make_tab, text="Make Solution")
        notebook.add(self.molality_tab, text="Molality")
        notebook.add(self.percent_tab, text="Percent")
        notebook.add(self.ppm_tab, text="ppm/ppb")
        notebook.add(self.mix_tab, text="Mixing")
        notebook.add(self.molefrac_tab, text="Mole Fraction")
        notebook.add(self.ionic_tab, text="Ionic Strength")

        self._build_molarity_tab()
        self._build_make_tab()
        self._build_molality_tab()
        self._build_percent_tab()
        self._build_ppm_tab()
        self._build_mix_tab()
        self._build_molefrac_tab()
        self._build_ionic_tab()

    # --- Molarity ---
    def _build_molarity_tab(self) -> None:
        c = self.molarity_tab
        row = ttk.Frame(c); row.pack(fill="x", pady=4)
        ttk.Label(row, text="Unknown:").grid(row=0, column=0, sticky="w")
        self.m_unknown = tk.StringVar(value="M")
        ttk.Combobox(row, textvariable=self.m_unknown, values=["M", "n", "V"], width=6, state="readonly").grid(row=0, column=1, padx=4)
        ttk.Label(row, text="M (mol/L):").grid(row=1, column=0, sticky="w")
        self.m_M = tk.StringVar(value="0.500")
        ttk.Entry(row, textvariable=self.m_M, width=12).grid(row=1, column=1, padx=4)
        ttk.Label(row, text="n (mol):").grid(row=1, column=2, sticky="w")
        self.m_n = tk.StringVar(value="0.250")
        ttk.Entry(row, textvariable=self.m_n, width=12).grid(row=1, column=3, padx=4)
        ttk.Label(row, text="V (L):").grid(row=1, column=4, sticky="w")
        self.m_V = tk.StringVar(value="0.500")
        ttk.Entry(row, textvariable=self.m_V, width=12).grid(row=1, column=5, padx=4)
        ttk.Button(c, text="Solve Molarity", command=self._on_molarity).pack(anchor="w", pady=8)
        self.m_result = tk.StringVar()
        ttk.Label(c, textvariable=self.m_result, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(2, 2))
        self.m_steps = scrolledtext.ScrolledText(c, height=10, wrap="word"); self.m_steps.pack(fill="both", expand=True)

    def _on_molarity(self) -> None:
        try:
            unknown = self.m_unknown.get()
            M = None if unknown == "M" else float(self.m_M.get())
            n = None if unknown == "n" else float(self.m_n.get())
            V = None if unknown == "V" else float(self.m_V.get())
            res, steps = solve_molarity(M, n, V)
            key = list(res.keys())[0]
            self.m_result.set(f"{key} = {res[key]:.6g}")
            self._write_text(self.m_steps, steps)
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    # --- Make Solution ---
    def _build_make_tab(self) -> None:
        c = self.make_tab
        left = ttk.Frame(c); left.pack(fill="x", pady=4)
        ttk.Label(left, text="Formula (solid):").grid(row=0, column=0, sticky="w")
        self.mk_formula = tk.StringVar(value="NaCl")
        ttk.Entry(left, textvariable=self.mk_formula, width=16).grid(row=0, column=1, padx=4)
        ttk.Label(left, text="Target M (mol/L):").grid(row=0, column=2, sticky="w")
        self.mk_Mt = tk.StringVar(value="0.1000")
        ttk.Entry(left, textvariable=self.mk_Mt, width=12).grid(row=0, column=3, padx=4)
        ttk.Label(left, text="Final volume (L):").grid(row=0, column=4, sticky="w")
        self.mk_Vf = tk.StringVar(value="1.00")
        ttk.Entry(left, textvariable=self.mk_Vf, width=12).grid(row=0, column=5, padx=4)
        ttk.Button(c, text="Grams from solid", command=self._on_make_solid).pack(anchor="w", pady=6)
        right = ttk.Frame(c); right.pack(fill="x", pady=4)
        ttk.Label(right, text="Stock M (mol/L):").grid(row=0, column=0, sticky="w")
        self.mk_Mstock = tk.StringVar(value="2.00")
        ttk.Entry(right, textvariable=self.mk_Mstock, width=12).grid(row=0, column=1, padx=4)
        ttk.Button(c, text="V_stock for dilution", command=self._on_make_stock).pack(anchor="w", pady=6)
        self.mk_result = tk.StringVar(); ttk.Label(c, textvariable=self.mk_result, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(2,2))
        self.mk_steps = scrolledtext.ScrolledText(c, height=10, wrap="word"); self.mk_steps.pack(fill="both", expand=True)

    def _on_make_solid(self) -> None:
        try:
            g, steps = grams_for_solution(self.mk_formula.get().strip(), float(self.mk_Mt.get()), float(self.mk_Vf.get()))
            self.mk_result.set(f"grams = {g:.6g} g")
            self._write_text(self.mk_steps, steps)
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _on_make_stock(self) -> None:
        try:
            V1, steps = volume_stock_for_dilution(float(self.mk_Mstock.get()), float(self.mk_Mt.get()), float(self.mk_Vf.get()))
            self.mk_result.set(f"V_stock = {V1:.6g} L")
            self._write_text(self.mk_steps, steps)
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    # --- Molality ---
    def _build_molality_tab(self) -> None:
        c = self.molality_tab
        row = ttk.Frame(c); row.pack(fill="x", pady=4)
        ttk.Label(row, text="Unknown:").grid(row=0, column=0, sticky="w")
        self.ml_unknown = tk.StringVar(value="m")
        ttk.Combobox(row, textvariable=self.ml_unknown, values=["m", "n_mol", "m_solvent_kg"], width=14, state="readonly").grid(row=0, column=1, padx=4)
        ttk.Label(row, text="m (mol/kg):").grid(row=1, column=0, sticky="w")
        self.ml_m = tk.StringVar(value="1.0"); ttk.Entry(row, textvariable=self.ml_m, width=12).grid(row=1, column=1, padx=4)
        ttk.Label(row, text="n (mol):").grid(row=1, column=2, sticky="w")
        self.ml_n = tk.StringVar(value="0.1"); ttk.Entry(row, textvariable=self.ml_n, width=12).grid(row=1, column=3, padx=4)
        ttk.Label(row, text="kg solvent:").grid(row=1, column=4, sticky="w")
        self.ml_kg = tk.StringVar(value="0.1"); ttk.Entry(row, textvariable=self.ml_kg, width=12).grid(row=1, column=5, padx=4)
        ttk.Button(c, text="Solve Molality", command=self._on_molality).pack(anchor="w", pady=8)
        self.ml_result = tk.StringVar(); ttk.Label(c, textvariable=self.ml_result, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(2,2))
        self.ml_steps = scrolledtext.ScrolledText(c, height=10, wrap="word"); self.ml_steps.pack(fill="both", expand=True)

    def _on_molality(self) -> None:
        try:
            unknown = self.ml_unknown.get()
            m = None if unknown == "m" else float(self.ml_m.get())
            n = None if unknown == "n_mol" else float(self.ml_n.get())
            kg = None if unknown == "m_solvent_kg" else float(self.ml_kg.get())
            res, steps = solve_molality(m, n, kg)
            key = list(res.keys())[0]
            self.ml_result.set(f"{key} = {res[key]:.6g}")
            self._write_text(self.ml_steps, steps)
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    # --- Percent ---
    def _build_percent_tab(self) -> None:
        c = self.percent_tab
        row = ttk.Frame(c); row.pack(fill="x", pady=4)
        ttk.Label(row, text="Mode:").grid(row=0, column=0, sticky="w")
        self.pc_mode = tk.StringVar(value="w/w")
        ttk.Combobox(row, textvariable=self.pc_mode, values=["w/w", "v/v", "w/v"], width=8, state="readonly").grid(row=0, column=1, padx=4)

        grid = ttk.Frame(c); grid.pack(fill="x", pady=4)
        ttk.Label(grid, text="a:").grid(row=0, column=0, sticky="w")
        self.pc_a = tk.StringVar(value="10.0"); ttk.Entry(grid, textvariable=self.pc_a, width=12).grid(row=0, column=1, padx=4)
        ttk.Label(grid, text="b:").grid(row=0, column=2, sticky="w")
        self.pc_b = tk.StringVar(value="110.0"); ttk.Entry(grid, textvariable=self.pc_b, width=12).grid(row=0, column=3, padx=4)
        ttk.Button(c, text="Compute", command=self._on_percent).pack(anchor="w", pady=8)
        self.pc_result = tk.StringVar(); ttk.Label(c, textvariable=self.pc_result, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(2,2))
        self.pc_steps = scrolledtext.ScrolledText(c, height=10, wrap="word"); self.pc_steps.pack(fill="both", expand=True)

    def _on_percent(self) -> None:
        try:
            mode = self.pc_mode.get(); a = float(self.pc_a.get()); b = float(self.pc_b.get())
            if mode == "w/w":
                val, steps = percent_w_w(a, b, "%")
            elif mode == "v/v":
                val, steps = percent_v_v(a, b, "%")
            else:
                val, steps = percent_w_v(a, b, "%")
            self.pc_result.set(f"Result = {val:.6g}")
            self._write_text(self.pc_steps, steps)
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    # --- ppm/ppb ---
    def _build_ppm_tab(self) -> None:
        c = self.ppm_tab
        grid = ttk.Frame(c); grid.pack(fill="x", pady=4)
        ttk.Label(grid, text="Basis:").grid(row=0, column=0, sticky="w")
        self.pp_basis = tk.StringVar(value="mass")
        ttk.Combobox(grid, textvariable=self.pp_basis, values=["mass", "volume"], width=10, state="readonly").grid(row=0, column=1, padx=4)
        ttk.Label(grid, text="solute (same basis):").grid(row=0, column=2, sticky="w")
        self.pp_sol = tk.StringVar(value="0.0500"); ttk.Entry(grid, textvariable=self.pp_sol, width=12).grid(row=0, column=3, padx=4)
        ttk.Label(grid, text="total (same basis):").grid(row=0, column=4, sticky="w")
        self.pp_tot = tk.StringVar(value="2.00"); ttk.Entry(grid, textvariable=self.pp_tot, width=12).grid(row=0, column=5, padx=4)
        ttk.Label(grid, text="Unit:").grid(row=1, column=0, sticky="w")
        self.pp_unit = tk.StringVar(value="ppm")
        ttk.Combobox(grid, textvariable=self.pp_unit, values=["ppm", "ppb"], width=8, state="readonly").grid(row=1, column=1, padx=4)
        ttk.Button(c, text="Compute ppm/ppb", command=self._on_ppm).pack(anchor="w", pady=6)
        row2 = ttk.Frame(c); row2.pack(fill="x", pady=4)
        ttk.Label(row2, text="mg/L:").grid(row=0, column=0, sticky="w")
        self.pp_mgL = tk.StringVar(value="25.0"); ttk.Entry(row2, textvariable=self.pp_mgL, width=12).grid(row=0, column=1, padx=4)
        ttk.Button(c, text="ppm from mg/L", command=self._on_ppm_mgL).pack(anchor="w", pady=6)
        self.pp_result = tk.StringVar(); ttk.Label(c, textvariable=self.pp_result, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(2,2))
        self.pp_steps = scrolledtext.ScrolledText(c, height=10, wrap="word"); self.pp_steps.pack(fill="both", expand=True)

    def _on_ppm(self) -> None:
        try:
            val, steps = ppm_general(float(self.pp_sol.get()), float(self.pp_tot.get()), self.pp_basis.get(), self.pp_unit.get())
            self.pp_result.set(f"{self.pp_unit.get()} = {val:.6g}")
            self._write_text(self.pp_steps, steps)
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _on_ppm_mgL(self) -> None:
        try:
            val, steps = ppm_aqueous_from_mg_per_L(float(self.pp_mgL.get()))
            self.pp_result.set(f"ppm = {val:.6g}")
            self._write_text(self.pp_steps, steps)
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    # --- Mixing ---
    def _build_mix_tab(self) -> None:
        c = self.mix_tab
        grid = ttk.Frame(c); grid.pack(fill="x", pady=4)
        ttk.Label(grid, text="V1 (L):").grid(row=0, column=0, sticky="w")
        self.mx_V1 = tk.StringVar(value="0.100"); ttk.Entry(grid, textvariable=self.mx_V1, width=12).grid(row=0, column=1, padx=4)
        ttk.Label(grid, text="M1 (mol/L):").grid(row=0, column=2, sticky="w")
        self.mx_M1 = tk.StringVar(value="1.000"); ttk.Entry(grid, textvariable=self.mx_M1, width=12).grid(row=0, column=3, padx=4)
        ttk.Label(grid, text="V2 (L):").grid(row=1, column=0, sticky="w")
        self.mx_V2 = tk.StringVar(value="0.400"); ttk.Entry(grid, textvariable=self.mx_V2, width=12).grid(row=1, column=1, padx=4)
        ttk.Label(grid, text="M2 (mol/L):").grid(row=1, column=2, sticky="w")
        self.mx_M2 = tk.StringVar(value="0.200"); ttk.Entry(grid, textvariable=self.mx_M2, width=12).grid(row=1, column=3, padx=4)
        ttk.Button(c, text="Mix", command=self._on_mix).pack(anchor="w", pady=6)
        self.mx_result = tk.StringVar(); ttk.Label(c, textvariable=self.mx_result, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(2,2))
        self.mx_steps = scrolledtext.ScrolledText(c, height=10, wrap="word"); self.mx_steps.pack(fill="both", expand=True)

    def _on_mix(self) -> None:
        try:
            Mf, steps = mix_solutions([float(self.mx_V1.get()), float(self.mx_V2.get())], [float(self.mx_M1.get()), float(self.mx_M2.get())])
            self.mx_result.set(f"M_final = {Mf:.6g} M")
            self._write_text(self.mx_steps, steps)
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    # --- Mole fraction ---
    def _build_molefrac_tab(self) -> None:
        c = self.molefrac_tab
        mode_row = ttk.Frame(c); mode_row.pack(fill="x", pady=4)
        self.mf_mode = tk.StringVar(value="masses+formulas")
        ttk.Combobox(mode_row, textvariable=self.mf_mode, values=["masses+formulas", "moles"], width=18, state="readonly").pack(side="left", padx=4)
        grid = ttk.Frame(c); grid.pack(fill="x", pady=2)
        ttk.Label(grid, text="Formula A:").grid(row=0, column=0, sticky="w")
        self.mf_formulaA = tk.StringVar(value="NaCl"); ttk.Entry(grid, textvariable=self.mf_formulaA, width=12).grid(row=0, column=1, padx=4)
        ttk.Label(grid, text="m_A (g):").grid(row=0, column=2, sticky="w")
        self.mf_mA = tk.StringVar(value="10.0"); ttk.Entry(grid, textvariable=self.mf_mA, width=12).grid(row=0, column=3, padx=4)
        ttk.Label(grid, text="Formula B:").grid(row=1, column=0, sticky="w")
        self.mf_formulaB = tk.StringVar(value="H2O"); ttk.Entry(grid, textvariable=self.mf_formulaB, width=12).grid(row=1, column=1, padx=4)
        ttk.Label(grid, text="m_B (g):").grid(row=1, column=2, sticky="w")
        self.mf_mB = tk.StringVar(value="100.0"); ttk.Entry(grid, textvariable=self.mf_mB, width=12).grid(row=1, column=3, padx=4)
        ttk.Label(grid, text="n_A (mol):").grid(row=2, column=0, sticky="w")
        self.mf_nA = tk.StringVar(value="0.171"); ttk.Entry(grid, textvariable=self.mf_nA, width=12).grid(row=2, column=1, padx=4)
        ttk.Label(grid, text="n_B (mol):").grid(row=2, column=2, sticky="w")
        self.mf_nB = tk.StringVar(value="5.55"); ttk.Entry(grid, textvariable=self.mf_nB, width=12).grid(row=2, column=3, padx=4)
        ttk.Button(c, text="Compute", command=self._on_molefrac).pack(anchor="w", pady=8)
        self.mf_result = tk.StringVar(); ttk.Label(c, textvariable=self.mf_result, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(2,2))
        self.mf_steps = scrolledtext.ScrolledText(c, height=10, wrap="word"); self.mf_steps.pack(fill="both", expand=True)

    def _on_molefrac(self) -> None:
        try:
            if self.mf_mode.get() == "masses+formulas":
                xA, xB, steps = mole_fraction_from_masses(self.mf_formulaA.get().strip(), float(self.mf_mA.get()), self.mf_formulaB.get().strip(), float(self.mf_mB.get()))
            else:
                xA, xB, steps = mole_fraction_from_moles(float(self.mf_nA.get()), float(self.mf_nB.get()))
            self.mf_result.set(f"x_A = {xA:.6g}, x_B = {xB:.6g}")
            self._write_text(self.mf_steps, steps)
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    # --- Ionic strength ---
    def _build_ionic_tab(self) -> None:
        c = self.ionic_tab
        grid = ttk.Frame(c); grid.pack(fill="x", pady=4)
        ttk.Label(grid, text="Species 1 name:").grid(row=0, column=0, sticky="w")
        self.io_name1 = tk.StringVar(value="Na+"); ttk.Entry(grid, textvariable=self.io_name1, width=10).grid(row=0, column=1, padx=4)
        ttk.Label(grid, text="c1 (M):").grid(row=0, column=2, sticky="w")
        self.io_c1 = tk.StringVar(value="0.200"); ttk.Entry(grid, textvariable=self.io_c1, width=12).grid(row=0, column=3, padx=4)
        ttk.Label(grid, text="z1 (charge):").grid(row=0, column=4, sticky="w")
        self.io_z1 = tk.StringVar(value="1"); ttk.Entry(grid, textvariable=self.io_z1, width=8).grid(row=0, column=5, padx=4)
        ttk.Label(grid, text="Species 2 name:").grid(row=1, column=0, sticky="w")
        self.io_name2 = tk.StringVar(value="SO4^2-"); ttk.Entry(grid, textvariable=self.io_name2, width=10).grid(row=1, column=1, padx=4)
        ttk.Label(grid, text="c2 (M):").grid(row=1, column=2, sticky="w")
        self.io_c2 = tk.StringVar(value="0.100"); ttk.Entry(grid, textvariable=self.io_c2, width=12).grid(row=1, column=3, padx=4)
        ttk.Label(grid, text="z2 (charge):").grid(row=1, column=4, sticky="w")
        self.io_z2 = tk.StringVar(value="-2"); ttk.Entry(grid, textvariable=self.io_z2, width=8).grid(row=1, column=5, padx=4)
        ttk.Button(c, text="Compute I", command=self._on_ionic).pack(anchor="w", pady=6)
        self.io_result = tk.StringVar(); ttk.Label(c, textvariable=self.io_result, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(2,2))
        self.io_steps = scrolledtext.ScrolledText(c, height=10, wrap="word"); self.io_steps.pack(fill="both", expand=True)

    def _on_ionic(self) -> None:
        try:
            I, steps = ionic_strength([
                (self.io_name1.get().strip(), float(self.io_c1.get()), int(float(self.io_z1.get()))),
                (self.io_name2.get().strip(), float(self.io_c2.get()), int(float(self.io_z2.get()))),
            ])
            self.io_result.set(f"I = {I:.6g}")
            self._write_text(self.io_steps, steps)
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    # --- Utils ---
    @staticmethod
    def _write_text(box: scrolledtext.ScrolledText, text: str) -> None:
        box.configure(state="normal")
        box.delete("1.0", "end")
        if isinstance(text, list):
            box.insert("end", "\n".join(text))
        else:
            box.insert("end", str(text))
        box.see("end")
        box.configure(state="normal")

class StoichiometryPage(ttk.Frame):
    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent)
        header = ttk.Label(self, text="🧮 Stoichiometry", font=("Segoe UI", 14, "bold"))
        header.pack(anchor="w")
        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=8)

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        self.limiting_tab = ttk.Frame(notebook)
        self.balance_tab = ttk.Frame(notebook)
        self.dilution_tab = ttk.Frame(notebook)
        self.redox_tab = ttk.Frame(notebook)
        notebook.add(self.balance_tab, text="Balance Reaction")
        notebook.add(self.limiting_tab, text="Limiting Reagent")
        notebook.add(self.dilution_tab, text="Dilution")
        notebook.add(self.redox_tab, text="🧮 Redox Balancer")

        self._build_balance_tab()
        self._build_limiting_tab()
        self._build_dilution_tab()
        self._build_redox_tab()

    # --- Limiting reagent tab ---
    def _build_balance_tab(self) -> None:
        c = self.balance_tab
        row = ttk.Frame(c); row.pack(fill="x", pady=4)
        ttk.Label(row, text="Chemical Equation:").grid(row=0, column=0, sticky="w")
        self.bal_rxn = tk.StringVar(value="Fe2(SO4)3 + KOH -> Fe(OH)3 + K2SO4")
        ttk.Entry(row, textvariable=self.bal_rxn, width=70).grid(row=0, column=1, padx=6, sticky="w")
        ttk.Button(c, text="Balance Equation", command=self._on_balance).pack(anchor="w", pady=8)

        self.bal_result = tk.StringVar(); ttk.Label(c, textvariable=self.bal_result, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(2,2))
        ttk.Label(c, text="Coefficients:").pack(anchor="w")
        self.bal_coeffs = scrolledtext.ScrolledText(c, height=8, wrap="word"); self.bal_coeffs.pack(fill="both", expand=True)
        ttk.Label(c, text="Steps:").pack(anchor="w")
        self.bal_steps = scrolledtext.ScrolledText(c, height=12, wrap="word"); self.bal_steps.pack(fill="both", expand=True)

    def _on_balance(self) -> None:
        try:
            result = balance_equation(self.bal_rxn.get().strip())
            self.bal_result.set(f"Balanced: {result['equation_str']}")
            # Coeffs listing
            self.bal_coeffs.configure(state="normal"); self.bal_coeffs.delete("1.0","end")
            for i, species in enumerate(result['species_order']):
                self.bal_coeffs.insert("end", f"- {species}: {result['coefficients'][i]}\n")
            self.bal_coeffs.see("end"); self.bal_coeffs.configure(state="normal")
            # Steps
            self.bal_steps.configure(state="normal"); self.bal_steps.delete("1.0","end")
            for s in result['steps']:
                self.bal_steps.insert("end", f"{s}\n")
            self.bal_steps.see("end"); self.bal_steps.configure(state="normal")
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    # --- Limiting reagent tab ---
    def _build_limiting_tab(self) -> None:
        container = self.limiting_tab

        # Reaction and product
        rxn_frame = ttk.Frame(container)
        rxn_frame.pack(fill="x", pady=4)
        ttk.Label(rxn_frame, text="Reaction (balanced or not):").grid(row=0, column=0, sticky="w")
        self.rxn_var = tk.StringVar(value="H2 + O2 -> H2O")
        ttk.Entry(rxn_frame, textvariable=self.rxn_var, width=60).grid(row=0, column=1, padx=6, sticky="w")

        ttk.Label(rxn_frame, text="Target product:").grid(row=1, column=0, sticky="w")
        self.target_product_var = tk.StringVar(value="H2O")
        ttk.Entry(rxn_frame, textvariable=self.target_product_var, width=20).grid(row=1, column=1, padx=6, sticky="w")

        # Reactant inputs
        reactants_header = ttk.Label(container, text="Reactants", font=("Segoe UI", 11, "bold"))
        reactants_header.pack(anchor="w", pady=(8, 2))

        count_row = ttk.Frame(container)
        count_row.pack(anchor="w")
        ttk.Label(count_row, text="Number of reactants:").pack(side="left")
        self.num_reactants_var = tk.IntVar(value=2)
        self.num_spin = ttk.Spinbox(count_row, from_=1, to=5, textvariable=self.num_reactants_var, width=5, command=self._rebuild_reactants_rows)
        self.num_spin.pack(side="left", padx=6)

        self.reactants_frame = ttk.Frame(container)
        self.reactants_frame.pack(fill="x", pady=6)
        self._reactant_rows: list[dict[str, tk.Variable]] = []
        self._rebuild_reactants_rows()

        # Optional actual yield
        ay_frame = ttk.Frame(container)
        ay_frame.pack(fill="x", pady=4)
        ttk.Label(ay_frame, text="Actual yield (g) [optional]:").grid(row=0, column=0, sticky="w")
        self.actual_yield_var = tk.StringVar(value="")
        ttk.Entry(ay_frame, textvariable=self.actual_yield_var, width=12).grid(row=0, column=1, padx=6, sticky="w")

        ttk.Button(container, text="Calculate Limiting Reagent", command=self._on_calc_limiting).pack(anchor="w", pady=8)

        # Results and steps
        self.lr_result_var = tk.StringVar()
        ttk.Label(container, textvariable=self.lr_result_var, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(4, 2))

        ttk.Label(container, text="Steps:").pack(anchor="w")
        self.lr_steps_box = scrolledtext.ScrolledText(container, height=16, wrap="word")
        self.lr_steps_box.pack(fill="both", expand=True)

    def _rebuild_reactants_rows(self) -> None:
        # Clear old rows
        for child in self.reactants_frame.winfo_children():
            child.destroy()
        self._reactant_rows.clear()

        headers = ["Formula", "Mode", "Value", "Unit", "Volume (mL)"]
        for col, h in enumerate(headers):
            ttk.Label(self.reactants_frame, text=h, font=("Segoe UI", 10, "bold")).grid(row=0, column=col, padx=4, pady=2, sticky="w")

        n = self.num_reactants_var.get()
        for i in range(n):
            formula_v = tk.StringVar(value="")
            mode_v = tk.StringVar(value="moles")
            value_v = tk.StringVar(value="1.0")
            unit_v = tk.StringVar(value="mol")
            vol_v = tk.StringVar(value="")  # only for solution (mL)

            ttk.Entry(self.reactants_frame, textvariable=formula_v, width=16).grid(row=i + 1, column=0, padx=4, pady=2, sticky="w")
            ttk.Combobox(self.reactants_frame, textvariable=mode_v, values=["moles", "mass", "solution"], width=10, state="readonly").grid(row=i + 1, column=1, padx=4, pady=2, sticky="w")
            ttk.Entry(self.reactants_frame, textvariable=value_v, width=12).grid(row=i + 1, column=2, padx=4, pady=2, sticky="w")
            ttk.Combobox(self.reactants_frame, textvariable=unit_v, values=["mol", "g", "M"], width=6, state="readonly").grid(row=i + 1, column=3, padx=4, pady=2, sticky="w")
            ttk.Entry(self.reactants_frame, textvariable=vol_v, width=12).grid(row=i + 1, column=4, padx=4, pady=2, sticky="w")

            self._reactant_rows.append({
                "formula": formula_v,
                "mode": mode_v,
                "value": value_v,
                "unit": unit_v,
                "volume": vol_v,
            })

    def _on_calc_limiting(self) -> None:
        try:
            equation = self.rxn_var.get().strip()
            target = self.target_product_var.get().strip()
            if not equation or not target:
                messagebox.showerror("Input Error", "Please provide reaction and target product.")
                return

            reactant_inputs = []
            for row in self._reactant_rows:
                formula = row["formula"].get().strip()
                if not formula:
                    continue
                mode = row["mode"].get()
                value_txt = row["value"].get().strip()
                unit = row["unit"].get()
                if not value_txt:
                    continue
                try:
                    value = float(value_txt)
                except ValueError:
                    messagebox.showerror("Input Error", f"Invalid numeric value for {formula}.")
                    return

                entry = {"formula": formula, "mode": mode, "value": value, "unit": unit}
                if mode == "solution":
                    vol_txt = row["volume"].get().strip()
                    if not vol_txt:
                        messagebox.showerror("Input Error", f"Volume (mL) required for solution input of {formula}.")
                        return
                    try:
                        entry["volume"] = float(vol_txt)
                    except ValueError:
                        messagebox.showerror("Input Error", f"Invalid volume (mL) for {formula}.")
                        return
                reactant_inputs.append(entry)

            actual_yield_g = None
            ay = self.actual_yield_var.get().strip()
            if ay:
                try:
                    actual_yield_g = float(ay)
                except ValueError:
                    messagebox.showerror("Input Error", "Actual yield must be a number (grams).")
                    return

            results, steps, _meta = calculate_limiting_reagent_with_steps(
                equation_str=equation,
                reactant_inputs=reactant_inputs,
                target_product=target,
                actual_yield=actual_yield_g,
            )

            parts = [
                f"Limiting reagent: {results['limiting_reagent']}",
                f"Theoretical yield: {results['theoretical_yield_mass']:.4f} g ({results['theoretical_yield_moles']:.4f} mol)",
            ]
            if results.get("percent_yield") is not None:
                parts.append(f"Percent yield: {results['percent_yield']:.1f}%")
            self.lr_result_var.set(" | ".join(parts))

            self.lr_steps_box.configure(state="normal")
            self.lr_steps_box.delete("1.0", "end")
            for s in steps:
                self.lr_steps_box.insert("end", f"{s}\n")
            self.lr_steps_box.see("end")
            self.lr_steps_box.configure(state="normal")
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    # --- Dilution tab ---
    def _build_dilution_tab(self) -> None:
        container = self.dilution_tab

        info = ttk.Label(container, text="Leave exactly one field empty; it will be solved from M1V1 = M2V2.")
        info.pack(anchor="w", pady=(0, 6))

        grid = ttk.Frame(container)
        grid.pack(anchor="w")

        # M1
        ttk.Label(grid, text="M1:").grid(row=0, column=0, sticky="w")
        self.m1_var = tk.StringVar(value="0.100")
        ttk.Entry(grid, textvariable=self.m1_var, width=10).grid(row=0, column=1, padx=4, sticky="w")
        self.m1_unit = tk.StringVar(value="M")
        ttk.Combobox(grid, textvariable=self.m1_unit, values=["M", "mM", "μM"], width=6, state="readonly").grid(row=0, column=2, padx=4, sticky="w")

        # V1
        ttk.Label(grid, text="V1:").grid(row=0, column=3, sticky="w")
        self.v1_var = tk.StringVar(value="")
        ttk.Entry(grid, textvariable=self.v1_var, width=10).grid(row=0, column=4, padx=4, sticky="w")
        self.v1_unit = tk.StringVar(value="L")
        ttk.Combobox(grid, textvariable=self.v1_unit, values=["L", "mL"], width=6, state="readonly").grid(row=0, column=5, padx=4, sticky="w")

        # M2
        ttk.Label(grid, text="M2:").grid(row=1, column=0, sticky="w")
        self.m2_var = tk.StringVar(value="0.050")
        ttk.Entry(grid, textvariable=self.m2_var, width=10).grid(row=1, column=1, padx=4, sticky="w")
        self.m2_unit = tk.StringVar(value="M")
        ttk.Combobox(grid, textvariable=self.m2_unit, values=["M", "mM", "μM"], width=6, state="readonly").grid(row=1, column=2, padx=4, sticky="w")

        # V2
        ttk.Label(grid, text="V2:").grid(row=1, column=3, sticky="w")
        self.v2_var = tk.StringVar(value="0.100")
        ttk.Entry(grid, textvariable=self.v2_var, width=10).grid(row=1, column=4, padx=4, sticky="w")
        self.v2_unit = tk.StringVar(value="L")
        ttk.Combobox(grid, textvariable=self.v2_unit, values=["L", "mL"], width=6, state="readonly").grid(row=1, column=5, padx=4, sticky="w")

        ttk.Button(container, text="Solve Dilution", command=self._on_calc_dilution).pack(anchor="w", pady=8)

        self.dil_result_var = tk.StringVar()
        ttk.Label(container, textvariable=self.dil_result_var, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(4, 2))

        ttk.Label(container, text="Steps:").pack(anchor="w")
        self.dil_steps_box = scrolledtext.ScrolledText(container, height=12, wrap="word")
        self.dil_steps_box.pack(fill="both", expand=True)

    def _on_calc_dilution(self) -> None:
        def parse_float(txt: str):
            t = txt.strip()
            if t == "":
                return None
            return float(t)

        try:
            m1 = parse_float(self.m1_var.get())
            v1 = parse_float(self.v1_var.get())
            m2 = parse_float(self.m2_var.get())
            v2 = parse_float(self.v2_var.get())

            results, steps, _meta = calculate_dilution_with_steps(
                m1=m1, v1=v1, m2=m2, v2=v2,
                m1_unit=self.m1_unit.get(), v1_unit=self.v1_unit.get(),
                m2_unit=self.m2_unit.get(), v2_unit=self.v2_unit.get(),
            )

            unknown = results["unknown"]
            value = results["result"]
            unit = results["result_unit"]
            self.dil_result_var.set(f"{unknown} = {value:.6g} {unit}")

            self.dil_steps_box.configure(state="normal")
            self.dil_steps_box.delete("1.0", "end")
            for s in steps:
                self.dil_steps_box.insert("end", f"{s}\n")
            self.dil_steps_box.see("end")
            self.dil_steps_box.configure(state="normal")
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    # --- Redox balance tab ---
    def _build_redox_tab(self) -> None:
        container = self.redox_tab

        # Reaction input
        rxn_frame = ttk.Frame(container)
        rxn_frame.pack(fill="x", pady=4)
        ttk.Label(rxn_frame, text="Reaction:").grid(row=0, column=0, sticky="w")
        self.redox_rxn = tk.StringVar(value="Fe2+ + MnO4- + H+ -> Fe3+ + Mn2+ + H2O")
        ttk.Entry(rxn_frame, textvariable=self.redox_rxn, width=70).grid(row=0, column=1, padx=6, sticky="w")

        # Medium selection
        medium_frame = ttk.Frame(container)
        medium_frame.pack(fill="x", pady=4)
        ttk.Label(medium_frame, text="Medium:").grid(row=0, column=0, sticky="w")
        self.medium_var = tk.StringVar(value="neutral")
        medium_radio = ttk.Frame(medium_frame)
        medium_radio.grid(row=0, column=1, padx=6, sticky="w")
        ttk.Radiobutton(medium_radio, text="Neutral", variable=self.medium_var, value="neutral").pack(side="left", padx=(0, 8))
        ttk.Radiobutton(medium_radio, text="Acidic", variable=self.medium_var, value="acid").pack(side="left", padx=(0, 8))
        ttk.Radiobutton(medium_radio, text="Basic", variable=self.medium_var, value="base").pack(side="left")

        ttk.Button(container, text="Balance Redox", command=self._on_balance_redox).pack(anchor="w", pady=8)

        # Results
        self.redox_result = tk.StringVar()
        ttk.Label(container, textvariable=self.redox_result, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(4, 2))

        # Coefficients
        ttk.Label(container, text="Coefficients:").pack(anchor="w")
        self.redox_coeffs = scrolledtext.ScrolledText(container, height=8, wrap="word")
        self.redox_coeffs.pack(fill="both", expand=True)

        # Steps
        ttk.Label(container, text="Steps:").pack(anchor="w")
        self.redox_steps = scrolledtext.ScrolledText(container, height=12, wrap="word")
        self.redox_steps.pack(fill="both", expand=True)

    def _on_balance_redox(self) -> None:
        try:
            equation = self.redox_rxn.get().strip()
            medium = self.medium_var.get()
            
            if not equation:
                messagebox.showerror("Error", "Please enter a reaction equation")
                return

            result, steps, meta = balance_redox_with_steps(equation, medium)
            
            # Display balanced equation
            self.redox_result.set(f"Balanced: {result}")
            
            # Display coefficients
            self.redox_coeffs.configure(state="normal")
            self.redox_coeffs.delete("1.0", "end")
            for i, species in enumerate(meta['species_order']):
                self.redox_coeffs.insert("end", f"{species}: {meta['coefficients'][i]}\n")
            self.redox_coeffs.see("end")
            self.redox_coeffs.configure(state="normal")
            
            # Display steps
            self.redox_steps.configure(state="normal")
            self.redox_steps.delete("1.0", "end")
            for step in steps:
                self.redox_steps.insert("end", f"{step}\n")
            self.redox_steps.see("end")
            self.redox_steps.configure(state="normal")
            
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

class GibbsPage(ttk.Frame):
    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent)
        header = ttk.Label(self, text="🔥 Gibbs Free Energy Calculator", font=("Segoe UI", 14, "bold"))
        header.pack(anchor="w")
        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=8)

        grid = ttk.Frame(self)
        grid.pack(fill="x", pady=4)

        # ΔH
        ttk.Label(grid, text="ΔH Value:").grid(row=0, column=0, sticky="w")
        self.h_val = tk.DoubleVar(value=-100.0)
        ttk.Entry(grid, textvariable=self.h_val, width=12).grid(row=0, column=1, padx=6, sticky="w")
        ttk.Label(grid, text="ΔH Unit:").grid(row=0, column=2, sticky="w")
        self.h_unit = tk.StringVar(value="kJ/mol")
        ttk.Combobox(grid, textvariable=self.h_unit, values=["kJ/mol", "J/mol"], width=10, state="readonly").grid(row=0, column=3, padx=6, sticky="w")

        # ΔS
        ttk.Label(grid, text="ΔS Value:").grid(row=1, column=0, sticky="w")
        self.s_val = tk.DoubleVar(value=200.0)
        ttk.Entry(grid, textvariable=self.s_val, width=12).grid(row=1, column=1, padx=6, sticky="w")
        ttk.Label(grid, text="ΔS Unit:").grid(row=1, column=2, sticky="w")
        self.s_unit = tk.StringVar(value="J/(mol·K)")
        ttk.Combobox(
            grid,
            textvariable=self.s_unit,
            values=["J/(mol·K)", "kJ/(mol·K)"],
            width=12,
            state="readonly",
        ).grid(row=1, column=3, padx=6, sticky="w")

        # Temperature
        ttk.Label(grid, text="Temperature:").grid(row=2, column=0, sticky="w")
        self.t_val = tk.DoubleVar(value=298.15)
        ttk.Entry(grid, textvariable=self.t_val, width=12).grid(row=2, column=1, padx=6, sticky="w")
        ttk.Label(grid, text="Temp Unit:").grid(row=2, column=2, sticky="w")
        self.t_unit = tk.StringVar(value="K")
        ttk.Combobox(grid, textvariable=self.t_unit, values=["K", "°C"], width=8, state="readonly").grid(row=2, column=3, padx=6, sticky="w")

        ttk.Button(self, text="Calculate ΔG", command=self._on_calculate).pack(anchor="w", pady=10)

        self.result_var = tk.StringVar()
        ttk.Label(self, textvariable=self.result_var, font=("Segoe UI", 11, "bold")).pack(anchor="w")

        self.info_var = tk.StringVar()
        ttk.Label(self, textvariable=self.info_var).pack(anchor="w", pady=(4, 0))

        ttk.Label(self, text="Steps:").pack(anchor="w", pady=(12, 0))
        self.steps_box = scrolledtext.ScrolledText(self, height=16, wrap="word")
        self.steps_box.pack(fill="both", expand=True)

    def _on_calculate(self) -> None:
        try:
            dh = float(self.h_val.get())
            ds = float(self.s_val.get())
            t = float(self.t_val.get())
            result, steps, meta = calculate_gibbs_free_energy_with_steps(
                dh, self.h_unit.get(), ds, self.s_unit.get(), t, self.t_unit.get()
            )

            self.result_var.set(f"ΔG = {result:.2f} kJ/mol")
            spontaneity = meta.get("spontaneity")
            if spontaneity == "spontaneous":
                self.info_var.set("Reaction is SPONTANEOUS at this temperature")
            elif spontaneity == "non-spontaneous":
                self.info_var.set("Reaction is NON-SPONTANEOUS at this temperature")
            else:
                self.info_var.set("Reaction is at EQUILIBRIUM at this temperature")

            self.steps_box.configure(state="normal")
            self.steps_box.delete("1.0", "end")
            for s in steps:
                self.steps_box.insert("end", f"{s}\n")
            self.steps_box.see("end")
            self.steps_box.configure(state="normal")
        except Exception as exc:
            messagebox.showerror("Error", str(exc))


if __name__ == "__main__":
    app = App()
    app.mainloop()


