"""UI renderer for boiling/freezing point calculators.

Currently includes the freezing-point depression calculator.
"""

from __future__ import annotations

from typing import Optional

import streamlit as st

from core.freezing_point_depression import (
    FreezingPointDepressionInput,
    convert_kf_to_c_kg_per_mol,
    convert_mass_to_g,
    convert_mass_to_kg,
    convert_molar_mass_to_g_per_mol,
    solve_freezing_point_depression,
    validate_freezing_point_inputs,
)
from core.boiling_point_elevation import (
    BoilingPointElevationInput,
    solve_boiling_point_elevation,
    validate_boiling_point_inputs,
)
from core.osmotic_pressure import (
    OsmoticPressureInput,
    solve_osmotic_pressure,
    validate_osmotic_pressure_inputs,
)


def render_kogepunkt_frysepunkt_page() -> None:
    st.title("🌡️ Koge- og frysepunkt (colligative properties)")
    st.markdown("---")

    tab_boiling, tab_freezing, tab_osmotic = st.tabs(["Kogepunktsforhøjelse", "Frysepunktsnedsættelse", "Osmotisk tryk"])
    with tab_boiling:
        _render_boiling_point_elevation_tab()
    with tab_freezing:
        _render_freezing_point_depression_tab()
    with tab_osmotic:
        _render_osmotic_pressure_tab()


def _render_boiling_point_elevation_tab() -> None:
    st.markdown("#### Kogepunktsforhøjelse")
    st.markdown("Formel: kogepunktet STIGER")
    st.latex(r"\Delta T_b = i \cdot K_b \cdot m")
    st.caption("Vælg enheder for input. Beregningen omregner automatisk til g, g/mol, kg og °C internt.")

    with st.form("boiling_point_elevation_form", clear_on_submit=False):
        col_left, col_right = st.columns(2)

        with col_left:
            mass_row1, mass_row2 = st.columns([3, 2])
            with mass_row1:
                mass_solute_raw = st.text_input(
                    "Masse af opløst stof",
                    key="bp_mass_solute_value",
                    placeholder="Fx 60",
                )
            with mass_row2:
                mass_solute_unit = st.selectbox(
                    "Enhed",
                    options=["g", "kg", "mg"],
                    key="bp_mass_solute_unit",
                )

            mm_row1, mm_row2 = st.columns([3, 2])
            with mm_row1:
                molar_mass_raw = st.text_input(
                    "Molarmasse for det opløste stof",
                    key="bp_molar_mass_value",
                    placeholder="Fx 180.156",
                )
            with mm_row2:
                molar_mass_unit = st.selectbox(
                    "Enhed",
                    options=["g/mol", "kg/mol"],
                    key="bp_molar_mass_unit",
                )

            ms_row1, ms_row2 = st.columns([3, 2])
            with ms_row1:
                mass_solvent_raw = st.text_input(
                    "Masse af opløsningsmiddel",
                    key="bp_mass_solvent_value",
                    placeholder="Fx 0.200",
                )
            with ms_row2:
                mass_solvent_unit = st.selectbox(
                    "Enhed",
                    options=["kg", "g", "mg"],
                    key="bp_mass_solvent_unit",
                )

        with col_right:
            i_raw = st.text_input(
                "van't Hoff-faktor i",
                key="bp_vant_hoff_i",
                placeholder="Fx 1",
                help="Indtastes manuelt. Eksempel: glucose=1, NaCl=2.",
            )

            kb_row1, kb_row2 = st.columns([3, 2])
            with kb_row1:
                kb_raw = st.text_input(
                    "Kogepunktskonstant K_b",
                    key="bp_kb_value",
                    placeholder="Fx 0.512",
                )
            with kb_row2:
                kb_unit = st.selectbox(
                    "Enhed",
                    options=["°C·kg/mol", "K·kg/mol"],
                    key="bp_kb_unit",
                )

            bp_row1, bp_row2 = st.columns([3, 2])
            with bp_row1:
                start_boiling_raw = st.text_input(
                    "Start-kogepunkt",
                    key="bp_start_boiling_value",
                    placeholder="Fx 100",
                )
            with bp_row2:
                start_boiling_unit = st.selectbox(
                    "Enhed",
                    options=["°C", "K", "°F"],
                    key="bp_start_boiling_unit",
                )

        submit = st.form_submit_button("Beregn", type="primary")

    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        if st.button("Brug vand", key="bp_use_water"):
            st.session_state["bp_kb_value"] = "0.512"
            st.session_state["bp_kb_unit"] = "°C·kg/mol"
            st.session_state["bp_start_boiling_value"] = "100"
            st.session_state["bp_start_boiling_unit"] = "°C"
            st.rerun()
    with col_btn2:
        if st.button("Nulstil", key="bp_reset"):
            _reset_boiling_point_state()
            st.rerun()

    if not submit:
        return

    try:
        data = BoilingPointElevationInput(
            mass_solute_g=_parse_required_float(mass_solute_raw, "Masse af opløst stof"),
            mass_solute_unit=mass_solute_unit,
            molar_mass_g_per_mol=_parse_required_float(molar_mass_raw, "Molarmasse for det opløste stof"),
            molar_mass_unit=molar_mass_unit,
            mass_solvent_kg=_parse_required_float(mass_solvent_raw, "Masse af opløsningsmiddel"),
            mass_solvent_unit=mass_solvent_unit,
            vant_hoff_i=_parse_required_float(i_raw, "van't Hoff-faktor i"),
            kb_c_kg_per_mol=_parse_required_float(kb_raw, "Kogepunktskonstant K_b"),
            kb_unit=kb_unit,
            start_boiling_point_c=_parse_required_float(start_boiling_raw, "Start-kogepunkt"),
            start_boiling_point_unit=start_boiling_unit,
        )

        validation_errors = validate_boiling_point_inputs(data)
        if validation_errors:
            raise ValueError("; ".join(validation_errors))

        result = solve_boiling_point_elevation(data)

        st.success("Beregning gennemført")
        out_col1, out_col2 = st.columns(2)
        with out_col1:
            st.metric("Stofmængde n", f"{result.n_mol:.6g} mol")
            st.metric("Molalitet m", f"{result.molality_mol_per_kg:.6g} mol/kg")
        with out_col2:
            st.metric("Kogepunktet stiger med (ΔT_b)", f"{result.delta_tb_c:.6g} °C")
            st.metric("Nyt kogepunkt", f"{result.new_boiling_point_c:.6g} °C")

        with st.expander("Vis mellemregninger", expanded=False):
            for step in result.steps:
                st.markdown(f"- {step}")

    except Exception as exc:
        st.error(str(exc))


def _render_freezing_point_depression_tab() -> None:
    st.markdown("#### Frysepunktsnedsættelse")
    st.markdown("Formel:")
    st.latex(r"\Delta T_f = i \cdot K_f \cdot m")
    st.caption("Vælg enheder for input/output. Beregningen omregner automatisk til korrekte SI-basenheder internt.")

    with st.form("freezing_point_depression_form", clear_on_submit=False):
        col_left, col_right = st.columns(2)

        with col_left:
            c1a, c1b = st.columns([3, 2])
            with c1a:
                mass_solute_raw = st.text_input(
                    "Masse af opløst stof",
                    key="fp_mass_solute_value",
                    placeholder="Fx 60",
                )
            with c1b:
                mass_solute_unit = st.selectbox(
                    "Enhed",
                    options=["g", "kg", "mg"],
                    key="fp_mass_solute_unit",
                )

            c2a, c2b = st.columns([3, 2])
            with c2a:
                molar_mass_raw = st.text_input(
                    "Molarmasse for det opløste stof",
                    key="fp_molar_mass_value",
                    placeholder="Fx 180.156",
                )
            with c2b:
                molar_mass_unit = st.selectbox(
                    "Enhed",
                    options=["g/mol", "kg/mol"],
                    key="fp_molar_mass_unit",
                )

            c3a, c3b = st.columns([3, 2])
            with c3a:
                mass_solvent_raw = st.text_input(
                    "Masse af opløsningsmiddel",
                    key="fp_mass_solvent_value",
                    placeholder="Fx 0.200",
                )
            with c3b:
                mass_solvent_unit = st.selectbox(
                    "Enhed",
                    options=["kg", "g", "mg"],
                    key="fp_mass_solvent_unit",
                )

        with col_right:
            i_raw = st.text_input(
                "van't Hoff-faktor i",
                key="fp_vant_hoff_i",
                placeholder="Fx 1",
                help="Typisk: glucose=1, NaCl=2, H2SO4=3.",
            )
            c4a, c4b = st.columns([3, 2])
            with c4a:
                kf_raw = st.text_input(
                    "Frysepunktskonstant K_f",
                    key="fp_kf_value",
                    placeholder="Fx 1.86",
                )
            with c4b:
                kf_unit = st.selectbox(
                    "K_f enhed",
                    options=["°C·kg/mol", "K·kg/mol"],
                    key="fp_kf_unit",
                )

        submit = st.form_submit_button("Beregn", type="primary")

    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        if st.button("Brug vand", key="fp_use_water"):
            st.session_state["fp_kf_value"] = "1.86"
            st.session_state["fp_kf_unit"] = "°C·kg/mol"
            st.rerun()
    with col_btn2:
        if st.button("Nulstil", key="fp_reset"):
            _reset_freezing_point_state()
            st.rerun()

    if not submit:
        return

    try:
        mass_solute_value = _parse_required_float(mass_solute_raw, "Masse af opløst stof")
        molar_mass_value = _parse_required_float(molar_mass_raw, "Molarmasse")
        mass_solvent_value = _parse_required_float(mass_solvent_raw, "Masse af opløsningsmiddel")
        kf_value = _parse_required_float(kf_raw, "Frysepunktskonstant K_f")

        data = FreezingPointDepressionInput(
            mass_solute_g=convert_mass_to_g(mass_solute_value, mass_solute_unit),
            molar_mass_g_per_mol=convert_molar_mass_to_g_per_mol(molar_mass_value, molar_mass_unit),
            mass_solvent_kg=convert_mass_to_kg(mass_solvent_value, mass_solvent_unit),
            vant_hoff_i=_parse_required_float(i_raw, "van't Hoff-faktor i"),
            kf_c_kg_per_mol=convert_kf_to_c_kg_per_mol(kf_value, kf_unit),
        )

        validation_errors = validate_freezing_point_inputs(data)
        if validation_errors:
            raise ValueError("; ".join(validation_errors))

        result = solve_freezing_point_depression(data)

        st.success("Beregning gennemført")
        out_col1, out_col2 = st.columns(2)
        with out_col1:
            st.metric("Stofmængde n", f"{result.n_mol:.6g} mol")
            st.metric("Molalitet m", f"{result.molality_mol_per_kg:.6g} mol/kg")
        with out_col2:
            st.metric("Frysepunktet falder med (ΔT_f)", f"{result.delta_tf_c:.6g} °C")
            st.metric("Frysepunktet falder med (ΔT_f)", f"{result.delta_tf_c:.6g} K")

        with st.expander("Vis mellemregninger", expanded=False):
            for step in result.steps:
                st.markdown(f"- {step}")

    except Exception as exc:
        st.error(str(exc))


def _render_osmotic_pressure_tab() -> None:
    st.markdown("#### Osmotisk tryk")
    st.markdown("Formel:")
    st.latex(r"\pi = i \cdot M \cdot R \cdot T")
    st.caption("Hvis du vælger Pa, omregnes volumen internt fra L til m³, så enhederne passer til gaskonstanten.")

    with st.form("osmotic_pressure_form", clear_on_submit=False):
        col_left, col_right = st.columns(2)

        with col_left:
            mass_row1, mass_row2 = st.columns([3, 2])
            with mass_row1:
                mass_solute_raw = st.text_input(
                    "Masse af opløst stof",
                    key="op_mass_solute_value",
                    placeholder="Fx 10",
                )
            with mass_row2:
                mass_solute_unit = st.selectbox(
                    "Enhed",
                    options=["g", "kg", "mg"],
                    key="op_mass_solute_unit",
                )

            mm_row1, mm_row2 = st.columns([3, 2])
            with mm_row1:
                molar_mass_raw = st.text_input(
                    "Molarmasse",
                    key="op_molar_mass_value",
                    placeholder="Fx 58.44",
                )
            with mm_row2:
                molar_mass_unit = st.selectbox(
                    "Enhed",
                    options=["g/mol", "kg/mol"],
                    key="op_molar_mass_unit",
                )

            vol_row1, vol_row2 = st.columns([3, 2])
            with vol_row1:
                volume_raw = st.text_input(
                    "Volumen af opløsning",
                    key="op_volume_value",
                    placeholder="Fx 1.0",
                    help="Volumen kan indtastes i L, mL eller m³.",
                )
            with vol_row2:
                volume_unit = st.selectbox(
                    "Enhed",
                    options=["L", "mL", "m³"],
                    key="op_volume_unit",
                )

        with col_right:
            temp_row1, temp_row2 = st.columns([3, 2])
            with temp_row1:
                temperature_raw = st.text_input(
                    "Temperatur",
                    key="op_temperature_value",
                    placeholder="Fx 25",
                    help="Temperaturen må gerne være negativ i °C.",
                )
            with temp_row2:
                temperature_unit = st.selectbox(
                    "Enhed",
                    options=["°C", "K", "°F"],
                    key="op_temperature_unit",
                )

            i_raw = st.text_input(
                "van't Hoff-faktor i",
                key="op_vant_hoff_i",
                placeholder="Fx 2",
                help="Indtastes manuelt. Eksempel: glucose=1, NaCl=2.",
            )
            pressure_unit = st.selectbox(
                "Trykenhed",
                options=["atm", "Pa"],
                key="op_pressure_unit",
                help="R vælges automatisk ud fra den valgte enhed.",
            )

        submit = st.form_submit_button("Beregn", type="primary")

    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        if st.button("Nulstil", key="op_reset"):
            _reset_osmotic_pressure_state()
            st.rerun()

    if not submit:
        return

    try:
        data = OsmoticPressureInput(
            mass_solute_g=_parse_required_float(mass_solute_raw, "Masse af opløst stof"),
            mass_solute_unit=mass_solute_unit,
            molar_mass_g_per_mol=_parse_required_float(molar_mass_raw, "Molarmasse"),
            molar_mass_unit=molar_mass_unit,
            volume_solution_l=_parse_required_float(volume_raw, "Volumen af opløsning"),
            volume_unit=volume_unit,
            temperature_c=_parse_required_float(temperature_raw, "Temperatur"),
            temperature_unit=temperature_unit,
            vant_hoff_i=_parse_required_float(i_raw, "van't Hoff-faktor i"),
            pressure_unit=pressure_unit,
        )

        validation_errors = validate_osmotic_pressure_inputs(data)
        if validation_errors:
            raise ValueError("; ".join(validation_errors))

        result = solve_osmotic_pressure(data)

        st.success("Beregning gennemført")
        out_col1, out_col2 = st.columns(2)
        with out_col1:
            st.metric("Stofmængde n", f"{result.n_mol:.6g} mol")
            st.metric("Molaritet M", f"{result.molarity_mol_per_l:.6g} mol/L")
        with out_col2:
            st.metric("Temperatur i Kelvin", f"{result.temperature_k:.6g} K")
            st.metric("Osmotisk tryk π", f"{result.osmotic_pressure:.6g} {result.pressure_unit}")

        with st.expander("Vis mellemregninger", expanded=False):
            for step in result.steps:
                st.markdown(f"- {step}")

    except Exception as exc:
        st.error(str(exc))


def _parse_required_float(raw_value: Optional[str], field_name: str) -> float:
    text = "" if raw_value is None else raw_value.strip().replace(",", ".")
    if not text:
        raise ValueError(f"{field_name} mangler.")
    try:
        return float(text)
    except ValueError as exc:
        raise ValueError(f"{field_name} skal være et gyldigt tal.") from exc


def _reset_freezing_point_state() -> None:
    keys = [
        "fp_mass_solute_value",
        "fp_mass_solute_unit",
        "fp_molar_mass_value",
        "fp_molar_mass_unit",
        "fp_mass_solvent_value",
        "fp_mass_solvent_unit",
        "fp_vant_hoff_i",
        "fp_kf_value",
        "fp_kf_unit",
    ]
    for key in keys:
        st.session_state.pop(key, None)


def _reset_boiling_point_state() -> None:
    keys = [
        "bp_mass_solute_value",
        "bp_mass_solute_unit",
        "bp_molar_mass_value",
        "bp_molar_mass_unit",
        "bp_mass_solvent_value",
        "bp_mass_solvent_unit",
        "bp_vant_hoff_i",
        "bp_kb_value",
        "bp_kb_unit",
        "bp_start_boiling_value",
        "bp_start_boiling_unit",
    ]
    for key in keys:
        st.session_state.pop(key, None)


def _reset_osmotic_pressure_state() -> None:
    keys = [
        "op_mass_solute_value",
        "op_mass_solute_unit",
        "op_molar_mass_value",
        "op_molar_mass_unit",
        "op_volume_value",
        "op_volume_unit",
        "op_temperature_value",
        "op_temperature_unit",
        "op_vant_hoff_i",
        "op_pressure_unit",
    ]
    for key in keys:
        st.session_state.pop(key, None)
