"""Interactive periodic table Streamlit tab."""

from __future__ import annotations

import html
from typing import Any, Dict, List, Optional, Set

import streamlit as st

from core.periodic_table import format_value, get_periodic_table_elements


CATEGORY_LABELS = {
    "alkali metal": "Alkalimetal",
    "alkaline earth metal": "Jordalkalimetal",
    "transition metal": "Overgangsmetal",
    "post-transition metal": "Post-transition metal",
    "metal": "Metal",
    "metalloid": "Halvmetal",
    "nonmetal": "Ikke-metal",
    "halogen": "Halogen",
    "noble gas": "Aedelgas",
    "lanthanide": "Lantanid",
    "actinide": "Aktinid",
    "unknown": "Ukendt",
}

CATEGORY_COLORS = {
    "alkali metal": "#f7d6b8",
    "alkaline earth metal": "#f6efbf",
    "transition metal": "#d4e3f5",
    "post-transition metal": "#dfe4ea",
    "metal": "#dfe4ea",
    "metalloid": "#d6eec7",
    "nonmetal": "#fde1d1",
    "halogen": "#d8f1da",
    "noble gas": "#d9e7ff",
    "lanthanide": "#eed8f6",
    "actinide": "#f6d8e8",
    "unknown": "#eceff1",
}

METAL_CATEGORIES = {
    "alkali metal",
    "alkaline earth metal",
    "transition metal",
    "post-transition metal",
    "metal",
    "lanthanide",
    "actinide",
}

TREND_OPTIONS = {
    "Kategori (standard)": "category",
    "Atomradius (pm)": "atomicRadius",
    "Elektronegativitet (Pauling)": "electronegativity",
    "1. ioniseringsenergi (kJ/mol)": "ionizationEnergy",
}


def _category_label(category: str) -> str:
    return CATEGORY_LABELS.get(category, category)


def _phase_label(phase: str) -> str:
    mapping = {"solid": "Fast", "liquid": "Vaeske", "gas": "Gas"}
    return mapping.get(phase, phase)


def _slug(text: str) -> str:
    return text.replace(" ", "-").replace("/", "-").lower()


def _trend_color(value: Optional[float], low: float, high: float) -> str:
    if value is None:
        return "#f3f4f6"
    if abs(high - low) < 1e-9:
        ratio = 0.5
    else:
        ratio = (value - low) / (high - low)
    ratio = max(0.0, min(1.0, ratio))
    light = int(240 - ratio * 80)
    sat = int(35 + ratio * 45)
    return f"hsl(198, {sat}%, {light}%)"


def _build_element_map(elements: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {element["symbol"]: element for element in elements}


def _valence_electrons(element: Dict[str, Any]) -> int:
    """Estimate Lewis valence electrons from outer shell (fallback: main-group by group)."""
    symbol = str(element.get("symbol") or "")
    if symbol == "He":
        return 2

    shells = element.get("shells") or []
    if shells:
        try:
            outer = int(shells[-1])
            return max(0, min(8, outer))
        except (TypeError, ValueError, IndexError):
            pass

    group = element.get("group")
    if isinstance(group, (int, float)):
        g = int(group)
        if 1 <= g <= 2:
            return g
        if 13 <= g <= 18:
            return g - 10
    return 0


def _render_lewis_symbol_html(symbol: str, valence: int, extra_class: str = "") -> str:
    """Render Lewis symbol using up to eight dots distributed around four sides."""
    valence = max(0, min(8, int(valence)))
    sides = ["top", "right", "bottom", "left"]
    counts = {side: 0 for side in sides}

    for i in range(min(valence, 4)):
        counts[sides[i]] += 1
    for i in range(min(max(valence - 4, 0), 4)):
        counts[sides[i]] += 1

    side_html: List[str] = []
    for side in sides:
        dot_count = counts[side]
        if dot_count <= 0:
            continue
        dots = "".join("<span class='pt-lewis-dot'>•</span>" for _ in range(dot_count))
        side_html.append(f"<div class='pt-lewis-side pt-lewis-{side}'>{dots}</div>")

    class_attr = "pt-lewis" + (f" {extra_class}" if extra_class else "")
    return (
        f"<div class='{class_attr}' aria-label='Lewis symbol'>"
        + "".join(side_html)
        + f"<span class='pt-lewis-symbol'>{html.escape(symbol)}</span>"
        + "</div>"
    )


def _matches_filters(element: Dict[str, Any], selected: Dict[str, Set[Any]]) -> bool:
    if selected["category"] and element["category"] not in selected["category"]:
        return False
    if selected["block"] and element["block"] not in selected["block"]:
        return False
    if selected["period"] and element["period"] not in selected["period"]:
        return False
    if selected["group"] and element["group"] not in selected["group"]:
        return False
    if selected["phase"] and element["phase"] not in selected["phase"]:
        return False
    return True


def _matches_search(element: Dict[str, Any], search: str) -> bool:
    if not search:
        return True
    query = search.strip().lower()
    if not query:
        return True

    if query == str(element["atomicNumber"]):
        return True

    haystacks = [
        str(element["symbol"]).lower(),
        str(element["name"]).lower(),
    ]
    return any(query in field for field in haystacks)


def _build_periodic_layout() -> Dict[str, Any]:
    """Return static periodic-table row layout used by the interactive grid."""
    main_rows = {
        1: {1: "H", 18: "He"},
        2: {1: "Li", 2: "Be", 13: "B", 14: "C", 15: "N", 16: "O", 17: "F", 18: "Ne"},
        3: {1: "Na", 2: "Mg", 13: "Al", 14: "Si", 15: "P", 16: "S", 17: "Cl", 18: "Ar"},
        4: {
            1: "K", 2: "Ca", 3: "Sc", 4: "Ti", 5: "V", 6: "Cr", 7: "Mn", 8: "Fe", 9: "Co", 10: "Ni",
            11: "Cu", 12: "Zn", 13: "Ga", 14: "Ge", 15: "As", 16: "Se", 17: "Br", 18: "Kr",
        },
        5: {
            1: "Rb", 2: "Sr", 3: "Y", 4: "Zr", 5: "Nb", 6: "Mo", 7: "Tc", 8: "Ru", 9: "Rh", 10: "Pd",
            11: "Ag", 12: "Cd", 13: "In", 14: "Sn", 15: "Sb", 16: "Te", 17: "I", 18: "Xe",
        },
        6: {
            1: "Cs", 2: "Ba", 3: "La", 4: "Hf", 5: "Ta", 6: "W", 7: "Re", 8: "Os", 9: "Ir", 10: "Pt",
            11: "Au", 12: "Hg", 13: "Tl", 14: "Pb", 15: "Bi", 16: "Po", 17: "At", 18: "Rn",
        },
        7: {
            1: "Fr", 2: "Ra", 3: "Ac", 4: "Rf", 5: "Db", 6: "Sg", 7: "Bh", 8: "Hs", 9: "Mt", 10: "Ds",
            11: "Rg", 12: "Cn", 13: "Nh", 14: "Fl", 15: "Mc", 16: "Lv", 17: "Ts", 18: "Og",
        },
    }
    lanth = ["La", "Ce", "Pr", "Nd", "Pm", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu"]
    act = ["Ac", "Th", "Pa", "U", "Np", "Pu", "Am", "Cm", "Bk", "Cf", "Es", "Fm", "Md", "No", "Lr"]
    return {"main_rows": main_rows, "lanth": lanth, "act": act}


def _render_clickable_grid(
    elements: List[Dict[str, Any]],
    visible_symbols: Set[str],
    selected_symbol: Optional[str],
) -> Optional[str]:
    by_symbol = _build_element_map(elements)
    layout = _build_periodic_layout()
    main_rows = layout["main_rows"]
    lanth = layout["lanth"]
    act = layout["act"]

    query_page_raw = st.query_params.get("page")
    if isinstance(query_page_raw, list):
        query_page_raw = query_page_raw[0] if query_page_raw else None
    query_page = str(query_page_raw).strip() if query_page_raw else ""

    query_atoms_tab_raw = st.query_params.get("atoms_tab")
    if isinstance(query_atoms_tab_raw, list):
        query_atoms_tab_raw = query_atoms_tab_raw[0] if query_atoms_tab_raw else None
    query_atoms_tab = str(query_atoms_tab_raw).strip() if query_atoms_tab_raw else ""

    picked_raw = st.query_params.get("pt_pick")
    if isinstance(picked_raw, list):
        picked_raw = picked_raw[0] if picked_raw else None
    clicked_symbol = str(picked_raw).strip() if picked_raw else None
    if clicked_symbol and clicked_symbol not in by_symbol:
        clicked_symbol = None

    def _render_row(row_map: Dict[int, str]) -> str:
        cells: List[str] = []
        for group in range(1, 19):
            symbol = row_map.get(group)
            if not symbol:
                cells.append("<div class='pt-cell pt-empty' aria-hidden='true'></div>")
                continue

            element = by_symbol[symbol]
            is_visible = symbol in visible_symbols
            classes = ["pt-cell", f"cat-{_slug(str(element['category']))}"]
            if symbol == selected_symbol:
                classes.append("is-selected")
            if not is_visible:
                classes.append("is-muted")

            mass = element.get("atomicMass")
            mass_text = "?" if mass is None else f"{mass:.3g}"
            title = (
                f"{element['name']} ({symbol})\n"
                f"Z={element['atomicNumber']}\n"
                f"Atommasse={mass_text} g/mol\n"
                f"Kategori={_category_label(str(element['category']))}"
            )
            body = (
                f"<span class='pt-z'>{element['atomicNumber']}</span>"
                f"<span class='pt-symbol'>{html.escape(symbol)}</span>"
                f"<span class='pt-mass'>{html.escape(mass_text)}</span>"
            )

            if is_visible:
                hidden_fields = [
                    f"<input type='hidden' name='pt_pick' value='{html.escape(symbol)}'>",
                ]
                if query_page:
                    hidden_fields.append(
                        f"<input type='hidden' name='page' value='{html.escape(query_page)}'>"
                    )
                if query_atoms_tab:
                    hidden_fields.append(
                        f"<input type='hidden' name='atoms_tab' value='{html.escape(query_atoms_tab)}'>"
                    )
                cells.append(
                    "<form class='pt-cell-form' method='get'>"
                    + "".join(hidden_fields)
                    + f"<button type='submit' class='{' '.join(classes)}' title='{html.escape(title)}'>"
                    + body
                    + "</button></form>"
                )
            else:
                cells.append(
                    f"<div class='{' '.join(classes)}' title='{html.escape(title)}' aria-disabled='true'>{body}</div>"
                )
        return "<div class='pt-row'>" + "".join(cells) + "</div>"

    html_rows = ["<div class='pt-grid'>"]
    for period in range(1, 8):
        html_rows.append(_render_row(main_rows.get(period, {})))
    html_rows.append("<div class='pt-gap-row'></div>")
    html_rows.append(_render_row({group: lanth[group - 3] for group in range(3, 18)}))
    html_rows.append(_render_row({group: act[group - 3] for group in range(3, 18)}))
    html_rows.append("</div>")
    st.markdown("".join(html_rows), unsafe_allow_html=True)
    return clicked_symbol


def _render_legend(trend_key: str, elements: List[Dict[str, Any]]) -> None:
    if trend_key == "category":
        labels = [
            "alkali metal", "alkaline earth metal", "transition metal", "post-transition metal", "metalloid",
            "nonmetal", "halogen", "noble gas", "lanthanide", "actinide",
        ]
        chips = []
        for category in labels:
            color = CATEGORY_COLORS.get(category, CATEGORY_COLORS["unknown"])
            chips.append(
                f'<span class="pt-legend-chip"><span class="pt-legend-swatch" style="background:{color};"></span>'
                f'{html.escape(_category_label(category))}</span>'
            )
        st.markdown("<div class='pt-legend'>" + "".join(chips) + "</div>", unsafe_allow_html=True)
        return

    values = [e.get(trend_key) for e in elements if isinstance(e.get(trend_key), (int, float))]
    if not values:
        st.caption("Ingen data til trend-visning.")
        return

    low = min(values)
    high = max(values)
    unit = {
        "atomicRadius": "pm",
        "electronegativity": "",
        "ionizationEnergy": "kJ/mol",
    }.get(trend_key, "")

    st.markdown(
        "<div class='pt-scale'>"
        "<span>Lav</span><div class='pt-scale-bar'></div><span>Hoj</span>"
        f"<span class='pt-scale-values'>{low:.3g} - {high:.3g} {unit}</span>"
        "</div>",
        unsafe_allow_html=True,
    )


def _render_css() -> None:
    st.markdown(
        """
<style>
.pt-shell { width: 100%; padding-bottom: 0.35rem; }
.pt-shell { overflow-x: auto; }
.pt-grid { width: max-content; min-width: 100%; display: flex; flex-direction: column; gap: 4px; }
.pt-row { display: grid; grid-template-columns: repeat(18, minmax(46px, 1fr)); gap: 4px; }
.pt-gap-row { height: 8px; }
.pt-cell-form { margin: 0; }
.pt-cell {
    border-radius: 0.35rem;
  border: 1px solid rgba(0,0,0,.12);
  color: #111827;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
    min-height: 52px;
    min-width: 46px;
  text-decoration: none;
    padding: 2px;
  transition: transform .08s ease, box-shadow .12s ease, border-color .12s ease;
}
.pt-cell-form button.pt-cell {
    width: 100%;
    cursor: pointer;
    font-family: inherit;
    appearance: none;
    -webkit-appearance: none;
}
.pt-cell:hover { transform: translateY(-1px); box-shadow: 0 2px 8px rgba(15,23,42,.16); }
.pt-cell:focus { outline: 3px solid #0f62fe; outline-offset: 1px; }
.pt-cell.is-selected {
    border-color: #0f62fe;
    border-width: 2px;
    box-shadow: 0 0 0 3px rgba(15,98,254,.28), 0 3px 10px rgba(15,23,42,.18);
}
.pt-cell.is-muted { opacity: .25; }
.pt-empty { background: transparent; border: none; min-height: 52px; }
.pt-z { font-size: 0.92rem; line-height: 1; }
.pt-symbol { font-size: 1.1rem; font-weight: 700; line-height: 1.05; }
.pt-mass { font-size: 1rem; line-height: 1; }
.pt-lewis {
    position: relative;
    width: 2.35rem;
    height: 1.45rem;
    display: flex;
    align-items: center;
    justify-content: center;
}
.pt-lewis-symbol {
    font-size: 1.1rem;
    font-weight: 700;
    line-height: 1;
}
.pt-lewis-side {
    position: absolute;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.08rem;
    line-height: 1;
    font-size: 0.95rem;
}
.pt-lewis-top { top: -0.25rem; left: 50%; transform: translateX(-50%); }
.pt-lewis-right { right: -0.34rem; top: 50%; transform: translateY(-50%); flex-direction: column; gap: 0; }
.pt-lewis-bottom { bottom: -0.25rem; left: 50%; transform: translateX(-50%); }
.pt-lewis-left { left: -0.34rem; top: 50%; transform: translateY(-50%); flex-direction: column; gap: 0; }
.pt-lewis-dot { display: inline-block; }
.pt-lewis-detail {
    width: 4.1rem;
    height: 2.9rem;
    margin: 0.15rem 0 0.25rem 0;
}
.pt-lewis-detail .pt-lewis-symbol {
    font-size: 1.35rem;
}
.pt-lewis-detail .pt-lewis-side {
    font-size: 1.1rem;
}
.pt-lewis-detail .pt-lewis-top { top: 0.0rem; }
.pt-lewis-detail .pt-lewis-right { right: 0.08rem; }
.pt-lewis-detail .pt-lewis-bottom { bottom: 0.0rem; }
.pt-lewis-detail .pt-lewis-left { left: 0.08rem; }
.pt-name { display: none; font-size: clamp(0.38rem, 0.72vw, 0.56rem); line-height: 1; margin-top: 0.08rem; text-align: center; }
@media (min-width: 1500px) { .pt-name { display: block; } }
.pt-cell.cat-alkali-metal { background: #f7d6b8; }
.pt-cell.cat-alkaline-earth-metal { background: #f6efbf; }
.pt-cell.cat-transition-metal { background: #d4e3f5; }
.pt-cell.cat-post-transition-metal { background: #dfe4ea; }
.pt-cell.cat-metal { background: #dfe4ea; }
.pt-cell.cat-metalloid { background: #d6eec7; }
.pt-cell.cat-nonmetal { background: #fde1d1; }
.pt-cell.cat-halogen { background: #d8f1da; }
.pt-cell.cat-noble-gas { background: #d9e7ff; }
.pt-cell.cat-lanthanide { background: #eed8f6; }
.pt-cell.cat-actinide { background: #f6d8e8; }
.pt-cell.cat-unknown { background: #eceff1; }
.pt-legend { display:flex; flex-wrap:wrap; gap:.45rem; margin: .45rem 0 .2rem 0; }
.pt-legend-chip { display:inline-flex; align-items:center; gap:.33rem; font-size:.78rem; background:#f8fafc; border:1px solid #e2e8f0; border-radius:.55rem; padding:.2rem .48rem; }
.pt-legend-swatch { width:.72rem; height:.72rem; border-radius:.18rem; border:1px solid rgba(15,23,42,.18); }
.pt-scale { display:flex; align-items:center; gap:.55rem; margin:.45rem 0; font-size:.78rem; }
.pt-scale-bar { width:170px; height:10px; border-radius:999px; border:1px solid rgba(15,23,42,.22); background: linear-gradient(90deg, hsl(198,35%,88%), hsl(198,80%,55%)); }
.pt-scale-values { color:#334155; }
.pt-section-title { margin-top:.6rem; margin-bottom:.2rem; font-weight:600; }
</style>
        """,
        unsafe_allow_html=True,
    )


def _badge_list(element: Dict[str, Any]) -> List[str]:
    badges: List[str] = []
    if element.get("isDiatomic"):
        badges.append("Diatomisk")
    if element.get("category") == "noble gas":
        badges.append("Aedelgas")
    if element.get("category") in METAL_CATEGORIES:
        badges.append("Metal")
    if element.get("category") in {"nonmetal", "halogen"}:
        badges.append("Ikke-metal")
    en = element.get("electronegativity")
    if isinstance(en, (int, float)) and en >= 3.0:
        badges.append("Hoj elektronegativitet")

    ox = element.get("oxidationStates") or []
    if ox:
        rendered = ", ".join(f"{int(v):+d}" for v in ox if isinstance(v, (int, float)))
        if rendered:
            badges.append(f"Oxidationstal: {rendered}")
    return badges


def _render_details_panel(selected: Optional[Dict[str, Any]]) -> None:
    st.markdown("### Elementdetaljer")
    if not selected:
        st.info("Vaelg et grundstof i tabellen for at se detaljer.")
        return

    st.markdown(f"#### {selected['name']} ({selected['symbol']})")
    badges = _badge_list(selected)
    if badges:
        st.caption(" | ".join(badges))

    st.markdown("**Grunddata**")
    st.markdown(f"- Atomnummer: {selected['atomicNumber']}")
    st.markdown(f"- Relativ atommasse: {format_value(selected.get('atomicMass'), 'g/mol')}")
    st.markdown(f"- Gruppe: {selected.get('group') if selected.get('group') is not None else 'Ikke angivet'}")
    st.markdown(f"- Periode: {selected.get('period') if selected.get('period') is not None else 'Ikke angivet'}")
    st.markdown(f"- Blok: {str(selected.get('block', 'Ikke angivet')).upper()}")
    st.markdown(f"- Kategori: {_category_label(str(selected.get('category', 'unknown')))}")
    st.markdown(f"- Standardtilstand: {_phase_label(str(selected.get('phase', 'ukendt')))}")

    st.markdown("**Elektronstruktur**")
    st.markdown(f"- Elektronkonfiguration: `{selected.get('electronConfiguration') or 'Ikke angivet'}`")
    shells = selected.get("shells") or []
    shell_text = ", ".join(str(value) for value in shells) if shells else "Ikke angivet"
    st.markdown(f"- Elektroner pr. skal: {shell_text}")
    ox_states = selected.get("oxidationStates") or []
    ox_text = ", ".join(f"{int(v):+d}" for v in ox_states if isinstance(v, (int, float)))
    st.markdown(f"- Typiske oxidationstal: {ox_text or 'Ikke angivet'}")

    st.markdown("**Periodiske egenskaber**")
    st.markdown(f"- Elektronegativitet (Pauling): {format_value(selected.get('electronegativity'))}")
    st.markdown(f"- 1. ioniseringsenergi: {format_value(selected.get('ionizationEnergy'), 'kJ/mol')}")
    st.markdown(f"- Atomradius (kovalent): {format_value(selected.get('atomicRadius'), 'pm')}")

    st.markdown("**Fysiske data**")
    st.markdown(f"- Smeltepunkt: {format_value(selected.get('meltingPoint'), 'K')}")
    st.markdown(f"- Kogepunkt: {format_value(selected.get('boilingPoint'), 'K')}")
    st.markdown(f"- Densitet: {format_value(selected.get('density'), 'g/cm^3')}")

    st.markdown("**Lewis-symbol**")
    valence = _valence_electrons(selected)
    st.markdown(
        _render_lewis_symbol_html(str(selected.get("symbol") or ""), valence, "pt-lewis-detail"),
        unsafe_allow_html=True,
    )
    st.caption(f"Valenselektroner: {valence}")

    st.markdown("**Kemi til eksamen**")
    exam_note = selected.get("examNotes") or "Ingen ekstra note angivet."
    st.markdown(exam_note)


def render_periodic_table_tab() -> None:
    """Render interactive periodic table tab content."""
    _render_css()

    elements = get_periodic_table_elements()
    by_symbol = _build_element_map(elements)

    st.markdown("### Interaktivt periodisk system")
    st.caption("Klik pa et grundstof i tabellen for detaljer. Hold musen over et felt for hurtig preview.")

    with st.container(border=True):
        col1, col2, col3 = st.columns([2.2, 1.1, 1.1])
        with col1:
            search = st.text_input(
                "Sog efter navn, symbol eller atomnummer",
                placeholder="fx oxygen, O eller 8",
                key="pt_search",
            )
        with col2:
            trend_label = st.selectbox("Trend-visning", list(TREND_OPTIONS.keys()), key="pt_trend")
        with col3:
            if st.button("Nulstil filtre", key="pt_reset"):
                st.session_state["pt_category_filter"] = []
                st.session_state["pt_block_filter"] = []
                st.session_state["pt_period_filter"] = []
                st.session_state["pt_group_filter"] = []
                st.session_state["pt_phase_filter"] = []
                st.session_state["pt_search"] = ""
                st.rerun()

        categories = sorted({_category_label(str(e["category"])) for e in elements})
        category_reverse = {_category_label(str(e["category"])): str(e["category"]) for e in elements}

        f1, f2, f3, f4, f5 = st.columns(5)
        with f1:
            category_values = st.multiselect("Kategori", categories, key="pt_category_filter")
        with f2:
            block_values = st.multiselect("Blok", ["s", "p", "d", "f"], key="pt_block_filter")
        with f3:
            period_values = st.multiselect("Periode", list(range(1, 8)), key="pt_period_filter")
        with f4:
            group_values = st.multiselect("Gruppe", list(range(1, 19)), key="pt_group_filter")
        with f5:
            phase_values = st.multiselect("Tilstand", ["solid", "liquid", "gas"], format_func=_phase_label, key="pt_phase_filter")

    selected_filters: Dict[str, Set[Any]] = {
        "category": {category_reverse[val] for val in category_values},
        "block": set(block_values),
        "period": set(period_values),
        "group": set(group_values),
        "phase": set(phase_values),
    }

    filtered = [
        element for element in elements
        if _matches_filters(element, selected_filters) and _matches_search(element, search)
    ]
    visible_symbols = {element["symbol"] for element in filtered}

    exact_matches = [
        element for element in filtered
        if search and search.strip().lower() in {element["symbol"].lower(), element["name"].lower(), str(element["atomicNumber"])}
    ]

    selected_symbol = st.session_state.get("pt_selected_symbol")
    if not selected_symbol and len(exact_matches) == 1:
        selected_symbol = exact_matches[0]["symbol"]
        st.session_state["pt_selected_symbol"] = selected_symbol

    if selected_symbol and selected_symbol not in by_symbol:
        selected_symbol = None

    trend_key = TREND_OPTIONS[trend_label]
    st.markdown(f"**Viser {len(filtered)} / {len(elements)} grundstoffer**")
    _render_legend(trend_key, filtered if filtered else elements)

    picked_raw = st.query_params.get("pt_pick")
    if isinstance(picked_raw, list):
        picked_raw = picked_raw[0] if picked_raw else None
    picked_symbol = str(picked_raw).strip() if picked_raw else ""
    if picked_symbol and picked_symbol in by_symbol:
        st.session_state["pt_selected_symbol"] = picked_symbol
        selected_symbol = picked_symbol

    with st.container():
        st.markdown("<div class='pt-shell'>", unsafe_allow_html=True)
        clicked = _render_clickable_grid(elements, visible_symbols, selected_symbol)
        st.markdown("</div>", unsafe_allow_html=True)

    if clicked and clicked in by_symbol:
        st.session_state["pt_selected_symbol"] = clicked
        selected_symbol = clicked
        try:
            st.query_params.pop("pt_pick")
        except Exception:
            pass
        st.rerun()

    selected = by_symbol.get(selected_symbol or "")
    _render_details_panel(selected)
