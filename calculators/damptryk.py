"""Streamlit UI for vapor pressure calculations.

The page currently focuses on the two-point Clausius-Clapeyron equation and
keeps the UI logic thin so the calculation engine remains in core/.
"""

from __future__ import annotations

from typing import Optional

import streamlit as st

from core.clausius_clapeyron import (
    ClausiusClapeyronProblem,
    collect_validation_errors,
    solve_clausius_clapeyron,
)


PRESSURE_UNITS = ["atm", "Pa", "kPa", "bar", "mmHg", "torr"]
TEMPERATURE_UNITS = ["K", "°C"]
ENTHALPY_UNITS = ["kJ/mol", "J/mol", "kJ/g", "J/g"]
UNKNOWN_OPTIONS = ["P1", "P2", "T1", "T2", "ΔHvap"]
UNKNOWN_TO_INTERNAL = {
    "P1": "P1",
    "P2": "P2",
    "T1": "T1",
    "T2": "T2",
    "ΔHvap": "deltaHvap",
}


def render_damptryk_page() -> None:
    """Render the Damptryk landing page and the Clausius-Clapeyron subpage."""
    st.title("🌫️ Damptryk")
    st.markdown("---")

    st.markdown(
        """
        Clausius-Clapeyron-ligningen bruges til at forbinde damptryk og temperatur.
        Temperaturen behandles altid internt i Kelvin, og tryk konverteres til et
        fælles SI-lag, før der beregnes.
        """
    )
    st.latex(r"\ln\left(\frac{P_2}{P_1}\right) = -\frac{\Delta H_{vap}}{R}\left(\frac{1}{T_2}-\frac{1}{T_1}\right)")
    st.caption("Ved energi angivet per gram kræves molarmasse for omregning til J/mol.")
    st.caption("Hvis kogepunktet er angivet, svarer P1 til 1 atm, og T1 svarer til det angivne kogepunkt.")

    overview_col1, overview_col2 = st.columns([2, 1])
    with overview_col1:
        st.info(
            "Denne side understøtter beregning af P1, P2, T1, T2 eller ΔHvap, "
            "så længe præcis én variabel er ukendt."
        )
    with overview_col2:
        st.markdown(
            """
            **Under sider**

            - Clausius-Clapeyron
            """
        )

    clausius_tab = st.tabs(["Clausius-Clapeyron"])[0]
    with clausius_tab:
        _render_clausius_clapeyron_calculator()


def _render_clausius_clapeyron_calculator() -> None:
    st.markdown("#### Clausius-Clapeyron (to-punkts-form)")
    st.markdown(
        "Indtast fire kendte værdier, vælg hvilken variabel der er ukendt, og lad "
        "systemet løse den sidste størrelse automatisk."
    )

    unknown_label = st.selectbox(
        "Beregn",
        UNKNOWN_OPTIONS,
        index=_get_default_unknown_index(),
        key="damptryk_unknown",
    )
    unknown_internal = UNKNOWN_TO_INTERNAL[unknown_label]

    st.info(
        f"{unknown_label} beregnes automatisk. Feltet er låst, så du kun kan indtaste i de øvrige felter."
    )

    with st.form("damptryk_clausius_form", clear_on_submit=False):
        left_col, right_col = st.columns(2)

        with left_col:
            p1_raw = _render_numeric_field(
                label="P1",
                placeholder="Fx 1.0",
                unit_key="damptryk_p1_unit",
                unit_options=PRESSURE_UNITS,
                default_unit="atm",
                disabled=unknown_internal == "P1",
                value_key="damptryk_p1_value",
                unknown_label=unknown_label,
            )
            p2_raw = _render_numeric_field(
                label="P2",
                placeholder="Fx 0.473",
                unit_key="damptryk_p2_unit",
                unit_options=PRESSURE_UNITS,
                default_unit="atm",
                disabled=unknown_internal == "P2",
                value_key="damptryk_p2_value",
                unknown_label=unknown_label,
            )

        with right_col:
            t1_raw = _render_numeric_field(
                label="T1",
                placeholder="Fx 373.15",
                unit_key="damptryk_t1_unit",
                unit_options=TEMPERATURE_UNITS,
                default_unit="K",
                disabled=unknown_internal == "T1",
                value_key="damptryk_t1_value",
                unknown_label=unknown_label,
            )
            t2_raw = _render_numeric_field(
                label="T2",
                placeholder="Fx 353.15",
                unit_key="damptryk_t2_unit",
                unit_options=TEMPERATURE_UNITS,
                default_unit="K",
                disabled=unknown_internal == "T2",
                value_key="damptryk_t2_value",
                unknown_label=unknown_label,
            )

        delta_hvap_raw, delta_hvap_unit = _render_enthalpy_field(
            disabled=unknown_internal == "deltaHvap",
            unknown_label=unknown_label,
        )

        molar_mass_raw = None
        if delta_hvap_unit.endswith("/g"):
            molar_mass_raw = st.text_input(
                "Molarmasse (g/mol)",
                key="damptryk_molar_mass_value",
                placeholder="Påkrævet ved J/g eller kJ/g",
            )
        else:
            st.session_state.pop("damptryk_molar_mass_value", None)

        submitted = st.form_submit_button("Beregn", type="primary")

    reset_col1, reset_col2 = st.columns([1, 4])
    with reset_col1:
        reset_clicked = st.button("Nulstil", key="damptryk_reset")
    with reset_col2:
        st.caption("Temperatur omregnes internt til Kelvin før beregning.")

    if reset_clicked:
        _reset_damptryk_state()
        st.rerun()

    if not submitted:
        return

    try:
        problem = ClausiusClapeyronProblem(
            unknown=unknown_internal,
            p1=_parse_optional_float(p1_raw),
            p1_unit=st.session_state.get("damptryk_p1_unit", "atm"),
            p2=_parse_optional_float(p2_raw),
            p2_unit=st.session_state.get("damptryk_p2_unit", "atm"),
            t1=_parse_optional_float(t1_raw),
            t1_unit=st.session_state.get("damptryk_t1_unit", "K"),
            t2=_parse_optional_float(t2_raw),
            t2_unit=st.session_state.get("damptryk_t2_unit", "K"),
            delta_hvap=_parse_optional_float(delta_hvap_raw),
            delta_hvap_unit=delta_hvap_unit,
            molar_mass_g_per_mol=_parse_optional_float(molar_mass_raw) if molar_mass_raw is not None else None,
        )

        validation_errors = collect_validation_errors(problem)
        if validation_errors:
            raise ValueError("; ".join(validation_errors))

        solution = solve_clausius_clapeyron(problem)

        st.success("Beregning gennemført")

        result_col1, result_col2 = st.columns(2)
        with result_col1:
            st.metric(
                label=f"Resultat ({solution.unit})",
                value=_format_result(solution.value, solution.unit),
            )
        with result_col2:
            st.metric(
                label=f"SI-visning ({solution.si_unit})",
                value=_format_result(solution.value_si, solution.si_unit),
            )

        if solution.unknown in {"T1", "T2"} and solution.unit == "°C":
            st.caption(f"Internt bruges {solution.value_si:.6g} K.")
        elif solution.unknown == "deltaHvap" and solution.unit.endswith("/g"):
            st.caption(f"Intern standardværdi: {solution.value_si:.6g} J/mol.")

        with st.expander("Vis mellemregninger", expanded=False):
            for step in solution.steps:
                st.markdown(f"- {step}")

        _append_history(solution)
        _render_history()

    except Exception as exc:
        st.error(str(exc))


def _render_numeric_field(
    *,
    label: str,
    placeholder: str,
    unit_key: str,
    unit_options: list[str],
    default_unit: str,
    disabled: bool,
    value_key: str,
    unknown_label: str,
) -> str:
    value_col, unit_col = st.columns([3, 1])
    with value_col:
        raw_value = st.text_input(
            f"{label} (beregnes)" if disabled else label,
            key=value_key,
            placeholder=placeholder,
            disabled=disabled,
            help="Denne størrelse beregnes automatisk." if disabled else None,
        )
    with unit_col:
        st.selectbox(
            "Enhed",
            unit_options,
            index=unit_options.index(default_unit),
            key=unit_key,
            help=f"Outputenhed for {unknown_label}." if disabled else None,
        )
    return raw_value


def _render_enthalpy_field(*, disabled: bool, unknown_label: str) -> tuple[str, str]:
    value_col, unit_col = st.columns([3, 1])
    with value_col:
        raw_value = st.text_input(
            "ΔHvap (beregnes)" if disabled else "ΔHvap",
            key="damptryk_delta_hvap_value",
            placeholder="Fx 40.65",
            disabled=disabled,
            help="Denne størrelse beregnes automatisk." if disabled else None,
        )
    with unit_col:
        unit = st.selectbox(
            "Enhed",
            ENTHALPY_UNITS,
            index=0,
            key="damptryk_delta_hvap_unit",
            help=f"Outputenhed for {unknown_label}." if disabled else None,
        )
    return raw_value, unit


def _parse_optional_float(raw_value: Optional[str]) -> Optional[float]:
    if raw_value is None:
        return None
    text = raw_value.strip().replace(",", ".")
    if not text:
        return None
    return float(text)


def _format_result(value: float, unit: str) -> str:
    if abs(value) >= 1e4 or (0 < abs(value) < 1e-3):
        return f"{value:.6e} {unit}"
    return f"{value:.6g} {unit}"


def _append_history(solution) -> None:
    history = st.session_state.setdefault("damptryk_history", [])
    history.insert(0, {"unknown": solution.unknown, "value": solution.value, "unit": solution.unit})
    del history[5:]


def _render_history() -> None:
    history = st.session_state.get("damptryk_history", [])
    if not history:
        return
    with st.expander("Seneste beregninger", expanded=False):
        for entry in history:
            st.markdown(f"- {entry['unknown']}: {_format_result(entry['value'], entry['unit'])}")


def _get_default_unknown_index() -> int:
    default_unknown = st.session_state.get("damptryk_unknown", "P2")
    try:
        return UNKNOWN_OPTIONS.index(default_unknown)
    except ValueError:
        return 1


def _reset_damptryk_state() -> None:
    keys_to_clear = [
        "damptryk_unknown",
        "damptryk_p1_value",
        "damptryk_p1_unit",
        "damptryk_p2_value",
        "damptryk_p2_unit",
        "damptryk_t1_value",
        "damptryk_t1_unit",
        "damptryk_t2_value",
        "damptryk_t2_unit",
        "damptryk_delta_hvap_value",
        "damptryk_delta_hvap_unit",
        "damptryk_molar_mass_value",
        "damptryk_history",
    ]
    for key in keys_to_clear:
        st.session_state.pop(key, None)
